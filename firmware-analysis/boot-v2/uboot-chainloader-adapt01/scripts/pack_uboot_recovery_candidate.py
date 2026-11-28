#!/usr/bin/env python3
# K1_DBY_W09_UBOOT_RECOVERY_CANDIDATE_BUILD01 — packer per taskbook §C
# (the provided pack_uboot_recovery_candidate.py was not present on this host;
#  this is a faithful local implementation of the §C contract: no avbtool, no device)
import argparse, hashlib, json, gzip, os, subprocess, sys, struct

def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for c in iter(lambda: f.read(1 << 20), b''):
            h.update(c)
    return h.hexdigest()

ap = argparse.ArgumentParser()
ap.add_argument('--stock-recovery', required=True)
ap.add_argument('--uboot-bin', required=True)
ap.add_argument('--mkbootimg', required=True)
ap.add_argument('--unpack-bootimg', required=True)
ap.add_argument('--unpack-dir', required=True)
ap.add_argument('--output', required=True)
ap.add_argument('--cmdline', required=True, choices=['cowave', 'stock'])
ap.add_argument('--expected-stock-sha256', required=True)
a = ap.parse_args()

report = {}
# identity gates
got = sha(a.stock_recovery)
if got != a.expected_stock_sha256:
    print('STOP: stock recovery sha mismatch %s != %s' % (got, a.expected_stock_sha256)); sys.exit(1)
report['stock_recovery_sha256'] = got
report['uboot_bin_sha256'] = sha(a.uboot_bin)

# read unpacked args (stock-mkbootimg-args.txt produced in step B)
args_file = os.path.join(os.path.dirname(a.unpack_dir), 'stock-mkbootimg-args.txt')
content = open(args_file, encoding='utf-8', errors='replace').read()
i = content.find('--header_version')
assert i >= 0, 'no --header_version args in %s' % args_file
toks = [t for t in content[i:].split('\x00') if t.strip()]
kv = {}
k = None
for t in toks:
    if t.startswith('--'):
        k = t.lstrip('-')
        kv[k] = ''
    elif k:
        kv[k] = t
kv['cmdline'] = kv.get('cmdline', '').strip()
assert kv.get('header_version') == '2', 'stock recovery header_version != 2: %r' % kv.get('header_version')
assert kv.get('kernel', '').endswith('kernel'), 'unexpected kernel arg: %r' % kv.get('kernel')
cmdline = kv['cmdline'] if a.cmdline == 'stock' else open('/home/kerneldev/build/rcand/cowave-cmdline.txt').read().strip()

kcomp = a.output + '.kernel.gz'
with open(a.uboot_bin, 'rb') as fi, gzip.GzipFile(filename='', mode='wb', compresslevel=9, fileobj=open(kcomp, 'wb')) as fo:
    fo.write(fi.read())
report['uboot_gz_sha256'] = sha(kcomp)

cmd = ['python3', a.mkbootimg,
       '--header_version', kv['header_version'],
       '--os_version', kv['os_version'], '--os_patch_level', kv['os_patch_level'],
       '--kernel', kcomp,
       '--ramdisk', os.path.join(a.unpack_dir, 'ramdisk'),
       '--recovery_dtbo', os.path.join(a.unpack_dir, 'recovery_dtbo'),
       '--dtb', os.path.join(a.unpack_dir, 'dtb'),
       '--pagesize', kv['pagesize'], '--base', kv['base'],
       '--kernel_offset', kv['kernel_offset'], '--ramdisk_offset', kv['ramdisk_offset'],
       '--second_offset', kv['second_offset'], '--dtb_offset', kv['dtb_offset'],
       '--board', kv.get('board', ''),
       '--cmdline', cmdline,
       '--output', a.output]
r = subprocess.run(cmd, capture_output=True, text=True)
report['mkbootimg_rc'] = r.returncode
report['mkbootimg_stderr_tail'] = r.stderr[-300:]
if r.returncode != 0:
    print(json.dumps(report, indent=1)); sys.exit(1)
report['candidate_sha256'] = sha(a.output)
report['candidate_bytes'] = os.path.getsize(a.output)
report['cmdline_mode'] = a.cmdline
with open(a.output + '.report.json', 'w') as f:
    json.dump(report, f, indent=1)
print(json.dumps(report, indent=1))
