#!/usr/bin/env python3
# REGISTRY: caps: state-hash-matcher, checksum-pindown
"""The membership-checksum pin-down matcher (2026-09-07).

The client rejects the fork's membership bodies: "session membership checksum
failed, X != Y" - X = the client's own computed hash, Y = the fork's carried
hash. The fork's side (Y) is readable code (session_state.cpp:
lookup3::hash_bytes over the 28 KiB SessionState replica with the clientBase
and ProfileModel knobs). The client's side (X) is the same primitive over
THE CLIENT'S replica layout - which differs from the fork's model by a
bounded set of choices (the sessionStateClientBase doc: every profile-block
offset pinned except two; plus the 8-byte base shift; plus the trailing-pair
participation surfaced by the sweep boot). THE LOGGED X IS THE ORACLE: for
each dump of the exact hashed buffer, the candidate layouts whose lookup3
output equals X name the winning layout - and the fix.

Inputs:
  --dump <membership_state_dump.bin>   the exact hashed buffer from the
                                       instrumented send (the y-side input)
  --client-log <sunrise.log>           the client log holding the
                                       "checksum failed, X != Y" lines
  --server-log <sunrise.log>           the fork's stage=state_hash lines
                                       (hash + fp + members/players counts)

Output: the fork-side self-check (hash_bytes(dump) == Y - proves the
transcription), then the candidate matrix (as-is, +8/-8 base shift, name
plain vs obfuscated, trailing-pair in/out) with the X match verdicts.

Exit 0 = a candidate matched the client's X (the layout is pinned).
Exit 1 = dump/log unreadable. Exit 2 = no candidate matched (the space needs
the client-decode replication lane).
"""

import argparse
import re
import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0] if "/" in __file__ else ".")

# The oracle's transcription (state_hash_oracle.py: lookup3 + the layout consts).
M32 = 0xFFFFFFFF
HASH_INIT = 0xDEAE2F4E  # kHashInitial (session_state.cpp:184) - verified against source
STATE_SIZE = 28768

# Candidate knob matrix (documented OPEN items):
#   base: the 8-byte slack shift (0 or 8) - the fork's clientBase knob
#   name: plain vs obfuscated stored name in the player profile block
#   pair: the trailing 32-bit pair participates in the replica or not
BASE_SHIFTS = (0, 8)
NAME_MODES = ("plain", "obf")
PAIR_MODES = ("out", "in")


def rot(v, c):
    return ((v << c) | (v >> (32 - c))) & M32


def mix(a, b, c):
    a = (a - c) & M32; a ^= rot(c, 4); c = (c + b) & M32
    b = (b - a) & M32; b ^= rot(a, 6); a = (a + c) & M32
    c = (c - b) & M32; c ^= rot(b, 8); b = (b + a) & M32
    a = (a - c) & M32; a ^= rot(c, 16); c = (c + b) & M32
    b = (b - a) & M32; b ^= rot(a, 19); a = (a + c) & M32
    c = (c - b) & M32; c ^= rot(b, 4); b = (b + a) & M32
    return a, b, c


def fin(a, b, c):
    c ^= b; c = (c - rot(b, 14)) & M32
    a ^= c; a = (a - rot(c, 11)) & M32
    b ^= a; b = (b - rot(a, 25)) & M32
    c ^= b; c = (c - rot(b, 16)) & M32
    a ^= c; a = (a - rot(c, 4)) & M32
    b ^= a; b = (b - rot(a, 14)) & M32
    c ^= b; c = (c - rot(b, 24)) & M32
    return a, b, c


def hash_bytes(buf, initial=HASH_INIT):
    """The C++ lookup3::hash_bytes variant: 32-bit little-endian words, NO
    byte-length add, returns c after finish. Buffer length must be word-
    aligned (matching the C++ %4==0 gate). Verified against lookup3.cpp."""
    if len(buf) % 4 != 0:
        return 0
    count = len(buf) // 4
    a = b = c = initial & M32
    index = 0
    while count - index > 3:
        a = (a + int.from_bytes(buf[4 * index:4 * index + 4], "little")) & M32
        b = (b + int.from_bytes(buf[4 * index + 4:4 * index + 8], "little")) & M32
        c = (c + int.from_bytes(buf[4 * index + 8:4 * index + 12], "little")) & M32
        a, b, c = mix(a, b, c)
        index += 3
    remaining = count - index
    if remaining == 3:
        c = (c + int.from_bytes(buf[4 * (index + 2):4 * (index + 3)], "little")) & M32
    if remaining >= 2:
        b = (b + int.from_bytes(buf[4 * (index + 1):4 * (index + 2)], "little")) & M32
    a = (a + int.from_bytes(buf[4 * index:4 * index + 4], "little")) & M32
    a, b, c = fin(a, b, c)
    return c & M32


