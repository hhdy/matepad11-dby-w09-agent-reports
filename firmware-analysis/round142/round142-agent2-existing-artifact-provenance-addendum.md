# ROUND142 — 2号 Agent existing-artifact provenance addendum

- Executor: **2号 Agent** (the local build agent that executed ROUND140; not 2号 AI, not WorkBuddy Agent)
- Date: 2026-11-26
- Device target: Huawei MatePad 11 (2021), DBY-W09 / KONA / SM8250 v2.1
- Fixed ACK: `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a` (`android17-6.18.33_r00`)
- Candidate content tree: `afe9517f8062b96bfeb5b4dd5714942861e6a44b`
- Mode: offline, read-only inspection of artifacts produced by ROUND140 in this Agent's own round directory
- Result: **PARTIAL — SOME PROVENANCE NOT RETAINED** (Workstream B reclassified from UNRESOLVED to COMPLIANT; certificate cause upgraded to directly demonstrated; BTF cause remains supported-not-demonstrated)

## 0. Scope, boundary and what this round actually did

Inspected roots (only these):

```
/home/kerneldev/work/matepad11/round140-agent2/tree       independent candidate source tree
/home/kerneldev/work/matepad11/round140-agent2/logs       ROUND140 logs (6 files)
/home/kerneldev/work/matepad11/round140-agent2/a30build   ROUND140 staging + its bazel output root
/home/kerneldev/work/matepad11/round140-agent2/out-dtb    ROUND140 independent DTB output
```

Not inspected: any other Agent's workspace (including `round135-r3-agent`, `round135-r3v-agent`, `round135-r2`, and WorkBuddy Agent directories), cloud storage, arbitrary drives or user folders. Because of that boundary, the **R3/ROUND135-side tool identity and command line are not re-inspectable in this round** and are reported as out of scope rather than re-derived.

Operations performed: `cat`/`grep`/`sed`/`readelf`/`find`/`stat`/`sha256sum`, one `pahole --version`, one gzip+JSON read of the retained Bazel profile, and one read-only Python parse of the retained decompiled DTB text. No build, no Kbuild, no Bazel, no repository rule, no dtc, no dtbs_check, no test execution, no cache clearing, no source/patch/DTS/DTBO/config modification.

Network: none was used for inspection. Two network uses are disclosed and were unavoidable/authorized:
1. the four ROUND142 §1 documents were read over HTTPS as instructed by the taskbook;
2. this addendum was pushed to its branch (ROUND142 §7).

## 1. Workstream A — BTF / pahole / signing-certificate provenance

### 1.1 Tool identity (retained, hashed)

| Item | Value | Evidence |
|---|---|---|
| pahole binary | `prebuilts/kernel-build-tools/linux_musl-x86/bin/pahole` | `prebuilts/kernel-build-tools/BUILD.bazel:193-196` (`prebuilt_tool(name = "pahole")`) |
| pahole size | 4 658 936 B | `stat` |
| pahole SHA-256 | `0009fccb6c76343c7877537ce0e8ff1a7e44be67735a44b4c0cbf4d51146cea2` | `sha256sum` |
| pahole version | **v1.27** | `pahole --version` (query only, no build) |
| pahole mtime | 2026-11-24 23:46:56 +08 — predates the build by ~2 days; pre-existing pinned prebuilt, not fetched | `stat` |
| Bazel-exposed tool | `bazel-out/k8-opt-exec-ST-d57f47055a04/bin/prebuilts/kernel-build-tools/pahole` | console line `[253 / 775] [Prepa] Creating symlink prebuilts/kernel-build-tools/pahole [for tool]` (`bazel-build-raw.log:24`) |
| PAHOLE handed to Kbuild | `PAHOLE=<root>/prebuilts/kernel-build-tools/pahole` (or the `bazel-out` exec path) | `bazel-out/k8-fastbuild/bin/common/dby_w09_env.sh:326-330` |
| `resolve_btfids` | source present at `tree/tools/bpf/resolve_btfids/{Makefile,main.c,Build}`; **built binary NOT RETAINED** | `find` over the execroot returns nothing; see §8 |

