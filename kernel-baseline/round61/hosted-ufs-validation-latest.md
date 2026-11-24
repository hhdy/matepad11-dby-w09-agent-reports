# ROUND61 hosted UFS / ROUND63 PHY validation

- Workflow commit: f203b96575e06a61549b8aad4b227e3bcc9c8038
- Workflow run ID: 45445601147
- Branch: ai-parallel/stagea-port-until-boot
- Job status: failure
- Fixed ACK commit: 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a


## Processed schema SHA-256
c8e48550ab557e8f3b5b402895cce89aa95ceb7e3cd92b20545a07f2b2f1e5fc  /home/runner/work/_temp/round61-processed-schema.json
## Patch application
3e46b9a47922243671eb49883a767a857ac2ff0edd32fc8f6a04f98ae9914438  /home/runner/work/_temp/round61-ufs-applied.diff
ACK HEAD: 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a
 M BUILD.bazel
 M Documentation/devicetree/bindings/phy/qcom,sc8280xp-qmp-ufs-phy.yaml
 M Documentation/devicetree/bindings/ufs/qcom,ufs-common.yaml
 M drivers/phy/qualcomm/phy-qcom-qmp-ufs.c
 M drivers/ufs/host/ufs-qcom.c
 M drivers/ufs/host/ufs-qcom.h
?? arch/arm64/configs/dby_w09_storage_first.fragment
 BUILD.bazel                                        |  19 ++
 .../bindings/phy/qcom,sc8280xp-qmp-ufs-phy.yaml    |   5 +
 .../devicetree/bindings/ufs/qcom,ufs-common.yaml   |  49 +++-
 drivers/phy/qualcomm/phy-qcom-qmp-ufs.c            | 123 ++++++++-
 drivers/ufs/host/ufs-qcom.c                        | 281 +++++++++++++++++++++
 drivers/ufs/host/ufs-qcom.h                        |   4 +
 6 files changed, 474 insertions(+), 7 deletions(-)

## ufs-sm8250-1-domain-valid-validation.log

## ufs-sm8250-2-domains-valid-validation.log
/home/runner/work/_temp/round61-ufs-fixtures/ufs-sm8250-2-domains-valid.dtb: ufs@1d84000 (qcom,sm8250-ufshc): power-domains: [[10], [0], [11], [0]] is too long
	from schema $id: http://devicetree.org/schemas/ufs/qcom,sc7180-ufshc.yaml
/home/runner/work/_temp/round61-ufs-fixtures/ufs-sm8250-2-domains-valid.dtb: ufs@1d84000 (qcom,sm8250-ufshc): power-domains: [[10], [0], [11], [0]] is too long
	from schema $id: http://devicetree.org/schemas/ufs/qcom,sc7180-ufshc.yaml
/home/runner/work/_temp/round61-ufs-fixtures/ufs-sm8250-2-domains-valid.dtb: ufs@1d84000 (qcom,sm8250-ufshc): Unevaluated properties are not allowed ('interrupts', 'power-domains', 'qcom,vccq-parent-max-microamp', 'qcom,vccq-parent-supply', 'qcom,vddp-ref-clk-max-microamp', 'qcom,vddp-ref-clk-supply' were unexpected)
	from schema $id: http://devicetree.org/schemas/ufs/qcom,sc7180-ufshc.yaml

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

## round61-dt-binding-check.log
  SCHEMA  Documentation/devicetree/bindings/processed-schema.json
