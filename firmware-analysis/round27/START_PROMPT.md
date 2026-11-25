请只在 ROUND25 和 ROUND26 的报告都已上传且由主 AI 审查后，执行 ROUND27。先检查这两份报告；任何一份缺失就停止，不要猜测。

本轮只做真正的 Kleaf/Bazel 设备树目标验证，不重编内核：
1. 在 ROUND18 现有本地 workspace 中读取 MODULE.bazel、MODULE.bazel.lock、build/kernel/kleaf/bzlmod/bazel.MODULE.bazel 和 repo manifest，锁定实际 rules_devicetree 版本/提交及 dtc toolchain。
2. 从 main 的 dby-w09-ack18-board.dts.rev2.candidate 与 dby-w09-ack18-rootparam.dtso.draft 精确复制临时源到 qcom DTS 目录。临时创建 BUILD.bazel，加载本地确切版本的 dtb、dtbo、dtb_composite，依赖 //common:dtc_includes_aarch64。
3. 只运行 query/cquery 和三个设备树 target 的 bazel build：base DTB、rootparam DTBO、composite DTB。禁止构建 kernel/Image 或 dtbo_image。
4. 检查 composite DTB 的五项 rootparam、root board-id 与 overlay board-id 区别、UFS Host MMCX index0/GCC GDSC index1、PHY GCC GDSC、UFS rail properties、缺少 vdd-hba-supply。
5. 对 composite 运行最窄可用的 dtbs_check / dt-validate，所有诊断都要记录。不要把 dtc exit 0 当成 schema PASS。
6. 删除临时 BUILD 和 staged files，确认 ROUND18 已有 patch/.config/Image 无变化；只上传脱敏报告，不上传二进制。

不下载、不安装、不 repo sync，不修改任何 tracked source/DTS/config，不做内核编译、不打包、不 AVB、不操作设备。完成报告后停止。