`resolve_btfids` binary SHA-256 and version: **NOT FOUND**. Kleaf copies only declared outputs into `bazel-out/k8-fastbuild/bin/common/dby_w09/`, which contains `.config`, `Image`, `System.map`, `vmlinux`, `include/` and two tarballs only; the per-build Kbuild intermediate tree (and therefore `tools/bpf/resolve_btfids/resolve_btfids`) is inside the sandbox and was discarded.

### 1.2 BTF generation command and flags (derived from retained inputs, not from a retained action log)

```
Kbuild:  scripts/link-vmlinux.sh:110-115  gen_btf()
         :115  LLVM_OBJCOPY="${OBJCOPY}" ${PAHOLE} -J ${PAHOLE_FLAGS} ${1}
         then objcopy --only-section=.BTF --set-section-flags .BTF=alloc,readonly --strip-all

Kleaf:   build/kernel/kleaf/impl/btf.bzl:44-52 (separate Btf action for the module BTF base)
         cp -Lp <vmlinux> <out>/vmlinux.btf ; <pahole> -J <out>/vmlinux.btf ; <llvm-strip> --strip-debug
```

Flag derivation, all inputs retained:

| Input | Value | Source |
|---|---|---|
| `CONFIG_PAHOLE_VERSION` | 127 | `.config:34` |
| branch selected | `>=126 and <130` → `--btf_features` form | `scripts/Makefile.btf:21-24` |
| BTF flags | `-j<JOBS> --btf_features=encode_force,var,float,enum64,decl_tag,type_tag,optimized_func,consistent_func,decl_tag_kfuncs` | `scripts/Makefile.btf:24` |
| extra flag | `--lang_exclude=rust` | `scripts/Makefile.btf:34` with `CONFIG_PAHOLE_HAS_LANG_EXCLUDE=y` (`.config:8364`) |
| `JOBS` | `$(patsubst -j%,%,$(filter -j%,$(MAKEFLAGS)))` → **12** in this build | `scripts/Makefile.btf:6`; `MAKEFLAGS` gain `-j$(MAKE_JOBS or nproc)` at `build/kernel/kleaf/impl/kernel_env.bzl:612-619`; `nproc=12` (`stage-b-kleaf-build.log:12`); no `--make_jobs` in the recorded command (`stage-b-kleaf-build.log:56`, `tools/bazel build //common:dby_w09 --jobs=2` — Bazel `--jobs` is not the `MAKE_JOBS` volatile status) |

Environment values that materially affect the output (retained, `dby_w09_env.sh`):

```
KBUILD_BUILD_HOST      = build-host                              (:85)
KBUILD_BUILD_TIMESTAMP = Thu Jan  1 00:00:00 UTC 1970            (:86)
KBUILD_BUILD_USER      = kleaf                                   (:87)
KBUILD_BUILD_VERSION   = 1                                       (:88)
SOURCE_DATE_EPOCH      = 0                                       (:117)
CC = clang ; LLVM = 1                                            (:74, :97)
```

The literal command line **as executed by the build action** is **NOT FOUND**: no per-action `.params`, `--subcommands`, `-s` action log or `debug_print_scripts` output was retained (the retained console log is the default progress log, 57 lines).

### 1.3 Signing certificate provenance

