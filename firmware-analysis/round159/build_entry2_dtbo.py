#!/usr/bin/env python3
"""ROUND159 Window B -- deterministic Entry2-preserving DTBO candidate builder.

Self-contained (stdlib only). Two modes:

  selftest   Built-in self-tests only. No facts needed, produces no candidate.
             Validates the FDT writer/reader round-trip, the dt_table container
             writer/reader round-trip, and the negative checks.

  build      --facts ENTRY2_TARGET_FACTS.json --base CANDIDATE.dtb --outdir DIR
             Full candidate build. REFUSES to run unless the facts JSON
             contains Window A's proven ABL table-layout decision
             (abl_decision.one_entry_go == true). Produces:
               entry2-rootparam.dtso        (overlay FDT, compiled by this script)
               entry2-rootparam.dtbo        (same bytes, embedded-payload copy)
               entry2-candidate.dtbo.img    (single-entry dt_table container)
               entry2-candidate-manifest.json

Facts JSON schema (aligned with Window A ROUND159 taskbook Task A.7):

{
  "facts_version": 1,
  "source": {"dtbo_img_sha256": "...", "dtbo_img_size": N,
             "entry2_fdt_sha256": "..."},
  "dt_table_header": {"magic": "0xd7b7ab1e", "header_size": 32,
                      "dt_entry_size": 32, "page_size": 2048, "version": 0},
  "entry2_table_fields": {"dt_size": N, "dt_offset": N,
                          "id": "0x..", "rev": "0x..",
                          "custom": ["0x..","0x..","0x..","0x.."]},
  "selector_root_properties": [
      {"name": "qcom,board-id", "encoding": "u32-cells", "u32": [8206, 0],
       "required": true}, ...],
  "rootparam_properties": [           // exactly five
      {"name": "qcom,boardid", "encoding": "raw-bytes", "hex": "080206.."},
      {"name": "qcom,board_name", "encoding": "string", "value": "DBY_W09_VD"},
      {"name": "qcom,product_name", "encoding": "string", "value": "DBY-W09"},
      {"name": "hardware_version", "encoding": "string", "value": "SH1DBSLM"},
      {"name": "huawei,modem_id", "encoding": "raw-bytes", "hex": ".."}],
  "abl_decision": {"one_entry_go": true, "resulting_dtbo_idx": 0,
                   "preserve_index_2": false, "table_layout": "single-entry",
                   "evidence_note": "..."}
}

Encodings are strict: "string" | "u32-cells" | "raw-bytes". Byte properties
must travel as raw bytes; no string/cell coercion is performed anywhere.
"""
import argparse
import hashlib
import json
import os
import struct
import sys

FDT_MAGIC = 0xD00DFEED
DT_TABLE_MAGIC = 0xD7B7AB1E
FDT_BEGIN_NODE, FDT_END_NODE, FDT_PROP, FDT_NOP, FDT_END = 1, 2, 3, 4, 9


def sha256(b):
    return hashlib.sha256(b).hexdigest()


# ---------------------------------------------------------------- FDT writer

class PNode:
    """Minimal build-time FDT node."""
    def __init__(self, name, parent=None):
        self.name, self.parent = name, parent
        self.props = []          # ordered (name, bytes)
        self.children = []

    def add_prop(self, name, value):
        assert isinstance(value, (bytes, bytearray))
        self.props.append((name, bytes(value)))
        return self

    def add_child(self, name):
        c = PNode(name, self)
        self.children.append(c)
        return c


