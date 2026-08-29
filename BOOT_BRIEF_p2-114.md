# BOOT BRIEF p2(114) - THE GRAND CAPTURE (observation only, paired)

STATUS: live (2026-08-29 ~14:4x). Author: Claude Code session.
Reads with FINDINGS 20.174 (the static pass), 20.173, 20.172, FRONT_e2e-stack.md.
Client DLL `45ef17f93b901db9` on BOTH machines. Server `b9b0f3823f74d1bf` UNCHANGED,
`membership_peer_retry_cap` = 2 (the tuned brake), restarted, claims 0.
ZERO behaviour change on either side. Two NEW observers, both read-only, both
DEFAULT-FALSE and armed by settings on BOTH clients for this boot.

## PURPOSE

p2(110) proved the session, activity and transport layers are FINISHED. 20.173 proved
the only thing missing is the profile/appearance block, and that it is missing in BOTH
directions in code we own. This boot gathers, in ONE run, every remaining fact needed to
write the server-side encoder - and writes nothing.

Four questions, all previously unanswerable:
  Q1 Does a profile block EVER reach either client, from any source? 0x1417AF360 runs
     ONLY when a player row's profile-present flag is set, so its firing IS the answer.
  Q2 What are the decoded bytes? Its arguments carry region A (232B), both 4B headers
     and the tail (20B); region B is at regionA+0xE8 on the wire path.
  Q3 Does the client ever send membership UPSTREAM? UNKNOWN and previously unknowable:
     the handle_message observer HARDCODES `dir=down` (line 118), so the absence of
     `dir=up` is an instrument limit, not a finding. A pcap sees both directions.
  Q4 Is the wire apply's no-validation reading correct at runtime? The static read says
     the apply passes verify=0 and a dummy hash and that 0x1417AF6D3 `je` skips the whole
     lookup3. Logging arg7/arg8 confirms or refutes it by execution.

WHAT THIS BOOT DOES NOT TEST. It authors no profile, so it cannot make a guardian
visible. It does not touch admission (closed), the retry cap (reverted), physics
(`physicsHostSession` stays OFF - its own doc says it produces no wire output and costs
a render-thread frame stall, exactly the black-screen class we are told to avoid), or
`serverDefaultEntity` (VERIFIED dead: 3 references, all settings-parsing, nothing reads
the gate).

## GRAPHICS DELTA  (L12)

ZERO new rendered models, and this is structural, not a hope: no profile block is
authored by anything in this boot, both clients stay `pc=0` exactly as in p2(110), and
p2(110) rendered correctly and was fully controllable on the mac. Both observers are
read-only. The mac's usual cold shader compile is the only cost. The rig's long-standing
black screen is USER-CONFIRMED PRE-EXISTING and reproduces solo; it is a constant, not a
result of this boot.

## FALSIFIABLE CLAIM  (L6)

CLAIM: both clients log `ev=ingress stage=install result=ok rva=0x17AF360`, and at least
one client logs `ev=ingress stage=apply` carrying `verify=0x0` and `hash=0xFFFFFFFF` with
a `caller_rva` resolving inside the wire apply (0x141781800..0x1417834CE, i.e. RVA
0x1781800..0x17834CE), followed by `tag=regionA` chunks totalling 232 bytes.

PRE-NAMED CONTENT NEGATIVE 1 (the one that most changes the plan):
  If `stage=install result=ok` appears on both clients and `stage=apply` NEVER fires with
  a wire-apply `caller_rva` - only with the registry caller (~RVA 0x17A6xxx) or not at
  all - then NO profile block ever crosses our wire in either direction. Q1 is answered
  NO, and the encoder must author a block from scratch with NO captured reference. That
  makes the wire ENCODING (the decoder was never located) the blocking unknown, and the
  next lane is finding the decoder, NOT writing a guessed encoder.

PRE-NAMED CONTENT NEGATIVE 2:
  If `stage=apply` fires with `verify` NONZERO or `hash` != 0xFFFFFFFF on the wire path,
  my static reading of the apply is WRONG, an authored block WOULD need a correct
  lookup3, and no encoder ships until the hash is reproduced and validated.

PRE-NAMED CONTENT NEGATIVE 3:
  If the pcap shows the client sending type-12 membership UPSTREAM (Q3 = yes), then a
  real client-authored profile block may be recoverable from the wire via bapdecode.py,
  and THAT becomes the encoder's ground truth instead of anything synthesized.

## ABSENCE NEGATIVE  (L13)