| Fact | Value | Source |
|---|---|---|
| module signing enabled | `CONFIG_MODULE_SIG=y`, `CONFIG_MODULE_SIG_ALL=y`, `CONFIG_MODULE_SIG_SHA1=y`, `CONFIG_MODULE_SIG_HASH="sha1"` | `.config:933,935,937,944` |
| key selection | `CONFIG_MODULE_SIG_KEY="certs/signing_key.pem"` (the auto-generate branch) | `.config:8133`; branch condition `certs/Makefile:43` |
| generation rule | `cmd_gen_key = openssl req -new -nodes -utf8 -sha1 -days 36500 -batch -x509 -config $< -outform PEM -out $@ -keyout $@` | `certs/Makefile:48` |
| regeneration trigger | `$(obj)/signing_key.pem: $(obj)/x509.genkey FORCE` | `certs/Makefile:52` |
| subject template | `default_bits = 4096`, `CN = Build time autogenerated kernel key` | `certs/default_x509.genkey` |
| key present in source? | **no** — neither `certs/signing_key.pem` nor `certs/x509.genkey` exists in the tree | `ls` fails on both |
| generated files retained? | **no** — no `certs/` under `bazel-out/.../bin/common/dby_w09`, no `signing_key*` anywhere in the execroot | `find` |
| certificate actually embedded? | yes — the literal `Build time autogenerated kernel key` byte string is present in **my own** `vmlinux`; the form `CN=Build time autogenerated kernel key` is not, because DER stores the RDN type separately from the value | direct byte scan of `vmlinux` |

`KBUILD_BUILD_TIMESTAMP=1970` and `SOURCE_DATE_EPOCH=0` do **not** pin this certificate: `openssl req` takes `notBefore` from the real clock and generates a fresh 4096-bit key and signature at every build. This is a fixed property of the configuration, not an accident of this run.

### 1.4 Verdicts (stated separately as required)

- **CERTIFICATE DIFFERENCE — directly demonstrated.** The configuration selects a per-build autogenerated RSA-4096 key (`certs/Makefile:43-52`, no fixed key in the tree, `.config:8133`), the subject literal from `default_x509.genkey` is demonstrably embedded in the produced `vmlinux`, and neither the timestamp nor `SOURCE_DATE_EPOCH` pins `openssl`. Byte-identical `Image` output is therefore unachievable without supplying a fixed signing key, which is not authorized.
- **BTF DELTA CAUSE — supported, not demonstrated.** The retained inputs fix the tool (`v1.27`, SHA-256 above), the flag set and the config; the delta is confined to the BTF type/string set. Independently re-verified this round in **my own** artifact: my `.BTF` string table does **not** contain `ro_image_end`, which corroborates the ROUND140 direction ("the R3 build carries one extra name, absent from mine"). A plausible mechanism is pahole's threaded type emission (`-j12`); there is no retained per-action log and no second identical-input build, so it stays a hypothesis.
- **BTF CROSS-BUILD REPRODUCIBILITY — not proven.** One comparison exists; reproducibility is neither established nor refuted.

Retained BTF baseline of my own artifact (for future rounds):

```
.BTF       size 0x70fce5 = 7 404 773   vaddr ffffffc081c4a000
.BTF_ids   size 0x1208   = 4 616
.init.data size 0x2d228  = 184 872
.debug_info size 0x7e34133 = 132 333 875
BTF header: ver=1 hdr_len=24 type_len=4 450 648 str_len=2 954 101
```

## 2. Workstream B — Bazel / Kleaf repository fetch and cache provenance

No Bazel command, repository rule, curl, wget or git fetch was run in this round. Only retained files were read.

### 2.1 Fetch-event inventory (what exists, and what does not)