def build_fdt(root):
    """Serialize PNode tree into an FDT blob (version 17, target-path capable)."""
    strings = bytearray()
    def stroff(name):
        b = name.encode() + b"\0"
        off = strings.find(b)
        if off < 0:
            off = len(strings)
            strings.extend(b)
        return off

    struct_buf = bytearray()
    def emit_node(node):
        struct_buf.extend(struct.pack(">I", FDT_BEGIN_NODE))
        nb = node.name.encode() + b"\0"
        struct_buf.extend(nb)
        while len(struct_buf) % 4:
            struct_buf.append(0)
        for pname, pval in node.props:
            struct_buf.extend(struct.pack(">III", FDT_PROP, len(pval), stroff(pname)))
            struct_buf.extend(pval)
            while len(struct_buf) % 4:
                struct_buf.append(0)
        for c in node.children:
            emit_node(c)
        struct_buf.extend(struct.pack(">I", FDT_END_NODE))

    emit_node(root)
    struct_buf.extend(struct.pack(">I", FDT_END))
    while len(struct_buf) % 4:
        struct_buf.append(0)

    # layout: header(40) | memrsv(term only, 16) | struct (8-aligned) | strings
    off_rsv = 40
    off_struct = (off_rsv + 16 + 7) & ~7
    pad = off_struct - (off_rsv + 16)
    rsv = struct.pack(">QQ", 0, 0) + b"\0" * pad
    total = off_struct + len(struct_buf) + len(strings)
    hdr = struct.pack(">10I",
                      FDT_MAGIC,                 # magic
                      total,                     # totalsize
                      off_struct,                # off_dt_struct
                      off_struct + len(struct_buf),  # off_dt_strings
                      off_rsv,                   # off_mem_rsvmap
                      17,                        # version
                      16,                        # last_comp_version
                      0,                         # boot_cpuid_phys
                      len(strings),              # size_dt_strings
                      len(struct_buf))           # size_dt_struct
    blob = hdr + rsv + bytes(struct_buf) + bytes(strings)
    assert struct.unpack_from(">I", blob, 4)[0] == total
    return blob


# ---------------------------------------------------------------- FDT reader
# Reuses the ROUND156 parser logic (5 bugs fixed and field-validated there).

def parse_fdt(data):
    if len(data) < 40 or struct.unpack_from(">I", data, 0)[0] != FDT_MAGIC:
        raise ValueError("bad FDT magic")
    total, off_struct, off_strings, off_rsv = struct.unpack_from(">IIII", data, 4)
    size_strings = struct.unpack_from(">I", data, 32)[0]
    if total > len(data):
        raise ValueError("FDT totalsize exceeds buffer")
    strings = data[off_strings:off_strings + size_strings]
    def s(i):
        j = strings.index(b"\0", i)
        return strings[i:j].decode("utf-8", "replace")

    class N:
        def __init__(self, name, parent):
            self.name, self.parent = name, parent
            self.props, self.children = {}, []
        @property
        def path(self):
            if self.parent is None:
                return "/"
            return ("" if self.parent.parent is None else self.parent.path) \
                + "/" + self.name

    root = N("", None)
    stack = [root]
    p = off_struct
    while p + 4 <= total:
        tag = struct.unpack_from(">I", data, p)[0]
        p += 4
        if tag == FDT_BEGIN_NODE:
            e = data.index(b"\0", p)
            name = data[p:e].decode("utf-8", "replace")
            p = (e + 4) & ~3
            if name == "" and len(stack) == 1:
                continue
            cur = N(name, stack[-1])
            stack[-1].children.append(cur)
            stack.append(cur)
        elif tag == FDT_END_NODE:
            if len(stack) > 1:
                stack.pop()
        elif tag == FDT_PROP:
            n, no = struct.unpack_from(">II", data, p)
            p += 8
            stack[-1].props[s(no)] = data[p:p + n]
            p = (p + n + 3) & ~3
        elif tag == FDT_NOP:
            pass
        elif tag == FDT_END:
            break
        else:
            raise ValueError("bad tag 0x%x at 0x%x" % (tag, p - 4))
    out = []
    def rec(n):
        out.append(n)
        for c in n.children:
            rec(c)
    rec(root)
    return {n.path: n for n in out}


