你是 **WorkBuddy Window A（1号 Agent）**，不是2号 AI，也不是 WorkBuddy Window B。

请执行 ROUND158 的离线 ABL 启动门槛审计。先完整读取任务书：
https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/workbuddy/round158-exact-hos43-rootparam-abl/firmware-analysis/round158/WORKBUDDY_A_ROUND158_EXACT_HOS43_ROOTPARAM_DTBO_AND_FASTBOOT_BOOT_AUDIT_TASKBOOK.md

目标是用户真实设备对应的 HOS 4.3.0.196 ABL，而不是把其他 HOS4.2 / 6GB 设备的结论照搬过来。重点查清 `/rootparam` 是否为该 ABL 的强制条件、Entry2(0x200e) 与 Entry8(0x206a) 的选择契约，以及 fastboot boot 是否被该 ABL 禁止。

只使用你自己的 ROUND155 已捕获 ABL/boot-chain 文件和 ROUND157 自己的源代码工作树。不要访问 Window B 的 workspace。禁止任何设备操作、ADB、fastboot、刷写、重启或分区读写。禁止生成可刷写包。

按任务书的证据等级给出明确结论；无法解码处列地址和原始指令，不要猜。报告上传 GitHub 后必须回读校验，然后停止。