| # | Evidence class | Observation | Source |
|---:|---|---|---|
| 1 | Build console | 57 lines total; **zero** `Fetching`, `Downloading`, `WARNING: Download` lines. The only cache-related output is `[n / 775] checking cached actions` (5 lines, action cache, not repository fetch) | `bazel-build-raw.log` (SHA-256 `894b8fa0…`) |
| 2 | Bazel build profile | 150 545 B gzip / 2 170 312 B JSON; **0 occurrences of any `http://` or `https://` URL**; 252 `context.prefetchInputs` (sandbox input staging) and 75 `fetch module file: <name>@<ver>` events with durations 12–260 µs, i.e. local file reads | `command.profile.gz` |
| 3 | bzlmod registry | `common:bzlmod --registry=file://%workspace%/external/bazelbuild-bazel-central-registry` — a **local file registry** | `build/kernel/kleaf/bazelrc/bzlmod.bazelrc:21` |
| 4 | Local registry snapshot | directory mtime 2026-11-24 23:38:20, git `HEAD 37c7fdc1ef273e518f1ded9495c5fc3afc2dabe9` — vendored ~2 days before the build | `external/bazelbuild-bazel-central-registry` |
| 5 | External repositories | 92 entries in the output root's `external/` = 25 directories + 21 symlinks + 46 `@*.marker` files; sampled repos are symlink farms into the workspace's own `external/{lz4,dtc,…}` trees (e.g. `+_repo_rules2+dtc/.git -> a30build/external/dtc/.git`) | `external/` |
| 6 | Archive payloads | `*.tar.gz|*.tar.xz|*.zip|*.tgz` under `external/` = **0** | `find` |
| 7 | Repository cache | `output_user_root/cache` **absent**; `~/.cache/bazel` **absent** → no archive cache existed to hit, and none was created | `ls` |
| 8 | Bazel's own accounting | `Remote (0.00% of the time): [parse 0.00%, queue 0.00%, network 0.00%, upload 0.00%, setup 0.00%, process 0.00%, fetch 0.00%, retry 0.00% …]` | `java.log:135` |
| 9 | Output-root provenance | `output_user_root` created 2026-11-26 20:17, build start 20:16:41 — fresh root, R3's output root neither reused nor read | `stat`, `stage-b-kleaf-build.log:16,51` |

### 2.2 Classification

**COMPLIANT** — the retained evidence shows no prohibited new dependency payload was fetched. Every external repository in this build was materialised from the workspace's own vendored trees plus a `file://` module registry that predates the build; there is no repository cache, no archive, no URL and no fetch-time accounting in Bazel's own statistics.

### 2.3 Self-correction of the ROUND140 report (required)

ROUND140 report line 39 states:

```
network             = external Kleaf repositories fetched at build time (mirror.bazel.build 200, github.com 200)
```

That sentence is **wrong as written** and is hereby corrected. It merged two different things:

1. a **reachability probe** issued by my own diagnostic shell before the build — HTTP status of four host roots (`mirror.bazel.build`, `releases.bazel.build`, `github.com`, `dl.google.com`) with the body discarded (`-o /dev/null`), two of which returned 200. The only retained record is `stage-b-kleaf-build.log:22-23`; shell history was not retained, so this cannot be re-executed or re-verified;
2. an **assumption** that Kleaf fetches external repositories at build time.

The retained build artifacts contradict (2): no fetch line, no URL in the profile, no repository cache, no archive, `fetch: 0.00%`. The two `200` codes belong to (1) only, and (1) transferred no repository payload.

Process disclosure, kept separate from the dependency-fetch question: the probe in (1) was outbound HTTP from the build host that the ROUND140 taskbook did not require. It is recorded here as a **minor process deviation**, not as a dependency-fetch deviation, and it must not be silently dropped. No firmware, source or dependency byte was downloaded at any point in ROUND140 or ROUND142.

## 3. Workstream C — candidate UFS source readback (read-only, my own tree)

### 3.1 `qcom,vddp-ref-clk-supply` consumer