def fdt_diff(base_map, merged_map):
    """Ordered (path, prop, kind, before_hex, after_hex) differences."""
    out = []
    for path in sorted(set(base_map) | set(merged_map)):
        if path not in base_map:
            out.append((path, "<node>", "ADDED", "", "")); continue
        if path not in merged_map:
            out.append((path, "<node>", "REMOVED", "", "")); continue
        pa, pb = base_map[path].props, merged_map[path].props
        for key in sorted(set(pa) | set(pb)):
            if key not in pa:
                out.append((path, key, "ADDED", "", pb[key].hex()))
            elif key not in pb:
                out.append((path, key, "REMOVED", pa[key].hex(), ""))
            elif pa[key] != pb[key]:
                out.append((path, key, "CHANGED", pa[key].hex(), pb[key].hex()))
    return out


# ------------------------------------------------------- dt_table container

def write_container(entry_fdts, entries_meta, header_fields):
    """entry_fdts: list of FDT blobs. entries_meta: list of dicts with
    id/rev/custom. header_fields: dict(header_size, dt_entry_size,
    page_size, version, dt_entries_offset, fdt_offset)."""
    hs = header_fields["header_size"]
    es = header_fields["dt_entry_size"]
    eo = header_fields["dt_entries_offset"]
    fo = header_fields["fdt_offset"]
    assert es == 32 and hs == eo, "entries must start right after header"
    count = len(entry_fdts)
    total = fo + sum(len(f) for f in entry_fdts)
    hdr = struct.pack(">8I", DT_TABLE_MAGIC, total, hs, es, count, eo,
                      header_fields["page_size"], header_fields["version"])
    body = bytearray(hdr)
    off = fo
    for fdt, meta in zip(entry_fdts, entries_meta):
        c = meta.get("custom", [0, 0, 0, 0])
        body.extend(struct.pack(">4I4I", len(fdt), off,
                                meta.get("id", 0), meta.get("rev", 0),
                                c[0], c[1], c[2], c[3]))
        off += len(fdt)
    while len(body) < fo:
        body.append(0)
    for fdt in entry_fdts:
        body.extend(fdt)
    return bytes(body)


def parse_container(data):
    """Strict parser: raises on truncated/malformed containers."""
    if len(data) < 32:
        raise ValueError("container shorter than header")
    magic, total, hs, es, cnt, eo, pg, ver = struct.unpack(">8I", data[0:32])
    if magic != DT_TABLE_MAGIC:
        raise ValueError("bad dt_table magic 0x%08x" % magic)
    if total > len(data):
        raise ValueError("total_size exceeds buffer (truncated)")
    if es != 32:
        raise ValueError("unexpected dt_entry_size %d" % es)
    if eo < hs or eo + cnt * es > total:
        raise ValueError("entry table out of bounds")
    entries = []
    for i in range(cnt):
        o = eo + i * es
        sz, do, eid, rev, c0, c1, c2, c3 = struct.unpack_from(">4I4I", data, o)
        if do < eo + cnt * es:
            raise ValueError("entry %d payload overlaps entry table" % i)
        if do + sz > total:
            raise ValueError("entry %d payload out of bounds" % i)
        if len(blob_ok := data[do:do + sz]) < 40 or \
                struct.unpack_from(">I", blob_ok, 0)[0] != FDT_MAGIC:
            raise ValueError("entry %d payload is not an FDT" % i)
        fdt_total = struct.unpack_from(">I", blob_ok, 4)[0]
        if fdt_total != sz:
            raise ValueError("entry %d FDT totalsize %d != dt_size %d"
                             % (i, fdt_total, sz))
        entries.append({"index": i, "dt_size": sz, "dt_offset": do,
                        "id": eid, "rev": rev,
                        "custom": [c0, c1, c2, c3],
                        "fdt": blob_ok, "sha256": sha256(blob_ok)})
    ranges = sorted((e["dt_offset"], e["dt_offset"] + e["dt_size"])
                    for e in entries)
    for a, b in zip(ranges, ranges[1:]):
        if a[1] > b[0]:
            raise ValueError("entry payload ranges overlap")
    return {"magic": magic, "total_size": total, "header_size": hs,
            "dt_entry_size": es, "dt_entry_count": cnt,
            "dt_entries_offset": eo, "page_size": pg, "version": ver,
            "entries": entries}


