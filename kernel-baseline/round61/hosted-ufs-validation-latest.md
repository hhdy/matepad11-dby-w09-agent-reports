# ROUND61 hosted UFS / ROUND63 PHY validation

- Workflow commit: 0dfefc43e707929e29d187d333b30d9a05d3eafb
- Workflow run ID: 45448394286
- Branch: ai-parallel/stagea-port-until-boot
- Job status: failure
- Fixed ACK commit: 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a


## Processed schema SHA-256
3f8969dba62b70a88b3b3278285ffdd532388fe0101047903fa273a16c4bf22a  /home/runner/work/_temp/round61-processed-schema.json
## Patch application
05eb2bd636595d93b9450eb9ac4d951738c611845240101294211b46dea9e26e  /home/runner/work/_temp/round61-ufs-applied.diff
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
 .../devicetree/bindings/ufs/qcom,ufs-common.yaml   |  49 +++-
 drivers/phy/qualcomm/phy-qcom-qmp-ufs.c            | 123 ++++++++-
 drivers/ufs/host/ufs-qcom.c                        | 281 +++++++++++++++++++++
 drivers/ufs/host/ufs-qcom.h                        |   4 +
 7 files changed, 475 insertions(+), 7 deletions(-)

## ufs-sm8250-1-domain-valid-validation.log
/home/runner/work/_temp/round61-ufs-fixtures/ufs-sm8250-1-domain-valid.dtb: ufs@1d84000: power-domains: [[10, 0]] is too short
	from schema $id: http://devicetree.org/schemas/ufs/qcom,sc7180-ufshc.yaml#
/home/runner/work/_temp/round61-ufs-fixtures/ufs-sm8250-1-domain-valid.dtb: ufs@1d84000: power-domains: [[10, 0]] is too short
	from schema $id: http://devicetree.org/schemas/ufs/qcom,sc7180-ufshc.yaml#
/home/runner/work/_temp/round61-ufs-fixtures/ufs-sm8250-1-domain-valid.dtb: ufs@1d84000: Unevaluated properties are not allowed ('interrupts', 'power-domains', 'qcom,vccq-parent-max-microamp', 'qcom,vccq-parent-supply', 'qcom,vddp-ref-clk-max-microamp', 'qcom,vddp-ref-clk-supply' were unexpected)
	from schema $id: http://devicetree.org/schemas/ufs/qcom,sc7180-ufshc.yaml#

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
/home/runner/work/_temp/ack/Documentation/devicetree/bindings/iommu/pkvm,pviommu.yaml: ignoring, error parsing file
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
/home/runner/work/_temp/dtschema-venv/bin/dt-extract-example:75: SyntaxWarning: "\s" is an invalid escape sequence. Such sequences will not work in the future. Did you mean "\\s"? A raw string is also an option.
  root_node = re.search('/\s*{', ex)
/home/runner/work/_temp/dtschema-venv/bin/dt-extract-example:79: SyntaxWarning: "\s" is an invalid escape sequence. Such sequences will not work in the future. Did you mean "\\s"? A raw string is also an option.
  int_val = re.search('\sinterrupts\s*=\s*<([0-9a-zA-Z |()_]+)>', ex).group(1)
  DTC [C] Documentation/devicetree/bindings/phy/qcom,sc8280xp-qmp-ufs-phy.example.dtb
  DTEX    Documentation/devicetree/bindings/ufs/ufs-common.example.dts
/home/runner/work/_temp/dtschema-venv/bin/dt-extract-example:75: SyntaxWarning: "\s" is an invalid escape sequence. Such sequences will not work in the future. Did you mean "\\s"? A raw string is also an option.
  root_node = re.search('/\s*{', ex)