| Element | Exact location | Content |
|---|---|---|
| compatibility guard | `drivers/ufs/host/ufs-qcom.c:1531-1534` | returns 0 unless `dev->of_node` **and** `of_device_is_compatible(dev->of_node, "qcom,sm8250-ufshc")` **and** `of_find_property(dev->of_node, "qcom,vddp-ref-clk-supply")` |
| load property | `:1536-1541` | reads `qcom,vddp-ref-clk-max-microamp`; missing → `dev_err_probe`; zero → `-EINVAL` |
| regulator get | `:1543-1544` | `devm_regulator_get(dev, "qcom,vddp-ref-clk")` — the framework resolves the `<name>-supply` property, so this is the same DT property, not a name mismatch |
| cleanup | `:1501-1523`, registered at `:1555` | `regulator_disable()` then `regulator_set_load(..., 0)` in `ufs_qcom_vddp_ref_clk_cleanup()` |
| load vote | `:1559-1562` | `regulator_set_load(host->vddp_ref_clk, load_uA)`, then `host->vddp_ref_clk_load_set = true` |
| enable | `:1564-1567` | `regulator_enable(host->vddp_ref_clk)`, then `host->vddp_ref_clk_enabled = true` |
| call site / ordering | `:1660` inside `ufs_qcom_init()` (`:1582`) | after `devm_phy_get()` `:1616` (get only — no `phy_power_on`), after `ufs_qcom_icc_init()` `:1623`, after `ufs_qcom_init_lane_clks()` `:1646`; **before** `ufs_qcom_setup_clocks(hba, true, POST_CHANGE)` `:1664`, which is where `phy_power_on()` is reached (`:1420`). `ufshcd_pltfrm_init()` runs later at `:3098`. |

So the REF_CLK pad rail is enabled while the PHY is still un-powered and the host clocks have not been ramped by `setup_clocks`; nothing re-orders it after PHY power-on. This is candidate-only behaviour (patch 06), consistent with ROUND141 §2.1.

### 3.2 `qcom,vccq-parent-supply` consumer search

```
grep -rn "vccq-parent" --include=*.c --include=*.h  → 0 hits (whole tree)
hits are confined to: arch/arm64/boot/dts/qcom/huawei-dby-w09.dts:136, 254, 276-281
                      Documentation/devicetree/bindings/ufs/qcom,ufs-common.yaml:56,61,112,115
```

A DT property plus its binding is not a consumer. The generic parser reads exactly four rails and nothing else:

```
drivers/ufs/host/ufshcd-pltfrm.c:175-196  ufshcd_parse_regulator_info()
  :181 vdd-hba   :185 vcc   :189 vccq   :193 vccq2
```

**Result: no effective consumer.** S8 remains inert metadata; the load vote at `dts:281` is a no-op and no enable or sequencing owner exists.

### 3.3 Property → provider → consumer → result

Providers resolved from the **already-existing** ROUND140 decompiled DTB (`logs/dtb-decompiled.dts`), no dtc run:

| UFS property | DTS line | Provider (DTB phandle) | Provider node in DTS | Code consumer | Result |
|---|---|---|---|---|---|
| `vcc-supply` | `:267` | `0x5d` → `/soc@0/rsc@18200000/regulators-0/ldo17` | `:209-217` (`regulator-name = pm8150_l17`) | `ufshcd-pltfrm.c:185` | DIRECT static link |
| `vccq-supply` | `:271` | `0x5e` → `…/regulators-0/ldo6` | `:187-195` (`pm8150_l6`) | `:189` | DIRECT static link |
| `vccq2-supply` | `:287` | `0x60` → `…/regulators-0/smps4` | `:168-173` (`pm8150_s4`) | `:193` | DIRECT static link |
| `qcom,vddp-ref-clk-supply` | `:284` | `0x5e` → `…/regulators-0/ldo6` | `:187-195` (`pm8150_l6`) | `ufs-qcom.c:1543/1559/1564` | DIRECT static link, **candidate-only** (patch 06) |
| `qcom,vccq-parent-supply` | `:280-281` | `0x5f` → `…/regulators-1/smps8` | `:235-242` (`regulator-name = pm8150l_s8`) | **none** (0 hits in `.c`/`.h`) | **INERT** — no enable, no vote, no sequence |
| `vdda-phy-supply` | `:294` | `0x63` → `…/regulators-0/ldo5` | `:176-184` (`pm8150_l5`) | `phy-qcom-qmp-ufs.c:1212-1215` (89 900 µA) | DIRECT static link |
| `vdda-pll-supply` | (PHY node) | `0x64` → `…/regulators-0/ldo9` | `:198-206` (`pm8150_l9`) | same bulk table (18 800 µA) | DIRECT static link |
| `vdd-hba-supply` | **absent** (`:252-253` explains why) | — | — | `ufshcd-pltfrm.c:181` missing-supply path (non-fatal, "assuming enabled") | deliberate omission; GDSC is **not** a regulator |