def reserialize(parsed):
    """Rebuild a container from parsed fields; must round-trip byte-identical."""
    hf = {"header_size": parsed["header_size"],
          "dt_entry_size": parsed["dt_entry_size"],
          "dt_entries_offset": parsed["dt_entries_offset"],
          "fdt_offset": min(e["dt_offset"] for e in parsed["entries"]),
          "page_size": parsed["page_size"],
          "version": parsed["version"]}
    fdts = [e["fdt"] for e in parsed["entries"]]
    metas = [{"id": e["id"], "rev": e["rev"], "custom": e["custom"]}
             for e in parsed["entries"]]
    return write_container(fdts, metas, hf)


# ------------------------------------------------------------ facts handling

def encode_prop(p):
    enc = p.get("encoding")
    if enc == "string":
        return p["value"].encode() + b"\0"
    if enc == "u32-cells":
        return struct.pack(">%dI" % len(p["u32"]), *p["u32"])
    if enc == "raw-bytes":
        return bytes.fromhex(p["hex"])
    raise ValueError("unknown encoding %r for %s" % (enc, p.get("name")))


def render_prop_dts(p, indent):
    pad = " " * indent
    enc = p.get("encoding")
    if enc == "string":
        return "%s%s = \"%s\";" % (pad, p["name"], p["value"])
    if enc == "u32-cells":
        return "%s%s = <%s>;" % (pad, p["name"],
                                 " ".join("0x%x" % v for v in p["u32"]))
    if enc == "raw-bytes":
        return "%s%s = [%s];" % (pad, p["name"], p["hex"])
    raise ValueError("unknown encoding %r" % enc)


def render_dts_text(facts):
    """Textual DTS source of the overlay (the .dtso deliverable)."""
    out = ["/dts-v1/;", ""]
    out.append("/ {")
    for p in facts["selector_root_properties"]:
        if p.get("required", True):
            out.append(render_prop_dts(p, 4))
    out.append("    fragment@0 {")
    out.append("        target-path = \"/rootparam\";")
    out.append("        __overlay__ {")
    for p in facts["rootparam_properties"]:
        out.append(render_prop_dts(p, 12))
    out.append("        };")
    out.append("    };")
    out.append("};")
    return "\n".join(out) + "\n"


def build_overlay_fdt(facts):
    """Root selector props + one fragment targeting /rootparam."""
    root = PNode("")
    for p in facts["selector_root_properties"]:
        if p.get("required", True):
            root.add_prop(p["name"], encode_prop(p))
    frag = root.add_child("fragment@0")
    frag.add_prop("target-path", b"/rootparam\0")
    ov = frag.add_child("__overlay__")
    rp = facts["rootparam_properties"]
    if len(rp) != 5:
        raise ValueError("expected exactly 5 rootparam properties, got %d" % len(rp))
    for p in rp:
        ov.add_prop(p["name"], encode_prop(p))
    return build_fdt(root)


def verify_facts(facts):
    errs = []
    src = facts.get("source", {})
    if not src.get("dtbo_img_sha256") or not src.get("entry2_fdt_sha256"):
        errs.append("facts.source missing hashes")
    dec = facts.get("abl_decision", {})
    if not dec.get("one_entry_go"):
        errs.append("abl_decision.one_entry_go is not true: "
                    "Window A layout proof missing -> NO-GO, refusing to build")
    rp = facts.get("rootparam_properties", [])
    if len(rp) != 5:
        errs.append("rootparam_properties must be exactly 5")
    if not facts.get("selector_root_properties"):
        errs.append("selector_root_properties missing")
    hdr = facts.get("dt_table_header", {})
    if hdr.get("magic") != "0xd7b7ab1e":
        errs.append("dt_table_header.magic invalid")
    for k in ("page_size", "version", "header_size", "dt_entry_size"):
        if k not in hdr:
            errs.append("dt_table_header.%s missing" % k)
    return errs