If ZERO `ev=ingress` lines appear: FIRST hypothesis is an invalid measurement.
  - Deployment provenance (L14): `grep -ac "ev=ingress stage=apply"` == 1 in the DEPLOYED
    DLL on both machines (deploy_client_dll.sh greps the deployed file; both asserted).
  - ADDRESS provenance, and this is new and mandatory after p2(112):
    `RE_scripts/verify_hook_rvas.py` = 35 RVAs, 0 bad, `kHelperARva 0x17AF360 -> ok fn
    0x1417af360..0x1417afb2b`. A module-range check passes on a WRONG address; .pdata is
    the only proof. The install line must print `rva=0x17AF360`.
  - Arming provenance: `profile_ingress` true in BOTH settings files (mac verified
    locally; rig verified by reading the file back off the rig - no BOM, no CRLF, 229
    keys, exactly 2 added, none removed or changed).
  - The disarmed path is LOUD (`install result=skipped why=disarmed`), so total silence
    indicts the DLL load, not the setting.
  - Capture liveness: en0 + lo0 both probe-verified BEFORE launch (UDP x2 + TCP/30975 x2;
    en0 6 pkts, lo0 3 pkts). The mac's "received by filter" counter is BOGUS (20.166);
    only the probe proves an empty pcap.
  - `ev=profile` (harvest) firing while `ev=ingress` stays silent is itself informative:
    it means the local registry commit runs but never routes through 0x1417AF360, which
    would refute the call-graph reading in profile-builder raw PHASE 2.

## CHAIN MARKS  (L16)

  L1  session/activity/transport complete       VERIFIED-BY-EXECUTION (p2(110), both machines)
  L2  every group_target row is pc=0            VERIFIED-BY-EXECUTION (p2(110), both)
  L3  our encoder hardcodes the profile bit 0   VERIFIED-BY-READING (session_messages.cpp)
  L4  the apply gates BOTH helpers on that bit  VERIFIED-BY-READING (0x14178241b/241f)
  L5  the wire apply passes verify=0 + dummy
      hash, and verify==0 skips the lookup3     VERIFIED-BY-READING (0x1417af6d3 `je`,
                                                arg frame: rbp+0x7d0 = arg7) - RUNTIME
                                                CONFIRMATION IS THIS BOOT (Q4)
  L6  region B helper is an unconditional 136B
      memcpy with no validation                 VERIFIED-BY-READING (0x1417af2d0, 8 movups
                                                + 1 movsd, dest 0x3c68 = 0x3b60+0x108)
  L7  0x1417AF2D0 is NOT a function start       VERIFIED-BY-EXECUTION (pdata_bounds: in a
                                                gap, chains to 0x1417AE4B0) - so it is
                                                deliberately NOT hooked
  L8  a profile block ever reaches a client     UNKNOWN  <- THIS BOOT (Q1)
  L9  its decoded bytes                         UNKNOWN  <- THIS BOOT (Q2)
  L10 client sends membership upstream          UNKNOWN  <- THIS BOOT (Q3, pcap only)
  L11 the wire ENCODING of the profile block    UNKNOWN - the decoder was never located.
                                                NOT resolved by this boot unless L10 is
                                                yes; content negative 1 names that fork.
  L12 two guardians VISIBLY render              UNKNOWN - behind L11

No link is written as "one boot away". L8/L9/L10 are what this boot resolves, and L5
gets its runtime confirmation.

## ADVERSARIAL PASS: waived: observation only. No writes of any class, no server change,
no behaviour switch, zero new rendered models, both new observers default-false and
disarmable without a rebuild. Every hooked address is .pdata-verified by a gate that
already caught two real errors today (p2(112)'s dropped digit, and 0x1417AF2D0 being a
mid-function fragment - which is why region B is read as an offset from region A rather
than hooked). This is the FIRST attempt at the profile-ingress question. Recorded as a
waiver, not a pass.

## INSTRUMENTS: ev=ingress stage=apply, ev=ingress stage=install, ev=profile stage=commit

All three verified present in the DEPLOYED DLL on both machines (`45ef17f93b901db9`).

## PRE-BOOT SEQUENCE (all DONE at time of writing)

  1. DONE - DLL built `45ef17f93b901db9`; verify_hook_rvas.py PASS (35 RVAs, 0 bad);
     deployed + hash-asserted + literal-checked on BOTH machines.
  2. DONE - `profile_harvest` and `profile_ingress` true on BOTH clients;
     `admission_inject` false/absent on both; rig settings verified byte-clean.
  3. DONE - server restarted, retry cap 2, 3/3 listeners + UDP 30976, nat ok, claims 0.
  4. DONE - both client log slates cleared; server log rotated by the restart.
  5. DONE - captures running on en0 AND lo0 with a combined filter
     (`tcp port 30975 or udp port 3097/3074/3075/30976`), both probe-verified.
  6. TODO (user) - launch RIG first, wait for `activity:in_world`.
  7. TODO (user) - launch MAC, both dwell in the Tower ~5 min.
  8. TODO - collect both client logs, server log, both pcaps into
     RE_output/captures/p2-114_grand_capture/; then decode the BAP stream with
     `RE_scripts/bapdecode.py` (miniconda python3; needs `cryptography`).