Supporting structural facts, from the same retained decompile:

```
ufshc@1d84000: power-domains = <0x34 0x06 0x30 0x04>         (DEC:2102)
               0x34 = qcom,sm8250-rpmhpd (DEC:5267-5270)
               0x30 = clock-controller@100000, qcom,gcc-sm8250 (DEC:975-983)
               0x06 = RPMHPD_MMCX, 0x04 = UFS_PHY_GDSC (dt-bindings/clock/qcom,gcc-sm8250.h:263)
               qcom,vddp-ref-clk-max-microamp = <0x64>       (DEC:2118) = 100 µA, matching dts:285
               18 direct reserved-memory children; /memory reg = <0x00 0x80000000 0x00 0x00>
```

`qcom,vddp-ref-clk-max-microamp` **is present** in the compiled DTB, so the `:1536-1541` error path is not tripped by the current DTB. (An earlier pass of my own checker printed this property as ABSENT; that was a key-name mismatch in my parser, not a Device Tree gap. Recorded so that no future round inherits the false negative.)

### 3.4 Required terminology correction — node availability is not enablement

All six rail provider nodes carry **no** `status` property and **no** `regulator-always-on`:

| rail | node | DTS lines | `status` | `regulator-always-on` |
|---|---|---|---|---|
| PM8150 S4 | `smps4` | `:168-173` | absent | absent |
| PM8150 L5 | `ldo5` | `:176-184` | absent | absent |
| PM8150 L6 | `ldo6` | `:187-195` | absent | absent |
| PM8150 L9 | `ldo9` | `:198-206` | absent | absent |
| PM8150 L17 | `ldo17` | `:209-217` | absent | absent |
| PM8150L S8 | `smps8` | `:235-242` | absent | absent |

Correct statement, to be used from now on: **the Device Tree node is available by the standard OF availability convention (it is not marked `disabled`); the runtime hardware enable state remains UNKNOWN.** An absent `status` does **not** mean the regulator output is on, has a valid upstream input, has received an RPMh request, or is supplying voltage. The ROUND140 §7.1 wording "absent → enabled" is withdrawn.

## 4. NOT FOUND / UNKNOWN (explicit)

NOT FOUND (searched, not retained):

