#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Read-only Android sparse + logical-partition metadata analyzer for
Huawei MatePad 11 DBY-W09 HarmonyOS 4.3 super.img.

Implements with the Python 3 standard library only:
  * Android sparse image virtual random-access reader (no full expansion)
  * LpMetadataGeometry / LpMetadataHeader / partition tables parser

Format and validation rules follow the official AOSP sources verbatim:
  system/core/fs_mgr/liblp/include/liblp/metadata_format.h
  system/core/fs_mgr/liblp/reader.cpp
  system/core/fs_mgr/liblp/utility.cpp
  system/core/libsparse/sparse_format.h
  system/core/libsparse/sparse_read.cpp

Safety: opens the source read-only, never writes to it, never extracts
partition binaries, never computes a whole-image hash. Any failed validation
raises VerificationError and aborts that branch (no guessing, no skipping).
"""

import argparse
import bisect
import csv
import hashlib
import json
import os
import struct
import sys
import zlib
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any

# ---------------------------------------------------------------------------
# Constants (AOSP)
# ---------------------------------------------------------------------------
SPARSE_HEADER_MAGIC = 0xED26FF3A
CHUNK_TYPE_RAW = 0xCAC1
CHUNK_TYPE_FILL = 0xCAC2
CHUNK_TYPE_DONT_CARE = 0xCAC3
CHUNK_TYPE_CRC32 = 0xCAC4
CHUNK_TYPE_NAMES = {
    CHUNK_TYPE_RAW: "RAW",
    CHUNK_TYPE_FILL: "FILL",
    CHUNK_TYPE_DONT_CARE: "DONT_CARE",
    CHUNK_TYPE_CRC32: "CRC32",
}

LP_METADATA_GEOMETRY_MAGIC = 0x616C4467
LP_METADATA_GEOMETRY_SIZE = 4096
LP_METADATA_HEADER_MAGIC = 0x414C5030
LP_METADATA_MAJOR_VERSION = 10
LP_METADATA_MINOR_VERSION_MAX = 2
LP_METADATA_VERSION_FOR_UPDATED_ATTR = 1
LP_METADATA_VERSION_FOR_EXPANDED_HEADER = 2
LP_SECTOR_SIZE = 512
LP_PARTITION_RESERVED_BYTES = 4096

LP_TARGET_TYPE_LINEAR = 0
LP_TARGET_TYPE_ZERO = 1

LP_PARTITION_ATTR_READONLY = 1 << 0
LP_PARTITION_ATTR_SLOT_SUFFIXED = 1 << 1
LP_PARTITION_ATTR_UPDATED = 1 << 2
LP_PARTITION_ATTR_DISABLED = 1 << 3
LP_PARTITION_ATTRIBUTE_MASK_V0 = LP_PARTITION_ATTR_READONLY | LP_PARTITION_ATTR_SLOT_SUFFIXED
LP_PARTITION_ATTRIBUTE_MASK_V1 = LP_PARTITION_ATTR_UPDATED | LP_PARTITION_ATTR_DISABLED

SIZE_GEOMETRY = 52
SIZE_HEADER_V1_0 = 128
SIZE_HEADER_V1_2 = 256
SIZE_PARTITION = 52
SIZE_EXTENT = 24
SIZE_GROUP = 48
SIZE_BLOCK_DEVICE = 64
EXPECT_ENTRY = {"partitions": SIZE_PARTITION, "extents": SIZE_EXTENT,
                "groups": SIZE_GROUP, "block_devices": SIZE_BLOCK_DEVICE}


class VerificationError(Exception):
    """A structural / checksum / bounds check failed; abort that branch."""


def hx(data: bytes) -> str:
    return data.hex().upper()


def fixed_name(raw: bytes) -> str:
    """AOSP NameFromFixedArray: null-terminated if last byte is 0, else whole buffer."""
    if not raw:
        return ""
    if raw[-1] == 0:
        return raw.split(b"\0", 1)[0].decode("ascii", "replace")
    return raw.decode("ascii", "replace")


# ---------------------------------------------------------------------------
# Sparse image virtual reader
# ---------------------------------------------------------------------------
@dataclass
class SparseHeader:
    magic: int
    major_version: int
    minor_version: int
    file_hdr_sz: int
    chunk_hdr_sz: int
    blk_sz: int
    total_blks: int
    total_chunks: int
    image_checksum: int

    def as_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["magic_hex"] = "0x%08X" % self.magic
        d["image_checksum_hex"] = "0x%08X" % self.image_checksum
        d["expanded_size_bytes"] = self.blk_sz * self.total_blks
        return d


@dataclass
class Chunk:
    index: int
    chunk_type: int
    type_name: str
    chunk_sz: int
    total_sz: int
    data_size: int
    file_header_offset: int
    file_data_offset: int
    output_block_start: int
    fill_bytes_hex: Optional[str] = None
    crc32_value: Optional[int] = None


class SparseImage:
    """Read-only random access over an Android sparse image."""

    def __init__(self, path: str, verify_crc_chunks: bool = True):
        self.path = path
        self.f = open(path, "rb")
        self.chunks: List[Chunk] = []
        self._block_starts: List[int] = []
        self.crc_chunk_results: List[Dict[str, Any]] = []
        self.file_size = os.fstat(self.f.fileno()).st_size
        try:
            self.header = self._parse_header()
            self._scan_chunks()
            if verify_crc_chunks:
                self._verify_crc_chunks()
        except Exception:
            self.f.close()
            raise

    def close(self):
        if self.f and not self.f.closed:
            self.f.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def _parse_header(self) -> SparseHeader:
        self.f.seek(0)
        raw = self.f.read(28)
        if len(raw) != 28:
            raise VerificationError("sparse header short read: %d bytes" % len(raw))
        (magic, major, minor, file_hdr_sz, chunk_hdr_sz, blk_sz,
         total_blks, total_chunks, image_checksum) = struct.unpack("<IHHHHIIII", raw)
        if magic != SPARSE_HEADER_MAGIC:
            raise VerificationError("bad sparse magic 0x%08X" % magic)
        if major > 1:
            raise VerificationError("unsupported sparse major version %d" % major)
        if file_hdr_sz < 28:
            raise VerificationError("file_hdr_sz %d < 28" % file_hdr_sz)
        if chunk_hdr_sz < 12:
            raise VerificationError("chunk_hdr_sz %d < 12" % chunk_hdr_sz)
        if blk_sz == 0 or blk_sz % 4 != 0:
            raise VerificationError("invalid blk_sz %d" % blk_sz)
        if total_blks == 0:
            raise VerificationError("total_blks is 0")
        if file_hdr_sz > self.file_size:
            raise VerificationError("file_hdr_sz exceeds file size")
        return SparseHeader(magic, major, minor, file_hdr_sz, chunk_hdr_sz,
                            blk_sz, total_blks, total_chunks, image_checksum)

    def _scan_chunks(self):
        h = self.header
        pos = h.file_hdr_sz
        out_block = 0
        for i in range(h.total_chunks):
            if pos + h.chunk_hdr_sz > self.file_size:
                raise VerificationError("chunk %d header beyond EOF" % i)
            self.f.seek(pos)
            chraw = self.f.read(h.chunk_hdr_sz)
            if len(chraw) < 12:
                raise VerificationError("chunk %d short header" % i)
            ctype, reserved, chunk_sz, total_sz = struct.unpack("<HHII", chraw[:12])
            if total_sz < h.chunk_hdr_sz:
                raise VerificationError("chunk %d total_sz < chunk_hdr_sz" % i)
            data_size = total_sz - h.chunk_hdr_sz
            data_off = pos + h.chunk_hdr_sz
            if data_off + data_size > self.file_size:
                raise VerificationError("chunk %d data beyond EOF" % i)

            fill_hex = None
            crc_val = None
            if ctype == CHUNK_TYPE_RAW:
                if data_size != chunk_sz * h.blk_sz:
                    raise VerificationError(
                        "RAW chunk %d data_size %d != chunk_sz*blk_sz %d" %
                        (i, data_size, chunk_sz * h.blk_sz))
            elif ctype == CHUNK_TYPE_FILL:
                if data_size != 4:
                    raise VerificationError("FILL chunk %d data_size != 4" % i)
                self.f.seek(data_off)
                fill_hex = hx(self.f.read(4))
            elif ctype == CHUNK_TYPE_DONT_CARE:
                if data_size != 0:
                    raise VerificationError("DONT_CARE chunk %d data_size != 0" % i)
            elif ctype == CHUNK_TYPE_CRC32:
                if chunk_sz != 0:
                    raise VerificationError("CRC32 chunk %d chunk_sz != 0" % i)
                if data_size != 4:
                    raise VerificationError("CRC32 chunk %d data_size != 4" % i)
                self.f.seek(data_off)
                crc_val = struct.unpack("<I", self.f.read(4))[0]
            else:
                raise VerificationError("chunk %d unknown type 0x%04X" % (i, ctype))

            self.chunks.append(Chunk(i, ctype, CHUNK_TYPE_NAMES[ctype], chunk_sz,
                                     total_sz, data_size, pos, data_off, out_block,
                                     fill_hex, crc_val))
            if chunk_sz:
                self._block_starts.append(out_block)
            out_block += chunk_sz
            pos += total_sz

        if out_block != h.total_blks:
            raise VerificationError("sum(chunk_sz)=%d != total_blks=%d" %
                                    (out_block, h.total_blks))
        self._final_file_pos = pos

    def _verify_crc_chunks(self):
        crc_chunks = [c for c in self.chunks if c.chunk_type == CHUNK_TYPE_CRC32]
        if not crc_chunks:
            return
        h = self.header
        running = 0
        for c in self.chunks:
            if c.chunk_type == CHUNK_TYPE_CRC32:
                stored = c.crc32_value
                actual = running & 0xFFFFFFFF
                ok = (stored == actual)
                self.crc_chunk_results.append({
                    "chunk_index": c.index,
                    "stored_crc32_hex": "0x%08X" % stored,
                    "computed_crc32_hex": "0x%08X" % actual,
                    "match": ok,
                })
                if not ok:
                    raise VerificationError(
                        "CRC32 chunk %d mismatch: stored 0x%08X computed 0x%08X" %
                        (c.index, stored, actual))
                running = 0
                continue
            if c.chunk_sz == 0:
                continue
            logical_start = c.output_block_start * h.blk_sz
            total = c.chunk_sz * h.blk_sz
            step = 4 * 1024 * 1024
            off = 0
            while off < total:
                n = min(step, total - off)
                running = zlib.crc32(self.read(logical_start + off, n), running)
                off += n

    def _chunk_for_block(self, block_index: int) -> Chunk:
        i = bisect.bisect_right(self._block_starts, block_index) - 1
        if i < 0 or i >= len(self._block_starts):
            raise VerificationError("block %d out of chunk range" % block_index)
        # _block_starts contains only chunks with chunk_sz>0 in order; map back.
        nonzero = [c for c in self.chunks if c.chunk_sz > 0]
        c = nonzero[i]
        if not (c.output_block_start <= block_index < c.output_block_start + c.chunk_sz):
            raise VerificationError("block %d not covered by chunk %d" %
                                    (block_index, c.index))
        return c

    def read(self, offset: int, size: int) -> bytes:
        """Read `size` bytes from the unsparse logical image at `offset`."""
        if offset < 0 or size < 0:
            raise VerificationError("negative read offset/size")
        total_logical = self.header.blk_sz * self.header.total_blks
        if offset + size > total_logical:
            raise VerificationError("read beyond logical image size")
        h = self.header
        out = bytearray()
        cur = offset
        remaining = size
        while remaining > 0:
            block_index = cur // h.blk_sz
            c = self._chunk_for_block(block_index)
            chunk_end = (c.output_block_start + c.chunk_sz) * h.blk_sz
            n = min(remaining, chunk_end - cur)
            rel = cur - c.output_block_start * h.blk_sz
            if c.chunk_type == CHUNK_TYPE_RAW:
                self.f.seek(c.file_data_offset + rel)
                part = self.f.read(n)
                if len(part) != n:
                    raise VerificationError("short RAW read at logical %d" % cur)
                out.extend(part)
            elif c.chunk_type == CHUNK_TYPE_FILL:
                pattern = bytes.fromhex(c.fill_bytes_hex)
                out.extend(pattern[(rel + k) % 4] for k in range(n))
            elif c.chunk_type == CHUNK_TYPE_DONT_CARE:
                out.extend(b"\0" * n)
            else:
                raise VerificationError("unexpected chunk type in read")
            cur += n
            remaining -= n
        return bytes(out)


# ---------------------------------------------------------------------------
# LP metadata structures
# ---------------------------------------------------------------------------
@dataclass
class Geometry:
    magic: int
    struct_size: int
    checksum_hex: str
    metadata_max_size: int
    metadata_slot_count: int
    logical_block_size: int
    source_offset: int
    source_label: str

    def as_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["magic_hex"] = "0x%08X" % self.magic
        return d


@dataclass
class Descriptor:
    offset: int
    num_entries: int
    entry_size: int

    def as_dict(self):
        return asdict(self)


@dataclass
class Metadata:
    source_label: str
    source_offset: int
    geometry: Geometry
    header: Dict[str, Any]
    validation: Dict[str, str]
    partitions: List[Dict[str, Any]]
    extents: List[Dict[str, Any]]
    groups: List[Dict[str, Any]]
    block_devices: List[Dict[str, Any]]

    def as_dict(self) -> Dict[str, Any]:
        return {
            "source_label": self.source_label,
            "source_offset_bytes": self.source_offset,
            "geometry": self.geometry.as_dict(),
            "header": self.header,
            "counts": {
                "partitions": len(self.partitions),
                "extents": len(self.extents),
                "groups": len(self.groups),
                "block_devices": len(self.block_devices),
            },
            "validation": self.validation,
            "partitions": self.partitions,
            "extents": self.extents,
            "groups": self.groups,
            "block_devices": self.block_devices,
        }

    def canonical(self) -> Dict[str, Any]:
        """Comparable content for slot diffing (exclude source/checksum cosmetics)."""
        return {
            "partitions": self.partitions,
            "extents": self.extents,
            "groups": self.groups,
            "block_devices": self.block_devices,
            "header_flags": self.header.get("flags"),
        }


def parse_geometry(raw: bytes, source_offset: int, source_label: str) -> Geometry:
    if len(raw) < SIZE_GEOMETRY:
        raise VerificationError("geometry short read")
    magic, struct_size = struct.unpack_from("<II", raw, 0)
    checksum = raw[8:40]
    mms, msc, lbs = struct.unpack_from("<III", raw, 40)
    if magic != LP_METADATA_GEOMETRY_MAGIC:
        raise VerificationError("bad geometry magic 0x%08X" % magic)
    if struct_size > SIZE_GEOMETRY:
        raise VerificationError("geometry struct_size %d > %d" % (struct_size, SIZE_GEOMETRY))
    tmp = bytearray(raw[:struct_size])
    tmp[8:40] = b"\0" * 32
    if hashlib.sha256(tmp).digest() != checksum:
        raise VerificationError("geometry checksum mismatch")
    if struct_size != SIZE_GEOMETRY:
        raise VerificationError("geometry struct_size != %d" % SIZE_GEOMETRY)
    if msc == 0:
        raise VerificationError("geometry metadata_slot_count == 0")
    if mms % LP_SECTOR_SIZE != 0:
        raise VerificationError("metadata_max_size not sector aligned")
    return Geometry(magic, struct_size, hx(checksum), mms, msc, lbs,
                    source_offset, source_label)


def _descriptor(buf: bytes, off: int) -> Descriptor:
    o, n, e = struct.unpack_from("<III", buf, off)
    return Descriptor(o, n, e)


def _check_table_bounds(tables_size: int, d: Descriptor) -> bool:
    if d.offset > tables_size:
        return False
    return tables_size - d.offset >= d.num_entries * d.entry_size


def parse_metadata(sparse: SparseImage, offset: int, geometry: Geometry,
                   source_label: str) -> Metadata:
    head = sparse.read(offset, SIZE_HEADER_V1_0)
    magic, major, minor = struct.unpack_from("<IHH", head, 0)
    if magic != LP_METADATA_HEADER_MAGIC:
        raise VerificationError("bad metadata header magic 0x%08X" % magic)
    if major != LP_METADATA_MAJOR_VERSION:
        raise VerificationError("metadata major version %d != %d" %
                                (major, LP_METADATA_MAJOR_VERSION))
    if minor > LP_METADATA_MINOR_VERSION_MAX:
        raise VerificationError("metadata minor version %d > %d" %
                                (minor, LP_METADATA_MINOR_VERSION_MAX))
    expected = (SIZE_HEADER_V1_2 if minor >= LP_METADATA_VERSION_FOR_EXPANDED_HEADER
                else SIZE_HEADER_V1_0)
    header_bytes = sparse.read(offset, expected)
    header_size = struct.unpack_from("<I", header_bytes, 8)[0]
    if header_size != expected:
        raise VerificationError("header_size %d != expected %d" % (header_size, expected))
    stored_header_cksum = header_bytes[12:44]
    tmp = bytearray(header_bytes[:header_size])
    tmp[12:44] = b"\0" * 32
    if hashlib.sha256(tmp).digest() != stored_header_cksum:
        raise VerificationError("metadata header checksum mismatch")

    tables_size = struct.unpack_from("<I", header_bytes, 44)[0]
    stored_tables_cksum = header_bytes[48:80]
    if tables_size > geometry.metadata_max_size:
        raise VerificationError("tables_size exceeds metadata_max_size")

    descs = {
        "partitions": _descriptor(header_bytes, 80),
        "extents": _descriptor(header_bytes, 92),
        "groups": _descriptor(header_bytes, 104),
        "block_devices": _descriptor(header_bytes, 116),
    }
    for name, d in descs.items():
        if not _check_table_bounds(tables_size, d):
            raise VerificationError("table %s out of bounds" % name)
        if d.entry_size != EXPECT_ENTRY[name]:
            raise VerificationError("table %s entry_size %d != %d" %
                                    (name, d.entry_size, EXPECT_ENTRY[name]))

    tables = sparse.read(offset + header_size, tables_size)
    if hashlib.sha256(tables).digest() != stored_tables_cksum:
        raise VerificationError("metadata tables checksum mismatch")

    def rows(name, unpack_fmt):
        d = descs[name]
        size = EXPECT_ENTRY[name]
        for i in range(d.num_entries):
            yield struct.unpack_from(unpack_fmt, tables, d.offset + i * size)

    valid_attrs = LP_PARTITION_ATTRIBUTE_MASK_V0
    if minor >= LP_METADATA_VERSION_FOR_UPDATED_ATTR:
        valid_attrs |= LP_PARTITION_ATTRIBUTE_MASK_V1

    partitions = []
    for name_b, attrs, first_ext, num_ext, grp in rows("partitions", "<36sIIII"):
        if attrs & ~valid_attrs:
            raise VerificationError("partition has invalid attributes 0x%X" % attrs)
        if first_ext + num_ext < first_ext:
            raise VerificationError("partition extent index overflow")
        if first_ext + num_ext > descs["extents"].num_entries:
            raise VerificationError("partition extent list out of range")
        if grp >= descs["groups"].num_entries:
            raise VerificationError("partition group index out of range")
        partitions.append({
            "name": fixed_name(name_b), "attributes": attrs,
            "attributes_hex": "0x%08X" % attrs, "group_index": grp,
            "first_extent_index": first_ext, "num_extents": num_ext,
        })

    extents = []
    for i, (num_sectors, target_type, target_data, target_source) in \
            enumerate(rows("extents", "<QIQI")):
        if target_type not in (LP_TARGET_TYPE_LINEAR, LP_TARGET_TYPE_ZERO):
            raise VerificationError("extent unknown target_type %d" % target_type)
        if target_type == LP_TARGET_TYPE_LINEAR and \
                target_source >= descs["block_devices"].num_entries:
            raise VerificationError("extent target_source >= block device count")
        extents.append({
            "index": i, "num_sectors": num_sectors,
            "num_bytes": num_sectors * LP_SECTOR_SIZE,
            "target_type": target_type,
            "target_type_name": "LINEAR" if target_type == LP_TARGET_TYPE_LINEAR else "ZERO",
            "target_data": target_data, "target_source": target_source,
        })

    groups = []
    for name_b, flags, max_size in rows("groups", "<36sIQ"):
        groups.append({"name": fixed_name(name_b), "flags": flags,
                       "maximum_size_bytes": max_size})

    block_devices = []
    for first_sector, align, align_off, size, name_b, flags in rows("block_devices", "<QIIQ36sI"):
        block_devices.append({
            "first_logical_sector": first_sector, "alignment": align,
            "alignment_offset": align_off, "size_bytes": size,
            "partition_name": fixed_name(name_b), "flags": flags,
        })

    if not block_devices:
        raise VerificationError("metadata has no block devices")

    metadata_region = (LP_PARTITION_RESERVED_BYTES +
                       (LP_METADATA_GEOMETRY_SIZE + geometry.metadata_max_size *
                        geometry.metadata_slot_count) * 2)
    first_logical = block_devices[0]["first_logical_sector"] * LP_SECTOR_SIZE
    if metadata_region > first_logical:
        raise VerificationError("metadata region overlaps logical partition area")

    header = {
        "magic": "0x%08X" % magic,
        "major_version": major, "minor_version": minor,
        "header_size": header_size,
        "header_checksum_hex": hx(stored_header_cksum),
        "tables_size": tables_size,
        "tables_checksum_hex": hx(stored_tables_cksum),
        "flags": struct.unpack_from("<I", header_bytes, 128)[0] if header_size > 128 else 0,
        "descriptors": {k: v.as_dict() for k, v in descs.items()},
    }
    validation = {
        "geometry_checksum": "PASS", "header_checksum": "PASS",
        "tables_checksum": "PASS", "table_bounds": "PASS",
        "entry_sizes": "PASS", "extent_refs": "PASS",
        "group_refs": "PASS", "attribute_mask": "PASS",
        "metadata_logical_overlap": "PASS",
    }
    return Metadata(source_label, offset, geometry, header, validation,
                    partitions, extents, groups, block_devices)


# ---------------------------------------------------------------------------
# Reporting / CLI
# ---------------------------------------------------------------------------
def write_text(path, lines):
    with open(path, "w", encoding="utf-8", newline="\r\n") as f:
        f.write("\n".join(lines) + "\n")


def write_json(path, obj):
    with open(path, "w", encoding="utf-8", newline="\r\n") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write("\n")


def run(args):
    out = args.out
    os.makedirs(out, exist_ok=True)

    with SparseImage(args.super, verify_crc_chunks=True) as sp:
        h = sp.header
        type_counts = {}
        for c in sp.chunks:
            type_counts[c.type_name] = type_counts.get(c.type_name, 0) + 1

        val_lines = [
            "DBY-W09 super.img - read-only sparse validation",
            "source_size_bytes: %d" % sp.file_size,
            "sparse_header: " + json.dumps(h.as_dict(), sort_keys=True),
            "chunk_type_counts: " + json.dumps(type_counts, sort_keys=True),
            "sum_chunk_blocks: %d (expected %d)" % (sum(c.chunk_sz for c in sp.chunks), h.total_blks),
            "all_chunk_headers_in_bounds: PASS",
            "all_chunk_data_sizes_valid: PASS",
            "all_chunk_data_in_bounds: PASS",
            "logical_block_total_check: PASS",
        ]
        if sp.crc_chunk_results:
            val_lines.append("crc32_chunks: " + json.dumps(sp.crc_chunk_results, sort_keys=True))
            val_lines.append("crc32_chunk_verification: PASS")
        else:
            val_lines.append("crc32_chunks: none present")
        val_lines += ["full_image_expansion: NOT PERFORMED",
                      "full_image_hash: NOT COMPUTED"]

        # geometry: primary, fallback backup
        geom_errors = {}
        geometry = None
        for label, off in (("primary", LP_PARTITION_RESERVED_BYTES),
                           ("backup", LP_PARTITION_RESERVED_BYTES + LP_METADATA_GEOMETRY_SIZE)):
            try:
                geometry = parse_geometry(sp.read(off, SIZE_GEOMETRY), off, label)
                break
            except VerificationError as e:
                geom_errors[label] = str(e)
        if geometry is None:
            write_text(os.path.join(out, "super_sparse_validation.txt"), val_lines)
            write_json(os.path.join(out, "super_metadata_slots_summary.json"),
                       {"status": "BLOCKED", "geometry_errors": geom_errors})
            print("GEOMETRY BLOCKED: %s" % geom_errors, file=sys.stderr)
            return 2

        val_lines += [
            "geometry_source: %s @ %d" % (geometry.source_label, geometry.source_offset),
            "geometry_magic: 0x%08X" % geometry.magic,
            "geometry_struct_size: %d" % geometry.struct_size,
            "geometry_checksum_hex: %s" % geometry.checksum_hex,
            "metadata_max_size: %d" % geometry.metadata_max_size,
            "metadata_slot_count: %d" % geometry.metadata_slot_count,
            "logical_block_size: %d" % geometry.logical_block_size,
        ]
        write_text(os.path.join(out, "super_sparse_validation.txt"), val_lines)

        slot_summaries = []
        valid_metas = []
        for slot in range(geometry.metadata_slot_count):
            base = LP_PARTITION_RESERVED_BYTES + LP_METADATA_GEOMETRY_SIZE * 2
            p_off = base + geometry.metadata_max_size * slot
            b_off = base + geometry.metadata_max_size * geometry.metadata_slot_count + \
                    geometry.metadata_max_size * slot
            attempts = []
            chosen = None
            for label, off in (("primary", p_off), ("backup", b_off)):
                try:
                    meta = parse_metadata(sp, off, geometry, "%s/slot%d" % (label, slot))
                    attempts.append({"source": label, "offset": off, "status": "VALID"})
                    if chosen is None:
                        chosen = meta
                except VerificationError as e:
                    attempts.append({"source": label, "offset": off,
                                     "status": "FAIL", "reason": str(e)})
            if chosen is None:
                slot_summaries.append({
                    "slot": slot, "primary_offset": p_off, "backup_offset": b_off,
                    "status": "BLOCKED", "attempts": attempts,
                })
                continue
            obj = chosen.as_dict()
            obj["attempts"] = attempts
            write_json(os.path.join(out, "super_metadata_slot%d.json" % slot), obj)
            valid_metas.append(chosen)
            slot_summaries.append({
                "slot": slot, "primary_offset": p_off, "backup_offset": b_off,
                "status": "VALID", "chosen_source": chosen.source_label,
                "attempts": attempts,
                "partition_count": len(chosen.partitions),
                "extent_count": len(chosen.extents),
                "group_count": len(chosen.groups),
                "block_device_count": len(chosen.block_devices),
                "partition_names": [p["name"] for p in chosen.partitions],
                "group_names": [g["name"] for g in chosen.groups],
                "content_sha256": hashlib.sha256(
                    json.dumps(chosen.canonical(), sort_keys=True).encode()).hexdigest().upper(),
            })

        if len(valid_metas) >= 2:
            identical = all(m.canonical() == valid_metas[0].canonical() for m in valid_metas)
        elif len(valid_metas) == 1:
            identical = True
        else:
            identical = None
        write_json(os.path.join(out, "super_metadata_slots_summary.json"), {
            "geometry": geometry.as_dict(),
            "slot_count": geometry.metadata_slot_count,
            "slots": slot_summaries,
            "slots_content_identical": identical,
            "note": "Both primary and backup attempts are recorded per slot. "
                    "No slot was silently selected as 'correct'; differences are reported by content_sha256.",
            "partition_extraction": "NOT PERFORMED",
            "binary_upload": "NOT PERFORMED",
        })

        csv_path = os.path.join(out, "super_partition_summary.csv")
        with open(csv_path, "w", encoding="utf-8", newline="") as f:
            fields = ["slot", "partition_name", "attributes", "group_index", "group_name",
                      "first_extent_index", "num_extents", "total_size_bytes", "extent_details"]
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            for mi, meta in enumerate(valid_metas):
                for p in meta.partitions:
                    exts = [e for e in meta.extents
                            if p["first_extent_index"] <= e["index"] <
                            p["first_extent_index"] + p["num_extents"]]
                    w.writerow({
                        "slot": slot_summaries[mi]["slot"],
                        "partition_name": p["name"],
                        "attributes": p["attributes_hex"],
                        "group_index": p["group_index"],
                        "group_name": meta.groups[p["group_index"]]["name"],
                        "first_extent_index": p["first_extent_index"],
                        "num_extents": p["num_extents"],
                        "total_size_bytes": sum(e["num_bytes"] for e in exts),
                        "extent_details": "; ".join(
                            "idx=%d type=%s sectors=%d target_data=%d target_source=%d" %
                            (e["index"], e["target_type_name"], e["num_sectors"],
                             e["target_data"], e["target_source"]) for e in exts),
                    })

        print("sparse=PASS chunks=%d slots=%d valid_slots=%d" %
              (len(sp.chunks), geometry.metadata_slot_count, len(valid_metas)))
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--super", required=True, help="path to super.img (read-only)")
    ap.add_argument("--out", required=True, help="output directory (outside source)")
    return run(ap.parse_args())


if __name__ == "__main__":
    sys.exit(main())
