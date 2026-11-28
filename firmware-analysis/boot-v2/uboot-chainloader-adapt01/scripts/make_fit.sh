#!/bin/sh
set -e
W=/mnt/c/Users/Administrator/.zcode/workspace/draft-4dcdb0bd-9b6e-4706-a220-ce0b212cdcbf/UBOOT_CHAINLOADER_ADAPT01
F=$W/fit
mkdir -p "$F"
cd "$F"
WS=/mnt/c/Users/Administrator/.zcode/workspace/draft-4dcdb0bd-9b6e-4706-a220-ce0b212cdcbf
# inputs: freeze identities
sha256sum $WS/K1_BOOT_LOAD_MAP01/evidence/prep_kernel.bin $WS/K1_BOOT_LOAD_MAP01/evidence/prep_dtb.bin > input_sha256.txt
gzip -6 -c $WS/K1_BOOT_LOAD_MAP01/evidence/prep_kernel.bin > Image.gz
sha256sum Image.gz >> input_sha256.txt
ls -la Image.gz
cat > dby-w09-ack.its <<'EOF'
/dts-v1/;

/ {
	description = "DBY-W09 ACK 6.18.33 Android17 FIT (reserved3 staging)";
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

		/* ACK inner image_size = 45,547,520 B (0x91000000..0x93D80000 decompressed).
		   DTB placed above decompressed kernel end. Addresses are CoWave-reference
		   placements: CONDITIONAL until final-FDT RAM map is captured. */
		fdt {
			description = "DBY-W09 VD ACK DTB (PREP04 candidate)";
			data = /incbin/("dby-w09-vd.dtb");
			type = "flat_dt";
			arch = "arm64";
			compression = "none";
			load = <0x0 0x96000000>;
		};
	};

	configurations {
		default = "conf-dby-w09-vd";
		conf-dby-w09-vd {
			kernel = "kernel";
			fdt = "fdt";
		};
	};
};
EOF
cp $WS/K1_BOOT_LOAD_MAP01/evidence/prep_dtb.bin dby-w09-vd.dtb
MK=/home/kerneldev/build/u-boot-2026.10/build/tools/mkimage
[ -x $MK ] || MK=mkimage
$MK -f dby-w09-ack.its dby-w09-ack.itb
echo '--- FIT listing (mkimage -l) ---'
$MK -l dby-w09-ack.itb
echo '--- FIT size vs reserved3 ---'
stat -c 'FIT_bytes=%s' dby-w09-ack.itb
echo 'reserved3_bytes=25165824'
echo '--- dumpimage structural check ---'
DK=/home/kerneldev/build/u-boot-2026.10/build/tools/dumpimage
[ -x $DK ] || DK=dumpimage
$DK -l dby-w09-ack.itb || true
echo FIT_DONE
