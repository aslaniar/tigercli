#!/usr/bin/env python3
# REGISTRY: caps: pcap-decode, bap-frame-decode, key-recovery, membership-decode
"""bapdecode.py - generalized pcap -> BAP-frame -> type-12 membership decoder.

Generalized 2026-08-28 from the GAH-REGION-DECODE lane's scratch decoders
(RE_output/scratch/gah_reassemble.py + gah_decode.py, which remain the raw
evidence of the lane). Reference doc: RE_output/claims/gah-region-decode.md.
The fork is the spec: these frames were sealed by the fork's own
middleware/secure_channel + server/bap code, so decode is self-consistent.

FRAME STACK (from the fork):
  outer   : [0]=0x01 [1]=type [2:6]=u32be len [6:]=payload   (type 1 = sealed)
  req hdr : [0:2]=u16be svc [2:6]=u32be task [6:]=body
  rsp hdr : [0:2]=u16be svc [2:6]=u32be task [6:8]=u16be status [8:]=body
  notif   : [0:2]=u16be svc(9) [2:6]=u32be seq [6:]=body
  svc9 env: [0]=disc [1:9]=u64be session [9:13]=u32be msgtype [13:17]=u32be len
  svc26   : [0:4]=u32be len(80) [4:20]=IV [20:52]=AES-CBC ct [52:84]=HMAC-SHA256
  seal    : [0:16]=tag [16:]=AES-GCM ct (nonce 12B LE counter)

CRYPTO CHAIN:
  derive_signon_secrets(token): HMAC-SHA256 over fixed labels -> enc/auth keys
  + 32B session token. svc-25 (c2s, plaintext) echoes the session token ->
  account slot. svc-26 (s2c, plaintext) carries nonce(12)+sessionKey(16) under
  AES-CBC(encKey, envelopeIv), authenticated HMAC(authKey). Thereafter frames
  are AES-128-GCM; s2c nonce base = nonce, advancing little-endian counter.

Usage:
  python3 RE_scripts/bapdecode.py --pcap F [--out PREFIX]
         [--token LABEL=TOK]... [--max-streams N]
  python3 RE_scripts/bapdecode.py --streams DIR --token ... [--out PREFIX]
  python3 RE_scripts/bapdecode.py --selftest
  python3 RE_scripts/bapdecode.py --verify STREAMS_DIR REPORT_JSON --token ...

  --pcap   : full pipeline (tshark reassembly -> decode). Needs tshark on PATH.
  --streams: DIR with streamN_s2c.bin / streamN_c2s.bin (pre-split; skips tshark)
  --token  : repeatable LABEL=HEX (account-slot bootstrap tokens; LABEL free
             text, slot = order of appearance)
  --selftest: SYNTHETIC oracle - builds a complete mini BAP session with
             planted keys/nonce/records, decodes it, then NEGATIVE tests:
             corrupt HMAC, corrupt GCM tag, wrong body size - each MUST be
             detected. Exits 0 only if every positive AND negative assert holds.
  --verify : re-decode a captured streams dir and assert against a prior
             decode_report.json (the 224-body ground truth from the GAH lane).

INTERPRETER: needs `cryptography` (miniconda python3 on this Mac; /usr/bin/python3
lacks it - the documented interpreter matrix in ENVIRONMENTS.md). Also needs
tshark on PATH for --pcap mode.

Exit codes: 0 ok / selftest-verify pass; 1 failure (asserts or verify);
2 usage/environment.
"""
import argparse
import hashlib
import hmac
import json
import os
import struct
import subprocess
import sys
import tempfile
import time

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

SRV_PORT = 30975
LABEL_ENC = b"sunrise-signon-encryption-key"
LABEL_AUTH = b"sunrise-signon-authentication-key"
LABEL_TOKEN = b"sunrise-signon-session-token"


# ---------------------------------------------------------------- crypto ---
def derive(token_hex):
    token = bytes.fromhex(token_hex)
    enc = hmac.new(token, LABEL_ENC, hashlib.sha256).digest()[:16]
    auth = hmac.new(token, LABEL_AUTH, hashlib.sha256).digest()[:16]
    session = hmac.new(token, LABEL_TOKEN, hashlib.sha256).digest()[:32]
    return enc, auth, session


