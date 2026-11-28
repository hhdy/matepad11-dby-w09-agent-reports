#!/usr/bin/env python3
import subprocess, re
WS = '/mnt/c/Users/Administrator/.zcode/workspace/draft-4dcdb0bd-9b6e-4706-a220-ce0b212cdcbf'
def children(f):
    txt = subprocess.run(['dtc','-I','dtb','-O','dts',f],capture_output=True,text=True).stdout
    seg = txt[txt.find('reserved-memory {'):]
    seg = seg[:seg.find('\n\t};')]
    out = {}
    blocks = re.split(r'\n\t\t(?=[a-zA-Z_])', seg)[1:]
    for b in blocks:
        name = b.split(' {')[0].strip()
        rm = re.search(r'reg = <([^>]+)>', b)
        if rm:
            v=[int(x,16) for x in re.findall(r'0x[0-9a-f]+', rm.group(1))]
            if len(v)>=4: base=(v[0]<<32)|v[1]; size=(v[2]<<32)|v[3]
            else: base,size=v[0],v[1]
        else: base=size=None
        fl=[]
        if 'no-map' in b: fl.append('no-map')
        if 'reusable' in b: fl.append('reusable')
        cm=re.search(r'compatible = "([^"\\]+)', b)
        if cm: fl.append('compat='+cm.group(1).split('\\0')[0])
        out[name]=(base,size,tuple(fl))
    return out
final = children(WS + '/final-fdt-capture/hos43-final-fdt.dtb')
ack = children(WS + '/K1_BOOT_LOAD_MAP01/evidence/prep_dtb.bin')
ub = children('/home/kerneldev/build/u-boot-2026.10/build/u-boot.dtb')
print('final=%d ack=%d uboot_ctrl=%d' % (len(final), len(ack), len(ub)))
print('-- 3-way (final | ack_dt | uboot_ctrl) --')
for name in sorted(set(final)|set(ack)|set(ub)):
    f=final.get(name); a=ack.get(name); u=ub.get(name)
    def fm(x): return ('%s+%s %s' % (hex(x[0]),hex(x[1]),','.join(x[2]))) if x and x[0] is not None else ('dyn[%s]' % ','.join(x[2]) if x else '-')
    if f and a and f[0]==a[0] and f[1]==a[1] and f[2]==a[2]: tag='MATCH'
    elif f and a and f[0]==a[0] and f[1]==a[1]: tag='MATCH(base,size) ATTR-DIFF'
    elif f and not a: tag='FINAL-ONLY(ACK-ABSENT)'
    elif a and not f: tag='ACK-ONLY(FINAL-ABSENT)'
    else: tag='DIFF/ABSENT'
    print('%-34s F:%s | A:%s | U:%s  [%s]' % (name, fm(f), fm(a), fm(u), tag))
