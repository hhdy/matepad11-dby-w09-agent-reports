#!/usr/bin/env python3
# ALIGN02 Stage A: identity re-check + payload +0x38 magic probes (compressed vs decompressed)
import struct, hashlib, gzip, io

WS = '/mnt/c/Users/Administrator/.zcode/workspace/draft-4dcdb0bd-9b6e-4706-a220-ce0b212cdcbf'
STOCK = WS + '/PREP12_WORK/W3A/stock-live-boot.img'
PREP10 = WS + '/K1_HOST_CANDIDATE_PREP/dby-w09-ack61833-stage1-k1-earlycon-preview-boot.img'
PE = WS + '/PREP12_WORK/W3A/abl-hos43-pe.bin'

def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()

print('stock boot   sha256=%s' % sha(STOCK))
print('PREP10 boot  sha256=%s' % sha(PREP10))
print('ABL PE       sha256=%s' % sha(PE))

stock = open(STOCK, 'rb').read()
prep = open(PREP10, 'rb').read()

# kernel payload starts at 0x1000 (page 4096) in both
sk = stock[0x1000:0x1000+22256282]
pk = prep[0x1000:0x1000+44820992]
print('\nstock payload first16 = %s' % sk[:16].hex())
print('stock payload [+0x38,+0x3C) = %s (LE u32=0x%08X)  ARM64magic? %s' % (
    sk[0x38:0x3C].hex(), struct.unpack('<I', sk[0x38:0x3C])[0], struct.unpack('<I', sk[0x38:0x3C])[0] == 0x644D5241))
print('PREP10 payload first16 = %s' % pk[:16].hex())
print('PREP10 payload [+0x38,+0x3C) = %s (LE u32=0x%08X)  ARM64magic? %s' % (
    pk[0x38:0x3C].hex(), struct.unpack('<I', pk[0x38:0x3C])[0], struct.unpack('<I', pk[0x38:0x3C])[0] == 0x644D5241))

# decompress stock gz and check inner header
raw = gzip.decompress(sk)
print('\nstock decompressed: %d B sha256=%s' % (len(raw), hashlib.sha256(raw).hexdigest()))
print('inner [+0x38,+0x3C) = %s (LE u32=0x%08X)  ARM64magic? %s' % (
    raw[0x38:0x3C].hex(), struct.unpack('<I', raw[0x38:0x3C])[0], struct.unpack('<I', raw[0x38:0x3C])[0] == 0x644D5241))
print('inner text_offset=%d image_size=%d flags=0x%X' % (
    struct.unpack('<Q', raw[8:16])[0], struct.unpack('<Q', raw[16:24])[0], struct.unpack('<Q', raw[24:32])[0]))
# first 16 bytes of gz payload (strncmp target in ABL 0x37344 compares 16 bytes at payload start)
print('\nstock payload first16 ASCII = %r' % sk[:16])
print('PREP10 payload first16 ASCII = %r' % pk[:16])
