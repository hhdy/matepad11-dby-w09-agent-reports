# ROUND61 hosted UFS / ROUND63 PHY validation

- Workflow commit: ee036878a3f709f3be7251bb6d0ba45cf39ee7ea
- Workflow run ID: 45444339257
- Branch: ai-parallel/stagea-port-until-boot
- Job status: failure
- Fixed ACK commit: 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a


## Processed schema SHA-256
7707ca89dc3f27d6c84ed39f26ddc04faa5b618e99faf1f1e296423be14dbdda  /home/runner/work/_temp/round61-processed-schema.json
## Patch application
d79a35bbfe6a44bfe9aa2e69c32caac0e3f2862349f26299d190f0bf092eef65  /home/runner/work/_temp/round61-ufs-applied.diff
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
 drivers/phy/qualcomm/phy-qcom-qmp-ufs.c            | 123 ++++++++-
 drivers/ufs/host/ufs-qcom.c                        | 281 +++++++++++++++++++++
 drivers/ufs/host/ufs-qcom.h                        |   4 +
 7 files changed, 498 insertions(+), 7 deletions(-)

## ufs-sm8250-1-domain-valid-validation.log
/home/runner/work/_temp/round61-ufs-fixtures/ufs-sm8250-1-domain-valid.dtb: /: 'compatible' is a required property
	from schema $id: http://devicetree.org/schemas/root-node.yaml
/home/runner/work/_temp/round61-ufs-fixtures/ufs-sm8250-1-domain-valid.dtb: /: 'model' is a required property
	from schema $id: http://devicetree.org/schemas/root-node.yaml
/home/runner/work/_temp/round61-ufs-fixtures/ufs-sm8250-1-domain-valid.dtb: ufs@1d84000 (qcom,sm8250-ufshc): power-domains: [[10]] is too short
	from schema $id: http://devicetree.org/schemas/ufs/qcom,sc7180-ufshc.yaml
/home/runner/work/_temp/round61-ufs-fixtures/ufs-sm8250-1-domain-valid.dtb: ufs@1d84000 (qcom,sm8250-ufshc): Unevaluated properties are not allowed ('interrupts', 'power-domains', 'qcom,vccq-parent-max-microamp', 'qcom,vccq-parent-supply', 'qcom,vddp-ref-clk-max-microamp', 'qcom,vddp-ref-clk-supply' were unexpected)
	from schema $id: http://devicetree.org/schemas/ufs/qcom,sc7180-ufshc.yaml
/home/runner/work/_temp/round61-ufs-fixtures/ufs-sm8250-1-domain-valid.dtb: ufs@1d84000 (qcom,sm8250-ufshc): power-domains: [[10]] is too short
	from schema $id: http://devicetree.org/schemas/ufs/qcom,ufs.yaml
/home/runner/work/_temp/round61-ufs-fixtures/ufs-sm8250-1-domain-valid.dtb: ufs@1d84000 (qcom,sm8250-ufshc): Unevaluated properties are not allowed ('interrupts', 'power-domains' were unexpected)
	from schema $id: http://devicetree.org/schemas/ufs/qcom,ufs.yaml

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
  DTEX    Documentation/devicetree/bindings/ufs/qcom,ufs-common.example.dts
  DTC [C] Documentation/devicetree/bindings/ufs/qcom,ufs-common.example.dtb
  DTEX    Documentation/devicetree/bindings/ufs/qcom,ufs.example.dts
  DTC [C] Documentation/devicetree/bindings/ufs/qcom,ufs.example.dtb
Documentation/devicetree/bindings/ufs/qcom,ufs.example.dtb: ufs@1d84000 (qcom,sm8150-ufshc): power-domains: [[4294967295, 3]] is too short
	from schema $id: http://devicetree.org/schemas/ufs/qcom,ufs.yaml
Documentation/devicetree/bindings/ufs/qcom,ufs.example.dtb: ufs@1d84000 (qcom,sm8150-ufshc): Unevaluated properties are not allowed ('#reset-cells', 'freq-table-hz', 'interrupts', 'iommus', 'lanes-per-direction', 'phy-names', 'phys', 'power-domains', 'reset-gpios', 'reset-names', 'resets', 'vcc-max-microamp', 'vcc-supply', 'vccq-max-microamp', 'vccq-supply' were unexpected)
	from schema $id: http://devicetree.org/schemas/ufs/qcom,ufs.yaml

## round61-ufs-example-validation.log
Documentation/devicetree/bindings/ufs/qcom,ufs.example.dtb: ufs@1d84000 (qcom,sm8150-ufshc): power-domains: [[4294967295, 3]] is too short
	from schema $id: http://devicetree.org/schemas/ufs/qcom,ufs.yaml
Documentation/devicetree/bindings/ufs/qcom,ufs.example.dtb: ufs@1d84000 (qcom,sm8150-ufshc): Unevaluated properties are not allowed ('#reset-cells', 'freq-table-hz', 'interrupts', 'iommus', 'lanes-per-direction', 'phy-names', 'phys', 'power-domains', 'reset-gpios', 'reset-names', 'resets', 'vcc-max-microamp', 'vcc-supply', 'vccq-max-microamp', 'vccq-supply' were unexpected)
	from schema $id: http://devicetree.org/schemas/ufs/qcom,ufs.yaml

## dt_binding_check log SHA-256
414f6b8a050d36ad6b8e86520eb4dcf3f6c2245e49c5f343c0f6ec04ac0c9bcc  /home/runner/work/_temp/round61-dt-binding-check.log
