# ROUND61 hosted manifest/Kleaf build result

- Date UTC: 2026-11-24T18:33:57Z
- Branch: ai-parallel/stagea-port-until-boot
- Trigger commit: 4877a6d2afb643e69e1ac68685983c4495e20936
- Workflow run ID: 45455279898
- Manifest commit: 46a1a5274ff0b40419952c861a8958bba5f28cfc
- ACK required commit: 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a
- Last stage: complete
- Exit code: 0
- Runner resources: CPUs=4, memory.max=unknown
- JAVA_HOME: /home/runner/work/_temp/ack-6.18.33/prebuilts/jdk/jdk11/linux-x86
- Clang path: prebuilts/clang/host/linux-x86/clang-3289846/bin/clang
- Rust path: prebuilts/rust-toolchain/linux-x86/1.91.1.p2/bin/rustc
Filesystem      Size  Used Avail Use% Mounted on
/dev/root       146G   95G   51G  65% /

## Source identity
8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a
2bebe7c443d0e6d5d549fb2a2377dce980d1b15e
6449879cd7081345cf0a2e7060a1e40b9edfe1b8b22629263c96f8e2141a1f11  /home/runner/work/_temp/round61-artifacts/manifest-pinned.xml

## Build log tail
Computing main repo mapping: 
Loading: 
Loading: 0 packages loaded
Analyzing: target //common:dby_w09 (0 packages loaded, 0 targets configured)
Analyzing: target //common:dby_w09 (0 packages loaded, 0 targets configured)

