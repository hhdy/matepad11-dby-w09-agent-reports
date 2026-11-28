# K1-HOST-PREP01 — AI1 独立验收报告

**项目：** Huawei MatePad 11 DBY-W09 / SM8250 / ACK Android 17 6.18.33  
**验收日期：** 2026-11-28  
**验收对象：** `K1_HOST_CANDIDATE_PREP.zip`  
**结论：** **候选镜像身份与 PREP06→PREP10 单字段变更通过；K1-HOST-PREP01 接受并关闭。** 随包复现工具存在非阻断性准确性/可移植性问题，见第 6 节。此验收不是刷写、临时启动或设备接受批准。

## 1. ZIP 与交付哈希

- ZIP 大小：18,592,531 B
- ZIP SHA-256：`6cd55956bd29bfc91ef310e8ecd332e0b02142dc32cc2a26300379c17122522f`，与 Agent 声明一致。
- ZIP CRC / testzip：通过。
- 条目数：6；未发现 `__pycache__` 或其他多余条目。
- `SHA256SUMS.txt` 覆盖的 5 个文件哈希均与实际条目内容一致。
- 候选镜像：46,563,215 B；SHA-256：`d1d76c2199dff54e762bffe98260116369af1e8b50f5d813fe197434ac1cc091`，与冻结目标完全一致。

## 2. 独立 boot v2 解析

| 字段 | 实测 | 判定 |
|---|---:|---|
| Magic / Header version | `ANDROID!` / 2 | PASS |
| Header size / Page size | 1660 B / 4096 B | PASS |
| Kernel | 44,820,992 B；SHA-256 `f89a283954b9c8df22aa790967f9cf8f6af84fc4aabf9bc4ff1659adc80bad21` | PASS |
| Embedded ramdisk | 519,986 B；SHA-256 `a4b94ff6bb2d9525fa6ad0010d8efa4c6fe2bd49d36956115c26a656b631af3c` | PASS |
| DTB slot | 1,216,399 B；SHA-256 `7bb9a1fba8d4574bce9d54795d67217d6f72857e792cbafa626ece3459b996b7` | PASS |
| Cmdline prefix | `ignore_loglevel earlycon=qcom_geni,0xa90000` | PASS |
| Stored ID field | `8f1501bcba02b9e787386b97171c6d0b852a9ef7` + 12 zero bytes | PASS，见第 4 节 |
| File end | 正好结束于 DTB payload 末字节 | 与冻结尺寸一致 |

## 3. PREP06 反向重建验证

ZIP 未包含 PREP06 原文件，因此 AI1 没有声称直接比较了两份原始文件。AI1 从交付候选的 512 B cmdline 字段移除 `ignore_loglevel `，其余字节完全不动，并恢复原 NUL 填充，反向重建 PREP06。

反向重建结果：
- 大小：46,563,215 B
- SHA-256：`aa25553170ace181bea3d2457962e0d13fff0277511ea7a7bead657e798196a8`
- 与冻结 PREP06 SHA-256 完全一致。

逐字节比较重建的 PREP06 与候选：
- 差异区间：18 个；
- 不同字节：423 个；
- 所有差异完全位于 cmdline 字段 `[0x40, 0x240)`；
- 字段外差异：0；文件长度差：0。

因此独立确认唯一字节变化就是 cmdline 前插入 `ignore_loglevel `；kernel、ramdisk、DTB、其余头字段与尾部均未改变。

## 4. Boot image ID 算法核验与修正

随包 `bootimg_tool.py` 和 `id_probe.py` 的简化 payload-SHA1 探针不完整：只把 payload 字节直接连接后做 SHA-1，遗漏了 AOSP `mkbootimg.py` 的 `update_sha()` 对每个组件追加的 4 字节小端长度；空组件也追加 `uint32(0)`。

AOSP 实现：<https://android.googlesource.com/platform/system/tools/mkbootimg/+/refs/heads/main/mkbootimg.py 。其 boot v2 ID 按版本依次覆盖 kernel、ramdisk、second、recovery_dtbo、DTB。AI1 按官方算法对上述各组件数据及各自 4 字节长度（空组件长度为 0）更新 SHA-1，结果为：

`8f1501bcba02b9e787386b97171c6d0b852a9ef7`

与镜像 ID 前 20 字节完全一致，后 12 字节为零。因此**保留 PREP06 ID 字段是正确的**，且交付镜像 ID 符合 AOSP 算法。Agent 报告中“经典 AOSP payload-SHA1 得出 `5492abd2…`”的说法不正确；该值是遗漏组件长度字段的简化算法结果，不能证明 AOSP ID 不等于 `8f1501bc…`。

## 5. 验收结论

| 验收对象 | 结果 |
|---|---|
| ZIP 身份与内容哈希 | PASS |
| 候选镜像冻结 SHA-256 | PASS |
| Android boot v2 结构与 payload | PASS |
| kernel / ramdisk / DTB 冻结身份 | PASS |
| cmdline 修改范围 | PASS，独立反向重建 PREP06 后验证 |
| AOSP boot image ID | PASS，按官方 `update_sha()` 算法重算 |
| 是否证明可刷写/可启动/设备接受 | **NO；未测试，仍不批准设备操作** |

**K1-HOST-PREP01：ACCEPTED / CLOSED。** 候选作为唯一 host-side preview 保留。PREP07 NO-GO 与 UART12 route HOLD 不变。

## 6. 随包复现工具的非阻断性问题

这些问题不推翻已独立验证的候选镜像身份，但工具当前状态不应被称为完全自包含、可移植的独立验收套件：

1. `bootimg_tool.py::parse()` 的 `calc_id` 只哈希 payload 拼接，没有按 AOSP `update_sha()` 追加每个组件的 4 字节长度；输出标签 `calculated AOSP id` 不准确，应实现官方算法或改名为简化诊断值。
2. `id_probe.py` 将 PREP06 路径硬编码为特定 WorkBuddy/WSL 工作目录，且探针集合遗漏 AOSP 长度字段规则；它不是可移植、完整的 AOSP ID 探针。
3. `final_verify.py` 的 `sys.path` 硬编码为特定工作区绝对路径，离开原 Agent 工作区无法直接运行。
4. `final_verify.py` 虽打印 diff range 是否落在 cmdline 与 `size_diff`，但没有把越界差异或长度差写入失败状态；可能在差异范围检查失败时仍打印 `ALL CHECKS PASS`。应将 `len(a)==len(b)`、所有差异区间都完全落在 `[0x40,0x240)`、NUL 后填充条件等纳入硬性断言，并在失败时返回非零退出码。
5. builder 对 cmdline NUL 后填充是否全零只打印结果，没有 assert；建议在写入前硬性验证，防止静默清除隐藏字段。

这些是后续工具清理项，不要求重新构建候选镜像，也不构成再做一轮固件静态审计的理由。候选原文件不应因工具清理而改动；任何修订包必须保持候选镜像 SHA-256 不变。

## 7. 安全边界

本验收只处理上传 ZIP 和主机端字节数据。未连接设备、未执行 ADB / fastboot / OEM / EDL、未 reboot、未 `fastboot boot`、未刷写或读取分区、未修改 AVB/vbmeta、未改 kernel/DTB/DTBO/ramdisk。

候选仍是主机端 preview。任何设备操作必须由后续单独任务明确授权，并在执行前重新核验设备识别、启动路径、恢复路径及回退条件。