1. executed pahole/BTF command line per action (no `.params`, `--subcommands` or `debug_print_scripts` record);
2. `resolve_btfids` binary and its hash/version;
3. the generated `certs/signing_key.pem` / `x509.genkey` files and any `GENKEY` log line;
4. R3/ROUND135-side tool identity and command line — **out of boundary this round** (another Agent's workspace);
5. shell history of the ROUND140 reachability probe (only its result line survives).

UNKNOWN (not closable by log inspection):

- whether pahole v1.27 with `-j12` emits BTF type numbering deterministically for these inputs;
- runtime enable state and actual voltage of all six UFS rails;
- physical PMIC input parents for L5/L6/L9/L17/S4/S8;
- MMCX/MX runtime CMD-DB / RPMh vote behaviour and physical-corner equivalence;
- final post-ABL FDT, usable RAM tuples, reservation ownership;
- actual device DTBO identity and ABL selection;
- ABL boot-v2 / independent ramdisk policy;
- full cryptographic AVB verification and `vbmeta_cust` footer provenance;
- device-matched backups and a tested HOS4.3 recovery route.

## 5. Impact on the first-boot gates

Nothing here closes or opens a hardware gate. Precisely:

| Gate | Before ROUND142 | After ROUND142 |
|---|---|---|
| Image byte-identity explanation | PARTIAL — certificate "sound explanation" | **CERTIFICATE: directly demonstrated**; BTF cause still supported-not-demonstrated |
| Network/dependency-policy compliance | UNRESOLVED | **COMPLIANT** (evidence-based), with one minor process deviation disclosed (§2.3) |
| UFS candidate consumer mapping | report-confirmed | **raw-source readback complete**, line-exact; S8 confirmed inert; missing-load error path confirmed not tripped |
| Regulator/provider status wording | "absent → enabled" | **corrected**: node available, runtime enable UNKNOWN |
| Physical PMIC inputs, MMCX/MX votes, final FDT/RAM, DTBO identity, ABL policy, AVB, recovery | BLOCKED / CONDITIONAL | **unchanged** |
| First device boot | NOT AUTHORIZED | **NOT AUTHORIZED** |

The two provenance questions assigned to this Agent are answered to the limit of the retained artifacts: fetch compliance is now evidence-based rather than unresolved, and the certificate half of the Image-digest difference is demonstrated rather than merely plausible. The BTF half stays honestly partial, and no rebuild was performed to force it.

## 6. Inspected-file digest register

```
894b8fa03294b7629add86a34b22b5f4fd9720b877c1d25e910485ab10e9b6b2   3894  logs/bazel-build-raw.log
fac6f4eee5d807caecec65dc460fb4659ab1cb73a01b317ea32da7ceffb41103   1317  logs/dtb-build-raw.log
d054ec0f95275fb006dd0bd12ed2f064fa43be43ae8e81f881a1caf8970663c1 146546  logs/dtb-decompiled.dts
ea95a91376845856ca8079dbff820ebcf0691d0701d16e31992133771139b723  26431  logs/stage-a-identity-apply.log
d8e991508fb20652a54193f6d16e446cb395e2356d684bdc57cde87ef862ac71   9550  logs/stage-b-kleaf-build.log
78be9bd1adbd2756d5ba79296102c2bcfb7fdfd84f918886132ce5f86bb8c923  12164  logs/stage-b4-dtb-build-and-structure.log
0009fccb6c76343c7877537ce0e8ff1a7e44be67735a44b4c0cbf4d51146cea2 4658936  prebuilts/kernel-build-tools/linux_musl-x86/bin/pahole (v1.27)
33a6df12cea466057ea984b2c35f00163b3a699b916eb4d81306c2b82599686f  77991  a30build/out/bazel/output_user_root/<hash>/java.log
```

Build outputs of ROUND140, re-hashed this round for continuity (not rebuilt):

```
a0f39ee8c992d554824af86c5abbf3f22bb32f324578fc78bde761f8ee7b969c  Image      44 820 992 B
c0e9329744ced3609d71a3a11ba89c783ac6d946844f1ab3391422ab99287faa  vmlinux   230 259 072 B
a952852a7f29b29bb6079386c7c60ee643e8e7c2c04a636c1be3a30ad3079900  System.map  7 611 571 B
cab82fe3901bdb40533197eeb48b2d99b08b46e5d5497ff1a6f688e9938db77e  huawei-dby-w09.dtb  108 648 B
```

No certificate, key, signature, key identifier or device-unique value is reproduced in this document.

## 7. Final status

**PARTIAL — SOME PROVENANCE NOT RETAINED.**

- Workstream A: tool identity and flag derivation complete and hashed; certificate cause **directly demonstrated**; BTF cause **supported, not demonstrated**; the executed action command line, the `resolve_btfids` binary and the generated key material are **NOT FOUND** because the build sandbox was discarded.
- Workstream B: **COMPLIANT**, evidence-based; the ROUND140 report's fetch sentence is corrected and one minor process deviation is disclosed.
- Workstream C: candidate readback complete with exact file:line evidence; S8 inert confirmed in raw source; the status-property wording corrected.

No gate was promoted. First device boot remains **BLOCKED / NOT AUTHORIZED**.

— END OF ROUND142 ADDENDUM —