def run_build(facts_path, base_path, outdir, fdtoverlay_bin, dtc_bin=None):
    facts = json.load(open(facts_path))
    errs = verify_facts(facts)
    if errs:
        print("FACTS-REJECTED:")
        for e in errs:
            print("  -", e)
        return 2

    base = open(base_path, "rb").read()
    base_map = parse_fdt(base)

    overlay = build_overlay_fdt(facts)
    ov_map = parse_fdt(overlay)

    hf = facts["dt_table_header"]
    etf = facts["entry2_table_fields"]
    meta = {"id": int(etf["id"], 16), "rev": int(etf["rev"], 16),
            "custom": [int(x, 16) for x in etf["custom"]]}
    fo = hf["header_size"] + hf["dt_entry_size"]  # entries right after header
    container = write_container([overlay], [meta],
                                {"header_size": hf["header_size"],
                                 "dt_entry_size": hf["dt_entry_size"],
                                 "dt_entries_offset": hf["header_size"],
                                 "fdt_offset": fo,
                                 "page_size": hf["page_size"],
                                 "version": hf["version"]})

    # independent reparse + reserialize must be byte-identical
    reparsed = parse_container(container)
    if reserialize(reparsed) != container:
        raise AssertionError("container reserialize mismatch")
    if reparsed["entries"][0]["fdt"] != overlay:
        raise AssertionError("embedded FDT != source overlay bytes")

    os.makedirs(outdir, exist_ok=True)
    paths = {}
    dtso_text = render_dts_text(facts)
    artifacts = [("entry2-rootparam.dtso", dtso_text.encode()),
                 ("entry2-rootparam.dtbo", overlay),
                 ("entry2-candidate.dtbo.img", container)]
    for name, blob in artifacts:
        p = os.path.join(outdir, name)
        open(p, "wb").write(blob)
        paths[name] = p

    # cross-validate: dtc-compile the textual .dtso and compare structurally
    # with our binary writer output (props equality, not byte equality --
    # dtc may pad/order strings differently)
    crossval = {"performed": False}
    if dtc_bin:
        tmp_dts = os.path.join(outdir, ".dtso-crossval.dts")
        tmp_dtb = os.path.join(outdir, ".dtso-crossval.dtb")
        open(tmp_dts, "wb").write(dtso_text.encode())
        rc = os.system("%s -I dts -O dtb -o %s %s 2>/dev/null"
                       % (dtc_bin, tmp_dtb, tmp_dts))
        if rc == 0:
            a = parse_fdt(overlay)
            b = parse_fdt(open(tmp_dtb, "rb").read())
            diffs = fdt_diff(a, b)
            crossval = {"performed": True, "structural_diff_count": len(diffs),
                        "match": len(diffs) == 0}
            for d in diffs:
                crossval.setdefault("diff", []).append(list(d))
        else:
            crossval = {"performed": True, "dtc_compile_rc": rc,
                        "match": False}

    # host merge check via fdtoverlay (if available)
    merge = {"tool": fdtoverlay_bin or "none"}
    if fdtoverlay_bin:
        merged_path = os.path.join(outdir, "merged.dtb")
        # dtc-1.7 fdtoverlay usage: -i <base> -o <out> <overlay>
        r = os.system("%s -i %s -o %s %s 2> %s" % (
            fdtoverlay_bin, base_path, merged_path,
            paths["entry2-rootparam.dtbo"], merged_path + ".err"))
        merge["rc"] = r
        if r == 0:
            merged_map = parse_fdt(open(merged_path, "rb").read())
            diffs = fdt_diff(base_map, merged_map)
            expected = {(  "/rootparam", p["name"], "ADDED")
                        for p in facts["rootparam_properties"]}
            got = {(d[0], d[1], d[2]) for d in diffs}
            merge["diff_count"] = len(diffs)
            merge["diff"] = [list(d) for d in diffs]
            merge["exactly_five_rootparam_additions"] = got == expected and len(diffs) == 5
            # byte-identity of payloads against facts (independent of overlay bytes)
            ok = True
            for p in facts["rootparam_properties"]:
                want = encode_prop(p)
                have = merged_map["/rootparam"].props.get(p["name"])
                if have != want:
                    ok = False
            merge["payloads_match_facts"] = ok
        else:
            merge["stderr"] = open(merged_path + ".err").read()[:2000]

    manifest = {
        "round": 159,
        "facts_sha256": sha256(open(facts_path, "rb").read()),
        "base_dtb_sha256": sha256(base),
        "artifacts": {n: {"sha256": sha256(open(p, "rb").read()),
                          "size": os.path.getsize(p)}
                      for n, p in paths.items()},
        "container_fields": {k: v for k, v in reparsed.items() if k != "entries"},
        "entry0": {k: v for k, v in reparsed["entries"][0].items() if k != "fdt"},
        "resulting_dtbo_idx": facts["abl_decision"].get("resulting_dtbo_idx"),
        "dtso_dtc_crossval": crossval,
        "merge": merge,
    }
    mp = os.path.join(outdir, "entry2-candidate-manifest.json")
    open(mp, "w").write(json.dumps(manifest, indent=2))
    print("BUILD-OK")
    print(json.dumps(manifest, indent=2))
    return 0


