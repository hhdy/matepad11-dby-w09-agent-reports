# PREP03 重新交付判定 — AI1 决定

- Decision owner: 1号 AI（ChatGPT）
- Device: Huawei MatePad 11 DBY-W09 / SM8250
- Target: Android 17 ACK 6.18.33 bring-up, then DerpFest Android 17
- Date: 2026-11-27
- Status: **DUAL-BUNDLE DELIVERY APPROVED; NO REBUILD / NO DEVICE ACCESS**

## 1. 判定结果

用户转交的 WorkBuddy 只读清点回报表明：**同一个 WorkBuddy 工作区同时持有设备资料组和内核构建组两份完整的既有 ZIP**，两份 ZIP 的 testzip 均通过，且报告称各自内部文件哈希匹配。

因此，针对本次 PREP03 重新交付，AI1 判定该 WorkBuddy 会话可同时承担：
- 设备资料归档（Device Bundle）
- 内核构建归档（Kernel Bundle）

**不需要再让另一个 WorkBuddy 窗口执行第二次查找，也不需要用户区分两个 Agent。** 本决定仅覆盖这次已有产物的双包交付，不改变未来项目中的独立工作区/角色隔离要求。

## 2. 已报告的归档身份（尚待 AI1 收到原始 ZIP 后独立复核）

### Device Bundle
- Path: `prep03\\windowA\\PREP03_WindowA_Device_Inputs.zip`
- Size: 206,133,919 bytes
- SHA-256: `2a6306c339ff2c3ccd200df2bd152618f950aacc54019cdc65f18b1b3dca39e5`
- Reported: ZIP integrity test passed; 7 entries; expected device input file hashes match; no missing items.

### Kernel Bundle
- Path: `prep03\\windowB\\PREP03_WindowB_Kernel_Inputs.zip`
- Size: 45,302,464 bytes
- SHA-256: `c2214d15525b16f1708e95bd14f971db660c83f933ddb3dcea3b3c514846b371`
- Reported: ZIP integrity test passed; 6 entries; no missing items; no Image.gz was produced by the frozen build and none was fabricated.

以上哈希与完整性目前来自 WorkBuddy 回报；AI1 尚未取得 ZIP 原始字节，不能把它们描述为已由 AI1 独立复算。

## 3. 配置身份差异必须保留

WorkBuddy 报告了两份不同配置：
- `config-used-for-build.config`: 238,410 bytes, SHA-256 `0850213dc3e2c8ed412e950ffb8e10c758bc2efed18a2d30d8271c282f2c6b15`
- `config-olddefconfig-normalized.config`: 237,316 bytes, SHA-256 `efb663e9c792840e2cfbbc03e115996bb486aefe964b448c1717828c55bf042f`

项目记录把 `0850213d…` 和 `efb663e9…` 用于不同阶段/含义；不得把它们视为相同文件，也不得静默互换。**两份都保留在 ZIP 并原样交付。** AI1 收到 ZIP 后将结合 build-provenance 和原始构建报告判断成功构建实际消费的配置身份。该差异暂不阻止 ZIP 交付，但在核对完成前不宣称配置身份已最终一致。

## 4. 立即执行的交付动作

收到本决定的 WorkBuddy 会话必须：
1. 不再只读等待，不再重复扫描两个 Agent 工作区。
2. 不重新打包、不重新生成文件（现有 ZIP 完整性测试已通过）；只对既有两个 ZIP 再计算一次 ZIP SHA-256，确认与本文件记录一致。
3. 复制到用户桌面：
   - `%USERPROFILE%\\Desktop\\PREP03_REDELIVERY\\DeviceBundle\\PREP03_WindowA_Device_Inputs.zip`
   - `%USERPROFILE%\\Desktop\\PREP03_REDELIVERY\\KernelBundle\\PREP03_WindowB_Kernel_Inputs.zip`
4. 在当前 WorkBuddy 回复中**同时附加两个 ZIP 文件本体**，让用户可直接点击下载。
5. 若 WorkBuddy 界面确实不支持附件，明确说明“当前界面不支持附件”，并给出两个桌面文件的完整绝对路径；不得虚称已附加。
6. 回复两份文件的大小、SHA-256、内部条目清单及缺失项（应为无）。
7. 不访问平板、不执行 ADB/Fastboot/重启/临时启动/分区写入，不重编译内核。

## 5. AI1 收到附件后的责任

AI1 收到两个 ZIP 后自行：
- 独立重算归档与内部各文件哈希；
- 核对 DTB、ABL、boot、ramdisk 和内核 Image 的身份；
- 复核 build-provenance 以及两份 config 的差异；
- 继续 Android 17 候选启动包离线解析和组装。

**本决定不批准临时启动或刷写。**
