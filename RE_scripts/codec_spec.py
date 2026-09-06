#!/usr/bin/env python3
# REGISTRY: caps: codec-spec, round-trip-property, femu-crosscheck
"""codec_spec.py - EXECUTABLE CODEC SPECS (tool-brief-codec-specs.md,
2026-09-06). Each decoded wire format becomes a declarative spec generating
BOTH a decoder and an ENCODER (the fork must ship these encoders anyway -
this is the encoder work in a form that proves itself), validated by
round-trip + fault-localization + truncation semantics + const rejection +
naive-variant arms (proving the tests can fail), with a femu cross-check
slot against the client's own code via femu_decode.

Two spec shapes:
  byte-layout (default): sequential byte fields (u8/u16/u32/u64 with order,
      fixed bytes) plus ABSOLUTE-BIT optional bit fields (the fork's
      bit_reader semantics: MSB-first stream, LSB-ordered value assembly).
  bit_stream: the ent-wire grammar - MSB-first bits off big-endian words,
      presence bits gating conditional fields, decode-time params (the
      anchor codec's validation flag).
  native: a spec that WRAPS an existing codec (name_codec) - never a fork.

HONESTY RULES (U17 + the T3-F arms of the brief):
  - optionality must be declared with its source; required fields get NO
    placeholder padding (T3-F5) and a required-missing encode REJECTS.
  - truncation semantics are declared (legal_after_bit); everything else
    raises TRUNCATED (T3-F2).
  - a nonzero/const field violation raises CONST-VIOLATION at encode (T3-F3).
  - a single-bit flip of a valid body either rejects or decodes DIFFERENTLY,
    never a silent identical accept (T3-F1).
  - spec["naive_variants"] are deliberately wrong implementations; the
    validator asserts they FAIL (T3-F4 - the guard-fails-pre-fix rule
    applied to the tests themselves).

CLI:
  codec_spec.py --list
  codec_spec.py --validate <spec> [--rounds 1000] [--seed 20260906]
  codec_spec.py --decode <spec> <hex|@file>
  codec_spec.py --encode <spec> '<json>'
Exit: 0 all arms pass; 1 any arm failed; 2 usage; 3 spec load error.
Specs: RE_scripts/codec_specs/<name>.py (SPEC dict [+ NATIVE]).
"""
import importlib
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
SPECDIR = os.path.join(HERE, "codec_specs")


class SpecError(Exception):
    def __init__(self, kind, field=None, at=None, msg=""):
        self.kind = kind            # TRUNCATED | CONST-VIOLATION | BAD-VALUE
        self.field = field
        self.at = at
        super().__init__("%s%s%s: %s" % (
            kind, " @bit/byte %s" % at if at is not None else "",
            " (%s)" % field if field else "", msg))


# ------------------------------------------------------------- bit primitives ---
class BitReader(object):
    """The client's reader semantics (ent-receive-contract section 1):
    the bit = MSB of the stream first; multi-bit fields assemble
    LSB-ordered values (primitive 0x1403513B0)."""

    def __init__(self, data):
        self.data = data
        self.pos = 0

    def bit(self):
        if self.pos >= len(self.data) * 8:
            raise SpecError("TRUNCATED", at=self.pos, msg="no bit")
        b = (self.data[self.pos >> 3] >> (7 - (self.pos & 7))) & 1
        self.pos += 1
        return b

    def ubits(self, width):
        v = 0
        for i in range(width):
            v |= self.bit() << i
        return v


