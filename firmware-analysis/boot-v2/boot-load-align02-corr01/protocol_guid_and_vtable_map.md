# protocol_guid_and_vtable_map.md

| 项 | 普通分区路径 | fastboot 路径 |
|---|---|---|
| 调用点 | 0x30858 `ldr x8,[x8,#0x28]` | 0x55944 同形态 |
| 基址对象 | LocateProtocol 返回接口（[x23]） | LocateProtocol 返回接口（[x29-0x98]） |
| LocateProtocol 包装 | 0x32968 = `ldr x8,[x8,#0x140]; br x8`（gBS+0x140 尾调用） | 直调 gBS->LocateProtocol @0x55930 |
| GUID 地址 / 字节 | 0x107F70 / `952e4da0 398e2bb9 34759edd 62779846` | 0x107FA0 / `8e3900a0 c969723b 225b4e96 5964d211` |
| GUID（混合端序） | {A04D2E95-8E39-B92B-3475-9EDD62779846} | {A000398E-69C9-3B72-225B-4E965964D211} |
| 名称 | UNKNOWN（非本 PE 实现） | UNKNOWN（非本 PE 实现） |
| GUID 出现次数 | 全镜像仅 1（调用点） | 全镜像仅 1（调用点） |
| +0x28 方法目标 | UNKNOWN — provider 不在冻结文件集 | UNKNOWN — 同左 |
| 方法实参 | x0=UTF-16 "secdata"（分区名标签） | w0=0xC5（同值门控 @0x55910 `cmp w8,#0xC5`） |
| 接口首字段门控 | `cmp x9,#0x20 lsl 12`（Revision ≥ 0x20000） | — |
| 与 ImageBuffer 关系 | 无（返回值走分区大小检查路径） | UNKNOWN（provider 缺失） |

缺少组件：两个 GUID 的 UEFI protocol provider 模块（不在 abl.img / Hybrid PE 内；推测位于 XBL 或 Huawei UEFI driver 集的独立 PE，冻结文件集未含）。不得以网络同型号固件替代（任务书 §10）。
