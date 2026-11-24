# ROUND61 hosted UFS / ROUND63 PHY validation

- Workflow commit: 40e6c909f9d23e0e489fb75d573d36464e7b3215
- Workflow run ID: 45457024349
- Branch: ai-parallel/stagea-port-until-boot
- Job status: failure
- Fixed ACK commit: 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a

## Patch application
b6897118cbef2fe36216d8fa00c22707531b7d6ba6aa5b35417c547185d54b90  /home/runner/work/_temp/round61-ufs-applied.diff
ACK HEAD: 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a
 M BUILD.bazel
 M Documentation/devicetree/bindings/phy/qcom,sc8280xp-qmp-ufs-phy.yaml
 M Documentation/devicetree/bindings/ufs/qcom,sc7180-ufshc.yaml
 M Documentation/devicetree/bindings/ufs/qcom,ufs-common.yaml
 M drivers/phy/qualcomm/phy-qcom-qmp-ufs.c
 M drivers/ufs/host/ufs-qcom.c
 M drivers/ufs/host/ufs-qcom.h
?? arch/arm64/configs/dby_w09_storage_first.fragment
 BUILD.bazel                                        |  19 ++
 .../bindings/phy/qcom,sc8280xp-qmp-ufs-phy.yaml    |   5 +
 .../devicetree/bindings/ufs/qcom,sc7180-ufshc.yaml |   1 +
 .../devicetree/bindings/ufs/qcom,ufs-common.yaml   |  51 +++-
 drivers/phy/qualcomm/phy-qcom-qmp-ufs.c            | 123 ++++++++-
 drivers/ufs/host/ufs-qcom.c                        | 281 +++++++++++++++++++++
 drivers/ufs/host/ufs-qcom.h                        |   4 +
 7 files changed, 477 insertions(+), 7 deletions(-)

## round33-checkpatch.log
total: 0 errors, 0 warnings, 0 checks, 232 lines checked

"[PATCH DRAFT] scsi: ufs: qcom: route SM8250 UFS OPP to RPMhPD" has no obvious style problems and is ready for submission.

## round52-0002-checkpatch.log
total: 0 errors, 0 warnings, 0 checks, 104 lines checked

"[PATCH DRAFT] scsi: ufs: qcom: manage SM8250 VDDP REF_CLK supply" has no obvious style problems and is ready for submission.

## round63-0001-checkpatch.log
Use of uninitialized value $root in concatenation (.) or string at /home/runner/work/_temp/ack/scripts/checkpatch.pl line 1191.
find: ‘/include’: No such file or directory
total: 0 errors, 0 warnings, 0 checks, 224 lines checked

"[PATCH DRAFT] phy: qcom-qmp-ufs: keep vdda-phy enabled when idle" has no obvious style problems and is ready for submission.

NOTE: Ignored message types: CAMELCASE
