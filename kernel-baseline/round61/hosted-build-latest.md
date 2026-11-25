# ROUND61 hosted manifest/Kleaf build result

- Date UTC: 2026-11-25T02:26:01Z
- Branch: ai-parallel/stagea-port-until-boot
- Trigger commit: eb37d21224a0878059b0ed5eef72a29cdbd69af9
- Workflow run ID: 45529395645
- Manifest commit: 46a1a5274ff0b40419952c861a8958bba5f28cfc
- ACK required commit: 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a
- Overall job status: success

## Stage outcomes
- Preflight: success
- Repo init/sync: success
- ACK pin/manifest: success
- Pinned toolchains: success
- Patch application: success
- Static checks/tests: success
- Bazel query/cquery: success
- Image build: success
- Artifact validation: success

## Source identity
8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a
2bebe7c443d0e6d5d549fb2a2377dce980d1b15e
176a19b81642073bd6b8dce5eb59e89522e9d8f3ebf07b1f9a4c50413b6a611b  /home/runner/work/_temp/round61-artifacts/manifest-pinned.xml

## Build log tail
Computing main repo mapping: 
Loading: 
Loading: 0 packages loaded
Analyzing: target //common:dby_w09 (0 packages loaded, 0 targets configured)
Analyzing: target //common:dby_w09 (0 packages loaded, 0 targets configured)

INFO: Analyzed target //common:dby_w09 (0 packages loaded, 0 targets configured).
[28 / 759] [Prepa] action 'SolibSymlink _solib_x86_64/_U_S_Sprebuilts_Skernel-build-tools_Cimported_Ulibs_Ulinux_Umusl-x86_Slib64_Slibz-host.so___Uprebuilts_Skernel-build-tools_Slinux_Umusl-x86_Slib64/libz-host.so'
[57 / 759] [Prepa] Creating symlink prebuilts/kernel-build-tools/mkfs.erofs [for tool]
[101 / 775] [Prepa] Expanding template build/kernel/_dispatched/bison_source.cpp [for tool]
[110 / 775] checking cached actions
[110 / 775] [Prepa] Expanding template build/kernel/kleaf/impl/cache_dir_config_tags [for tool]
[129 / 775] checking cached actions
[131 / 775] checking cached actions
[131 / 775] [Prepa] action 'SolibSymlink _solib_x86_64/_U_S_Sprebuilts_Skernel-build-tools_Cimported_Ulibs_Ulinux_Umusl-x86_Slib64_Slibsqlite.so___Uprebuilts_Skernel-build-tools_Slinux_Umusl-x86_Slib64/libsqlite.so'
[152 / 775] checking cached actions
[226 / 775] checking cached actions
[226 / 775] [Prepa] Symlinking virtual headers for //prebuilts/kernel-build-tools:imported_libs [for tool]
[369 / 775] Compiling build/kernel/_dispatched/bison_source.cpp [for tool]; 0s linux-sandbox ... (3 actions, 2 running)
[376 / 775] Compiling build/kernel/_dispatched/bison_source.cpp [for tool]; 1s linux-sandbox ... (3 actions, 2 running)
[389 / 775] Executing genrule @@+_repo_rules2+dtc//:dtc_parser_srcs [for tool]; 0s linux-sandbox ... (3 actions, 2 running)
[406 / 775] Compiling toys/posix/tar.c [for tool]; 0s linux-sandbox ... (3 actions, 2 running)
[422 / 775] Compiling toys/posix/ps.c [for tool]; 0s linux-sandbox ... (3 actions, 2 running)
[440 / 775] Compiling toys/posix/grep.c [for tool]; 0s linux-sandbox ... (3 actions running)
[460 / 775] Compiling toys/posix/dd.c [for tool]; 0s linux-sandbox ... (3 actions, 2 running)
[481 / 775] Compiling build/kernel/_dispatched/flex_source.cpp [for tool]; 0s linux-sandbox ... (3 actions, 2 running)
[493 / 775] Compiling lib/dictBuilder/cover.c [for tool]; 0s linux-sandbox ... (3 actions, 2 running)
[510 / 775] Compiling lib/decompress/huf_decompress.c [for tool]; 0s linux-sandbox ... (2 actions, 1 running)
[525 / 775] Compiling lib/xwrap.c [for tool]; 0s linux-sandbox ... (3 actions running)
[541 / 775] Compiling lib/compress/zstd_lazy.c [for tool]; 0s linux-sandbox ... (3 actions, 2 running)
[559 / 775] Compiling programs/lz4cli.c [for tool]; 0s linux-sandbox ... (3 actions, 2 running)
[578 / 775] Compiling checks.c [for tool]; 0s linux-sandbox ... (3 actions, 2 running)
[599 / 775] Compiling lib/lz4.c [for tool]; 1s linux-sandbox ... (3 actions, 2 running)
[751 / 775] Compiling lib/lz4frame.c [for tool]; 0s linux-sandbox ... (3 actions, 2 running)
[757 / 775] Compiling lib/lz4hc.c [for tool]; 0s linux-sandbox ... (3 actions, 2 running)
[766 / 775] Compiling build/kernel/_dispatched/rsync_source.cpp [for tool]; 0s linux-sandbox ... (2 actions, 1 running)
[773 / 775] Creating kernel config (dby_w09_storage_first.fragment) //common:dby_w09_config; 0s linux-sandbox
[774 / 775] [Prepa] Building kernel (dby_w09_storage_first.fragment) //common:dby_w09
[774 / 775] Building kernel (dby_w09_storage_first.fragment) //common:dby_w09; 0s linux-sandbox
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
[774 / 775] Building kernel (dby_w09_storage_first.fragment) //common:dby_w09; 1301s linux-sandbox
[775 / 775] no actions running
INFO: Found 1 target...
Target //common:dby_w09 up-to-date:
  bazel-bin/common/dby_w09/.config
  bazel-bin/common/dby_w09/Image
  bazel-bin/common/dby_w09/System.map
  bazel-bin/common/dby_w09/vmlinux
INFO: Elapsed time: 1362.003s, Critical Path: 1327.37s
INFO: 775 processes: 523 internal, 252 linux-sandbox.
INFO: Build completed successfully, 775 total actions

## Repo sync log tail
Finalizing sync state...
repo sync has finished successfully.
