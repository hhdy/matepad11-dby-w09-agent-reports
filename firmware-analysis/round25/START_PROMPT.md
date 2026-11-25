请执行 ROUND25，先读取 ROUND25/AGENT_TASK.md。

只针对 HOS4.3 本地既有 decompiled DTS 中与 UFS 相关的 MMCX/MX ARC 节点，提取 provider qcom,resource-name、consumer qcom,set、qcom,init-voltage-level、qcom,min-dropout-voltage-level、parent-supply phandle 目标，以及 UFS 请求参与 ACTIVE/SLEEP/两者的证据。

使用 ROUND19 已解码文件和 ROUND11/16/30 现有报告，不重新跑全量父子图扫描，不重提取 firmware，不访问设备，不装工具，不编译，不改任何文件。

将结果与 ACK 6.18.33 的事实比较：SM8250 使用 plain MMCX 没有 MX parent；通用 GenPD 若增加 parent 且无 required-opps 译码只会传递同一 pstate，不会自动实现 HOS dropout delta。

所有物理地址脱敏；不上传 AUX 二进制；找不到就标 NOT_CAPTURED，不猜。

只上传一份报告到 firmware-audit-v1/firmware-analysis/round25/round25-hos43-mmcx-mx-arc-request-semantics.txt，完成后停止。