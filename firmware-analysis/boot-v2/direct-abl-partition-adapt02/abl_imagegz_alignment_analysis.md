# ABL Image.gz physical alignment analysis

## ACK facts from taskbook / prior build evidence

ACK source ref android17-6.18.33_r00; commit 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9; patched tree c56d93eafa35057d65176db6594d67d5144868a0. Raw Image is 44,820,992 B, SHA-256 f89a283954b9c8df22aa790967f9cf8f6af84fc4aabf9bc4ff1659adc80bad21. Header: text_offset=0, image_size=45,547,520, flags=0xA, magic=0x644D5241. PREP10 boot candidate: 46,563,215 B, SHA-256 d1d76c2199dff54e762bffe98260116369af1e8b50f5d813fe197434ac1cc091.

File length being smaller than image_size is not by itself invalid; image_size is a memory footprint field.

## What public source proves

svesnav build scripts pass Image.gz as the kernel payload. repack_boot.py treats it as opaque bytes and does not inspect the decompressed ARM64 Image header or prove the ABL decompression destination. README reports Linux 7.0.14 works on DBY-W09; that is an existence report for that project's particular firmware/kernel/device combination, not a measurement of this ACK payload's physical address residue.

The pinned configure-and-build.sh runs arm64 defconfig and toggles many symbols, but the reviewed pinned source does not provide the final .config. CONFIG_RELOCATABLE, CONFIG_RANDOMIZE_BASE and page-size values therefore remain unverified here.

## Alignment formula

Required formula from taskbook:
(ImageBuffer_phys + ABL_kernel_offset - text_offset) mod 0x200000 = 0.

For ACK raw Image, text_offset=0. If ABL uses offset 0x8000, ImageBuffer_phys must have residue 0x1f8000 modulo 0x200000. If ABL uses 0x80000, required residue is 0x180000. These are conditional arithmetic examples only; the exact target offset is not established in reviewed evidence.

For Image.gz, apply the same equation to the decompressed ImageBuffer and its decompressed Image header. Compression changes container and loader path; it does not automatically eliminate the alignment requirement. The physical residue of the decompression buffer or a proven fixed destination remains decisive.

## A/B/C comparison

| Variant | Decision | Reason |
|---|---|---|
| A. PREP10 raw Image | UNKNOWN | Exact HOS4.3 raw branch, kernel offset and allocator residue not closed |
| B. Same ACK Image gzip-compressed | UNKNOWN | No proof gzip bypasses alignment; decompressed header remains same |
| C. ACK source/config adaptation | UNKNOWN | No source change justified before loader contract is known |

## Required missing proof

1. Exact ABL predicate distinguishing raw Image from gzip payload.
2. Actual kernel offset for each path; resolve 0x8000 vs 0x80000.
3. Decompression destination allocation/base calculation and relocation behavior.
4. Decompressed ACK Image header as consumed by ABL.
5. Runtime ImageBuffer_phys modulo 0x200000, or exact fixed destination.
6. Proof final kernel entry/text address follows ARM64 boot protocol.

Without item 5, alignment remains UNKNOWN even if static branch is identified. Do not infer ACK success from svesnav Linux 7.0.14 success. No source edit, build, image generation or device observation was performed.
