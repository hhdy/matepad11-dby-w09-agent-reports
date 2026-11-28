#!/usr/bin/env python3
# K1_BOOT_LOAD_MAP01 Stage B2 (rev3): census of ALL composed VAs in .text, matched to string windows
import sys, struct, bisect
sys.path.insert(0, '/mnt/c/Users/Administrator/.zcode/workspace/draft-4dcdb0bd-9b6e-4706-a220-ce0b212cdcbf/K1_ABL_AUTH_CLOSE01_REPORT/scripts')
import dataflow_xref
from dataflow_xref import parse_insns, branch_targets, VOLATILE

PE = '/mnt/c/Users/Administrator/.zcode/workspace/draft-4dcdb0bd-9b6e-4706-a220-ce0b212cdcbf/PREP12_WORK/W3A/abl-hos43-pe.bin'
data = open(PE, 'rb').read()
dataflow_xref.data = data

STRINGS = {
    0xCEB24: 'KernelLoadAddr_log',
    0xCEB3F: 'KernelSizeActual_log',
    0xCEB73: 'RamdiskLoadAddr_log',
    0xCEB8F: 'RamdiskSizeActual_log',
    0xCEBAA: 'RamdiskOffset_log',
    0xCEA42: 'BootLinux_invalidparam',
    0xCEAAD: 'BootLinux_GetImage_failed',
    0xCEC95: 'ANDROID!_magic_str',
    0xCF250: 'NotEnoughSpace_kernel',
    0xCF209: 'UNCOMPRESSED_IMG',
    0xCF774: 'move_ramdisk_to_img_addr',
    0xCF89A: 'KernelSizeOverLimit',
    0xCF86F: 'OverflowKernelCopy',
    0xD490B: 'KernelModeCheck64',
    0xD48F1: 'KernelBaseAddress_log',
    0xCFA72: 'DTBOffsetNull',
    0xC8019: 'g_fdt_addr_not_set',
    0xC8031: 'set_g_fdt_addr',
    0xCF6E9: 'start_loadramdisk',
    0xCF719: 'RamdiskSizeOverLimit',
    0xCF343: 'PatchedKernelDetected',
    0xCF35C: 'DTBOffsetBeyondKernelSize',
    0xCFBFC: 'DTBOffsetIncorrect_noAppendedDTB',
    0xCFAEE: 'BestMatchDTBTags',
    0xCBC34: 'FailedLoadAuthBootImage',
    0xCF0B3: 'FailedKernelSize_log',
    0xD0C26: 'linux_initrd_start',
    0xD0C77: 'linux_initrd_end',
    0xD0B99: 'kaslr_seed',
    0xCF3D6: 'DtbOffsetBeyondImageSize',
    0xCF41A: 'SingleAppendedDTBFound',
    0xCFE82: 'DtboCount_LocalBoardDtMatch',
    0xD0F28: 'InvalidMemoryConfig',
    0xD0F8F: 'RAM_Partitions',
}

# build window index: every VA in [s-16, s+80] maps to string name
win = {}
for s, n in STRINGS.items():
    for v in range(s - 16, s + 80):
        win[v] = n

def census(start, end):
    insns = parse_insns(start, end)
    tgset = branch_targets(insns)
    env = {}; const = {}
    comps = []   # (site, kind, reg, value)
    for (a, m, o, ok) in insns:
        if not ok:
            env.clear(); const.clear(); continue
        if a in tgset:
            env.clear(); const.clear()
        try:
            if m in ('adrp', 'adr'):
                rd, imm = o.split(', ')
                env[rd] = int(imm.replace('#', ''), 0)
                const.pop(rd, None)
            elif m == 'add' and o.count(', ') >= 2 and o.split(', ')[2].startswith('#'):
                p = o.split(', '); rd, rn = p[0], p[1]
                imm = int(p[2].replace('#', ''), 0)
                if rn in env:
                    env[rd] = env[rn] + imm
                    comps.append((a, 'adr_add', rd, env[rd]))
                    const.pop(rd, None)
                else:
                    env.pop(rd, None)
            elif m == 'mov' and o.count(', ') == 1 and not o.split(', ')[1].startswith('#'):
                rd, rn = o.split(', ')
                if rn in env: env[rd] = env[rn]
                elif rn in const: const[rd] = const[rn]
                else: env.pop(rd, None)
            elif m in ('movz', 'movk'):
                p = o.split(', '); rd = p[0]
                imm = int(p[1].replace('#', ''), 0)
                shift = int(p[2].split('#')[1]) if len(p) > 2 and 'lsl' in p[2] else 0
                if m == 'movz':
                    const[rd] = imm << shift; env.pop(rd, None)
                elif const.get(rd) is not None:
                    const[rd] = (const[rd] & ~(0xffff << shift)) | (imm << shift)
            elif m == 'ldr' and '[' in o:
                rd = o.split(',')[0].strip()
                base = o[o.find('[')+1:o.find(']')]
                p = base.split(', '); rn = p[0].strip()
                offv = int(p[1].replace('#', ''), 0) if len(p) > 1 and p[1].startswith('#') else 0
                if rn in env:
                    pv = env[rn] + offv
                    env[rd] = ('ptr', pv)
                    comps.append((a, 'ldr_ptr', rd, pv))
                    const.pop(rd, None)
                elif rn in const:
                    env[rd] = ('caddr', const[rn] + offv)
                else:
                    env.pop(rd, None)
            elif m == 'bl':
                for r in list(env.keys()):
                    rr = int(r[1:]) if r[0] in 'wx' else None
                    if rr is not None and rr < 18: env.pop(r)
                for r in list(const.keys()):
                    rr = int(r[1:]) if r[0] in 'wx' else None
                    if rr is not None and rr < 18: const.pop(r)
            elif m in ('b', 'ret'):
                env.clear(); const.clear()
        except Exception:
            pass
    return comps

comps = census(0x1000, 0x109000)
print('composed values total: %d' % len(comps))

hits = [(a, k, r, v) for (a, k, r, v) in comps if v in win]
print('string-window hits: %d' % len(hits))
for (a, k, r, v) in hits:
    print('  site 0x%06X %-8s reg=%s va=0x%06X -> %s' % (a, k, r, v, win[v]))

insns = parse_insns(0x1000, 0x109000)
prologues = [a for (a, m, o, ok) in insns if ok and m == 'stp' and o.startswith('x29, x30')]
funcs = {}
for (a, k, r, v) in hits:
    i = bisect.bisect_left(prologues, a) - 1
    f = prologues[i] if i >= 0 else None
    funcs.setdefault(f, set()).add(win[v])
print('\n# ==== functions referencing load-path strings ====')
for f in sorted(funcs, key=lambda x: (x is None, x)):
    print('  func~0x%s : %s' % ('%06X' % f if f else '??????', ','.join(sorted(funcs[f]))))