def advance_nonce(n):
    n = bytearray(n)
    for i in range(len(n)):
        n[i] = (n[i] + 1) & 0xFF
        if n[i] != 0:
            break
    return bytes(n)


# ------------------------------------------------------------- framing ----
def read_u16be(b, o): return struct.unpack(">H", b[o:o + 2])[0]
def read_u32be(b, o): return struct.unpack(">I", b[o:o + 4])[0]
def read_u64be(b, o): return struct.unpack(">Q", b[o:o + 8])[0]


def parse_frames(buf):
    """Split a direction byte buffer into BAP outer frames.
    Returns list of (type, payload); type is int, or str for anomalies."""
    frames = []
    i = 0
    n = len(buf)
    while i + 6 <= n:
        if buf[i] != 0x01:
            j = buf.find(b"\x01", i + 1)
            if j < 0:
                break
            frames.append(("resync-skip", buf[i:j]))
            i = j
            continue
        ftype = buf[i + 1]
        plen = struct.unpack(">I", buf[i + 2:i + 6])[0]
        if i + 6 + plen > n:
            frames.append(("truncated", buf[i:]))
            break
        frames.append((ftype, buf[i + 6:i + 6 + plen]))
        i += 6 + plen
    return frames


def reassemble_pcap(pcap):
    """pcap -> {stream: {dir: bytes}} via tshark TCP reassembly."""
    if not subprocess.run(["which", "tshark"], capture_output=True).returncode == 0:
        raise SystemExit("ERROR: tshark not on PATH (brew install wireshark) "
                         "- required for --pcap mode")
    fields = ["tcp.stream", "ip.src", "tcp.srcport", "ip.dst", "tcp.dstport",
              "tcp.seq_raw", "tcp.len", "tcp.payload"]
    cmd = ["tshark", "-r", pcap, "-Y", "tcp",
           "-T", "fields", "-E", "separator=,", "-E", "occurrence=a"]
    for f in fields:
        cmd += ["-e", f]
    out = subprocess.run(cmd, capture_output=True, text=True)
    if out.returncode != 0:
        raise SystemExit("ERROR: tshark failed: %s" % out.stderr[-300:])
    streams = {}
    for line in out.stdout.splitlines():
        parts = line.split(",")
        if len(parts) < 8 or not parts[7]:
            continue
        try:
            stream = int(parts[0])
            sport, dport = int(parts[2]), int(parts[4])
            seq = int(parts[5])
            payload = bytes.fromhex(parts[7])
        except (ValueError, IndexError):
            continue
        direction = "c2s" if dport == SRV_PORT else \
            ("s2c" if sport == SRV_PORT else None)
        if direction is None:
            continue
        streams.setdefault(stream, {}).setdefault(direction, []).append(
            (seq, payload))
    out_streams = {}
    for stream, dirs in streams.items():
        out_streams[stream] = {}
        for direction, segs in dirs.items():
            segs.sort(key=lambda s: s[0])
            buf = bytearray()
            cursor = None
            for seq, payload in segs:
                if cursor is None:
                    buf = bytearray(payload)
                    cursor = seq + len(payload)
                    continue
                overlap = cursor - seq
                if overlap >= len(payload):
                    continue
                if overlap > 0:
                    buf += payload[overlap:]
                    cursor += len(payload) - overlap
                else:
                    if seq > cursor:
                        buf += b"\x00" * (seq - cursor)
                        cursor = seq
                    buf += payload
                    cursor = seq + len(payload)
            out_streams[stream][direction] = bytes(buf)
    return out_streams


# ------------------------------------------------------------- svc9/12 ----
def parse_svc9(plaintext):
    """Plaintext -> (session, msgtype, body) for svc-9 notifications, else None."""
    if len(plaintext) < 6 or read_u16be(plaintext, 0) != 9:
        return None
    env = plaintext[6:]
    if len(env) < 17 or env[0] != 1:
        return None
    session = read_u64be(env, 1)
    msgtype = read_u32be(env, 9)
    plen = read_u32be(env, 13)
    body = env[17:17 + plen]
    return session, msgtype, body


