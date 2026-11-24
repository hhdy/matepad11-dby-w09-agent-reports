# ROUND61 hosted manifest/Kleaf build result

- Date UTC: 2026-11-24T18:21:43Z
- Branch: ai-parallel/stagea-port-until-boot
- Trigger commit: 1b833dd74ddb39dd90f7a691f62ce313e0dfe5d2
- Workflow run ID: 45453412267
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
[30 / 759] [Prepa] Expanding template build/kernel/kleaf/impl/_cache_dir_config_tags.venv/lib/python3.11/site-packages/_bazel_site_init.py [for tool]
[43 / 759] [Prepa] Creating symlink prebuilts/build-tools/bzip2 [for tool]
[53 / 759] checking cached actions
[149 / 775] checking cached actions
[159 / 775] checking cached actions
[159 / 775] [Prepa] Creating common_config_tags //common:dby_w09_env
[163 / 775] checking cached actions
[164 / 775] checking cached actions
[164 / 775] [Prepa] Symlinking virtual headers for //prebuilts/kernel-build-tools:imported_libs [for tool]
[280 / 775] checking cached actions
[280 / 775] [Prepa] Symlinking virtual headers for //prebuilts/kernel-build-tools:imported_libs [for tool]
[372 / 775] Compiling build/kernel/_dispatched/bison_source.cpp [for tool]; 0s linux-sandbox ... (2 actions, 1 running)
[380 / 775] Executing genrule @@+_repo_rules2+dtc//:dtc_parser_srcs [for tool]; 0s linux-sandbox ... (3 actions, 2 running)
[396 / 775] Compiling lib/decompress/zstd_decompress_block.c [for tool]; 0s linux-sandbox ... (3 actions, 2 running)
[412 / 775] Compiling lib/compress/zstd_lazy.c [for tool]; 0s linux-sandbox ... (3 actions, 2 running)
[429 / 775] Compiling lib/compress/fse_compress.c [for tool]; 0s linux-sandbox ... (3 actions, 2 running)
[462 / 775] Compiling toys/posix/xargs.c [for tool]; 0s linux-sandbox ... (3 actions, 2 running)
[483 / 775] Compiling build/kernel/_dispatched/tar_source.cpp [for tool]; 0s linux-sandbox ... (3 actions running)
[501 / 775] Compiling toys/posix/tee.c [for tool]; 0s linux-sandbox ... (3 actions running)
[514 / 775] Compiling pigz.c [for tool]; 0s linux-sandbox ... (3 actions running)
[527 / 775] Compiling lib/lib.c [for tool]; 0s linux-sandbox ... (3 actions, 2 running)
[541 / 775] Compiling toys/posix/file.c [for tool]; 0s linux-sandbox ... (3 actions, 2 running)
[554 / 775] Compiling lib/lz4hc.c [for tool]; 0s linux-sandbox ... (3 actions, 2 running)
[562 / 775] Compiling lib/lz4.c [for tool]; 0s linux-sandbox ... (3 actions, 2 running)
[578 / 775] Compiling toys/posix/cat.c [for tool]; 0s linux-sandbox ... (3 actions running)
[592 / 775] Compiling programs/bench.c [for tool]; 0s linux-sandbox ... (3 actions, 2 running)
[754 / 775] Compiling util.c [for tool]; 0s linux-sandbox ... (3 actions, 1 running)
[773 / 775] [Prepa] Creating kernel config (dby_w09_storage_first.fragment) //common:dby_w09_config
[773 / 775] Creating kernel config (dby_w09_storage_first.fragment) //common:dby_w09_config; 1s linux-sandbox
[773 / 775] Creating kernel config (dby_w09_storage_first.fragment) //common:dby_w09_config; 10s linux-sandbox
[774 / 775] Building kernel (dby_w09_storage_first.fragment) //common:dby_w09; 1s linux-sandbox
[774 / 775] Building kernel (dby_w09_storage_first.fragment) //common:dby_w09; 11s linux-sandbox
[774 / 775] Building kernel (dby_w09_storage_first.fragment) //common:dby_w09; 41s linux-sandbox
[774 / 775] Building kernel (dby_w09_storage_first.fragment) //common:dby_w09; 101s linux-sandbox
[774 / 775] Building kernel (dby_w09_storage_first.fragment) //common:dby_w09; 161s linux-sandbox
[774 / 775] Building kernel (dby_w09_storage_first.fragment) //common:dby_w09; 221s linux-sandbox
[774 / 775] Building kernel (dby_w09_storage_first.fragment) //common:dby_w09; 281s linux-sandbox
[774 / 775] Building kernel (dby_w09_storage_first.fragment) //common:dby_w09; 341s linux-sandbox
[774 / 775] Building kernel (dby_w09_storage_first.fragment) //common:dby_w09; 401s linux-sandbox
[774 / 775] Building kernel (dby_w09_storage_first.fragment) //common:dby_w09; 461s linux-sandbox
[774 / 775] Building kernel (dby_w09_storage_first.fragment) //common:dby_w09; 521s linux-sandbox
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
[775 / 775] no actions running
INFO: Found 1 target...
Target //common:dby_w09 up-to-date:
  bazel-bin/common/dby_w09/.config
  bazel-bin/common/dby_w09/Image
  bazel-bin/common/dby_w09/System.map
  bazel-bin/common/dby_w09/vmlinux
INFO: Elapsed time: 1348.097s, Critical Path: 1311.53s
INFO: 775 processes: 523 internal, 252 linux-sandbox.
INFO: Build completed successfully, 775 total actions

## Repo sync log tail
Finalizing sync state...
repo sync has finished successfully.

BUILD_PASS
