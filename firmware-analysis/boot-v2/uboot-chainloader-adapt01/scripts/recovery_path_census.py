#!/usr/bin/env python3
# Group B: recovery-path string xrefs in Hybrid PE + memory-reg evidence grep
import sys
sys.path.insert(0, '/mnt/c/Users/Administrator/.zcode/workspace/draft-4dcdb0bd-9b6e-4706-a220-ce0b212cdcbf/K1_ABL_AUTH_CLOSE01_REPORT/scripts')
import dataflow_xref
from dataflow_xref import parse_insns, branch_targets

PE = '/mnt/c/Users/Administrator/.zcode/workspace/draft-4dcdb0bd-9b6e-4706-a220-ce0b212cdcbf/PREP12_WORK/W3A/abl-hos43-pe.bin'
data = open(PE, 'rb').read()
dataflow_xref.data = data

# find exact file offsets of recovery-related strings first
targets = {}
for s in [b'AppendRecoveryCmdline', b'Recovery Dtbo Offset: 0x%x', b'Recovery Dtbo Size: 0x%x',
          b'Invalid recovery dtbo', b'bootmode: %d, PartitionName %a Adjusted to %a',
          b'resuce_recovery', b'rescue_recovery', b'BOOTIMG-RECOVERY', b'--truncate_to_size']:
    o = data.find(s)
    if o >= 0:
        targets[o] = s.decode('ascii', 'replace')[:30]
print('string offsets found:')
for o, n in sorted(targets.items()):
    print('  0x%06X %s' % (o, n))

win = {}
for s, n in targets.items():
    for v in range(s - 8, s + 8):
        win[v] = n

def census(start, end):
    insns = parse_insns(start, end)
    tgset = branch_targets(insns)
    env = {}; const = {}
    out = []
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
                    if env[rd] in win:
                        out.append((a, env[rd], win[env[rd]]))
                    const.pop(rd, None)
                else:
                    env.pop(rd, None)
            elif m == 'ldr' and '[' in o:
                rd = o.split(',')[0].strip()
                base = o[o.find('[')+1:o.find(']')]
                p = base.split(', '); rn = p[0].strip()
                offv = int(p[1].replace('#', ''), 0) if len(p) > 1 and p[1].startswith('#') else 0
                if rn in env:
                    env[rd] = ('ptr', env[rn] + offv)
                else:
                    env.pop(rd, None)
            elif m in ('bl', 'blr'):
                for r in list(env.keys()):
                    rr = int(r[1:]) if r[0] in 'wx' else None
                    if rr is not None and rr < 18: env.pop(r)
            elif m in ('b', 'ret'):
                env.clear(); const.clear()
        except Exception:
            pass
    return out

hits = census(0x1000, 0x109000)
print('\nxref sites (composed VA in +-8 window):')
for (a, v, n) in hits:
    print('  site 0x%06X va=0x%06X -> %s' % (a, v, n))