class BitReader:
    def __init__(self, data, bit=0):
        self.data = data
        self.bit = bit

    def read(self, width):
        v = 0
        for _ in range(width):
            byte = self.data[self.bit // 8] if self.bit // 8 < len(self.data) else 0
            v = (v << 1) | ((byte >> (7 - (self.bit % 8))) & 1)
            self.bit += 1
        return v


class BitWriter:
    def __init__(self):
        self.bits = []

    def write(self, value, width):
        for i in range(width - 1, -1, -1):
            self.bits.append((value >> i) & 1)

    def bytes(self):
        out = bytearray()
        for i in range(0, len(self.bits), 8):
            byte = 0
            for b in self.bits[i:i + 8]:
                byte = (byte << 1) | b
            if len(self.bits) - i < 8 and len(self.bits) - i > 0:
                byte <<= 8 - (len(self.bits) - i)
            out.append(byte)
        return bytes(out)


def decode_region_block(body, start_bit):
    """Decode 64 region records starting at start_bit. Returns list of dicts."""
    br = BitReader(body, start_bit)
    records = []
    for bubble in range(64):
        rec = {}
        rec["region_index"] = br.read(32) - 0x80000000
        br.read(2)                       # constant 1
        br.read(8)                       # constant 0
        br.read(2)                       # ambassador assigned = 2
        rec["ambassador_slot"] = br.read(6) - 1
        br.read(1)                       # 0
        br.read(32)                      # 0
        br.read(8)                       # 0
        br.read(32)                      # 0
        tokens = [br.read(8) for _ in range(32)]
        rec["transition_token"] = tokens[0]
        desc_count = br.read(8)
        if desc_count == 128:
            rec["advertised"] = True
            rec["descriptor"] = bytes(br.read(8) for _ in range(128)).hex()
            rec["online_session_id"] = br.read(64)
        else:
            rec["advertised"] = False
            rec["online_session_id"] = br.read(64)
        records.append(rec)
    return records


# bits: 835 head + peer*673 + 64 records + 333 tail
BITS_BASE = 30032
BITS_PEER = 673
BITS_ADV = 1024
REGION_START = 835


def decode_membership(payload):
    """Decode a type-12 body. Shape is inferred from size, then the region
    block is decoded and SELF-CHECKED (region_index == bubble*8, advertised
    count == candidate). Returns summary dict; decoded=False on no confident
    candidate (never raises)."""
    n = len(payload)
    result = {"size": n}
    candidates = []
    for peer in (0, 1):
        for adv in range(0, 4):
            bits = BITS_BASE + peer * BITS_PEER + adv * BITS_ADV
            expected = bits // 8 + (1 if bits % 8 else 0)
            if expected == n:
                candidates.append((peer, adv))
    result["shape_candidates"] = candidates
    best = None
    for peer, adv in candidates:
        start_bit = REGION_START + peer * BITS_PEER
        try:
            records = decode_region_block(payload, start_bit)
        except IndexError:
            continue
        ok = all(r["region_index"] == i * 8 for i, r in enumerate(records))
        nadv = sum(1 for r in records if r["advertised"])
        if ok and nadv == adv:
            best = (peer, adv, records)
            break
    if best is None:
        result["decoded"] = False
        return result
    peer, adv, records = best
    result["decoded"] = True
    result["peer_present"] = bool(peer)
    result["advert_count"] = adv
    result["regions"] = []
    for i, r in enumerate(records):
        if r["advertised"]:
            result["regions"].append({
                "bubble": i, "region_index": r["region_index"],
                "ambassador_slot": r["ambassador_slot"],
                "transition_token": r["transition_token"],
                "online_session_id": r["online_session_id"],
                "descriptor_head": r["descriptor"][:32],
            })
    result["region48_advertised"] = records[6]["advertised"]
    result["region56_advertised"] = records[7]["advertised"]
    result["region48"] = records[6]
    result["region56"] = records[7]
    return result


# ------------------------------------------------------------- pipeline ---
def recover_and_decode(streams, tokens, max_streams=None):
    """streams: {stream: {dir: bytes}}. tokens: list of hex strings (slot order).
    Returns report dict {stream: entry}."""
    derived = [derive(t) for t in tokens]
    session_to_slot = {d[2]: i for i, d in enumerate(derived)}
    report = {}
    stream_ids = sorted(streams)
    if max_streams:
        stream_ids = stream_ids[:max_streams]
    for stream in stream_ids:
        dirs = streams[stream]
        entry = {"stream": stream}
        s2c = dirs.get("s2c", b"")
        c2s = dirs.get("c2s", b"")
        s2c_frames = parse_frames(s2c)
        c2s_frames = parse_frames(c2s)

        slot = None
        for ftype, payload in c2s_frames:
            if ftype in (0, 2) and len(payload) >= 6:
                if read_u16be(payload, 0) == 25:
                    body = payload[6:]
                    if len(body) >= 34:
                        tok = body[2:34]
                        slot = session_to_slot.get(tok)
                        entry["svc25_token"] = tok.hex()
                        if slot is not None:
                            break
        entry["svc25_slot"] = slot
        enc_key = derived[slot][0] if slot is not None else None
        auth_key = derived[slot][1] if slot is not None else None

        nonce = None
        session_key = None
        for ftype, payload in s2c_frames:
            if ftype in (0, 2) and len(payload) >= 8:
                if read_u16be(payload, 0) == 26 and enc_key is not None:
                    body = payload[8:]
                    if len(body) >= 84:
                        iv = body[4:20]
                        ct = body[20:52]
                        mac = body[52:84]
                        calc = hmac.new(auth_key, body[0:52],
                                        hashlib.sha256).digest()
                        entry["svc26_hmac_ok"] = (calc == mac)
                        if calc != mac:
                            continue
                        dec = Cipher(algorithms.AES(enc_key),
                                     modes.CBC(iv)).decryptor()
                        pt = dec.update(ct) + dec.finalize()
                        nonce = pt[0:12]
                        session_key = pt[12:28]
        if session_key is None:
            entry["recovered"] = False
            entry["reason"] = "no svc26 / no slot / hmac fail"
            report[stream] = entry
            continue
        entry["recovered"] = True
        entry["nonce"] = nonce.hex()
        entry["session_key"] = session_key.hex()

        gcm = AESGCM(session_key)
        send_nonce = nonce
        memberships = []
        counts = {"total": 0, "membership12": 0, "decrypt_fail": 0,
                  "plaintext": 0}
        for ftype, payload in s2c_frames:
            if ftype in (0, 2):
                counts["plaintext"] += 1
                continue
            if ftype != 1:
                continue
            counts["total"] += 1
            tag, ct = payload[:16], payload[16:]
            try:
                pt = gcm.decrypt(send_nonce, ct + tag, None)
            except Exception:
                counts["decrypt_fail"] += 1
                send_nonce = advance_nonce(send_nonce)
                continue
            send_nonce = advance_nonce(send_nonce)
            svc9 = parse_svc9(pt)
            if svc9:
                session, msgtype, mbody = svc9
                if msgtype == 12:
                    counts["membership12"] += 1
                    memberships.append({
                        "session_id": session,
                        "session_hex": "0x%016X" % session,
                        "size": len(mbody),
                        "decode": decode_membership(mbody),
                    })
        entry["body_count"] = counts
        entry["memberships"] = memberships
        report[stream] = entry
    return report


# ------------------------------------------------------------ selftest ----
def build_synthetic_fixture():
    """Build a complete mini BAP session with PLANTED secrets and a planted
    type-12 body (bubbles 6+7 advertised). Returns (streams, truth)."""
    token_hex = "11" * 32
    enc, auth, session_token = derive(token_hex)
    nonce = bytes(range(12))
    session_key = bytes(range(16, 32))
    session_id = 0x9EAA300100200042

    # c2s: svc-25 request echoing the session token (body = [u16][32B token])
    c2s_plain = struct.pack(">HI", 25, 7) + b"\x00\x00" + session_token
    # s2c: svc-26 response [u16be 26][u32be task][u16be status] + env
    iv = bytes(range(16, 32))
    pad = b"\x00" * 4
    plain26 = nonce + session_key + pad
    pad_len = (16 - len(plain26) % 16) % 16
    plain26 += b"\x00" * pad_len
    cbc = Cipher(algorithms.AES(enc), modes.CBC(iv)).encryptor()
    ct26 = cbc.update(plain26) + cbc.finalize()
    env26 = struct.pack(">I", 80) + iv + ct26
    mac26 = hmac.new(auth, env26, hashlib.sha256).digest()
    s2c_plain = struct.pack(">HIH", 26, 8, 0) + env26 + mac26

    # planted type-12 body: peer=0, adv=2 (bubbles 6 and 7 advertised)
    bw = BitWriter()
    bw.write(0, 835)
    for bubble in range(64):
        adv = bubble in (6, 7)
        bw.write(0x80000000 + bubble * 8, 32)
        bw.write(1, 2)
        bw.write(0, 8)
        bw.write(2, 2)
        bw.write((1 if bubble == 7 else 2), 6)  # ambassador slot 0 (r56) / 1 (r48)
        bw.write(0, 1)
        bw.write(0, 32)
        bw.write(0, 8)
        bw.write(0, 32)
        for k in range(32):
            bw.write((k * 3) & 0xFF, 8)
        if adv:
            bw.write(128, 8)
            desc = bytes([(bubble * 16 + i) & 0xFF for i in range(128)])
            for byte in desc:
                bw.write(byte, 8)
        else:
            bw.write(0, 8)
        bw.write(0x9EAA300100200003 if bubble == 7 else 0, 64)
    bw.write(0, 333)
    mbody = bw.bytes()
    assert len(mbody) == (BITS_BASE + 2 * BITS_ADV) // 8, \
        "fixture body size %d != shape prediction" % len(mbody)

    # svc-9 notification carrying the type-12 body (plaintext frame)
    env9 = b"\x01" + struct.pack(">QII", session_id, 12, len(mbody)) + mbody
    notif = struct.pack(">HI", 9, 1) + env9

    # seal one encrypted frame with the planted key/nonce
    # wire order is TAG FIRST: [0:16]=tag [16:]=ct (per the fork's seal format)
    gcm = AESGCM(session_key)
    sealed = gcm.encrypt(nonce, notif, None)
    s2c_sealed = b"\x01\x01" + struct.pack(">I", len(sealed)) + \
        sealed[-16:] + sealed[:-16]

    streams = {
        7: {"c2s": b"\x01\x02" + struct.pack(">I", len(c2s_plain)) + c2s_plain,
            "s2c": b"\x01\x02" + struct.pack(">I", len(s2c_plain)) + s2c_plain +
                   s2c_sealed},
    }
    truth = {
        "token_hex": token_hex, "nonce": nonce.hex(),
        "session_key": session_key.hex(), "session_id": session_id,
        "body_size": len(mbody), "descriptor": desc.hex(),
        "ambassador_r48": 1, "ambassador_r56": 0,
    }
    return streams, truth


def selftest():
    fails = []

    def check(name, cond, detail=""):
        print("%s %-52s %s" % ("PASS" if cond else "FAIL", name, detail))
        if not cond:
            fails.append(name)

    print("== A. positive: planted session decodes end to end ==")
    streams, truth = build_synthetic_fixture()
    report = recover_and_decode(streams, [truth["token_hex"]])
    e = report[7]
    check("svc25 slot resolved", e.get("svc25_slot") == 0,
          str(e.get("svc25_slot")))
    check("svc26 HMAC verified", e.get("svc26_hmac_ok") is True,
          str(e.get("svc26_hmac_ok")))
    check("nonce+key recovered exactly", e.get("nonce") == truth["nonce"] and
          e.get("session_key") == truth["session_key"])
    ms = e.get("memberships", [])
    check("type-12 body found with planted session",
          len(ms) == 1 and ms[0]["session_hex"] ==
          "0x%016X" % truth["session_id"],
          str([m["session_hex"] for m in ms]))
    if not ms:
        print("SELFTEST FAIL (no membership decoded)")
        return 1
    d = ms[0]["decode"]
    check("body decoded confidently", d.get("decoded") is True,
          str(d.get("shape_candidates")))
    check("advert count == 2 (r48+r56)", d.get("advert_count") == 2 and
          d.get("region48_advertised") and d.get("region56_advertised"))
    check("region56 descriptor head matches planted",
          d.get("region56", {}).get("descriptor", "").startswith(
              truth["descriptor"][:32]))
    check("ambassador slots decoded (r56=0 peer, r48=1 self)",
          d.get("region56", {}).get("ambassador_slot") == 0 and
          d.get("region48", {}).get("ambassador_slot") == 1)
    check("online_session_id r56 == planted",
          d.get("region56", {}).get("online_session_id") == 0x9EAA300100200003)

    print("== B. negatives: corruptions MUST be detected ==")
    # B1: corrupt svc26 HMAC -> recovery must fail (no silent accept)
    bad = json.loads(json.dumps({}))  # placeholder to keep structure clear
    streams_b = json.loads(json.dumps({}))  # deep-copy via rebuild below
    streams_b2, _ = build_synthetic_fixture()
    c2s = bytearray(streams_b2[7]["c2s"])
    s2c = bytearray(streams_b2[7]["s2c"])
    # svc26 hmac sits in the plaintext response frame; flip a mac byte
    hmac_pos = 6 + 8 + 4 + 16 + 32  # outer hdr + rsp hdr + len + iv + ct
    s2c[hmac_pos] ^= 0xFF
    rep = recover_and_decode({7: {"c2s": bytes(c2s), "s2c": bytes(s2c)}},
                             [truth["token_hex"]])
    check("corrupt svc26 HMAC -> recovery REJECTED",
          rep[7].get("recovered") is not True, str(rep[7].get("reason")))

    # B2: corrupt GCM tag -> counted as decrypt_fail, not a crash/ghost body
    streams_c, _ = build_synthetic_fixture()
    s2c_c = bytearray(streams_c[7]["s2c"])
    s2c_c[-1] ^= 0xFF  # last byte of the sealed frame = tag
    rep = recover_and_decode({7: {"c2s": streams_c[7]["c2s"],
                                  "s2c": bytes(s2c_c)}},
                             [truth["token_hex"]])
    bc = rep[7].get("body_count", {})
    check("corrupt GCM tag -> decrypt_fail counted, no ghost body",
          bc.get("decrypt_fail") == 1 and bc.get("membership12") == 0,
          str(bc))

    # B3: wrong body size -> no shape candidate -> decoded False (unit test on
    # decode_membership directly; appending at stream level would not enter
    # the frame payload at all)
    streams_e, _ = build_synthetic_fixture()
    good_rep = recover_and_decode(streams_e, [truth["token_hex"]])
    good = good_rep[7]["memberships"][0]["decode"]
    check("wrong body size -> no shape candidate -> decoded False",
          good.get("decoded") is True and
          decode_membership(b"\x00" * 4011)["decoded"] is False and
          decode_membership(b"\x00" * 4009)["decoded"] is False,
          "good=%s candidates(4011)=%s" % (
              good.get("decoded"),
              decode_membership(b"\x00" * 4011)["shape_candidates"]))

    print("SELFTEST %s" % ("PASS" if not fails else "FAIL: %s" % fails))
    return 0 if not fails else 1


# --------------------------------------------------------------- verify ---
def verify(streams_dir, report_json, tokens):
    """Re-decode captured streams; assert against a prior decode_report.json."""
    with open(report_json) as fh:
        truth = json.load(fh)
    streams = {}
    for f in os.listdir(streams_dir):
        if f.endswith(".bin"):
            stem = f[:-4]
            try:
                stream = int(stem.split("_")[0][6:])
                direction = stem.split("_")[1]
            except (ValueError, IndexError):
                continue
            streams.setdefault(stream, {})[direction] = \
                open(os.path.join(streams_dir, f), "rb").read()
    got = recover_and_decode(streams, tokens)
    fails = []
    for stream, tentry in sorted(truth.items()):
        gentry = got.get(int(stream), {})
        tb = tentry.get("body_count", {})
        gb = gentry.get("body_count", {})
        if tb.get("membership12", 0) == 0:
            continue  # ground-truth stream carries no vectors
        if gentry.get("recovered") != tentry.get("recovered"):
            fails.append("stream %s recovery mismatch" % stream)
            continue
        if gb.get("membership12") != tb.get("membership12"):
            fails.append("stream %s: m12 %d != truth %d" %
                         (stream, gb.get("membership12"),
                          tb.get("membership12")))
            continue
        for tm, gm in zip(tentry.get("memberships", []),
                          gentry.get("memberships", [])):
            td, gd = tm.get("decode", {}), gm.get("decode", {})
            for key in ("decoded", "peer_present", "advert_count",
                        "region48_advertised", "region56_advertised"):
                if td.get(key) != gd.get(key):
                    fails.append("stream %s body %s: %s %r != truth %r" %
                                 (stream, tm.get("session_hex"), key,
                                  gd.get(key), td.get(key)))
            if td.get("region56", {}).get("descriptor", "")[:32] != \
                    gd.get("region56", {}).get("descriptor", "")[:32]:
                fails.append("stream %s: region56 descriptor head mismatch" %
                             stream)
    total = sum(e.get("body_count", {}).get("membership12", 0)
                for e in got.values())
    print("verify: %d membership bodies re-decoded across %d streams" %
          (total, len(got)))
    if fails:
        print("VERIFY FAIL:")
        for f in fails[:12]:
            print("  - %s" % f)
        return 1
    print("VERIFY PASS: all decoded fields match the ground truth")
    return 0


# ------------------------------------------------------------------ main ---
def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--pcap")
    ap.add_argument("--streams")
    ap.add_argument("--token", action="append", default=[],
                    help="LABEL=HEX (repeatable; slot = order)")
    ap.add_argument("--out", default=None, help="output report prefix")
    ap.add_argument("--max-streams", type=int, default=None)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--verify", nargs=2, metavar=("STREAMS_DIR", "REPORT_JSON"))
    args = ap.parse_args(argv)

    if args.selftest:
        return selftest()
    if args.verify:
        tokens = [t.split("=", 1)[1] for t in args.token]
        if not tokens:
            print("ERROR: --verify needs --token LABEL=HEX (slot order)")
            return 2
        return verify(args.verify[0], args.verify[1], tokens)

    tokens = []
    for spec in args.token:
        tokens.append(spec.split("=", 1)[1] if "=" in spec else spec)
    if args.pcap:
        streams = reassemble_pcap(args.pcap)
    elif args.streams:
        streams = {}
        for f in os.listdir(args.streams):
            if not f.endswith(".bin"):
                continue
            stem = f[:-4]
            try:
                stream = int(stem.split("_")[0][6:])
                direction = stem.split("_")[1]
            except (ValueError, IndexError):
                continue
            with open(os.path.join(args.streams, f), "rb") as fh:
                streams.setdefault(stream, {})[direction] = fh.read()
    else:
        ap.print_help()
        return 2
    report = recover_and_decode(streams, tokens, args.max_streams)
    prefix = args.out or "bapdecode_%s" % time.strftime("%Y%m%d_%H%M%S")
    with open(prefix + "_report.json", "w") as fh:
        json.dump(report, fh, indent=2)
    n12 = sum(e.get("body_count", {}).get("membership12", 0)
              for e in report.values())
    dec = sum(1 for e in report.values() for m in e.get("memberships", [])
              if m["decode"].get("decoded"))
    print("LIVENESS: streams=%d m12=%d decoded=%d report=%s_report.json" %
          (len(report), n12, dec, prefix))
    for stream in sorted(report):
        e = report[stream]
        bc = e.get("body_count", {})
        if e.get("recovered") and bc.get("total"):
            print("  stream %d: slot=%s bodies=%d m12=%d fail=%d" %
                  (stream, e.get("svc25_slot"), bc["total"],
                   bc["membership12"], bc["decrypt_fail"]))
    return 0 if n12 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
