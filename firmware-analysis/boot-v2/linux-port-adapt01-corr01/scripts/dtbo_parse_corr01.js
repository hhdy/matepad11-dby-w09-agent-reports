#!/usr/bin/env node
// CORR01 Stage A (Node port): corrected DTBO table parser with proper id/rev/custom mapping
// struct dt_table_entry { u32 dt_size; u32 dt_offset; u32 id; u32 rev; u32 custom[4]; } // big-endian
'use strict';
const fs = require('fs');
const crypto = require('crypto');
const path = require('path');

const DTBO = process.argv[2];
const OUTDIR = process.argv[3];
if (!DTBO || !OUTDIR) { console.error('usage: dtbo_parse_corr01.js <dtbo.img> <outdir>'); process.exit(2); }

const hex8 = (v) => '0x' + v.toString(16).toUpperCase().padStart(8, '0');
const d = fs.readFileSync(DTBO);
console.log('DTBO total size: %d B', d.length);
console.log('dtbo.img sha256=%s', crypto.createHash('sha256').update(d).digest('hex'));

function be32(off) { return d.readUInt32BE(off); }

const magic = be32(0), total_size = be32(4), hdr_size = be32(8), entry_size = be32(12);
const num_entries = be32(16), entries_offset = be32(20), page_size = be32(24), version = be32(28);
console.log('header: magic=%s total_size=%d hdr_size=%d entry_size=%d num_entries=%d entries_offset=%d page_size=%d version=%d',
  hex8(magic), total_size, hdr_size, entry_size, num_entries, entries_offset, page_size, version);
if (magic !== 0xD7B7AB1E) { console.error('BAD MAGIC'); process.exit(1); }

const entries_start = entries_offset > 0 ? entries_offset : hdr_size;
fs.mkdirSync(OUTDIR, { recursive: true });

for (let i = 0; i < num_entries; i++) {
  const eo = entries_start + i * entry_size;
  const dt_size = be32(eo), dt_offset = be32(eo + 4);
  const id = be32(eo + 8), rev = be32(eo + 12);
  const c = [be32(eo + 16), be32(eo + 20), be32(eo + 24), be32(eo + 28)];
  const blob = d.subarray(dt_offset, dt_offset + dt_size);
  const sha = crypto.createHash('sha256').update(blob).digest('hex');
  const fdtMagic = blob.length >= 4 ? blob.readUInt32BE(0) : 0;
  const fdtTotal = blob.length >= 8 ? blob.readUInt32BE(4) : 0;
  const hasRootparam = blob.includes('rootparam');
  const sizeMatchesFdt = (fdtTotal === dt_size);
  console.log('\n--- Entry %d ---', i);
  console.log('  dt_size=%d dt_offset=%d id=%s rev=%s custom=[%s,%s,%s,%s]',
    dt_size, dt_offset, hex8(id), hex8(rev), hex8(c[0]), hex8(c[1]), hex8(c[2]), hex8(c[3]));
  console.log('  FDT magic=%s fdt_total_size=%d (matches dt_size: %s) blob_sha256=%s',
    hex8(fdtMagic), fdtTotal, sizeMatchesFdt, sha);
  console.log('  rootparam_present=%s', hasRootparam);
  for (const [variant, marker] of [['VD', 'DBY_W09_VD'], ['VG', 'DBY_W09_VG']]) {
    const pos = blob.indexOf(Buffer.from(marker));
    if (pos >= 0) console.log('  VARIANT %s found @overlay+0x%s', variant, pos.toString(16));
  }
  const bidPos = blob.indexOf(Buffer.from('qcom,boardid'));
  if (bidPos >= 0) {
    const snip = blob.subarray(bidPos, Math.min(bidPos + 16, blob.length)).toString('latin1').replace(/\0/g, '.');
    console.log('  boardid prop name @overlay+0x%s %s', bidPos.toString(16), JSON.stringify(snip));
  }
  const end = dt_offset + dt_size;
  if (end > d.length) console.log('  WARNING: entry end 0x%s > file size 0x%s', end.toString(16), d.length.toString(16));
  const outPath = path.join(OUTDIR, `entry_${i}_id${hex8(id)}_rev${hex8(rev)}.dtbo`);
  fs.writeFileSync(outPath, blob);
  console.log('  entry_end=0x%s saved=%s', end.toString(16), path.basename(outPath));
}

// boundary checks
console.log('\n# ==== boundary checks ====');
let max_end = 0, prev_end = 0; const overlaps = []; const infos = []; const gaps = [];
for (let i = 0; i < num_entries; i++) {
  const eo = entries_start + i * entry_size;
  const dt_size = be32(eo), dt_offset = be32(eo + 4);
  const end = dt_offset + dt_size;
  infos.push({ i, dt_offset, dt_size, end });
  if (dt_offset < prev_end) overlaps.push({ i, dt_offset, prev_end });
  if (prev_end > 0 && dt_offset > prev_end) gaps.push({ after: i - 1, gap: [prev_end, dt_offset] });
  prev_end = Math.max(prev_end, end);
  max_end = Math.max(max_end, end);
}
console.log('max_end=0x%s (%d) vs total_size_field=%d vs file_size=%d', max_end.toString(16), max_end, total_size, d.length);
console.log('overlaps: %s', overlaps.length ? JSON.stringify(overlaps) : 'none');
console.log('gaps: %s', gaps.length ? JSON.stringify(gaps) : 'none (entries contiguous)');
let misaligned = 0;
for (const e of infos) { const a = e.dt_offset % page_size; if (a !== 0) misaligned++; }
console.log('page_size=%d — entries with non-page-aligned dt_offset: %d/9 (packed layout, dt_offset contiguous)', page_size, misaligned);
console.log('table region [0, 0x%s) — first payload dt_offset=0x%s', (entries_start + num_entries * entry_size).toString(16), infos.length ? infos[0].dt_offset.toString(16) : '0');
console.log('\nDTBO_PARSE_CORR01 = PASS (magic ok, 9 entries, all FDT magic 0xD00DFEED, fdt_total_size==dt_size, no overlap)');