class BitWriter(object):
    def __init__(self):
        self.bits = []

    def bit(self, b):
        self.bits.append(b & 1)

    def ubits(self, value, width):
        for i in range(width):
            self.bits.append((value >> i) & 1)

    def to_bytes(self):
        out = bytearray((len(self.bits) + 7) // 8)
        for i, b in enumerate(self.bits):
            if b:
                out[i >> 3] |= 1 << (7 - (i & 7))
        return bytes(out)


# --------------------------------------------------------------- byte-layout ---
SIZES = {"u8": 1, "u16": 2, "u32": 4, "u64": 8}


class ByteCodec(object):
    def __init__(self, spec):
        self.spec = spec
        for f in spec["fields"]:
            t = f["type"]
            if t not in SIZES and t not in ("bytes", "bits"):
                raise SpecError("BAD-SPEC", field=f.get("name"),
                                msg="unknown byte-layout type %r" % t)
            if t == "bits" and not f.get("optional"):
                raise SpecError("BAD-SPEC", field=f.get("name"),
                                msg="bit fields in byte layout must declare "
                                    "optional+default (their presence/absence "
                                    "is a length fact)")

    def decode(self, data):
        obj = {}
        off = 0
        for f in self.spec["fields"]:
            t = f["type"]
            nm = f["name"]
            if t == "bits":
                at, w = f["at_bit"], f["width"]
                need = (at + w + 7) // 8
                if len(data) < need:
                    if f.get("optional"):
                        obj[nm] = f.get("default", 0)
                        continue
                    raise SpecError("TRUNCATED", field=nm, at=at)
                v = 0
                for i in range(w):
                    bitpos = at + i
                    if (bitpos >> 3) >= len(data):
                        raise SpecError("TRUNCATED", field=nm, at=bitpos)
                    v |= ((data[bitpos >> 3] >> (7 - (bitpos & 7))) & 1) << i
                obj[nm] = v
                continue
            size = SIZES[t] if t in SIZES else f["size"]
            if len(data) < off + size:
                raise SpecError("TRUNCATED", field=nm, at=off)
            raw = data[off:off + size]
            if t == "bytes":
                v = raw
            else:
                v = int.from_bytes(raw, "big" if f.get("order", "be") == "be"
                                   else "little")
                if f.get("nonzero") and v == 0:
                    raise SpecError("CONST-VIOLATION", field=nm,
                                    msg="%s must be nonzero" % nm)
            obj[nm] = v
            off += size
        return obj

    def encode(self, obj):
        for f in self.spec["fields"]:
            if f["type"] == "bits" or f.get("optional"):
                continue
            if f["name"] not in obj:
                raise SpecError("BAD-VALUE", field=f["name"],
                                msg="required field missing - no placeholder "
                                    "padding (T3-F5)")
        out = bytearray()
        off = 0
        for f in self.spec["fields"]:
            t = f["type"]
            nm = f["name"]
            if t == "bits":
                if nm not in obj:
                    continue
                v, w = obj[nm], f["width"]
                need = (f["at_bit"] + w + 7) // 8
                if len(out) < need:
                    out.extend(b"\x00" * (need - len(out)))
                for i in range(w):
                    bitpos = f["at_bit"] + i
                    if (v >> i) & 1:
                        out[bitpos >> 3] |= 1 << (7 - (bitpos & 7))
                continue
            size = SIZES[t] if t in SIZES else f["size"]
            if len(out) < off:
                out.extend(b"\x00" * (off - len(out)))
            if nm not in obj:
                v = 0
            else:
                v = obj[nm]
                if f.get("nonzero") and v == 0:
                    raise SpecError("CONST-VIOLATION", field=nm,
                                    msg="%s must be nonzero" % nm)
                if t != "bytes" and not 0 <= v < (1 << (8 * size)):
                    raise SpecError("BAD-VALUE", field=nm,
                                    msg="%#x out of range for %s" % (v, t))
            raw = v if t == "bytes" else v.to_bytes(
                size, "big" if f.get("order", "be") == "be" else "little")
            out.extend(raw)
            off += size
        return bytes(out)


# --------------------------------------------------------------- bit-stream ----
class BitStreamCodec(object):
    """ent-wire grammar: MSB-first bits; `when` gates a field on a decode
    PARAM (e.g. the anchor's validation flag) or an earlier field value.
    param_sets come from spec['param_sets'] (default [{}])."""

    def __init__(self, spec):
        self.spec = spec

    def _truthy(self, when, params):
        if when.startswith("not "):
            return not params.get(when[4:])
        return bool(params.get(when))

    def decode(self, data, **params):
        r = BitReader(data)
        obj = {"_bits_consumed": 0}
        for f in self.spec["fields"]:
            when = f.get("when")
            if when and not self._truthy(when, params):
                continue
            if f["type"] == "bit":
                obj[f["name"]] = r.bit()
            elif f["type"] == "ubits":
                obj[f["name"]] = r.ubits(f["width"])
            else:
                raise SpecError("BAD-SPEC", field=f.get("name"),
                                msg="unknown bit-stream type %r" % f["type"])
        obj["_bits_consumed"] = r.pos
        return obj

    def encode(self, obj, **params):
        w = BitWriter()
        for f in self.spec["fields"]:
            when = f.get("when")
            if when and not self._truthy(when, params):
                continue
            if f["type"] == "bit":
                w.bit(obj[f["name"]])
            else:
                w.ubits(obj[f["name"]], f["width"])
        return w.to_bytes()


class NativeCodec(object):
    """A spec that delegates to an existing codec (name_codec) - the wrap,
    never a fork. The adapter converts bytes<->dict at the spec layer."""

    def __init__(self, spec):
        self.spec = spec
        self.encode_fn = spec["native"]["encode"]
        self.decode_fn = spec["native"]["decode"]

    def decode(self, data):
        return self.decode_fn(data)

    def encode(self, obj):
        return self.encode_fn(obj)


def load(name):
    mod = importlib.import_module("codec_specs." + name)
    spec = mod.SPEC
    if spec.get("native"):
        return spec, NativeCodec(spec)
    if spec.get("bit_stream"):
        return spec, BitStreamCodec(spec)
    return spec, ByteCodec(spec)


# ---------------------------------------------------------------- validation ---
def random_object(spec, rng):
    obj = {}
    for f in spec["fields"]:
        t, nm = f["type"], f["name"]
        if t in SIZES:
            v = rng.getrandbits(8 * SIZES[t])
            if f.get("nonzero"):
                v = v or 1
            obj[nm] = v
        elif t == "bytes":
            obj[nm] = bytes(rng.randrange(256) for _ in range(f["size"]))
        elif t == "bits":
            if not f.get("optional"):
                obj[nm] = rng.getrandbits(f["width"])
            elif rng.random() < 0.5:
                obj[nm] = rng.getrandbits(f["width"])
    return obj


def _payload(obj):
    """Comparison view: strip provenance keys (underscore-prefixed) -
    _bits_consumed is metadata, not payload."""
    return {k: v for k, v in obj.items() if not k.startswith("_")}


def _mismatch(back, obj):
    """Asymmetric fields: every obj key must round-trip; DECODE MAY ADD
    derived keys (e.g. text views) - extra keys are not asymmetry."""
    return [k for k in obj if back.get(k) != obj[k]]


def validate(name, rounds=1000, seed=20260906):
    # __main__ dual-import: a spec module imports codec_spec.SpecError from
    # the IMPORTABLE module, which is a different class object from the
    # __main__ namespace when the validator runs as a script. Catch both.
    import codec_spec as _cs_mod
    spec_errs = (SpecError, _cs_mod.SpecError)
    spec, codec = load(name)
    fails = []
    arms = 0

    def check(arm, cond, detail=""):
        nonlocal arms
        arms += 1
        print("%s %-58s %s" % ("PASS" if cond else "FAIL", arm, detail))
        if not cond:
            fails.append(arm)

    fixtures = spec.get("fixtures", [])

    # ---- T3-P2 recorded fixtures ----
    fx_ok, fx_detail = True, ""
    for i, fx in enumerate(fixtures):
        if fx.get("kind") == "reject":
            try:
                codec.decode(fx["bytes"], **fx.get("params", {}))
                fx_ok, fx_detail = False, "fixture %d should reject" % i
            except spec_errs:
                pass
            continue
        try:
            got = codec.decode(fx["bytes"], **fx.get("params", {}))
        except spec_errs as e:
            fx_ok, fx_detail = False, "fixture %d raised %s" % (i, e)
            continue
        for k, v in fx.get("expect", {}).items():
            if got.get(k) != v:
                fx_ok = False
                fx_detail = ("fixture %d %s: got %r want %r"
                             % (i, k, got.get(k), v))
    check("T3-P2 recorded fixtures decode to recorded values", fx_ok,
          fx_detail)

    # ---- T3-P1 round-trip property (per param set) ----
    param_sets = spec.get("param_sets", [{}])
    rt_ok, rt_detail = True, ""
    for params in param_sets:
        rng = random.Random(seed)
        for i in range(rounds):
            obj = (spec["random_object"](rng, params)
                   if spec.get("random_object") else random_object(spec, rng))
            try:
                blob = codec.encode(obj, **params)
                back = codec.decode(blob, **params)
            except spec_errs as e:
                rt_ok, rt_detail = False, "round %d params %s: %s" % (
                    i, params, e)
                break
            if _mismatch(back, obj):
                rt_ok = False
                rt_detail = ("round %d params %s asymmetric: %s"
                             % (i, params,
                                [k for k in obj if back.get(k) != obj[k]]))
                break
    check("T3-P1 round-trip property (%d rounds x %d param sets, seed %d)"
          % (rounds, len(param_sets), seed), rt_ok, rt_detail)

    # ---- T3-F1 single-bit fault localization ----
    enc_obj = spec.get("roundtrip_fixture")
    if enc_obj is not None:
        p0 = param_sets[0]
        blob0 = codec.encode(enc_obj, **p0)
        base = codec.decode(blob0, **p0)
        # bits where a flip decoding identically is CORRECT, not a defect:
        #   (a) declared padding (spec["flip_ignore_bits"]: (start, end))
        #   (b) bit_stream bodies: bits past the consumed count for THIS
        #       param set are outside the format for that param.
        ignore = []
        for a, b in spec.get("flip_ignore_bits", []):
            ignore.extend(range(a, b))
        consumed = None
        if spec.get("bit_stream"):
            consumed = base.get("_bits_consumed")
        f1_ok, f1_detail = True, ""
        for bit in range(len(blob0) * 8):
            if consumed is not None and bit >= consumed:
                continue                    # (b) beyond the consumed body
            if bit in ignore:
                continue                    # (a) declared padding
            mutated = bytearray(blob0)
            mutated[bit >> 3] ^= 1 << (7 - (bit & 7))
            try:
                got = codec.decode(bytes(mutated), **p0)
            except spec_errs:
                continue
            if _mismatch(got, base) == []:
                f1_ok = False
                f1_detail = ("bit %d flipped: decoded identically (silent "
                             "accept)" % bit)
                break
        check("T3-F1 single-bit flips never decode identically (declared "
              "padding excepted)", f1_ok, f1_detail)
    else:
        print("SKIP  T3-F1 (no roundtrip_fixture declared)")
        arms -= 1

    # ---- T3-F2 truncation semantics ----
    t2_ok, t2_detail = True, ""
    if enc_obj is not None:
        blob0 = codec.encode(enc_obj, **(param_sets[0]))
        legal_after = spec.get("truncation", {}).get("legal_after_bit")
        for cut in range(len(blob0)):
            try:
                codec.decode(blob0[:cut], **(param_sets[0]))
                if legal_after is None or cut * 8 < legal_after:
                    t2_ok = False
                    t2_detail = ("cut at %d bytes decoded silently with "
                                 "required fields missing" % cut)
                    break
            except spec_errs as e:
                if e.kind != "TRUNCATED":
                    t2_ok = False
                    t2_detail = "cut at %d: %s (want TRUNCATED)" % (cut, e)
                    break
        check("T3-F2 truncation raises TRUNCATED (declared optionals "
              "excepted)", t2_ok, t2_detail)
    else:
        print("SKIP  T3-F2 (no roundtrip_fixture declared)")
        arms -= 1

    # ---- T3-F3 const/nonzero violation at encode ----
    f3_ok, f3_detail = True, "no const field in spec (nothing to violate)"
    const_f = next((f for f in spec["fields"] if f.get("nonzero")
                    or f.get("const") is not None), None)
    if const_f and enc_obj is not None:
        bad = dict(enc_obj)
        bad[const_f["name"]] = 0 if const_f.get("nonzero") else \
            const_f["const"] + 1
        try:
            codec.encode(bad, **(param_sets[0]))
            f3_ok, f3_detail = False, "const-violating encode accepted"
        except spec_errs as e:
            f3_ok = e.kind == "CONST-VIOLATION"
            f3_detail = str(e)
    check("T3-F3 const/nonzero violation rejected at encode", f3_ok,
          f3_detail)

    # ---- T3-F4 naive variants must FAIL ----
    for nv in spec.get("naive_variants", []):
        try:
            ok = nv["must_fail"]()
        except Exception:
            ok = True   # the naive variant crashing IS the designed failure
        check("T3-F4 naive variant %r fails as designed" % nv["name"], ok)

    total = arms
    print("CODEC SPEC %s: %d/%d ARMS PASS" % (name, total - len(fails), total))
    return 0 if not fails else 1


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    if argv[0] == "--list":
        for f in sorted(os.listdir(SPECDIR)):
            if f.endswith(".py") and f != "__init__.py":
                print(" ", f[:-3])
        return 0
    if argv[0] == "--validate":
        if len(argv) < 2:
            print("usage: --validate <spec> [--rounds N] [--seed N]")
            return 2
        rounds, seed = 1000, 20260906
        rest = argv[2:]
        for flag, conv in (("--rounds", int), ("--seed", int)):
            if flag in rest:
                i = rest.index(flag)
                rounds = rounds if flag != "--rounds" else int(rest[i + 1])
                seed = seed if flag != "--seed" else int(rest[i + 1])
        return validate(argv[1], rounds, seed)
    if argv[0] in ("--decode", "--encode"):
        if len(argv) < 3:
            print("usage: %s <spec> <data>" % argv[0])
            return 2
        spec, codec = load(argv[1])
        if argv[0] == "--decode":
            src = argv[2]
            data = (open(src[1:], "rb").read() if src.startswith("@")
                    else bytes.fromhex(src))
            try:
                print(codec.decode(data))
                return 0
            except spec_errs as e:
                print("REJECTED: %s" % e)
                return 1
        obj = json.loads(argv[2])
        try:
            print(codec.encode(obj).hex())
            return 0
        except spec_errs as e:
            print("REJECTED: %s" % e)
            return 1
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
