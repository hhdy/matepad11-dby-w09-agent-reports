#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Read-only device-tree extractor/validator for DBY-W09 boot.img and dtbo.img.

DTBO entry offsets/sizes are read from the round2 firmware_analysis.txt report
(never hard-coded). Source images are opened read-only; only small extracted
FDT work copies are written to the local output directory and are NEVER
uploaded.

Implements FDT header validation, structure-block token decoding, string-table
reference checks, and extraction of key node/property evidence.
"""

import argparse
import csv
import json
import os
import re
import struct
import sys
from dataclasses import dataclass, field

FDT_MAGIC = 0xD00DFEED
FDT_BEGIN_NODE = 1
FDT_END_NODE = 2
FDT_PROP = 3
FDT_NOP = 4
FDT_END = 9

# Key property names requested by the task.
KEY_PROPS = {
    "model", "compatible", "status", "qcom,msm-id", "qcom,board-id",
    "qcom,pmic-id", "__symbols__", "__fixups__", "__local_fixups__",
}
# Key node path substrings (case-insensitive).
KEY_NODE_HINTS = (
    "panel", "dsi", "display", "touch", "spi", "i2c", "regulator",
    "gpio", "pinctrl", "clock", "qcom", "soc", "chosen", "memory",
)


class DTError(Exception):
    pass


def hx(b):
    return b.hex().upper()


@dataclass
class FDT:
    source: str
    entry_index: int
    offset: int
    size: int
    valid: bool
    validation: str
    header: dict = field(default_factory=dict)
    model: str = ""
    compatible: str = ""
    key_nodes: list = field(default_factory=list)
    key_props: dict = field(default_factory=dict)
    overlay_meta: dict = field(default_factory=dict)
    candidate: bool = False


def parse_fdt_header(blob):
    if len(blob) < 40:
        raise DTError("FDT blob shorter than 40 bytes")
    fields = struct.unpack_from(">IIIIIIIIII", blob, 0)
    (magic, totalsize, off_dt_struct, off_dt_strings, off_mem_rsvmap,
     version, last_comp, boot_cpuid, size_dt_strings, size_dt_struct) = fields
    if magic != FDT_MAGIC:
        raise DTError("bad FDT magic 0x%08X" % magic)
    if totalsize > len(blob):
        raise DTError("totalsize %d > blob %d" % (totalsize, len(blob)))
    if version < 16 or last_comp > version:
        raise DTError("unsupported FDT version %d/%d" % (version, last_comp))
    struct_end = off_dt_struct + size_dt_struct
    strings_end = off_dt_strings + size_dt_strings
    if struct_end > totalsize or strings_end > totalsize:
        raise DTError("FDT block end beyond totalsize")
    if off_dt_struct < 40 or off_dt_strings < 40:
        raise DTError("FDT block offsets overlap header")
    return {
        "magic": "0x%08X" % magic, "totalsize": totalsize,
        "off_dt_struct": off_dt_struct, "off_dt_strings": off_dt_strings,
        "off_mem_rsvmap": off_mem_rsvmap, "version": version,
        "last_comp_version": last_comp, "boot_cpuid_phys": boot_cpuid,
        "size_dt_strings": size_dt_strings, "size_dt_struct": size_dt_struct,
    }


def decode_structure(blob, hdr):
    """Decode FDT structure block; returns (nodes, props, errors)."""
    off = hdr["off_dt_struct"]
    end = off + hdr["size_dt_struct"]
    strbase = hdr["off_dt_strings"]
    strend = strbase + hdr["size_dt_strings"]
    stack = []
    nodes = []
    props = {}
    path_parts = []
    errors = []
    depth = 0
    seen_end = False
    while off < end:
        if off + 4 > end:
            errors.append("token header beyond struct end")
            break
        token = struct.unpack_from(">I", blob, off)[0]
        off += 4
        if token == FDT_BEGIN_NODE:
            # name is null-terminated, aligned to 4
            name_end = blob.find(b"\0", off, end)
            if name_end < 0:
                errors.append("unterminated BEGIN_NODE name")
                break
            name = blob[off:name_end].decode("utf-8", "replace")
            off = (name_end + 1 + 3) & ~3
            if off > end:
                errors.append("BEGIN_NODE padding beyond end")
                break
            depth += 1
            if depth > 64:
                errors.append("node depth > 64")
                break
            path_parts.append(name or "/")
            path = "/" + "/".join(p for p in path_parts if p not in ("/", ""))
            nodes.append({"path": path, "depth": depth})
        elif token == FDT_END_NODE:
            if depth == 0:
                errors.append("END_NODE with depth 0")
                break
            depth -= 1
            if path_parts:
                path_parts.pop()
        elif token == FDT_NOP:
            continue
        elif token == FDT_PROP:
            if off + 8 > end:
                errors.append("PROP header beyond end")
                break
            length, nameoff = struct.unpack_from(">II", blob, off)
            off += 8
            if off + length > end:
                errors.append("PROP value beyond struct end")
                break
            value = blob[off:off + length]
            off = (off + length + 3) & ~3
            if nameoff >= hdr["size_dt_strings"]:
                errors.append("PROP nameoff beyond strings block")
                break
            ns = strbase + nameoff
            ne = blob.find(b"\0", ns, strend)
            if ne < 0:
                errors.append("unterminated property name")
                break
            pname = blob[ns:ne].decode("ascii", "replace")
            path = "/" + "/".join(p for p in path_parts if p not in ("/", ""))
            entry = {"path": path, "name": pname, "length": length}
            # decode string/stringlist/u32 values when possible
            if length >= 4 and length % 4 == 0 and all(
                    b == 0 for b in value[:1]):
                pass
            if length > 0 and value[-1] == 0 and b"\0" not in value[:-1]:
                entry["string"] = value[:-1].decode("utf-8", "replace")
            elif length > 0 and value.count(b"\0") > 1 and value[-1] == 0:
                entry["stringlist"] = [s.decode("utf-8", "replace")
                                       for s in value.split(b"\0") if s]
            if pname in ("model", "compatible") and "string" not in entry and "stringlist" not in entry:
                entry["raw_hex"] = hx(value)
            if length % 4 == 0 and length <= 64:
                entry["u32_values"] = [struct.unpack_from(">I", value, i)[0]
                                       for i in range(0, length, 4)]
            props.setdefault(path, {})[pname] = entry
        elif token == FDT_END:
            seen_end = True
            break
        else:
            errors.append("unknown token 0x%08X at offset %d" % (token, off - 4))
            break
    if not seen_end and not errors:
        errors.append("FDT END token not reached")
    if depth != 0 and not errors:
        errors.append("unclosed nodes at end (depth=%d)" % depth)
    return nodes, props, errors


def analyze_blob(blob, source, entry_index, offset, size, candidate=False):
    d = FDT(source, entry_index, offset, size, False, "", candidate=candidate)
    try:
        hdr = parse_fdt_header(blob[:size] if size else blob)
        d.header = hdr
        nodes, props, errors = decode_structure(blob[:hdr["totalsize"]], hdr)
        if errors:
            d.validation = "FAIL: " + "; ".join(errors[:3])
            return d
        model = ""
        compat = ""
        for p, entries in props.items():
            if "model" in entries and not model:
                e = entries["model"]
                model = e.get("string", e.get("raw_hex", ""))
            if "compatible" in entries and not compat:
                e = entries["compatible"]
                compat = e.get("string", e.get("stringlist", [""])[0]
                               if "stringlist" in e else e.get("raw_hex", ""))
        d.model = str(model)
        d.compatible = str(compat)
        for n in nodes:
            p = n["path"].lower()
            if any(h in p for h in KEY_NODE_HINTS):
                d.key_nodes.append({"path": n["path"], "depth": n["depth"],
                                    "props": sorted(props.get(n["path"], {}).keys())})
        for p, entries in props.items():
            for pname, e in entries.items():
                if pname in KEY_PROPS or any(h in pname.lower() for h in
                                             ("panel", "touch", "status", "regulator", "clock")):
                    d.key_props.setdefault(p, {})[pname] = e
        for meta in ("__symbols__", "__fixups__", "__local_fixups__"):
            for p, entries in props.items():
                if meta in entries:
                    d.overlay_meta[meta] = {"path": p, "length": entries[meta]["length"]}
        d.valid = True
        d.validation = "VALID"
    except DTError as e:
        d.validation = "FAIL: " + str(e)
    return d


def read_dtbo_entries(report_path):
    """Parse DTBO entry size/offset/id/rev from round2 report (no hard-coded values)."""
    text = open(report_path, encoding="utf-8-sig").read()
    entries = {}
    pat = re.compile(r"DTBO_ENTRY_(\d+):\s*SIZE_BYTES=(\d+)\s+OFFSET=(\d+)\s+"
                     r"ID=(0x[0-9A-Fa-f]+)\s+REV=(0x[0-9A-Fa-f]+)")
    for m in pat.finditer(text):
        entries[int(m.group(1))] = {
            "size": int(m.group(2)), "offset": int(m.group(3)),
            "id": m.group(4), "rev": m.group(5),
        }
    total = re.search(r"DTBO_TOTAL_SIZE_BYTES:\s*(\d+)", text)
    return entries, int(total.group(1)) if total else None


def find_fdt_candidates(data, label, expected_size=None, expected_range=None):
    """Scan for FDT headers; only report those passing full header validation."""
    found = []
    magic = struct.pack(">I", FDT_MAGIC)
    start = 0
    while True:
        idx = data.find(magic, start)
        if idx < 0:
            break
        start = idx + 1
        if idx + 40 > len(data):
            continue
        try:
            hdr = parse_fdt_header(data[idx:])
        except DTError:
            continue
        if expected_size and hdr["totalsize"] != expected_size:
            continue
        if expected_range and not (expected_range[0] <= idx < expected_range[1]):
            continue
        found.append((idx, hdr["totalsize"]))
    return found


def run(args):
    out = args.out
    work = os.path.join(out, "dtb_work")
    os.makedirs(work, exist_ok=True)

    # --- DTBO entries from round2 report ---
    entries, total_size = read_dtbo_entries(args.round2_report)
    if not entries:
        print("No DTBO entries found in round2 report", file=sys.stderr)
        return 2
    indices = sorted(entries)
    report_lines = [
        "DBY-W09 device tree extraction and validation",
        "DTBO entry source: round2 firmware_analysis.txt (offsets/sizes read, not hand-typed)",
        "DTBO entry count from report: %d" % len(entries),
        "DTBO total_size from report: %s" % total_size,
    ]
    inventory = []
    dtbo_data = open(args.dtbo, "rb").read()
    report_lines.append("DTBO source size: %d bytes" % len(dtbo_data))
    fdt_objects = []

    for i in indices:
        e = entries[i]
        off, size = e["offset"], e["size"]
        bound_ok = (off >= 0 and size > 0 and off + size <= len(dtbo_data) and
                    (total_size is None or off + size <= total_size))
        if not bound_ok:
            report_lines.append("DTBO entry %d: BOUNDS FAIL off=%d size=%d" % (i, off, size))
            inventory.append([ "dtbo.img", i, off, size, "BOUNDS_FAIL", "", "", e["id"], e["rev"] ])
            continue
        blob = dtbo_data[off:off + size]
        d = analyze_blob(blob, "dtbo.img", i, off, size)
        d.id = e["id"]
        d.rev = e["rev"]
        # local work copy only
        wp = os.path.join(work, "dtbo_entry_%d.dtbo" % i)
        with open(wp, "wb") as f:
            f.write(blob)
        fdt_objects.append(d)
        report_lines.append(
            "DTBO entry %d: off=%d size=%d id=%s rev=%s validation=%s model=%r compatible=%r" %
            (i, off, size, e["id"], e["rev"], d.validation, d.model, d.compatible))
        inventory.append(["dtbo.img", i, off, size, d.validation,
                          d.model, d.compatible, e["id"], e["rev"]])

    # --- boot.img DTB candidates ---
    boot_data = open(args.boot, "rb").read()
    report_lines.append("")
    report_lines.append("BOOT.IMG scan: size=%d bytes" % len(boot_data))
    if args.boot_dtb_range:
        lo, hi = [int(x) for x in args.boot_dtb_range.split(":")]
        cands = find_fdt_candidates(boot_data, "boot.img",
                                    expected_range=(lo, hi))
        report_lines.append("Search window: [%d, %d)" % (lo, hi))
        report_lines.append("Window origin derived from Android boot header v2 layout: "
                            "page_size + align_up(page_size + kernel_size, page_size) + "
                            "align_up(ramdisk_start + ramdisk_size, page_size).")
        report_lines.append("Note: round2 DTB_SIZE_BYTES is the boot-header DTB region size "
                            "(incl. padding); the actual FDT totalsize is smaller, so no "
                            "exact size filter is applied - every FDT magic in the window "
                            "is header-validated and reported.")
    else:
        cands = find_fdt_candidates(boot_data, "boot.img")
        report_lines.append("Full-file raw FDT magic scan (no window constraint)")
    report_lines.append("Valid FDT candidates found: %d" % len(cands))
    for n, (off, sz) in enumerate(cands):
        d = analyze_blob(boot_data[off:off + sz], "boot.img", n, off, sz, candidate=True)
        fdt_objects.append(d)
        wp = os.path.join(work, "boot_fdt_candidate_%d.dtb" % n)
        with open(wp, "wb") as f:
            f.write(boot_data[off:off + sz])
        report_lines.append(
            "BOOT FDT candidate %d: offset=%d size=%d validation=%s model=%r compatible=%r" %
            (n, off, sz, d.validation, d.model, d.compatible))
        inventory.append(["boot.img", n, off, sz, d.validation + " (candidate)",
                          d.model, d.compatible, "", ""])

    # --- write outputs ---
    with open(os.path.join(out, "device_tree_inventory.csv"), "w",
              encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["source_image", "entry_index", "offset", "size_bytes",
                    "fdt_validation", "model", "compatible", "dtbo_id", "dtbo_rev"])
        w.writerows(inventory)

    with open(os.path.join(out, "device_tree_analysis.txt"), "w",
              encoding="utf-8", newline="\r\n") as f:
        f.write("\n".join(report_lines) + "\n")
        f.write("\n=== KEY NODES / PROPERTIES PER FDT ===\n")
        for d in fdt_objects:
            f.write("\n[%s entry %d @ %d size %d] %s\n" %
                    (d.source, d.entry_index, d.offset, d.size, d.validation))
            f.write("  header: %s\n" % json.dumps(d.header, sort_keys=True))
            f.write("  model=%r compatible=%r\n" % (d.model, d.compatible))
            for n in d.key_nodes[:40]:
                f.write("  NODE %s depth=%d props=%s\n" %
                        (n["path"], n["depth"], ",".join(n["props"][:12])))
            for p, entries in list(d.key_props.items())[:40]:
                for pname, e in entries.items():
                    f.write("  PROP %s :: %s = %s\n" % (p, pname, json.dumps(e, ensure_ascii=False)))
            if d.overlay_meta:
                f.write("  OVERLAY_META: %s\n" % json.dumps(d.overlay_meta, sort_keys=True))

    print("dtbo_entries=%d boot_fdt_candidates=%d" %
          (len([d for d in fdt_objects if d.source == "dtbo.img"]),
           len([d for d in fdt_objects if d.source == "boot.img"])))
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--round2-report", required=True)
    ap.add_argument("--dtbo", required=True)
    ap.add_argument("--boot", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--boot-dtb-size", default="")
    ap.add_argument("--boot-dtb-range", default="", help="lo:hi absolute byte window")
    return run(ap.parse_args())


if __name__ == "__main__":
    sys.exit(main())
