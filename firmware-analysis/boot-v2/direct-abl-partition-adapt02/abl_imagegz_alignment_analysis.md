# ABL Image.gz physical alignment analysis — corrected with load-map and allocator evidence

## Target ABL static reverse-engineering evidence
Prior Hybrid ABL reports for PE SHA-256 a14e29daf5c2f08edd2125202cf62140186005a6a37cb91cf85ef93747dbb404 establish:
- raw ARM64 Image magic at payload+0x38 selects the 64-bit path;
- gzip detection selects inflate path;
- both paths set KernelLoadAddress = ImageBuffer + 0x80000;
- gzip inflate destination is the same KernelLoadAddress;
- ImageBuffer is returned by EFI gBS->AllocatePages(AllocateAnyPages=0, EfiBootServicesData=4, EFI_SIZE_TO_PAGES(size));
- no 2MiB alignment request, mask or secondary relocation was found in the corrected allocator chain;
- allocation guarantee is EFI 4KiB page granularity only; runtime ImageBuffer_phys modulo 2MiB remains UNKNOWN.

The corrected ALIGN02-CORR01 report explicitly retracts the earlier false 32-site allocator count. The true gBS AllocatePages site is 0x3468C through helper 0x34624; ImageBuffer is the direct returned base.

## ACK image facts
Exact ACK source commit 8ad08f75ddf056e1ee600e1339e0463c5fcbdc9. Frozen Image header: text_offset=0, image_size=45,547,520, flags=0xA, magic=0x644D5241. Raw Image SHA-256 f89a283954b9c8df22aa790967f9cf8f6af84fc4aabf9bc4ff1659adc80bad21.

## Formula and result
(ImageBuffer_phys + ABL_kernel_offset - text_offset) mod 0x200000 = 0.

| Payload | ABL offset | Inner text_offset | Required ImageBuffer residue mod 2MiB | Status |
|---|---:|---:|---:|---|
| stock inner Image | 0x80000 | 0x80000 | 0 | empirical successful instances only |
| PREP10 raw ACK | 0x80000 | 0 | 0x180000 | UNKNOWN |
| gzip of same ACK | 0x80000 | 0 | 0x180000 | UNKNOWN |

Stock boot success implies the particular successful instances met their requirement; it does not establish a general allocator guarantee. If an ACK-sized buffer happens to have residue 0, ACK entry is misaligned by 0x80000. Because allocator residue is runtime-dependent and not statically constrained to 0x180000, no PASS can be issued.

## Why gzip does not fix it
Gzip changes the outer payload encoding only. The uncompressed Image header remains text_offset=0 and ABL inflates into the same +0x80000 destination. Required residue remains 0x180000. Smaller compressed size is not an alignment argument.

The exact svesnav release Image.gz binary was not among the fetched source files, so its inner header was not directly measured. 0x80000 is the relevant arm64 protocol expectation for the reference configuration, not a direct measurement of that release artifact.

## Source adaptation
ALIGN02-CORR01 discusses changing ACK head.S L59 text_offset slot 0 to 0x80000 as CONDITIONAL only. It may affect __PHYS_OFFSET, relocations and entry assumptions. Requires independent source review, complete rebuild and ARM64 boot protocol verification. No source edit/build was performed.

Final: PREP10_RAW_ALIGNMENT=UNKNOWN; ACK_IMAGE_GZ_ALIGNMENT=UNKNOWN; ACK_SOURCE_ADAPTATION_NEEDED=UNKNOWN.