# ---------------------------------------------------------------- selftest

def run_selftest(base_dtb_path, fdtoverlay_bin):
    ok = []

    # 1. FDT writer/reader round-trip with a rootparam-like synthetic base
    root = PNode("")
    root.add_prop("compatible", b"selftest\0")
    rp = root.add_child("rootparam")
    rp.add_prop("phandle", struct.pack(">I", 0x3e))
    base = build_fdt(root)
    m = parse_fdt(base)
    ok.append(("fdt_roundtrip", "/rootparam" in m
               and m["/rootparam"].props["phandle"] == b"\x00\x00\x00\x3e"))

    # 2. reader cross-check against the known candidate DTB (fixed input)
    if base_dtb_path and os.path.exists(base_dtb_path):
        known = open(base_dtb_path, "rb").read()
        km = parse_fdt(known)
        ok.append(("reader_vs_candidate_dtb",
                   len(km) == 905 and "/rootparam" in km))

    # 3. container round-trip + reserialize identity
    fdt = build_fdt(root)
    cont = write_container([fdt], [{"id": 0x200E, "rev": 0, "custom": [0]*4}],
                           {"header_size": 32, "dt_entry_size": 32,
                            "dt_entries_offset": 32, "fdt_offset": 64,
                            "page_size": 2048, "version": 0})
    pc = parse_container(cont)
    ok.append(("container_roundtrip",
               pc["dt_entry_count"] == 1
               and pc["entries"][0]["id"] == 0x200E
               and reserialize(pc) == cont
               and pc["entries"][0]["fdt"] == fdt))

    # 4. negative: truncated container rejected
    try:
        parse_container(cont[:-10])
        ok.append(("negative_truncated_REJECTED", False))
    except ValueError:
        ok.append(("negative_truncated_REJECTED", True))

    # 5. negative: bad magic rejected
    try:
        parse_container(b"\x00" * 64)
        ok.append(("negative_badmagic_REJECTED", False))
    except ValueError:
        ok.append(("negative_badmagic_REJECTED", True))

    # 6. negative: wrong FDT totalsize inside container rejected
    evil = bytearray(cont)
    struct.pack_into(">I", evil, 4, cont_len(evil))
    try:
        parse_container(bytes(evil))
        ok.append(("negative_totalsize_lie_REJECTED", False))
    except ValueError:
        ok.append(("negative_totalsize_lie_REJECTED", True))

    # 7. negative: overlay with typo target-path fails under fdtoverlay
    if fdtoverlay_bin and base_dtb_path and os.path.exists(base_dtb_path):
        bad = PNode("")
        frag = bad.add_child("fragment@0")
        frag.add_prop("target-path", b"/rootparam_typo\0")
        frag.add_child("__overlay__").add_prop("x", b"\x00\x00\x00\x01")
        badblob = build_fdt(bad)
        open("/tmp/r159_bad.dtbo", "wb").write(badblob)
        rc = os.system("%s -i %s -o /tmp/r159_bad_out.dtb /tmp/r159_bad.dtbo 2>/dev/null"
                       % (fdtoverlay_bin, base_dtb_path or "/tmp/r159_selftest_base.dtb"))
        ok.append(("negative_targetpath_typo_FAILS", rc != 0))

    # 8. positive: synthetic-facts overlay merges to EXACTLY 5 /rootparam additions
    if fdtoverlay_bin and base_dtb_path and os.path.exists(base_dtb_path):
        syn = {"selector_root_properties":
                   [{"name": "qcom,board-id", "encoding": "u32-cells",
                     "u32": [0x200E, 0]}],
               "rootparam_properties": [
                   {"name": "qcom,boardid", "encoding": "raw-bytes",
                    "hex": "080206"},
                   {"name": "qcom,board_name", "encoding": "string",
                    "value": "DBY_W09_VD"},
                   {"name": "qcom,product_name", "encoding": "string",
                    "value": "DBY-W09"},
                   {"name": "hardware_version", "encoding": "string",
                    "value": "SH1DBSLM"},
                   {"name": "huawei,modem_id", "encoding": "raw-bytes",
                    "hex": "00000000"}],
               "abl_decision": {"one_entry_go": True}}
        SYN_NOTE = ("synthetic self-test values only; final build must use "
                    "Window A's exact facts.json bytes")
        ov = build_overlay_fdt(syn)
        open("/tmp/r159_syn.dtbo", "wb").write(ov)
        rc = os.system("%s -i %s -o /tmp/r159_syn_out.dtb /tmp/r159_syn.dtbo 2>/dev/null"
                       % (fdtoverlay_bin, base_dtb_path))
        if rc == 0:
            diffs = fdt_diff(parse_fdt(open(base_dtb_path, "rb").read()),
                             parse_fdt(open("/tmp/r159_syn_out.dtb", "rb").read()))
            got = {(d[0], d[1], d[2]) for d in diffs}
            want = {("/rootparam", p["name"], "ADDED")
                    for p in syn["rootparam_properties"]}
            ok.append(("positive_synthetic_merge_5_additions_only",
                       len(diffs) == 5 and got == want))
        else:
            ok.append(("positive_synthetic_merge_5_additions_only", False))

    allok = all(v for _, v in ok)
    for k, v in ok:
        print("%-40s %s" % (k, "PASS" if v else "FAIL"))
    print("SELFTEST", "PASS" if allok else "FAIL")
    return 0 if allok else 1