/home/runner/work/_temp/ack/Documentation/devicetree/bindings/firmware/gunyah-cma-mem.yaml: ignoring, error parsing file
  HOSTCC  scripts/basic/fixdep
  HOSTCC  scripts/dtc/dtc.o
  HOSTCC  scripts/dtc/flattree.o
  HOSTCC  scripts/dtc/fstree.o
  HOSTCC  scripts/dtc/data.o
  HOSTCC  scripts/dtc/livetree.o
  HOSTCC  scripts/dtc/treesource.o
  HOSTCC  scripts/dtc/srcpos.o
  HOSTCC  scripts/dtc/checks.o
  HOSTCC  scripts/dtc/util.o
  LEX     scripts/dtc/dtc-lexer.lex.c
  YACC    scripts/dtc/dtc-parser.tab.[ch]
  HOSTCC  scripts/dtc/dtc-lexer.lex.o
  HOSTCC  scripts/dtc/dtc-parser.tab.o
  HOSTLD  scripts/dtc/dtc
  CHKDT   ./Documentation/devicetree/bindings
  LINT    ./Documentation/devicetree/bindings
  DTEX    Documentation/devicetree/bindings/phy/qcom,sc8280xp-qmp-ufs-phy.example.dts
  DTC [C] Documentation/devicetree/bindings/phy/qcom,sc8280xp-qmp-ufs-phy.example.dtb
  DTEX    Documentation/devicetree/bindings/ufs/ufs-common.example.dts
  DTC [C] Documentation/devicetree/bindings/ufs/ufs-common.example.dtb
  DTEX    Documentation/devicetree/bindings/ufs/qcom,sc7180-ufshc.example.dts
  DTC [C] Documentation/devicetree/bindings/ufs/qcom,sc7180-ufshc.example.dtb
Documentation/devicetree/bindings/ufs/qcom,sc7180-ufshc.example.dtb: ufs@1d84000 (qcom,sm8450-ufshc): power-domains: [[4294967295, 2]] is too short
	from schema $id: http://devicetree.org/schemas/ufs/qcom,sc7180-ufshc.yaml
Documentation/devicetree/bindings/ufs/qcom,sc7180-ufshc.example.dtb: ufs@1d84000 (qcom,sm8450-ufshc): Unevaluated properties are not allowed ('#reset-cells', 'freq-table-hz', 'interconnect-names', 'interconnects', 'interrupts', 'iommus', 'lanes-per-direction', 'phy-names', 'phys', 'power-domains', 'reset-gpios', 'reset-names', 'resets', 'vcc-max-microamp', 'vcc-supply', 'vccq-max-microamp', 'vccq-supply' were unexpected)
	from schema $id: http://devicetree.org/schemas/ufs/qcom,sc7180-ufshc.yaml
  DTEX    Documentation/devicetree/bindings/ufs/qcom,ufs.example.dts
  DTC [C] Documentation/devicetree/bindings/ufs/qcom,ufs.example.dtb
Documentation/devicetree/bindings/ufs/qcom,ufs.example.dtb: ufs@1d84000 (qcom,sm8150-ufshc): power-domains: [[4294967295, 3]] is too short
	from schema $id: http://devicetree.org/schemas/ufs/qcom,ufs.yaml
Documentation/devicetree/bindings/ufs/qcom,ufs.example.dtb: ufs@1d84000 (qcom,sm8150-ufshc): Unevaluated properties are not allowed ('#reset-cells', 'freq-table-hz', 'interrupts', 'iommus', 'lanes-per-direction', 'phy-names', 'phys', 'power-domains', 'reset-gpios', 'reset-names', 'resets', 'vcc-max-microamp', 'vcc-supply', 'vccq-max-microamp', 'vccq-supply' were unexpected)
	from schema $id: http://devicetree.org/schemas/ufs/qcom,ufs.yaml
  DTEX    Documentation/devicetree/bindings/ufs/qcom,ufs-common.example.dts
  DTC [C] Documentation/devicetree/bindings/ufs/qcom,ufs-common.example.dtb

## round61-ufs-example-validation.log
Documentation/devicetree/bindings/ufs/qcom,ufs.example.dtb: ufs@1d84000 (qcom,sm8150-ufshc): power-domains: [[4294967295, 3]] is too short
	from schema $id: http://devicetree.org/schemas/ufs/qcom,ufs.yaml
Documentation/devicetree/bindings/ufs/qcom,ufs.example.dtb: ufs@1d84000 (qcom,sm8150-ufshc): Unevaluated properties are not allowed ('#reset-cells', 'freq-table-hz', 'interrupts', 'iommus', 'lanes-per-direction', 'phy-names', 'phys', 'power-domains', 'reset-gpios', 'reset-names', 'resets', 'vcc-max-microamp', 'vcc-supply', 'vccq-max-microamp', 'vccq-supply' were unexpected)
	from schema $id: http://devicetree.org/schemas/ufs/qcom,ufs.yaml

## dt_binding_check log SHA-256
442fc6840f776f2cfc1228e4db1ccb6ac6f0463ecc58a9d71d3edd2f85e5bb59  /home/runner/work/_temp/round61-dt-binding-check.log
