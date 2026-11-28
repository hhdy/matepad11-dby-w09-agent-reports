# VD DTBO policy

Target evidence reused from prior HOS4.3 reports: live FDT root qcom,board-id=<0x200e 0>; selected stock DTBO Entry 2; observed androidboot.dtbo_idx=2. Stock Entry 2 rootparam is VD-specific, including qcom,boardid=<0x08 0x02 0x00 0x06>, qcom,board_name="DBY_W09_VD", qcom,product_name="DBY-W09" and hardware_version="SH1DBSLM".

Public svesnav overlay is VG: root qcom,board-id=<0x206a 0>; qcom,boardid=<0x08 0x02 0x09 0x08>; qcom,board_name="DBY_W09_VG"; modem_id placeholder <0xffffffff 0x00>. It must not be transplanted to this VD device.

Public pack_dtbo.py emits a 32-byte Android DT table header and one 32-byte entry, dt_offset=64, count=1, page_size=4096, zero id/rev/custom fields. This documents the public project's package format only; it does not prove HOS4.3 ABL accepts the same table metadata. androidboot.dtbo_idx=2 is selector output, not selector input.

VD_DTBO_POLICY = KEEP_STOCK_VD_ENTRY2 for partition-preservation planning. This does not prove the stock overlay is compatible with the minimal ACK candidate base. Earlier candidate analysis reported unresolved external symbol fixups/missing targets when applying stock overlay to the minimal base. Do not replace the live stock partition or create a new overlay without an exact approved target-specific integration review.

ROUND159's host-side component review is not authorization to replace the live DTBO partition or evidence of integrated Android boot. No overlay was authored, compiled, packed or tested here.
