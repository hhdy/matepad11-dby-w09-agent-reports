#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Synthetic unit tests for Analyze-DBY-W09-Super.py.

All fixtures are generated in a temporary directory; no real firmware is read.
Run: python Test-DBY-W09-SuperParser.py
Prints explicit PASS/FAIL per test and exits non-zero on any failure.
"""

import hashlib
import importlib.util
import json
import os
import struct
import sys
import tempfile
import zlib

_HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location(
    "super_parser", os.path.join(_HERE, "Analyze-DBY-W09-Super.py"))
A = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(A)

RESULTS = []


def check(name, cond, detail=""):
    ok = bool(cond)
    RESULTS.append((name, ok, detail))
    print(("PASS" if ok else "FAIL") + ": " + name + ((" | " + detail) if detail else ""))
    return ok


def expect_raises(fn, exc=A.VerificationError, label="expected error"):
    try:
        fn()
        return False, "no exception raised"
    except exc as e:
        return True, str(e)


# ---- sparse fixture builders ----------------------------------------------
def sparse_header(total_blks, total_chunks, blk_sz=4, checksum=0,
                  magic=A.SPARSE_HEADER_MAGIC, major=1, file_hdr_sz=28, chunk_hdr_sz=12):
    return struct.pack("<IHHHHIIII", magic, major, 0, file_hdr_sz, chunk_hdr_sz,
                       blk_sz, total_blks, total_chunks, checksum)


def chunk(ctype, chunk_sz, payload=b"", total_sz=None):
    if total_sz is None:
        total_sz = 12 + len(payload)
    return struct.pack("<HHII", ctype, 0, chunk_sz, total_sz) + payload


def write_sparse(path, chunks, total_blks, blk_sz=4):
    data = sparse_header(total_blks, len(chunks), blk_sz) + b"".join(chunks)
    with open(path, "wb") as f:
        f.write(data)
    return path


# ---- LP metadata fixture builders -----------------------------------------
def make_geometry(metadata_max_size=4096, slot_count=1, logical_block_size=4):
    g = struct.pack("<II", A.LP_METADATA_GEOMETRY_MAGIC, 52) + b"\0" * 32 + \
        struct.pack("<III", metadata_max_size, slot_count, logical_block_size)
    ck = hashlib.sha256(g).digest()
    return g[:8] + ck + g[40:]


def make_metadata(slot_count=1, metadata_max_size=4096, partitions=None,
                  extents=None, groups=None, block_devices=None,
                  minor=0, corrupt_header=None, corrupt_tables=None,
                  table_bad_offset=None, bad_entry_size=None, bad_extent_source=None):
    if partitions is None:
        partitions = [(b"system\0", 0, 0, 1, 0)]
    if extents is None:
        extents = [(100, A.LP_TARGET_TYPE_LINEAR, 0, 0)]
    if groups is None:
        groups = [(b"default\0", 0, 0)]
    if block_devices is None:
        block_devices = [(3072, 4, 0, 100000, b"super\0", 0)]

    part_bytes = b"".join(struct.pack("<36sIIII", *p) for p in partitions)
    ext_bytes = b"".join(struct.pack("<QIQI", *e) for e in extents)
    grp_bytes = b"".join(struct.pack("<36sIQ", *g) for g in groups)
    blk_bytes = b"".join(struct.pack("<QIIQ36sI", *b) for b in block_devices)

    # tables: group, extents, partitions, block_devices (offsets relative to end of header)
    off_part = 0
    off_ext = off_part + len(part_bytes)
    off_grp = off_ext + len(ext_bytes)
    off_blk = off_grp + len(grp_bytes)
    tables = part_bytes + ext_bytes + grp_bytes + blk_bytes
    tables_size = len(tables)
    tables_ck = hashlib.sha256(tables).digest()
    if corrupt_tables == "checksum":
        tables_ck = b"\x00" * 32

    header_size = 128 if minor < 2 else 256
    desc_part = struct.pack("<III", off_part, len(partitions), 52)
    desc_ext = struct.pack("<III", off_ext, len(extents), 24)
    desc_grp = struct.pack("<III", off_grp, len(groups), 48)
    desc_blk = struct.pack("<III", off_blk, len(block_devices), 64)
    if table_bad_offset == "partitions":
        desc_part = struct.pack("<III", tables_size + 1, len(partitions), 52)
    if bad_entry_size == "partitions":
        desc_part = struct.pack("<III", off_part, len(partitions), 999)
    if bad_extent_source:
        ext_bytes2 = b"".join(
            struct.pack("<QIQI", e[0], e[1], e[2], 99) for e in extents)
        # rebuild tables with fixed ext bytes
        off_ext2 = off_part + len(part_bytes)
        off_grp2 = off_ext2 + len(ext_bytes2)
        off_blk2 = off_grp2 + len(grp_bytes)
        tables = part_bytes + ext_bytes2 + grp_bytes + blk_bytes
        tables_size = len(tables)
        tables_ck = hashlib.sha256(tables).digest()
        desc_ext = struct.pack("<III", off_ext2, len(extents), 24)
        desc_grp = struct.pack("<III", off_grp2, len(groups), 48)
        desc_blk = struct.pack("<III", off_blk2, len(block_devices), 64)

    header = struct.pack("<IHHI", A.LP_METADATA_HEADER_MAGIC, 10, minor, header_size)
    header += b"\0" * 32  # header checksum placeholder
    header += struct.pack("<I", tables_size) + tables_ck
    header += desc_part + desc_ext + desc_grp + desc_blk
    header += b"\0" * (header_size - len(header))
    header_ck = hashlib.sha256(header).digest()
    if corrupt_header == "checksum":
        header_ck = b"\x11" * 32
    header = header[:12] + header_ck + header[44:]

    return header + tables


def wrap_sparse_from_metadata(md_bytes, blk_sz=4096):
    """Put metadata bytes into a sparse image via RAW chunk at logical 0."""
    total_blks = (len(md_bytes) + blk_sz - 1) // blk_sz
    payload = md_bytes + b"\0" * (total_blks * blk_sz - len(md_bytes))
    return write_sparse_bytes(sparse_header(total_blks, 1, blk_sz) +
                              chunk(A.CHUNK_TYPE_RAW, total_blks, payload), total_blks, blk_sz)


def write_sparse_bytes(data, total_blks, blk_sz):
    fd, path = tempfile.mkstemp(suffix=".img")
    with os.fdopen(fd, "wb") as f:
        f.write(data)
    return path, blk_sz * total_blks


def make_full_sparse_super(slot_count=1, metadata_max_size=4096):
    """Build a synthetic sparse super: geometry at 4096/8192, metadata at 12288."""
    blk_sz = 4096
    # geometry occupies block 1 (4096) and its backup block 2 (8192)
    geom = make_geometry(metadata_max_size, slot_count)
    geom_block = geom + b"\0" * (blk_sz - len(geom))
    md = make_metadata(slot_count=slot_count, metadata_max_size=metadata_max_size)
    md_pad = md + b"\0" * (metadata_max_size - len(md))
    logical_size = 12 * 1024 * 1024
    total_blks = logical_size // blk_sz
    # Use DONT_CARE for blocks 0,3.. then RAW for 1,2, metadata slots at block 3..
    chunks = []
    # block 0: dont care
    chunks.append(chunk(A.CHUNK_TYPE_DONT_CARE, 1))
    # blocks 1-2: raw geometry (2 blocks)
    chunks.append(chunk(A.CHUNK_TYPE_RAW, 2, geom_block * 2))
    # metadata primary at 12288 = block 3
    n_md_blks = metadata_max_size // blk_sz
    chunks.append(chunk(A.CHUNK_TYPE_RAW, n_md_blks, md_pad))
    # backup metadata area (slot_count blocks)
    chunks.append(chunk(A.CHUNK_TYPE_RAW, n_md_blks, md_pad))
    # rest dont care
    used = 1 + 2 + n_md_blks + n_md_blks
    chunks.append(chunk(A.CHUNK_TYPE_DONT_CARE, total_blks - used))
    data = sparse_header(total_blks, len(chunks), blk_sz) + b"".join(chunks)
    fd, path = tempfile.mkstemp(suffix="_super.img")
    with os.fdopen(fd, "wb") as f:
        f.write(data)
    return path


# ---- tests -----------------------------------------------------------------
def test_sparse_raw_fill_dontcare():
    blk = 4
    payload = b"ABCD"
    chunks = [
        chunk(A.CHUNK_TYPE_RAW, 1, payload),
        chunk(A.CHUNK_TYPE_FILL, 1, b"\x7f\0\0\0"),
        chunk(A.CHUNK_TYPE_DONT_CARE, 1),
    ]
    fd, path = tempfile.mkstemp(suffix=".img")
    with os.fdopen(fd, "wb") as f:
        f.write(sparse_header(3, 3, blk) + b"".join(chunks))
    try:
        with A.SparseImage(path) as s:
            check("sparse RAW read", s.read(0, 4) == b"ABCD", repr(s.read(0, 4)))
            check("sparse FILL read", s.read(4, 4) == b"\x7f\0\0\0", repr(s.read(4, 4)))
            check("sparse DONT_CARE read", s.read(8, 4) == b"\0\0\0\0")
            check("sparse cross-chunk read",
                  s.read(2, 8) == b"CD\x7f\0\0\0\0\0", repr(s.read(2, 8)))
    finally:
        os.unlink(path)


def test_sparse_crc32_chunk():
    blk = 4
    payload = b"ABCD"
    crc = zlib.crc32(payload) & 0xFFFFFFFF
    chunks = [
        chunk(A.CHUNK_TYPE_RAW, 1, payload),
        chunk(A.CHUNK_TYPE_CRC32, 0, struct.pack("<I", crc)),
    ]
    fd, path = tempfile.mkstemp(suffix=".img")
    with os.fdopen(fd, "wb") as f:
        f.write(sparse_header(1, 2, blk) + b"".join(chunks))
    try:
        with A.SparseImage(path) as s:
            check("sparse CRC32 chunk accepted",
                  len(s.crc_chunk_results) == 1 and s.crc_chunk_results[0]["match"],
                  json.dumps(s.crc_chunk_results))
    finally:
        os.unlink(path)


def test_sparse_bad_magic():
    fd, path = tempfile.mkstemp(suffix=".img")
    with os.fdopen(fd, "wb") as f:
        f.write(sparse_header(1, 0, magic=0xDEADBEEF))
    try:
        ok, detail = expect_raises(lambda: A.SparseImage(path))
        check("sparse bad magic rejected", ok, detail)
    finally:
        os.unlink(path)


def test_sparse_sum_blocks_mismatch():
    fd, path = tempfile.mkstemp(suffix=".img")
    with os.fdopen(fd, "wb") as f:
        f.write(sparse_header(5, 1, blk_sz=4) + chunk(A.CHUNK_TYPE_RAW, 1, b"ABCD"))
    try:
        ok, detail = expect_raises(lambda: A.SparseImage(path))
        check("sparse block total mismatch rejected", ok, detail)
    finally:
        os.unlink(path)


def test_sparse_raw_size_mismatch():
    fd, path = tempfile.mkstemp(suffix=".img")
    with os.fdopen(fd, "wb") as f:
        f.write(sparse_header(1, 1, blk_sz=4) + chunk(A.CHUNK_TYPE_RAW, 1, b"AB"))
    try:
        ok, detail = expect_raises(lambda: A.SparseImage(path))
        check("sparse RAW size mismatch rejected", ok, detail)
    finally:
        os.unlink(path)


def test_geometry_checksum():
    g = make_geometry()
    geo = A.parse_geometry(g, 4096, "primary")
    check("geometry checksum valid", geo.metadata_slot_count == 1, str(geo.metadata_max_size))
    bad = bytearray(g)
    bad[40] ^= 0xFF
    ok, detail = expect_raises(lambda: A.parse_geometry(bytes(bad), 4096, "primary"))
    check("geometry checksum rejection", ok, detail)


def test_metadata_full_parse():
    path = make_full_sparse_super(slot_count=1)
    try:
        with A.SparseImage(path) as s:
            g = A.parse_geometry(s.read(4096, 52), 4096, "primary")
            m = A.parse_metadata(s, 12288, g, "primary/slot0")
            check("metadata header checksum valid", True)
            check("partition parsed", len(m.partitions) == 1 and
                  m.partitions[0]["name"] == "system", json.dumps(m.partitions))
            check("group parsed", len(m.groups) == 1 and m.groups[0]["name"] == "default")
            check("block device parsed", len(m.block_devices) == 1 and
                  m.block_devices[0]["partition_name"] == "super", json.dumps(m.block_devices))
            check("extent parsed", len(m.extents) == 1 and
                  m.extents[0]["num_bytes"] == 100 * 512, json.dumps(m.extents))
    finally:
        os.unlink(path)


def test_metadata_corrupt_header_checksum():
    md = make_metadata(corrupt_header="checksum")
    path, _ = wrap_sparse_from_metadata(md)
    try:
        with A.SparseImage(path) as s:
            g = A.parse_geometry(make_geometry(), 0, "x")
            ok, detail = expect_raises(lambda: A.parse_metadata(s, 0, g, "bad"))
            check("metadata header checksum rejection", ok, detail)
    finally:
        os.unlink(path)


def test_metadata_corrupt_tables_checksum():
    md = make_metadata(corrupt_tables="checksum")
    path, _ = wrap_sparse_from_metadata(md)
    try:
        with A.SparseImage(path) as s:
            g = A.parse_geometry(make_geometry(), 0, "x")
            ok, detail = expect_raises(lambda: A.parse_metadata(s, 0, g, "bad"))
            check("metadata tables checksum rejection", ok, detail)
    finally:
        os.unlink(path)


def test_metadata_table_out_of_bounds():
    md = make_metadata(table_bad_offset="partitions")
    path, _ = wrap_sparse_from_metadata(md)
    try:
        with A.SparseImage(path) as s:
            g = A.parse_geometry(make_geometry(), 0, "x")
            ok, detail = expect_raises(lambda: A.parse_metadata(s, 0, g, "bad"))
            check("metadata table bounds rejection", ok, detail)
    finally:
        os.unlink(path)


def test_metadata_bad_entry_size():
    md = make_metadata(bad_entry_size="partitions")
    path, _ = wrap_sparse_from_metadata(md)
    try:
        with A.SparseImage(path) as s:
            g = A.parse_geometry(make_geometry(), 0, "x")
            ok, detail = expect_raises(lambda: A.parse_metadata(s, 0, g, "bad"))
            check("metadata entry_size rejection", ok, detail)
    finally:
        os.unlink(path)


def test_metadata_bad_extent_source():
    md = make_metadata(bad_extent_source=True)
    path, _ = wrap_sparse_from_metadata(md)
    try:
        with A.SparseImage(path) as s:
            g = A.parse_geometry(make_geometry(), 0, "x")
            ok, detail = expect_raises(lambda: A.parse_metadata(s, 0, g, "bad"))
            check("metadata extent block-device index rejection", ok, detail)
    finally:
        os.unlink(path)


def test_slot_identical_and_diff():
    p1 = make_full_sparse_super(slot_count=2)
    try:
        with A.SparseImage(p1) as s:
            g = A.parse_geometry(s.read(4096, 52), 4096, "primary")
            m0 = A.parse_metadata(s, 12288, g, "slot0")
            m1 = A.parse_metadata(s, 12288 + g.metadata_max_size, g, "slot1")
            check("two slots canonical identical", m0.canonical() == m1.canonical())
            check("slot content sha256 stable",
                  hashlib.sha256(json.dumps(m0.canonical(), sort_keys=True).encode()).hexdigest() ==
                  hashlib.sha256(json.dumps(m1.canonical(), sort_keys=True).encode()).hexdigest())
    finally:
        os.unlink(p1)


def main():
    tests = [
        test_sparse_raw_fill_dontcare,
        test_sparse_crc32_chunk,
        test_sparse_bad_magic,
        test_sparse_sum_blocks_mismatch,
        test_sparse_raw_size_mismatch,
        test_geometry_checksum,
        test_metadata_full_parse,
        test_metadata_corrupt_header_checksum,
        test_metadata_corrupt_tables_checksum,
        test_metadata_table_out_of_bounds,
        test_metadata_bad_entry_size,
        test_metadata_bad_extent_source,
        test_slot_identical_and_diff,
    ]
    for t in tests:
        try:
            t()
        except Exception as e:
            check(t.__name__ + " (unexpected exception)", False, repr(e))
    total = len(RESULTS)
    passed = sum(1 for _, ok, _ in RESULTS if ok)
    print("\nTOTAL=%d PASS=%d FAIL=%d" % (total, passed, total - passed))
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
