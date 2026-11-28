#!/usr/bin/env node
// Generate SHA256SUMS.txt for the CORR01 deliverable directory (excluding itself and ZIP)
'use strict';
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const ROOT = process.argv[2];
if (!ROOT) { console.error('usage: make_sums.js <dir>'); process.exit(2); }

const files = [];
(function walk(dir) {
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, e.name);
    if (e.isDirectory()) walk(p);
    else files.push(p);
  }
})(ROOT);

const lines = [];
for (const p of files.sort()) {
  const rel = path.relative(ROOT, p).split(path.sep).join('/');
  if (rel === 'SHA256SUMS.txt' || rel.endsWith('.zip')) continue;
  const h = crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
  lines.push(h + '  ' + rel);
  console.log(h.slice(0, 16) + '  ' + rel);
}
fs.writeFileSync(path.join(ROOT, 'SHA256SUMS.txt'), lines.join('\n') + '\n');
console.log('\nSHA256SUMS.txt written: %d entries', lines.length);