INFO: Analyzed target //common:dby_w09 (0 packages loaded, 0 targets configured).
[40 / 759] [Prepa] action 'SolibSymlink _solib_x86_64/_U_S_Sprebuilts_Skernel-build-tools_Cimported_Ulibs_Ulinux_Umusl-x86_Slib64_Slibz-host.so___Uprebuilts_Skernel-build-tools_Slinux_Umusl-x86_Slib64/libz-host.so'
[123 / 775] checking cached actions
[123 / 775] [Prepa] Creating symlink prebuilts/kernel-build-tools/e2fsck [for tool]
[147 / 775] checking cached actions
[147 / 775] [Prepa] Symlinking virtual headers for //prebuilts/kernel-build-tools:imported_libs [for tool]
[186 / 775] [Prepa] Creating config_tags //common:dby_w09_env
[188 / 775] checking cached actions
[246 / 775] Compiling build/kernel/_dispatched/bison_source.cpp [for tool]; 0s linux-sandbox ... ( 1 action running)
[372 / 775] Compiling build/kernel/_dispatched/bison_source.cpp [for tool]; 1s linux-sandbox ... (3 actions, 2 running)
[384 / 775] Compiling lib/env.c [for tool]; 0s linux-sandbox ... (3 actions running)
[398 / 775] Compiling toys/posix/sort.c [for tool]; 0s linux-sandbox ... (3 actions running)
[412 / 775] Compiling lib/utf8.c [for tool]; 0s linux-sandbox ... (3 actions running)
[428 / 775] Compiling toys/posix/patch.c [for tool]; 0s linux-sandbox ... (3 actions, 2 running)
[448 / 775] Compiling libfdt/fdt_ro.c [for tool]; 0s linux-sandbox ... (2 actions running)
[466 / 775] Compiling build/kernel/_dispatched/flex_source.cpp [for tool]; 0s linux-sandbox ... (2 actions running)
[475 / 775] Compiling pigz.c [for tool]; 0s linux-sandbox ... (3 actions running)
[489 / 775] Compiling toys/posix/cut.c [for tool]; 0s linux-sandbox ... (3 actions running)
[511 / 775] Executing genrule @@+_repo_rules2+dtc//:dtc_parser_srcs [for tool]; 0s linux-sandbox ... (3 actions, 2 running)
[528 / 775] Compiling lib/compress/zstdmt_compress.c [for tool]; 0s linux-sandbox ... (3 actions, 1 running)
[539 / 775] Compiling lib/compress/zstd_lazy.c [for tool]; 0s linux-sandbox ... (3 actions, 2 running)
[555 / 775] Compiling lib/common/fse_decompress.c [for tool]; 0s linux-sandbox ... (3 actions, 2 running)
[571 / 775] Compiling lib/lz4.c [for tool]; 1s linux-sandbox ... (3 actions, 2 running)
[581 / 775] Compiling build/kernel/_dispatched/swig_source.cpp [for tool]; 1s linux-sandbox ... (3 actions, 2 running)
[594 / 775] Compiling gzwrite.c [for tool]; 0s linux-sandbox ... (3 actions, 2 running)
[633 / 775] Compiling build/kernel/_dispatched/rsync_source.cpp [for tool]; 0s linux-sandbox ... (3 actions, 1 running)
[772 / 775] Determining scmversion //common:dby_w09_config; 0s linux-sandbox
[773 / 775] Creating kernel config (dby_w09_storage_first.fragment) //common:dby_w09_config; 1s linux-sandbox
[773 / 775] Creating kernel config (dby_w09_storage_first.fragment) //common:dby_w09_config; 11s linux-sandbox
[774 / 775] [Sched] Building kernel (dby_w09_storage_first.fragment) //common:dby_w09
[774 / 775] Building kernel (dby_w09_storage_first.fragment) //common:dby_w09; 0s linux-sandbox
[774 / 775] Building kernel (dby_w09_storage_first.fragment) //common:dby_w09; 10s linux-sandbox
[774 / 775] Building kernel (dby_w09_storage_first.fragment) //common:dby_w09; 40s linux-sandbox
[774 / 775] Building kernel (dby_w09_storage_first.fragment) //common:dby_w09; 100s linux-sandbox
[774 / 775] Building kernel (dby_w09_storage_first.fragment) //common:dby_w09; 160s linux-sandbox
[774 / 775] Building kernel (dby_w09_storage_first.fragment) //common:dby_w09; 220s linux-sandbox
[774 / 775] Building kernel (dby_w09_storage_first.fragment) //common:dby_w09; 280s linux-sandbox
[774 / 775] Building kernel (dby_w09_storage_first.fragment) //common:dby_w09; 340s linux-sandbox
[774 / 775] Building kernel (dby_w09_storage_first.fragment) //common:dby_w09; 400s linux-sandbox
[774 / 775] Building kernel (dby_w09_storage_first.fragment) //common:dby_w09; 460s linux-sandbox
[774 / 775] Building kernel (dby_w09_storage_first.fragment) //common:dby_w09; 520s linux-sandbox
[774 / 775] Building kernel (dby_w09_storage_first.fragment) //common:dby_w09; 581s linux-sandbox
[774 / 775] Building kernel (dby_w09_storage_first.fragment) //common:dby_w09; 641s linux-sandbox
[774 / 775] Building kernel (dby_w09_storage_first.fragment) //common:dby_w09; 701s linux-sandbox
[774 / 775] Building kernel (dby_w09_storage_first.fragment) //common:dby_w09; 761s linux-sandbox
[774 / 775] Building kernel (dby_w09_storage_first.fragment) //common:dby_w09; 821s linux-sandbox
[774 / 775] Building kernel (dby_w09_storage_first.fragment) //common:dby_w09; 881s linux-sandbox
[774 / 775] Building kernel (dby_w09_storage_first.fragment) //common:dby_w09; 941s linux-sandbox
[774 / 775] Building kernel (dby_w09_storage_first.fragment) //common:dby_w09; 1001s linux-sandbox
[774 / 775] Building kernel (dby_w09_storage_first.fragment) //common:dby_w09; 1061s linux-sandbox
[774 / 775] Building kernel (dby_w09_storage_first.fragment) //common:dby_w09; 1121s linux-sandbox
[774 / 775] Building kernel (dby_w09_storage_first.fragment) //common:dby_w09; 1181s linux-sandbox
[774 / 775] Building kernel (dby_w09_storage_first.fragment) //common:dby_w09; 1241s linux-sandbox
[774 / 775] Building kernel (dby_w09_storage_first.fragment) //common:dby_w09; 1301s linux-sandbox
INFO: Found 1 target...
Target //common:dby_w09 up-to-date:
  bazel-bin/common/dby_w09/.config
  bazel-bin/common/dby_w09/Image
  bazel-bin/common/dby_w09/System.map
  bazel-bin/common/dby_w09/vmlinux
INFO: Elapsed time: 1411.429s, Critical Path: 1374.40s
INFO: 775 processes: 523 internal, 252 linux-sandbox.
INFO: Build completed successfully, 775 total actions

## Repo sync log tail
Finalizing sync state...
repo sync has finished successfully.

BUILD_PASS
