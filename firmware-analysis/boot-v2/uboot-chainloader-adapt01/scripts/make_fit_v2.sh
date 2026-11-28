#!/bin/sh
set -e
W=/mnt/c/Users/Administrator/.zcode/workspace/draft-4dcdb0bd-9b6e-4706-a220-ce0b212cdcbf/UBOOT_CHAINLOADER_ADAPT01
F=$W/fit
cd "$F"
WS=/mnt/c/Users/Administrator/.zcode/workspace/draft-4dcdb0bd-9b6e-4706-a220-ce0b212cdcbf
# extract gzip payload from live wrapper (offset 0x800, len 0x15749A) — local backup, byte-verified
python3 - <<'PYEOF'
d = open('/mnt/c/Users/Administrator/.zcode/workspace/draft-4dcdb0bd-9b6e-4706-a220-ce0b212cdcbf/PREP12_WORK/W3A/stock-live-ramdisk.img','rb').read()
import hashlib
h = hashlib.sha256(d).hexdigest()
assert h == '4dd6d91a2d456e1cccbf86acd799cbfd6971f52ba2bfe3c879bb73940a3cfdbb', 'wrapper hash mismatch'
p = d[0x800:0x800+0x15749A]
open('ramdisk-payload.gz','wb').write(p)
print('payload bytes:', len(p), 'sha256:', hashlib.sha256(p).hexdigest())
PYEOF
cat > dby-w09-ack-v2.its <<'EOF'
/dts-v1/;

/ {
	description = "DBY-W09 ACK 6.18.33 Android17 FIT v2 (kernel+dtb+initrd)";
	#address-cells = <2>;

	images {
		kernel {
			description = "ACK 6.18.33 Image (gzip)";
			data = /incbin/("Image.gz");
			type = "kernel";
			arch = "arm64";
			os = "linux";
			compression = "gzip";
			load = <0x0 0x91000000>;
			entry = <0x0 0x91000000>;
		};

		fdt {
			description = "DBY-W09 VD ACK DTB (PREP04 candidate)";
			data = /incbin/("dby-w09-vd.dtb");
			type = "flat_dt";
			arch = "arm64";
			compression = "none";
			load = <0x0 0x96000000>;
		};

		ramdisk {
			description = "Android initrd gzip payload (from live separate ramdisk wrapper)";
			data = /incbin/("ramdisk-payload.gz");
			type = "ramdisk";
			arch = "arm64";
			os = "linux";
			compression = "none";
		};
	};

	configurations {
		default = "conf-dby-w09-vd";
		conf-dby-w09-vd {
			kernel = "kernel";
			fdt = "fdt";
			ramdisk = "ramdisk";
		};
	};
};
EOF
MK=/home/kerneldev/build/u-boot-2026.10/build/tools/mkimage
DK=/home/kerneldev/build/u-boot-2026.10/build/tools/dumpimage
$MK -f dby-w09-ack-v2.its dby-w09-ack-v2.itb
MRC=$?
echo "MKIMAGE_EXIT=$MRC"
$DK -l dby-w09-ack-v2.itb > dby-w09-ack-v2.list 2>&1
DRC=$?
echo "DUMPIMAGE_EXIT=$DRC"
grep -E 'Type:|Data Size|Compression|Load Address|Configuration' dby-w09-ack-v2.list
sz=$(stat -c %s dby-w09-ack-v2.itb)
echo "FIT_V2_BYTES=$sz  reserved3=25165824  headroom=$((25165824 - sz))"
sha256sum dby-w09-ack-v2.itb ramdisk-payload.gz
echo FIT_V2_DONE