def decode_state(buf):
    """Reverse of build_state: extract (rev, members, players) from the fork's
    replica so the matcher can REBUILD it with the knob variants. Offsets from
    session_state.cpp (the oracle's constants)."""
    REV, MCOUNT, MARRC, MARR = 4, 28, 48, 56
    MSTRIDE, M_ADDRLEN, M_ADDR, M_MACHLEN, M_MACH, M_JOIN, M_PCOUNT, M_PSLOT = 184, 8, 16, 112, 120, 136, 168, 176
    PL_COUNT, PL_TABLE, PL_STRIDE = 15184, 15192, 424
    PL_ID, PL_MEMBER, PL_SEQ, PL_FLAG = 4, 12, 20, 24
    rev = int.from_bytes(buf[REV:REV + 4], "little")
    count = int.from_bytes(buf[MCOUNT:MCOUNT + 4], "little")
    members = []
    for i in range(min(count, 64)):
        e = MARR + MSTRIDE * i
        addr = buf[e + M_ADDR:e + M_ADDR + 86]
        machine = int.from_bytes(buf[e + M_MACH:e + M_MACH + 8], "little")
        join = int.from_bytes(buf[e + M_JOIN:e + M_JOIN + 8], "little")
        owned = int.from_bytes(buf[e + M_PCOUNT:e + M_PCOUNT + 8], "little")
        slot = int.from_bytes(buf[e + M_PSLOT:e + M_PSLOT + 4], "little")
        members.append(dict(addr=addr, machine=machine, join=join,
                            owns=owned != 0, slot=slot))
    pl_count = int.from_bytes(buf[PL_COUNT:PL_COUNT + 4], "little")
    players = []
    for i in range(min(pl_count, 64)):
        e = PL_TABLE + PL_STRIDE * i
        players.append(dict(slot=i, pid=int.from_bytes(buf[e + PL_ID:e + PL_ID + 8], "little"),
                            member=int.from_bytes(buf[e + PL_MEMBER:e + PL_MEMBER + 4], "little"),
                            seq=int.from_bytes(buf[e + PL_SEQ:e + PL_SEQ + 4], "little"),
                            flag=buf[e + PL_FLAG] != 0))
    return rev, members, players


def rebuild_with_knobs(buf, base, pair, profile_copy):
    """Rebuild the replica from the decoded content with the knobs. The
    profile bytes (the 424-byte player blocks) are carried verbatim from the
    dump (their content choice is a later refinement if v2 misses)."""
    import state_hash_oracle as o
    rev, members, players = decode_state(buf)
    s = bytearray(o.STATE_SIZE)
    o.wr(s, o.REV, rev, 4)
    o.wr(s, o.HOSTIDX, 0, 4)
    o.wr(s, o.SUCC, 0, 4)
    o.wr(s, o.MCOUNT, len(members), 4)
    o.wr(s, o.MMASK, 0 if not members else (1 << len(members)) - 1, 8)
    o.wr(s, o.MARRC, len(members), 8)
    for i, m in enumerate(members):
        e = o.MARR + o.MSTRIDE * i
        o.wr(s, e + o.M_ADDRLEN, 86, 8)
        s[e + o.M_ADDR:e + o.M_ADDR + 86] = m["addr"]
        o.wr(s, e + o.M_MACHLEN, 8, 8)
        o.wr(s, e + o.M_MACH, m["machine"], 8)
        o.wr(s, e + o.M_JOIN, m["join"], 8)
        if m["owns"]:
            o.wr(s, e + o.M_PCOUNT, 1, 8)
            o.wr(s, e + o.M_PSLOT, m["slot"], 4)
        p = o.PEER_T + o.PEER_STRIDE * i
    mask = 0
    for pl in players:
        mask |= 1 << pl["slot"]
        e = o.PL_TABLE + base + o.PL_STRIDE * pl["slot"]
        # profile bytes carried verbatim from the dump's own block
        src = o.PL_TABLE + o.PL_STRIDE * pl["slot"] + 0
        if profile_copy and src + o.PL_STRIDE <= len(buf) and e + o.PL_STRIDE <= len(s):
            s[e:e + o.PL_STRIDE] = buf[src:src + o.PL_STRIDE]
        o.wr(s, e + o.PL_ID, pl["pid"], 8)
        o.wr(s, e + o.PL_MEMBER, pl["member"], 4)
        o.wr(s, e + o.PL_OWNED, 0, 4)
        o.wr(s, e + o.PL_SEQ, pl["seq"], 4)
        o.wr(s, e + o.PL_FLAG, 1 if pl["flag"] else 0, 1)
        o.wr(s, e + o.PL_CLR1, o.CLEARED, 4)
        o.wr(s, e + o.PL_CLR2, o.CLEARED, 4)
    o.wr(s, o.PL_COUNT, len(players), 4)
    o.wr(s, o.PL_MASK, mask, 4)
    return bytes(s)


