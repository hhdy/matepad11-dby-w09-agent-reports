# ROUND130 — AI1 four-patch UFS lifecycle integration review

Owner: 1号 AI (ChatGPT)
Branch: ai1/round130-stagea-ufs-lifecycle-integration
Status: PREPARED FOR JOINT AGENT VALIDATION; NOT YET ACCEPTED.

ROUND124 proved ROUND120 per-HBA async scan join + ROUND122 UFS regulator
load-first on a Stage A 15-patch tree. ROUND129 proved ROUND128 V2 QMP
two-rail state + ROUND126 proxy load-first on the accepted Stage A 17-patch
tree. Those are separate group runs. ROUND130 is required to prove all four
coexist on the same exact 17-patch base.

Fixed base:
  ai-parallel/stagea-port-until-boot@2f21233148a04afdd61e44b1be7688399967d9d0
  ACK 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a
  Existing 17-patch order: kernel-baseline/round61/round32-stagea-series.txt

Candidate order after the 17 base patches:
  18 ROUND120 async scan join
  19 ROUND122 UFS load-first
  20 ROUND128 V2 QMP dual-rail state
  21 ROUND126 proxy-consumer load-first

ROUND120 and ROUND122 both touch ufshcd.c, but the earlier ROUND124 source
review found their hunks in separate regions: ROUND120 changes private HBA
state, allocation/init/remove and async scheduling; ROUND122 changes the
earlier regulator helper functions. Apply ROUND120 first, then ROUND122.
Actual 21-patch git apply/check/diff-check with no fuzz is mandatory.

ROUND128 V2 touches only phy-qcom-qmp-ufs.c and reuses ROUND63's existing
qmp_ufs_power_off callback. Never use rejected original ROUND125.
ROUND126 touches proxy-consumer.c and is known to apply after the Stage A
17-patch self-target-only change; ROUND129 proved this exact base.

Expected candidate overlay adds exactly four source paths:
- drivers/ufs/core/ufshcd-priv.h
- drivers/ufs/core/ufshcd.c
- drivers/phy/qualcomm/phy-qcom-qmp-ufs.c
- drivers/regulator/proxy-consumer.c

Candidate files and original identities are recorded in
kernel-baseline/round130/round130-ai1-series.txt.
Test taskbook:
firmware-analysis/round130/TEST_AGENT_ROUND130_COMBINED_TASKBOOK.md
on firmware-audit-v1.

Acceptance boundary:
Even if ROUND130 passes, it establishes only an integrated buildable AI1
candidate series. It does not prove async runtime race behavior, physical
PMIC rail sequencing, parent input topology, final ABL/DTBO/FDT/EFI memory
handoff, boot or hardware stability. It must not be merged into AI2
automatically. Phase E/F remain BLOCKED; Phase G remains NOT RUN.
