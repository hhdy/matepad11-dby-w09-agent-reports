#!/usr/bin/env python3
# K1_BOOT_LOAD_MAP01 Stage B2 (rev2): string refs via .data 64-bit pointer pool + dataflow xref
import sys, struct
sys.path.insert(0, '/mnt/c/Users/Administrator/.zcode/workspace/draft-4dcdb0bd-9b6e-4706-a220-ce0b212cdcbf/K1_ABL_AUTH_CLOSE01_REPORT/scripts')
import dataflow_xref
from dataflow_xref import parse_insns, scan

PE = '/mnt/c/Users/Administrator/.zcode/workspace/draft-4dcdb0bd-9b6e-4706-a220-ce0b212cdcbf/PREP12_WORK/W3A/abl-hos43-pe.bin'
data = open(PE, 'rb').read()
dataflow_xref.data = data   # rebind module-global (it consumed its own argv at import)

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
    0xD4841: 'MP_DATA_entry_not_found',
    0xD4C94: 'fdt_is_null',
    0xCADDB: 'common_cmd_hwdog_certify_relock_UNUSED',
}

# Step 1: find 8-byte LE pointers equal to each string VA anywhere in image
pool = {}   # pool_va -> string name
for va, name in STRINGS.items():
    needle = struct.pack('<Q', va)
    off = 0
    while True:
        off = data.find(needle, off)
        if off < 0:
            break
        if off % 8 == 0:   # aligned pointer slots only
            pool[off] = name + '@pool'
            print('pool: 0x%06X -> %s (string 0x%X)' % (off, name, va))
        off += 1

# Step 2: targets = strings + pools (also keep a known-good sanity target)
T = dict(STRINGS)
T[0x105B38] = 'SANITY_console_tty'
for p, name in pool.items():
    T[p] = name

h, ic = scan(0x1000, 0x109000, T, 'loadmap01')

# cluster hits into functions via nearest stp x29,x30 prologue
insns = parse_insns(0x1000, 0x109000)
prologues = [a for (a, m, o, ok) in insns if ok and m == 'stp' and o.startswith('x29, x30')]
import bisect
print('\n# ==== functions referencing load-path strings ====')
funcs = {}
for (a, m, o, r, v) in h:
    name = T.get(v, '?')
    i = bisect.bisect_left(prologues, a) - 1
    f = prologues[i] if i >= 0 else None
    funcs.setdefault(f, []).append((a, name))
for f in sorted(funcs, key=lambda x: (x is None, x)):
    names = sorted(set(n for (_, n) in funcs[f]))
    sites = [hex(a) for (a, _) in funcs[f]]
    print('  func~0x%s : %s   sites=%s' % ('%06X' % f if f else '??????', ','.join(names), ','.join(sites)))