/home/runner/work/_temp/dtschema-venv/bin/dt-extract-example:79: SyntaxWarning: "\s" is an invalid escape sequence. Such sequences will not work in the future. Did you mean "\\s"? A raw string is also an option.
  int_val = re.search('\sinterrupts\s*=\s*<([0-9a-zA-Z |()_]+)>', ex).group(1)
  DTC [C] Documentation/devicetree/bindings/ufs/ufs-common.example.dtb
  DTEX    Documentation/devicetree/bindings/ufs/qcom,sc7180-ufshc.example.dts
/home/runner/work/_temp/dtschema-venv/bin/dt-extract-example:75: SyntaxWarning: "\s" is an invalid escape sequence. Such sequences will not work in the future. Did you mean "\\s"? A raw string is also an option.
  root_node = re.search('/\s*{', ex)
/home/runner/work/_temp/dtschema-venv/bin/dt-extract-example:79: SyntaxWarning: "\s" is an invalid escape sequence. Such sequences will not work in the future. Did you mean "\\s"? A raw string is also an option.
  int_val = re.search('\sinterrupts\s*=\s*<([0-9a-zA-Z |()_]+)>', ex).group(1)
  DTC [C] Documentation/devicetree/bindings/ufs/qcom,sc7180-ufshc.example.dtb
  DTEX    Documentation/devicetree/bindings/ufs/qcom,ufs.example.dts
/home/runner/work/_temp/dtschema-venv/bin/dt-extract-example:75: SyntaxWarning: "\s" is an invalid escape sequence. Such sequences will not work in the future. Did you mean "\\s"? A raw string is also an option.
  root_node = re.search('/\s*{', ex)
/home/runner/work/_temp/dtschema-venv/bin/dt-extract-example:79: SyntaxWarning: "\s" is an invalid escape sequence. Such sequences will not work in the future. Did you mean "\\s"? A raw string is also an option.
  int_val = re.search('\sinterrupts\s*=\s*<([0-9a-zA-Z |()_]+)>', ex).group(1)
  DTC [C] Documentation/devicetree/bindings/ufs/qcom,ufs.example.dtb
  DTEX    Documentation/devicetree/bindings/ufs/qcom,ufs-common.example.dts
/home/runner/work/_temp/dtschema-venv/bin/dt-extract-example:75: SyntaxWarning: "\s" is an invalid escape sequence. Such sequences will not work in the future. Did you mean "\\s"? A raw string is also an option.
  root_node = re.search('/\s*{', ex)
/home/runner/work/_temp/dtschema-venv/bin/dt-extract-example:79: SyntaxWarning: "\s" is an invalid escape sequence. Such sequences will not work in the future. Did you mean "\\s"? A raw string is also an option.
  int_val = re.search('\sinterrupts\s*=\s*<([0-9a-zA-Z |()_]+)>', ex).group(1)
  DTC [C] Documentation/devicetree/bindings/ufs/qcom,ufs-common.example.dtb

## round61-ufs-example-validation.log
/home/runner/work/_temp/ack/Documentation/devicetree/bindings/ufs/qcom,ufs.example.dtb: ufs@1d84000: power-domains: [[4294967295, 3]] is too short
	from schema $id: http://devicetree.org/schemas/ufs/qcom,ufs.yaml#
/home/runner/work/_temp/ack/Documentation/devicetree/bindings/ufs/qcom,ufs.example.dtb: ufs@1d84000: Unevaluated properties are not allowed ('#reset-cells', 'freq-table-hz', 'interrupts', 'iommus', 'lanes-per-direction', 'phy-names', 'phys', 'power-domains', 'reset-gpios', 'reset-names', 'resets', 'vcc-max-microamp', 'vcc-supply', 'vccq-max-microamp', 'vccq-supply' were unexpected)
	from schema $id: http://devicetree.org/schemas/ufs/qcom,ufs.yaml#

## dt_binding_check log SHA-256
3991e6bd283b3e1e09f6b185c6337839fed89fa21f48e329775b094d1bba4258  /home/runner/work/_temp/round61-dt-binding-check.log
