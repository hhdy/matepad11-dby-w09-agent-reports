# ROUND61 hosted UFS / ROUND63 PHY validation

- Workflow commit: a1df7a5c63042a1bc78d20306929eb44bae30824
- Workflow run ID: 45443067117
- Branch: ai-parallel/stagea-port-until-boot
- Job status: failure
- Fixed ACK commit: 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a

## Patch application
Applied diff not produced; inspect job log.
ACK HEAD: 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a
 M Documentation/devicetree/bindings/phy/qcom,sc8280xp-qmp-ufs-phy.yaml
 M Documentation/devicetree/bindings/ufs/qcom,ufs-common.yaml
 M Documentation/devicetree/bindings/ufs/qcom,ufs.yaml
 M drivers/phy/qualcomm/phy-qcom-qmp-ufs.c
 M drivers/ufs/host/ufs-qcom.c
 M drivers/ufs/host/ufs-qcom.h
?? drivers/phy/qualcomm/phy-qcom-qmp-ufs.c.rej
 .../bindings/phy/qcom,sc8280xp-qmp-ufs-phy.yaml    |   5 +
 .../devicetree/bindings/ufs/qcom,ufs-common.yaml   |  18 +-
 .../devicetree/bindings/ufs/qcom,ufs.yaml          |  55 ++++
 drivers/phy/qualcomm/phy-qcom-qmp-ufs.c            | 115 ++++++++-
 drivers/ufs/host/ufs-qcom.c                        | 281 +++++++++++++++++++++
 drivers/ufs/host/ufs-qcom.h                        |   4 +
 6 files changed, 474 insertions(+), 4 deletions(-)
