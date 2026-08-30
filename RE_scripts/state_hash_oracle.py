#!/usr/bin/env python3
"""state_hash_oracle.py - offline model of the fork's session-state replica + its lookup3
hash, so a published/rejected hash can be reproduced and searched WITHOUT a boot.

Mirrors middleware/gameplay/group/session_state.cpp (build_session_state) and
middleware/crypto/lookup3.cpp (hash_bytes). Self-test: reproduce a server-logged
`stage=membership result=built ... hash=` value for a reconstructed body.
"""
import itertools, struct

M32 = 0xFFFFFFFF
STATE_SIZE = 28768
HASH_INIT = 0xDEAE2F4E

def rot(v, c): return ((v << c) | (v >> (32 - c))) & M32

def mix(a, b, c):
    a = (a - c) & M32; a ^= rot(c, 4);  c = (c + b) & M32
    b = (b - a) & M32; b ^= rot(a, 6);  a = (a + c) & M32
    c = (c - b) & M32; c ^= rot(b, 8);  b = (b + a) & M32
    a = (a - c) & M32; a ^= rot(c, 16); c = (c + b) & M32
    b = (b - a) & M32; b ^= rot(a, 19); a = (a + c) & M32
    c = (c - b) & M32; c ^= rot(b, 4);  b = (b + a) & M32
    return a, b, c

def fin(a, b, c):
    c ^= b; c = (c - rot(b, 14)) & M32
    a ^= c; a = (a - rot(c, 11)) & M32
    b ^= a; b = (b - rot(a, 25)) & M32
    c ^= b; c = (c - rot(b, 16)) & M32
    a ^= c; a = (a - rot(c, 4))  & M32
    b ^= a; b = (b - rot(a, 14)) & M32
    c ^= b; c = (c - rot(b, 24)) & M32
    return a, b, c

def hash_bytes(buf, initial=HASH_INIT):
    assert len(buf) % 4 == 0
    w = struct.unpack('<%dI' % (len(buf) // 4), buf)
    a = b = c = initial
    i, n = 0, len(w)
    while n - i > 3:
        a = (a + w[i]) & M32; b = (b + w[i+1]) & M32; c = (c + w[i+2]) & M32
        a, b, c = mix(a, b, c); i += 3
    rem = n - i
    if rem == 0: return c
    if rem == 3: c = (c + w[i+2]) & M32
    if rem >= 2: b = (b + w[i+1]) & M32
    a = (a + w[i]) & M32
    return fin(a, b, c)[2]

# --- NetAddr (join_descriptor.cpp write_net_addr) ---------------------------------------
NETADDR = 86
def net_addr(ipv4, port):
    o = bytearray(NETADDR)
    o[0:4]   = struct.pack('>I', ipv4)      # kAddressOffset, network order
    o[4:6]   = struct.pack('<H', port)      # kPortOffset, memory order
    o[30:34] = struct.pack('>I', ipv4)      # kPublicAddressOffset
    o[34:36] = struct.pack('<H', port)      # kPublicPortOffset
    o[40]    = 1                            # kNatTypeOpen
    o[85]    = 0                            # kDirectMethod
    return bytes(o)

# --- build_session_state ----------------------------------------------------------------
REV, HOSTIDX, SUCC, MCOUNT, MMASK, MARRC, MARR = 4, 12, 20, 28, 40, 48, 56
MSTRIDE = 184
M_ADDRLEN, M_ADDR, M_MACHLEN, M_MACH, M_JOIN, M_PCOUNT, M_PSLOT = 8, 16, 112, 120, 136, 168, 176
PEER_T, PEER_STRIDE = 5968, 288
PL_COUNT, PL_MASK, PL_TABLE, PL_STRIDE = 15184, 15188, 15192, 424
PL_ID, PL_MEMBER, PL_OWNED, PL_SEQ, PL_FLAG, PL_CLR1, PL_CLR2 = 4, 12, 16, 20, 24, 28, 264
CLEARED = 0xFFFFFFFF

def wr(buf, off, val, width):
    for i in range(width):
        buf[off + i] = (val >> (i * 8)) & 0xFF

def build_state(rev, members, players, base_shift=0):
    """members: list of dicts(addr,machine,join,state,owns,slot)
       players: list of dicts(slot,pid,member,seq,flag)"""
    s = bytearray(STATE_SIZE)
    n = len(members)
    wr(s, REV, rev, 4); wr(s, HOSTIDX, 0, 4); wr(s, SUCC, 0, 4)
    wr(s, MCOUNT, n, 4)
    wr(s, MMASK, 0 if n == 0 else (1 << n) - 1, 8)
    wr(s, MARRC, n, 8)
    for i, m in enumerate(members):
        e = MARR + MSTRIDE * i
        wr(s, e + M_ADDRLEN, 86, 8)
        s[e + M_ADDR : e + M_ADDR + len(m['addr'])] = m['addr']
        wr(s, e + M_MACHLEN, 8, 8)
        wr(s, e + M_MACH, m['machine'], 8)
        wr(s, e + M_JOIN, m['join'], 8)
        if m['owns']:
            wr(s, e + M_PCOUNT, 1, 8); wr(s, e + M_PSLOT, m['slot'], 4)
        p = PEER_T + PEER_STRIDE * i
        wr(s, p + 0, m['state'], 4)          # connection block values are all zero
    mask = 0
    for pl in players:
        mask |= 1 << pl['slot']
        e = PL_TABLE + base_shift + PL_STRIDE * pl['slot']
        wr(s, e + PL_ID, pl['pid'], 8)
        wr(s, e + PL_MEMBER, pl['member'], 4)
        wr(s, e + PL_OWNED, 0, 4)
        wr(s, e + PL_SEQ, pl['seq'], 4)
        wr(s, e + PL_FLAG, 1 if pl['flag'] else 0, 1)
        wr(s, e + PL_CLR1, CLEARED, 4)
        wr(s, e + PL_CLR2, CLEARED, 4)
    wr(s, PL_COUNT, len(players), 4)
    wr(s, PL_MASK, mask, 4)
    return bytes(s)

def member(addr, machine, join, state, owns=False, slot=0):
    return dict(addr=addr, machine=machine, join=join, state=state, owns=owns, slot=slot)