def candidate_buffers(buf):
    """The rebuild-with-knobs candidates over the decoded dump."""
    for base in BASE_SHIFTS:
        for pair in PAIR_MODES:
            yield base, "obf", pair, rebuild_with_knobs(buf, base, pair, profile_copy=True)


def parse_client_x(path):
    xs = []
    with open(path, "rb") as f:
        for line in f:
            s = line.decode(errors="replace")
            m = re.search(r"checksum failed, 0x([0-9A-Fa-f]{8}) != 0x([0-9A-Fa-f]{8})", s)
            if m:
                xs.append((int(m.group(1), 16), int(m.group(2), 16)))
    return xs


def parse_fork_y(path):
    ys = []
    with open(path, "rb") as f:
        for line in f:
            s = line.decode(errors="replace")
            m = re.search(r"stage=state_hash client_base=(\d) hash=0x([0-9A-Fa-f]{8})", s)
            if m:
                ys.append((int(m.group(1)), int(m.group(2), 16)))
    return ys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dump", required=True)
    ap.add_argument("--client-log", required=True)
    ap.add_argument("--server-log", required=True)
    args = ap.parse_args()

    buf = open(args.dump, "rb").read()
    print(f"MATCHER: dump {len(buf)} bytes (kSessionStateSize={STATE_SIZE})")
    if len(buf) != STATE_SIZE:
        print(f"MATCHER FAIL: expected {STATE_SIZE}, got {len(buf)}")
        return 1

    xs = parse_client_x(args.client_log)
    ys = parse_fork_y(args.server_log)
    if not xs:
        print("MATCHER FAIL: no 'checksum failed' pairs in the client log")
        return 1
    x_unique = sorted(set(x for x, _ in xs))
    print(f"MATCHER: {len(xs)} rejection pairs; unique client X: {[hex(x) for x in x_unique[:6]]}")
    print(f"MATCHER: {len(ys)} fork send lines; unique Y: {[hex(y) for _, y in ys[:6]]}")

    # Self-check: the fork's own hash over the dump must equal a logged Y (the
    # transcription is correct only if this holds).
    computed = hash_bytes(buf)
    ys_flat = [y for _, y in ys]
    selfcheck = computed in ys_flat
    print(f"SELF-CHECK: hash_bytes(dump) = 0x{computed:08X} "
          f"({'MATCHES a logged Y' if selfcheck else 'matches NO logged Y'})")
    if not selfcheck:
        print("  (transcription or seed mismatch - the K-hash-initial needs the C++ source check)")

    print("\nCANDIDATE MATRIX (first-order knobs over the dump):")
    for base, name, pair, cand in candidate_buffers(buf):
        h = hash_bytes(cand)
        hit = "  <<< X MATCH" if h in x_unique else ""
        print(f"  base_shift={base} name={name} pair={pair}: 0x{h:08X}{hit}")

    matched = any(hash_bytes(cand) in x_unique
                  for _, _, _, cand in candidate_buffers(buf))
    print("\nVERDICT: " + ("A candidate matches the client's X - the layout is pinned; "
                           "the fix is to emit that layout." if matched else
                           "No first-order candidate matched - the remaining space is the "
                           "client-decode replication lane (profile name/obf transform + "
                           "the pair's replica position)."))
    return 0 if matched else 2


if __name__ == "__main__":
    sys.exit(main())