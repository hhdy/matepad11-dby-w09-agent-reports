# ROUND61 hosted UFS / ROUND63 PHY validation

- Workflow commit: 74bab6eb690d45f388f2e58df14561cc9f886cfa
- Branch: ai-parallel/stagea-port-until-boot
- Job status: failure
- Fixed ACK commit: 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a

## Patch application
e65fba3961af908d1ea435f5a05c124fba26d31927618f44ae2ab083b10a9446  /home/runner/work/_temp/round61-ufs-applied.diff
ACK HEAD: 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a
 M BUILD.bazel
 M Documentation/devicetree/bindings/phy/qcom,sc8280xp-qmp-ufs-phy.yaml
 M Documentation/devicetree/bindings/ufs/qcom,ufs-common.yaml
 M Documentation/devicetree/bindings/ufs/qcom,ufs.yaml
 M drivers/phy/qualcomm/phy-qcom-qmp-ufs.c
 M drivers/ufs/host/ufs-qcom.c
 M drivers/ufs/host/ufs-qcom.h
?? arch/arm64/configs/dby_w09_storage_first.fragment
 BUILD.bazel                                        |  19 ++
 .../bindings/phy/qcom,sc8280xp-qmp-ufs-phy.yaml    |   5 +
 .../devicetree/bindings/ufs/qcom,ufs-common.yaml   |  18 +-
 .../devicetree/bindings/ufs/qcom,ufs.yaml          |  55 ++++
 drivers/phy/qualcomm/phy-qcom-qmp-ufs.c            | 121 ++++++++-
 drivers/ufs/host/ufs-qcom.c                        | 281 +++++++++++++++++++++
 drivers/ufs/host/ufs-qcom.h                        |   4 +
 7 files changed, 497 insertions(+), 6 deletions(-)

## round33-checkpatch.log
total: 0 errors, 0 warnings, 0 checks, 232 lines checked

"[PATCH DRAFT] scsi: ufs: qcom: route SM8250 UFS OPP to RPMhPD" has no obvious style problems and is ready for submission.

## round52-0002-checkpatch.log
total: 0 errors, 0 warnings, 0 checks, 104 lines checked

"[PATCH DRAFT] scsi: ufs: qcom: manage SM8250 VDDP REF_CLK supply" has no obvious style problems and is ready for submission.

## round63-0001-checkpatch.log
Use of uninitialized value $root in concatenation (.) or string at /home/runner/work/_temp/ack/scripts/checkpatch.pl line 1191.
find: ‘/include’: No such file or directory
WARNING: Prefer a maximum 75 chars per line (possible unwrapped commit description?)
#6: 
regulator enable while dropping its active load vote when the PHY is powered

ERROR: Please use git commit description style 'commit <12+ chars of sha1> ("<title line>")' - ie: 'commit 0123456789ab ("commit description")'
#25: 
Pinned source: ACK 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a

ERROR: Please use git commit description style 'commit <12+ chars of sha1> ("<title line>")' - ie: 'commit 0123456789ab ("commit description")'
#26: 
Source blob: 8af777f7ddd0385a6bb9d9b9563f0e6329699cd3

CHECK: Avoid CamelCase: <init_load_uA>
#89: FILE: drivers/phy/qualcomm/phy-qcom-qmp-ufs.c:1869:
+				 qmp->vregs[0].init_load_uA);

CHECK: Alignment should match open parenthesis
#228: FILE: drivers/phy/qualcomm/phy-qcom-qmp-ufs.c:1997:
+	qphy_clrbits(qmp->pcs, cfg->regs[QPHY_PCS_POWER_DOWN_CONTROL],
+			SW_PWRDN);

total: 2 errors, 1 warnings, 2 checks, 224 lines checked

NOTE: For some of the reported defects, checkpatch may be able to
      mechanically convert to the typical style using --fix or --fix-inplace.

"[PATCH DRAFT] phy: qcom-qmp-ufs: keep vdda-phy enabled when idle" has style problems, please review.

NOTE: If any of the errors are false positives, please report
      them to the maintainer, see CHECKPATCH in MAINTAINERS.
