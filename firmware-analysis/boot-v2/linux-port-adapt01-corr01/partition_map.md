# CORR01 — partition_map.md（启动链相关分区映射）

来源：设备实机采集（PREP12 轮 `evidence_partition_sizes.txt`，root shell `ls -l /dev/block/by-name` + `blockdev --getsize64`）。

## 本候选方案（CORR01/PREP10）涉及的分区

| 分区 | 块设备 | 容量 (B) | 状态 | 操作 |
|---|---|---|---|---|
| **boot** | /dev/block/sde9 | 100,663,296 (96 MiB) | stock `7a95c897…39d24a8`；payload 0–24,449,024，尾部全零 | **唯一写入目标**（前缀写 46,563,215 B） |
| **dtbo** | /dev/block/sde13 | 25,165,824 | 9 entries（见 dtbo_parse_corr01），Entry 2=VD /dev_w09_VD | **不写**，保持 stock |
| **ramdisk** | /dev/block/sda22 | 2,097,152 | separate ramdisk：init stub + init.real + ksu.ko（ABL 作为 kernel initrd 加载） | **不写**，保持 stock |
| **vbmeta** | /dev/block/sde12 | 1,048,576 | GhostLock 工程 ABL 轮次已改写（rb_loc=2） | **不写** |
| **abl** | /dev/block/sde6 | 4,194,304 | GhostLock 工程 ABL（china_compile） | **不写** |
| **misc** | /dev/block/sda4 | 2,097,152 | bootloader 消息 | **不写** |

## 完整分区表（供审计；与 PREP12 采集一致）

| by-name | 块设备 | 字节 |
|---|---|---|
| abl | sde6 | 4,194,304 |
| aop | sde1 | 524,288 |
| apdp | sde18 | 262,144 |
| bluetooth | sde5 | 1,048,576 |
| boot | sde9 | 100,663,296 |
| bootfail_info | sda8 | 8,388,608 |
| bsp_info | sda5 | 1,048,576 |
| cache | sda10 | 109,051,904 |
| cdt | sdd2 | 131,072 |
| ddr | sdd3 | 33,271,808 |
| devcfg | sde10 | 1,048,576 |
| devinfo | sde16 | 1,048,576 |
| dfx | sde24 | 1,712,152,576 |
| dip | sde17 | 1,048,576 |
| dsp | sde7 | 67,108,864 |
| dtbo | sde13 | 25,165,824 |
| eng_system | sda14 | 25,165,824 |
| eng_vendor | sda15 | 25,165,824 |
| erecovery | sda16 | 100,663,296 |
| erecovery_ramdisk | sda17 | 37,748,736 |
| erecovery_vbmeta | sda23 | 1,048,576 |
| erecovery_vendor | sda18→sda18(注) | — |
| featenabler | sde15 | 131,072 |
| frp | sda11 | 1,048,576 |
| fsc | sdf5 | 20,819,968 |
| fsg | sdf4 | 4,194,304 |
| fw_ufsdev | sda34 | 4,194,304 |
| hyp | sde3 | 524,288 |
| keymaster | sde8 | 1,048,576 |
| kpatch | sda31 | 4,194,304 |
| limits | sde19 | 32,768 |
| log | sda12 | 83,886,080 |
| metadata | sda32 | 16,777,216 |
| misc | sda4 | 2,097,152 |
| modem | sde4 | 197,132,288 |
| modemst1 | sdf2 | 4,194,304 |
| modemst2 | sdf3 | 4,194,304 |
| nvme | sda3 | 5,242,880 |
| oeminfo | sda7 | 100,663,296 |
| patch | sda30 | 268,435,456 |
| persist | sda2 | 33,554,432 |
| preas | sda35 | 310,378,496 |
| preavs | sda36 | 33,554,432 |
| preload | sda39 | 1,468,006,400 |
| qupfw | sde11 | 65,536 |
| ramdisk | sda22 | 2,097,152 |
| rawdump | sde20 | 26,214,400 |
| recovery | sda19 | 100,663,296 |
| recovery_ramdisk | sda20 | 37,748,736 |
| recovery_vbmeta | sda24 | 1,048,576 |
| recovery_vendor | sda21 | 25,165,824 |
| reserved1 | sda6 | 8,355,840 |
| reserved2 | sda33 | 20,971,520 |
| reserved3 | sda13 | 25,165,824 |
| reserved4 | sdc1 | 8,343,552 |
| rrecord | sda9 | 8,388,608 |
| secdata | sde23 | 28,672 |
| ssd | sda1 | 8,192 |
| storsec | sde21 | 131,072 |
| super | sda37 | 7,692,353,536 |
| tz | sde2 | 4,194,304 |
| uefisecapp | sde14 | 2,097,152 |
| uefivarstore | sde22 | 524,288 |
| userdata | sda40 | 114,521,276,416 |
| vbmeta | sde12 | 1,048,576 |
| vbmeta_cust | sda28 | 1,048,576 |
| vbmeta_hw_product | sda29 | 1,048,576 |
| vbmeta_odm | sda27 | 1,048,576 |
| vbmeta_system | sda25 | 1,048,576 |
| vbmeta_vendor | sda26 | 1,048,576 |
| version | sda38 | 603,979,776 |
| xbl | sdb1 | 4,018,176 |
| xbl_config | sdb2 | 4,325,376 |
| ALIGN_TO_128K_1 | sdd1 | 106,496 |
| ALIGN_TO_128K_2 | sdf1 | 106,496 |

（`hw_product`/`system`/`vendor`/`odm`/`cust` 为 dm-verity 映射设备 dm-0..dm-4，属运行时映射，非物理分区。erecovery_vendor 对应 sda18 与 apdp 冲突行为原始记录如此，如实保留。）

## 启动链分区读取顺序（PREP04/12 已证实）

1. **xbl / xbl_config**（sdb1/sdb2）→ 加载 **abl**（sde6）
2. ABL 读 **vbmeta**（sde12，rb_loc=2）做 AVB 校验路径
3. ABL 读 **boot**（sde9）：kernel（Image）+ embedded ramdisk + DTB
4. ABL 读 **dtbo**（sde13）：按 board 匹配 Entry 2（VD）合并 overlay
5. ABL 读 **ramdisk**（sda22，separate ramdisk）作为 kernel initrd
6. 跳转 kernel（0x8000 处 Image，DTB @0x1f00000，tags @0x100）
