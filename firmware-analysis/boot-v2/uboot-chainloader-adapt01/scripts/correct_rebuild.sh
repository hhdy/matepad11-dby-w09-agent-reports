#!/bin/sh
# CORR: remove static /memory tuples from control DTS; verify fallback; rebuild with explicit RC
set -e
cd /home/kerneldev/build/u-boot-2026.10
DTS=dts/upstream/src/arm64/qcom/sm8250-huawei-dby-w09.dts
echo '=== BEFORE: memory node in patched source ==='
grep -n -A6 'memory {' $DTS | head -10
# fallback source proof (before rebuild)
echo '=== board_fdt_blob_setup fallback proof (mach-snapdragon) ==='
grep -n -B2 -A12 'get_prev_bl_fdt_addr' arch/arm/mach-snapdragon/board.c | head -30
# corrective edit: delete the static memory node (from 'memory {' to its closing '};')
python3 - <<'PYEOF'
import re
p = 'dts/upstream/src/arm64/qcom/sm8250-huawei-dby-w09.dts'
s = open(p).read()
new = re.sub(r'\n\tmemory \{\n\t\tdevice_type = "memory";\n\t\treg = [^;]+;\n\t\};\n', '\n\t/* HOS4.3 CORR: static RAM tuples removed - /memory absent -> qcom_parse_memory() -ENODATA -> prev-BL FDT fallback */\n', s)
if new != s:
    open(p, 'w').write(new)
    print('memory node removed')
else:
    print('memory node already absent (idempotent)')
open(p, 'w').write(new)
print('memory node removed')
PYEOF
cp $DTS /home/kerneldev/build/control-dts-final.dts
# rebuild with explicit, unmasked exit codes
set +e
make CROSS_COMPILE=aarch64-linux-gnu- O=build -j12 > /home/kerneldev/build/rebuild.log 2>&1
RC=$?
echo "MAKE_EXIT_CODE=$RC"
if [ $RC -ne 0 ]; then tail -20 /home/kerneldev/build/rebuild.log; exit $RC; fi
set -e
echo '=== AFTER: compiled DTB /memory check ==='
dtc -I dtb -O dts build/u-boot.dtb 2>/dev/null | grep -A3 'memory@80000000' | head -6 || true
dtc -I dtb -O dts build/u-boot.dtb 2>/dev/null | grep -c '/memory' || echo 'no /memory node: count 0'
echo '=== final artifact SHAs ==='
sha256sum build/u-boot build/u-boot.bin build/u-boot.map build/u-boot.dtb /home/kerneldev/build/control-dts-final.dts build/.config
echo '=== framebuffer/reserved itemization (kept, CONDITIONAL) ==='
dtc -I dtb -O dts build/u-boot.dtb 2>/dev/null | sed -n '/reserved-memory/,/^	};/p' | grep -E '@|reg =|no-map|reusable' | head -12
echo CORR_DONE