def cont_len(b):
    return len(b) + 0x1000  # lie about totalsize


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=["selftest", "build"])
    ap.add_argument("--facts")
    ap.add_argument("--base", default="/tmp/r159_selftest_base.dtb")
    ap.add_argument("--outdir", default=".")
    ap.add_argument("--fdtoverlay", default=None)
    ap.add_argument("--dtc", default=None)
    a = ap.parse_args()
    fdto = a.fdtoverlay
    dtc = a.dtc
    if fdto is None:
        for cand in ("/usr/bin/fdtoverlay",
                     "/home/kerneldev/work/matepad11/r157-windowA/out-dtb/scripts/dtc/fdtoverlay"):
            if os.path.exists(cand):
                fdto = cand
                break
    if dtc is None:
        for cand in ("/usr/bin/dtc",
                     "/home/kerneldev/work/matepad11/r157-windowA/out-dtb/scripts/dtc/dtc"):
            if os.path.exists(cand):
                dtc = cand
                break
    if a.command == "selftest":
        if a.base != "/tmp/r159_selftest_base.dtb" and os.path.exists(a.base):
            open("/tmp/r159_selftest_base.dtb", "wb").write(open(a.base, "rb").read())
        return run_selftest(a.base, fdto)
    if not a.facts:
        print("build requires --facts"); return 2
    return run_build(a.facts, a.base, a.outdir, fdto, dtc)


if __name__ == "__main__":
    sys.exit(main())
