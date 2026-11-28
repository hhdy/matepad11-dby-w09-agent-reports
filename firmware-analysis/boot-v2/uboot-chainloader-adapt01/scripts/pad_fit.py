#!/usr/bin/env python3
import hashlib
d = open('dby-w09-ack-v2.itb', 'rb').read()
pad = (-len(d)) % 4096
out = d + b'\x00' * pad
open('dby-w09-ack-v2-padded.itb', 'wb').write(out)
print('orig=%d pad=%d new=%d' % (len(d), pad, len(out)))
print('sha256 new:', hashlib.sha256(out).hexdigest())
