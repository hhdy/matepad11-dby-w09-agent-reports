# ROUND61 hosted UFS / ROUND63 PHY validation

- Workflow commit: 6c22d14157720edfafa1f4a525552bee65a7fff2
- Workflow run ID: 45627361865
- Branch: ai-parallel/stagea-port-until-boot
- Job status: success
- Fixed ACK commit: 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a


## Processed schema SHA-256
35e2f6a6681fe33a4ecf3d41c4991891582655aa8c708a96b06f9e9f7f064c05  /home/runner/work/_temp/round61-processed-schema.json
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

## round63-phy-legacy-validation.log

## round63-phy-positive-validation.log

## ufs-sm8250-1-domain-valid-validation.log

## ufs-sm8250-2-domains-valid-validation.log

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
  DTEX    Documentation/devicetree/bindings/ufs/qcom,sc7180-ufshc.example.dts
/home/runner/work/_temp/dtschema-venv/bin/dt-extract-example:75: SyntaxWarning: "\s" is an invalid escape sequence. Such sequences will not work in the future. Did you mean "\\s"? A raw string is also an option.
  root_node = re.search('/\s*{', ex)
/home/runner/work/_temp/dtschema-venv/bin/dt-extract-example:79: SyntaxWarning: "\s" is an invalid escape sequence. Such sequences will not work in the future. Did you mean "\\s"? A raw string is also an option.
  int_val = re.search('\sinterrupts\s*=\s*<([0-9a-zA-Z |()_]+)>', ex).group(1)
  DTC [C] Documentation/devicetree/bindings/ufs/qcom,sc7180-ufshc.example.dtb
  DTEX    Documentation/devicetree/bindings/ufs/qcom,ufs-common.example.dts
/home/runner/work/_temp/dtschema-venv/bin/dt-extract-example:75: SyntaxWarning: "\s" is an invalid escape sequence. Such sequences will not work in the future. Did you mean "\\s"? A raw string is also an option.
  root_node = re.search('/\s*{', ex)
/home/runner/work/_temp/dtschema-venv/bin/dt-extract-example:79: SyntaxWarning: "\s" is an invalid escape sequence. Such sequences will not work in the future. Did you mean "\\s"? A raw string is also an option.
  int_val = re.search('\sinterrupts\s*=\s*<([0-9a-zA-Z |()_]+)>', ex).group(1)
  DTC [C] Documentation/devicetree/bindings/ufs/qcom,ufs-common.example.dtb
  DTEX    Documentation/devicetree/bindings/ufs/qcom,ufs.example.dts
/home/runner/work/_temp/dtschema-venv/bin/dt-extract-example:75: SyntaxWarning: "\s" is an invalid escape sequence. Such sequences will not work in the future. Did you mean "\\s"? A raw string is also an option.
  root_node = re.search('/\s*{', ex)
/home/runner/work/_temp/dtschema-venv/bin/dt-extract-example:79: SyntaxWarning: "\s" is an invalid escape sequence. Such sequences will not work in the future. Did you mean "\\s"? A raw string is also an option.
  int_val = re.search('\sinterrupts\s*=\s*<([0-9a-zA-Z |()_]+)>', ex).group(1)
  DTC [C] Documentation/devicetree/bindings/ufs/qcom,ufs.example.dtb
  DTEX    Documentation/devicetree/bindings/ufs/ufs-common.example.dts
/home/runner/work/_temp/dtschema-venv/bin/dt-extract-example:75: SyntaxWarning: "\s" is an invalid escape sequence. Such sequences will not work in the future. Did you mean "\\s"? A raw string is also an option.
  root_node = re.search('/\s*{', ex)
/home/runner/work/_temp/dtschema-venv/bin/dt-extract-example:79: SyntaxWarning: "\s" is an invalid escape sequence. Such sequences will not work in the future. Did you mean "\\s"? A raw string is also an option.
  int_val = re.search('\sinterrupts\s*=\s*<([0-9a-zA-Z |()_]+)>', ex).group(1)
  DTC [C] Documentation/devicetree/bindings/ufs/ufs-common.example.dtb

## round61-ufs-example-validation.log

## round63-phy-negative-validation.log
vdda-phy-always-on: size (4) error for type flag
/home/runner/work/_temp/round63-phy-always-on-invalid-type.dtb: ufs-phy@1d87000: vdda-phy-always-on: [[1]] is not of type 'boolean'
	from schema $id: http://devicetree.org/schemas/phy/qcom,sc8280xp-qmp-ufs-phy.yaml#

## round63-phy-undeclared-validation.log
/home/runner/work/_temp/round63-phy-undeclared-property.dtb: ufs-phy@1d87000: 'vdda-phy-always-on-extra' does not match any of the regexes: 'pinctrl-[0-9]+'
	from schema $id: http://devicetree.org/schemas/phy/qcom,sc8280xp-qmp-ufs-phy.yaml#

## dt_binding_check log SHA-256
a87faad1f06f6db6839b141aeeec6dffd241e8e3444a39c21cbe687af053cb2e  /home/runner/work/_temp/round61-dt-binding-check.log
