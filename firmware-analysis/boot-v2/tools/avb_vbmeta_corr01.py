#!/usr/bin/env python3
"""Read-only AVB vbmeta parser for K1 CLOSE01-CORR01.

AOSP definitions:
  descriptor tags: PROPERTY=0, HASHTREE=1, HASH=2,
                   KERNEL_CMDLINE=3, CHAIN_PARTITION=4
  AvbVBMetaImageHeader: flags at 120, rollback_index_location at 124
  digest: SHA256(full 256-byte header || auxiliary block)

Requires Python 3. Optional: cryptography for RSA verification.
"""
import argparse
import hashlib
import struct
from pathlib import Path

def u32(b, o): return struct.unpack_from(">I", b, o)[0]
def u64(b, o): return struct.unpack_from(">Q", b, o)[0]
def align8(n): return (n + 7) & ~7

TAGS = {0:"PROPERTY", 1:"HASHTREE", 2:"HASH",
        3:"KERNEL_CMDLINE", 4:"CHAIN_PARTITION"}

def verify_rsa(pub_blob, sig, digest):
    try:
        from cryptography.hazmat.primitives.asymmetric import rsa, padding
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric.utils import Prehashed
    except ImportError:
        return "NOT_CHECKED (install cryptography)"
    bits = u32(pub_blob, 0)
    if bits != 2048 or len(pub_blob) < 8 + bits // 8:
        return "NOT_CHECKED (unsupported key format)"
    modulus = int.from_bytes(pub_blob[8:8 + bits // 8], "big")
    key = rsa.RSAPublicNumbers(65537, modulus).public_key()
    try:
        key.verify(sig, digest, padding.PKCS1v15(), Prehashed(hashes.SHA256()))
        return "PASS"
    except Exception:
        return "FAIL"

def parse_descriptors(aux, offset, size):
    end = offset + size
    if end > len(aux): raise ValueError("descriptor block exceeds auxiliary data")
    rows, p = [], offset
    while p < end:
        if p + 16 > end: raise ValueError("truncated descriptor header")
        tag, nbf = u64(aux, p), u64(aux, p + 8)
        nxt = p + 16 + nbf
        if nbf % 8 or nxt > end: raise ValueError("invalid descriptor length")
        row = {"tag":tag, "type":TAGS.get(tag, f"UNKNOWN_{tag}"), "num_bytes_following":nbf}
        if tag == 4:
            # AvbChainPartitionDescriptor: parent(16), 4*u32, reserved[60], name, key
            if p + 92 > nxt: raise ValueError("short chain descriptor")
            rb, name_len, key_len, flags = (u32(aux, p + x) for x in (16,20,24,28))
            reserved = aux[p+32:p+92]
            name_start = p + 92
            key_start = name_start + name_len
            key_end = key_start + key_len
            if key_end > nxt: raise ValueError("chain variable data exceeds descriptor")
            name = aux[name_start:key_start].decode("utf-8")
            expected = align8(76 + name_len + key_len)
            row.update(partition=name, rollback_index_location=rb,
                       partition_name_len=name_len, public_key_len=key_len,
                       descriptor_flags=flags, reserved_zero=not any(reserved),
                       public_key_sha256=hashlib.sha256(aux[key_start:key_end]).hexdigest(),
                       expected_num_bytes_following=expected,
                       length_valid=(expected == nbf))
        elif tag == 2:
            # AvbHashDescriptor fixed size: 132 bytes total including parent.
            if p + 132 > nxt: raise ValueError("short hash descriptor")
            image_size = u64(aux, p+16)
            algo = aux[p+24:p+56].split(b"\0",1)[0].decode("ascii")
            name_len, salt_len, digest_len, flags = (u32(aux,p+x) for x in (56,60,64,68))
            reserved = aux[p+72:p+132]
            v = p + 132
            name = aux[v:v+name_len].decode("utf-8")
            salt = aux[v+name_len:v+name_len+salt_len]
            dg = aux[v+name_len+salt_len:v+name_len+salt_len+digest_len]
            row.update(partition=name,image_size=image_size,hash_algorithm=algo,
                       salt_len=salt_len,digest_len=digest_len,digest=dg.hex(),
                       descriptor_flags=flags,reserved_zero=not any(reserved))
        rows.append(row)
        p = nxt
    if p != end: raise ValueError("descriptor walk did not end at exact boundary")
    return rows

def parse(path, label):
    d = Path(path).read_bytes()
    if len(d) < 256 or d[:4] != b"AVB0": raise ValueError(f"{label}: invalid AVB0")
    auth_sz, aux_sz = u64(d,12), u64(d,20)
    algo = u32(d,28)
    hash_off, hash_sz = u64(d,32), u64(d,40)
    sig_off, sig_sz = u64(d,48), u64(d,56)
    pk_off, pk_sz = u64(d,64), u64(d,72)
    desc_off, desc_sz = u64(d,96), u64(d,104)
    rollback, flags, rb_loc = u64(d,112), u32(d,120), u32(d,124)
    auth_start, aux_start = 256, 256 + auth_sz
    auth, aux = d[auth_start:aux_start], d[aux_start:aux_start+aux_sz]
    if len(aux) != aux_sz: raise ValueError(f"{label}: truncated auxiliary block")
    stored = auth[hash_off:hash_off+hash_sz]
    sig = auth[sig_off:sig_off+sig_sz]
    pub = aux[pk_off:pk_off+pk_sz]
    raw = hashlib.sha256(d[:256] + aux).digest()
    zhead = bytearray(d[:256]); zhead[120:124] = b"\0"*4
    zero = hashlib.sha256(bytes(zhead) + aux).digest()
    rows = parse_descriptors(aux, desc_off, desc_sz)
    result = {
        "label":label,"size":len(d),"sha256":hashlib.sha256(d).hexdigest(),
        "algorithm_type":algo,"auth_size":auth_sz,"aux_size":aux_sz,
        "rollback_index":rollback,"flags":flags,"rollback_index_location":rb_loc,
        "hashtree_disabled":bool(flags&1),"verification_disabled":bool(flags&2),
        "stored_hash":stored.hex(),"raw_digest":raw.hex(),"raw_hash_match":raw==stored,
        "flags_zero_digest":zero.hex(),"flags_zero_hash_match":zero==stored,
        "raw_rsa":verify_rsa(pub,sig,raw),"flags_zero_rsa":verify_rsa(pub,sig,zero),
        "public_key_sha256":hashlib.sha256(pub).hexdigest(),
        "signature_sha256":hashlib.sha256(sig).hexdigest(),"descriptors":rows,
        "trailing_padding_bytes":len(d)-(256+auth_sz+aux_sz),
        "trailing_padding_all_zero":not any(d[256+auth_sz+aux_sz:])
    }
    print("\n==", label, "==")
    for k,v in result.items():
        if k != "descriptors": print(f"{k}={v}")
    for x in rows: print("descriptor=",x)
    return result, d

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--r155",required=True)
    ap.add_argument("--toolkit",required=True)
    a=ap.parse_args()
    ra, da=parse(a.r155,"R155")
    rb, db=parse(a.toolkit,"TOOLKIT")
    diff=[i for i,(x,y) in enumerate(zip(da,db)) if x!=y]
    print("\n== comparison ==")
    print("same_length=",len(da)==len(db))
    print("different_bytes=",len(diff))
    print("different_offsets=",[hex(x) for x in diff])
    print("public_keys_identical=",ra["public_key_sha256"]==rb["public_key_sha256"])
    print("signatures_identical=",ra["signature_sha256"]==rb["signature_sha256"])
    print("stored_hash_identical=",ra["stored_hash"]==rb["stored_hash"])
    print("descriptor_lists_identical=",ra["descriptors"]==rb["descriptors"])
    if diff != [123] or ra["flags"] != 3 or rb["flags"] != 2:
        raise SystemExit("unexpected comparison; review inputs and parser")
    if not (ra["flags_zero_hash_match"] and rb["flags_zero_hash_match"]):
        raise SystemExit("flags-zero digest did not match stored hash")
if __name__=="__main__": main()
