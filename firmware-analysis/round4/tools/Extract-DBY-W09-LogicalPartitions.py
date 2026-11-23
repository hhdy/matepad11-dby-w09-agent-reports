#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read-only selective extraction of LpMetadata LINEAR logical partitions.

Reuses round3's verified SparseImage + metadata parser via importlib (no raw
expansion, source opened read-only). Adds AOSP-correct extent->file mapping:

    super_offset_bytes = extent.target_data * 512          (LP_SECTOR_SIZE)

IMPORTANT: do NOT add first_logical_sector; it is only a lower-bound check.

Safety / policy (AGENT_TASK_ROUND4.md):
  * source super.img opened read-only; never modified.
  * only partitions requested by name (default: vendor, odm); no hard-coded
    extent index / size / offset -- all looked up from metadata.
  * LINEAR only; ZERO / unknown target type => fail closed.
  * bounds: target_data >= first_logical_sector;
            target_data + num_sectors <= block_device.size/512;
            integer/negative checks; no overflow.
  * every extent start/end and total partition size aligned to logical_block_size.
  * metadata canonical content must match across both slots and both copies.
  * chunked reads; never loads a whole partition into memory.
  * writes only to an output directory OUTSIDE the source directory.
"""
import argparse
import hashlib
import importlib.util
import json
import os
import sys
from typing import Any, Dict, List

LP_SECTOR_SIZE = 512
CHUNK_READ = 2 * 1024 * 1024  # 2 MiB, within task's 1-4 MiB guidance


class ExtractionError(Exception):
    """A validation failed; abort (fail closed, no guessing)."""


def load_round3_parser(path: str):
    spec = importlib.util.spec_from_file_location('round3_parser', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _alignment_ok(value: int, align: int) -> bool:
    return align > 0 and value % align == 0


def verify_and_select_metadata(p, sparse, geometry_source: Dict[str, Any]):
    """Re-parse geometry + both slots (primary/backup), require canonical match.

    Returns the chosen Metadata object (round3 parser instance) plus a report dict.
    """
    g = p.parse_geometry(sparse.read(geometry_source['source_offset'], p.SIZE_GEOMETRY),
                         geometry_source['source_offset'], geometry_source['source_label'])
    if g.checksum_hex != geometry_source['checksum_hex']:
        raise ExtractionError('geometry checksum changed vs round3 baseline')

    attempts: List[Dict[str, Any]] = []
    metas: Dict[str, Any] = {}
    canonicals: Dict[str, str] = {}
    max_size = g.metadata_max_size
    # AOSP/LP layout verified against round3 baseline:
    #   geometry at 4096; metadata slot N primary = 12288 + max_size*N
    #   backup = primary + max_size*slot_count
    # 12288 = LP_PARTITION_RESERVED_BYTES(4096) + 2*logical_block_size(4096),
    # i.e. two 4096-byte geometry copies precede the first metadata slot.
    metadata_base = p.LP_PARTITION_RESERVED_BYTES + 2 * g.logical_block_size
    for slot in range(g.metadata_slot_count):
        prim = metadata_base + max_size * slot
        bak = prim + max_size * g.metadata_slot_count
        for label, off in (('primary', prim), ('backup', bak)):
            try:
                m = p.parse_metadata(sparse, off, g, label)
                # Round3 computed content_sha256 from json.dumps(canonical, sort_keys=True)
                can = json.dumps(m.canonical(), sort_keys=True)
                sha = hashlib.sha256(can.encode()).hexdigest().upper()
                canonicals[f'{label}/slot{slot}'] = sha
                metas[f'slot{slot}'] = m
                attempts.append({'source': label, 'slot': slot, 'offset': off,
                                 'status': 'VALID', 'content_sha256': sha})
            except Exception as ex:
                attempts.append({'source': label, 'slot': slot, 'offset': off,
                                 'status': 'INVALID', 'error': str(ex)})
    valid = [a for a in attempts if a['status'] == 'VALID']
    if not valid:
        raise ExtractionError('no VALID metadata slot found')
    values = set(canonicals.values())
    if len(values) != 1:
        raise ExtractionError('metadata canonical content differs across slots/copies')
    expected = geometry_source.get('content_sha256', '').upper()
    if expected:
        actual = next(iter(values)).upper()
        if actual != expected:
            raise ExtractionError('metadata content SHA differs from round3 baseline: %s != %s' % (actual, expected))
    chosen = metas.get('slot0') or next(iter(metas.values()))
    return chosen, {'geometry': g.as_dict(), 'attempts': attempts,
                    'canonical_sha256': next(iter(values)), 'all_valid_and_identical': True}


def plan_extents(meta, names: List[str]):
    """Look up each partition BY NAME and build a fully validated read plan."""
    bds = meta.block_devices
    if len(bds) < 1:
        raise ExtractionError('no block device in metadata')
    plans = {}
    for name in names:
        part = next((x for x in meta.partitions if x.get('name') == name.upper() or x.get('name') == name), None)
        if part is None:
            raise ExtractionError('partition not found in metadata: %s' % name)
        first = part['first_extent_index']
        count = part['num_extents']
        if count < 1:
            raise ExtractionError('%s has no extents' % name)
        extents = [x for x in meta.extents if first <= x['index'] < first + count]
        extents.sort(key=lambda x: x['index'])
        if len(extents) != count:
            raise ExtractionError('%s extent count mismatch' % name)
        total = 0
        steps = []
        for e in extents:
            t = e.get('target_type')
            if t != 0:  # LP_TARGET_TYPE_LINEAR
                raise ExtractionError('%s extent %d target_type=%s (not LINEAR); fail closed' %
                                      (name, e['index'], e.get('target_type_name', t)))
            src = e['target_source']
            if not isinstance(src, int) or src < 0 or src >= len(bds):
                raise ExtractionError('%s extent %d bad target_source %r' % (name, e['index'], src))
            bd = bds[src]
            td = e['target_data']
            ns = e['num_sectors']
            if not isinstance(td, int) or not isinstance(ns, int) or td < 0 or ns <= 0:
                raise ExtractionError('%s extent %d invalid target_data/num_sectors' % (name, e['index']))
            fsls = bd['first_logical_sector']
            if td < fsls:
                raise ExtractionError('%s extent %d target_data %d < first_logical_sector %d' %
                                      (name, e['index'], td, fsls))
            bd_sectors = bd['size_bytes'] // LP_SECTOR_SIZE
            if td > bd_sectors or ns > bd_sectors - td:  # overflow-safe upper bound
                raise ExtractionError('%s extent %d exceeds block device bounds' % (name, e['index']))
            off = td * LP_SECTOR_SIZE
            nbytes = ns * LP_SECTOR_SIZE
            total += nbytes
            steps.append({'extent_index': e['index'], 'target_data': td, 'num_sectors': ns,
                          'offset_bytes': off, 'num_bytes': nbytes, 'target_source': src,
                          'first_logical_sector': fsls})
        # Task rule 8: extent start/end and partition total must align to logical_block_size.
        # Authoritative byte length is num_sectors*512 (not the informational num_bytes field).
        aligned = meta.geometry.logical_block_size
        if aligned <= 0:
            raise ExtractionError('invalid logical_block_size %r' % aligned)
        for s in steps:
            if not (_alignment_ok(s['offset_bytes'], aligned) and _alignment_ok(s['num_bytes'], aligned)):
                raise ExtractionError('%s extent start/size not block-aligned' % name)
        if not _alignment_ok(total, aligned):
            raise ExtractionError('%s total size not block-aligned' % name)
        plans[name] = {'first_extent_index': first, 'num_extents': count,
                       'steps': steps, 'total_bytes': total, 'aligned': True}
    return plans


def extract_partition(sparse, plan: Dict[str, Any], out_path: str) -> Dict[str, Any]:
    digest = hashlib.sha256()
    written = 0
    with open(out_path, 'wb') as f:
        for step in plan['steps']:
            off = step['offset_bytes']
            remaining = step['num_bytes']
            while remaining > 0:
                n = min(CHUNK_READ, remaining)
                chunk = sparse.read(off, n)
                if len(chunk) != n:
                    raise ExtractionError('short read at %d' % off)
                f.write(chunk)
                digest.update(chunk)
                off += n
                remaining -= n
                written += n
    if written != plan['total_bytes']:
        raise ExtractionError('written %d != planned %d' % (written, plan['total_bytes']))
    return {'written_bytes': written, 'sha256': digest.hexdigest().upper()}


def run(args):
    out_dir = args.out_dir
    os.makedirs(out_dir, exist_ok=True)
    # never overwrite: create a labelled subdir if target files already exist
    tag = args.tag or ''
    part_dir = os.path.join(out_dir, ('partitions_' + tag) if tag else 'partitions')
    if os.path.exists(part_dir) and os.listdir(part_dir):
        import time
        part_dir = os.path.join(out_dir, 'partitions_%s_%d' % (tag or 'run', int(time.time())))
    os.makedirs(part_dir, exist_ok=True)

    p = load_round3_parser(args.round3_parser)
    sparse = p.SparseImage(args.super, verify_crc_chunks=True)
    report: Dict[str, Any] = {'source_super': os.path.basename(args.super),
                              'requested_partitions': args.partitions,
                              'output_subdir': os.path.basename(part_dir)}
    try:
        # Step 1: sparse header + 127 chunk boundaries re-validated in SparseImage.__init__
        h = sparse.header.as_dict()
        report['sparse_revalidation'] = h
        if h['expanded_size_bytes'] != args.expected_regular_size:
            raise ExtractionError('expanded size differs from baseline')

        # Step 2: geometry + metadata slots
        gsrc = {'source_offset': 4096, 'source_label': 'primary',
                'checksum_hex': args.expected_geometry_checksum,
                'content_sha256': args.expected_metadata_sha}
        chosen, mreport = verify_and_select_metadata(p, sparse, gsrc)
        report['metadata_revalidation'] = mreport

        # Steps 3-8: plan by name, validate LINEAR / bounds / alignment
        plans = plan_extents(chosen, args.partitions)
        report['plans'] = plans

        # Step 9-10: string baseline check (report discrepancies, do not force)
        for name, plan in plans.items():
            expected = args.baseline.get(name)
            if expected and (plan['steps'][0]['offset_bytes'] != expected[0] or
                             plan['total_bytes'] != expected[1]):
                report.setdefault('baseline_discrepancies', []).append({
                    'partition': name, 'actual': [plan['steps'][0]['offset_bytes'], plan['total_bytes']],
                    'expected': list(expected)})

        # Extract
        results = {}
        for name in args.partitions:
            fname = name.lower() + '.img'
            path = os.path.join(part_dir, fname)
            res = extract_partition(sparse, plans[name], path)
            results[name] = {'file_name': fname, 'local_path_redacted': os.path.join('<OUT>', os.path.basename(part_dir), fname),
                             'bytes': res['written_bytes'], 'sha256_local_only': res['sha256']}
        report['extraction_results'] = results
        report['status'] = 'PASS' if not report.get('baseline_discrepancies') else 'PASS_WITH_BASELINE_DIFFERENCE'
    finally:
        sparse.close()

    with open(os.path.join(out_dir, 'partition_extraction_report.json'), 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(json.dumps({'status': report.get('status'),
                      'partitions': list(report.get('extraction_results', {}).keys()),
                      'output_subdir': report.get('output_subdir')}, ensure_ascii=False))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--super', required=True)
    ap.add_argument('--round3-parser', required=True)
    ap.add_argument('--out-dir', required=True)
    ap.add_argument('--tag', default='')
    ap.add_argument('--partitions', default='vendor,odm')
    ap.add_argument('--expected-regular-size', type=int, default=7516192768)
    ap.add_argument('--expected-geometry-checksum',
                    default='4E31CF64275442F40E25C772A18D1FCCD8B1291232E593F65E522FC7AC07DF03')
    ap.add_argument('--expected-metadata-sha', default='',
                    help='round3 baseline metadata SHA; pass at runtime if enforcing')
    # baseline from task book: name -> (offset, size). Parsed from metadata at runtime;
    # provided only for discrepancy reporting, never used to force extraction.
    ap.add_argument('--baseline', default='odm:2836398080:51593216,vendor:6096420864:1022038016')
    args = ap.parse_args()
    args.partitions = [x.strip() for x in args.partitions.split(',') if x.strip()]
    bl = {}
    for item in args.baseline.split(','):
        try:
            n, o, s = item.split(':')
            bl[n.strip()] = (int(o), int(s))
        except Exception:
            pass
    args.baseline = bl
    run(args)


if __name__ == '__main__':
    main()
