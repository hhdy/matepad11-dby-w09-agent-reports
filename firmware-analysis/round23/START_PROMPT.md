请执行 ROUND23。先读取 ROUND23/AGENT_TASK.md，再从 main 最新版本读取 board rev2 candidate 和 rootparam overlay candidate。

本轮只做临时验证：
1. 按 ROUND22 相同的 cpp + dtc 流程编译 dby-w09-ack18-board.dts.rev2.candidate，确认新增的 qcom,rpmhpd.h / qcom,gcc-sm8250.h、RPMHPD_MMCX=6、UFS_PHY_GDSC=4 和 provider label。
2. 使用预装 dtc -@ 编译 dby-w09-ack18-rootparam.dtso.draft，检查 rootparam fixup。
3. 如 fdtoverlay 已安装，将这一份 overlay 应用到 rev2 base DTB 的临时副本；检查五项 rootparam 值、root board-id/compatible、UFS Host 双电源域顺序、UFS PHY GDSC、供电属性和 vdd-hba-supply 缺席。
4. 将 overlay table entry / rev 与 root qcom,board-id 分开看，不打包 dtbo.img。

不做：源码/DTS/DTBO修改、Kleaf/Bazel、内核编译、dtbs_check、schema、mkdtimg、Boot/AVB打包、设备连接或写入。工具不存在就标 BLOCKED，不安装。

只上传一个脱敏报告到 firmware-audit-v1/firmware-analysis/round23/round23_rev2_dts_and_rootparam_overlay_composite_validation.txt，成功后停止。