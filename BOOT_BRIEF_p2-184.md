# BOOT_BRIEF_p2-184 — THE NONCE FRONT: MEASURING BOTH SIDES OF THE FAILED COMPARISON

STATUS: live (2026-09-06, drafted post-p2-183).
FRONT: instance-nonce

INSTRUMENTS: join_type0a (pktdump), inst_nonce

## PRIOR ART (required field)
q.sh terms: inst_nonce / 0x1416C1260 / join_type0a / nonce. Read in full:
connection-layer-join-delivery.md (the p2-183 decode: OOB channel + declared
size 1536 - both proven correct by p2-183); the p2-183 outcome (join_type0a
FIRED on the mac, died ~1 ms, no close/refuse/rebuild -> the nonce's silent
drop, not the lookup path). The nonce getter's shape (verified-by-reading
this session): FNV-1a lowercased (0x1402F6A60) of a runtime string global
(0x142003448), truncated to 16 bits, XOR a word that is 0x4A-derived (the
alternate branch reads a stored dword at 0x142003400) or 0x4A/0x128
fallbacks - runtime values, hence the instrument.

## PURPOSE (ONE CONTRACT)
Measure BOTH sides of the failed comparison in one boot: the packet record's
word[+0] as the OOB consumer built it (what arrived), and 0x1416C1260()'s
return (what the receiver computes). The diff names the fix: if the record's
nonce is a wire field, the fork stamps the relayed join with the receiver's
nonce; if the record's word comes from connection state, the transport
envelope is the fix surface.

## THE CHANGE
- server 4f1dfced4f5a9e9e: UNCHANGED (the p2-183 OOB relay stays).
- clients BOTH: +1 hook (inst_nonce 0x1416C1260, Probe::retwatch - the
  getter's change-gated return) and join_type0a upgraded in place with
  Probe::pktdump (enter-side dump of the packet record's first 0x20 bytes,
  novelty-gated). 56 -> 57. verify_hook_rvas PASS (105 RVAs, 0 bad, 57/57).
- SERVER-SIDE GAP (governing-constraint ledger): the fork does not yet know
  each client's instance nonce; until this boot measures it, the relay cannot
  stamp the receiver's nonce. This boot's instruments READ both sides; no
  client behavior is modified.

## INSTRUMENTS
join_type0a (now with pktdump: stage=pktdump lines - nonce/flags/count/key16)
/ inst_nonce (stage=retwatch lines naming the getter's return) / the p2-182
set (join_processor/admit/add_candidates/sess_state/join_gate/join_reserve/
join_handler/join_msg/resv) / server: join_relay result=sent, joincapture.

## READOUT TRIGGER (required field)
- stage=pktdump: NEVER-OBSERVED (new instrument; fires at the join gate's
  enter - the p2-183 boot PROVED the gate fires on a relayed join, so the
  trigger's event exists in recorded data: the p2-183 mac log shows
  join_type0a call=1 at t=260701; the replay arm is the pktdump's own
  novelty gate over that single recorded event - one fire).
- stage=retwatch fn=inst_nonce: NEVER-OBSERVED (new instrument; the getter's
  first call emits its baseline).
- join_relay/join_processor/admit/resv: existing behaviors (p2-183 proven).

## PRE-NAMED OUTCOMES
  (a) pktdump shows word[0]=N, inst_nonce shows R, N != R, and N looks like a
      wire-carried value (present in the captured container bytes) -> the fix
      is a server-side nonce STAMP on the relayed container: learn each
      client's nonce (from its own packets/getter) and patch the word.
  (b) N == R at the gate but join_processor still silent -> the lookup or the
      state check failed differently than concluded -> re-read the handler
      paths against the pktdump's flags/count values.
  (c) pktdump silent + join_type0a fires -> the record pointer wasn't readable
      (instrument defect - the r8 assumption) -> fix the probe, not the front.
  (d) inst_nonce never fires -> the getter runs on a different path than the
      gate (or the join never arrives again) -> check join_type0a first.

## ABANDON OUTCOME (empty-mask #7)
If (c) reproduces (the record unreadable on both machines), the pktdump
instrument dies - the nonce provenance falls back to the static decode of the
OOB receive loop (the 0x141C9AD28-vtable object). No retries; the front's
question stays open with the static road.

## EFFECT CLAIM (empty-mask #5)
Not a behavior claim. The EFFECT: the first direct measurement of the packet
record's nonce word AND the receiver's computed nonce in one archive - the
two numbers whose diff blocked the join processor since p2-183.

## STATE READERS (empty-mask #1)
- the record's fields: DIRECT = stage=pktdump (dumped from r8 at the gate).
- the receiver's nonce: DIRECT = stage=retwatch fn=inst_nonce (the getter's
  own return).
- the handler's outcome: DIRECT = join_processor/admit enter lines (existing).

## FIX SURFACE: server
No behavior change this boot (instruments only, read-only; the p2-183 relay
stays as deployed). The NEXT change (post-measurement) is server-side:
stamping the relayed join's nonce word. CLIENT-SIDE GAP: none - the getter's
nonce is provably computable client-side; the fork needs the receiver's value
on the wire, which this boot measures.

## WIDE NET
- joincapture (server, unconditional) - did the joins arrive.
- join_relay result=sent - did the relay deliver (p2-183 proven).
- join_type0a + pktdump - the gate's entry and the record's contents.
- inst_nonce - the receiver's computed nonce.
- join_processor/admit/resv - everything downstream, pre-wired.

## CHAIN MARKS (L16)
  L1 both machines land                     verified-by-execution (p2-180)
  L2 clean transition completes             verified-by-execution (p2-180)
  L3 record identity compositions match     verified-by-dump (20.309)
  L4 record born containerless              verified-by-log (20.286/20.308)
  L5 hosted sessions exist in-fork          verified-by-execution (p2-182)
  L6 join delivered on the connection layer verified-by-execution (p2-183:
                                            join_type0a FIRED on the mac)
  L7 the join gate's nonce gate passes      unknown (THIS BOOT - the contract)
  L8 the ladder climbs to (4,5)             unknown
  L9 guard/receiver/codec/entity/render     unknown

## OBSERVER BUDGET / CALL FREQUENCY
- inst_nonce: retwatch class (change-gated; the getter may be called per
  join-check and elsewhere - budget 12 distinct values).
- pktdump: per-join event class, novelty-gated, budget 24.
- everything else: unchanged from p2-182/p2-183.

## HOOK COUNT: 57 (56 + inst_nonce; hook_targets declares=57 initializers=57)
## INSTRUMENT SOURCES: RE_build/Sunrise-fork-inventory/Sunrise/src/client/hooks/milestone_trace/milestone_trace_observer.cpp
## INSTRUMENT LIVENESS
the names ("inst_nonce", "join_type0a", "join_processor", "sess_state") must
appear in BOTH clients' attach lines.

## FALSIFIABLE CLAIM
With relay_peer_join on and both links up: stage=pktdump fires >= 1 time
across the two machines (the relayed join reaches the gate again), AND
stage=retwatch fn=inst_nonce fires >= 1 per machine. REFUTED if pktdump is
absent while join_type0a fires (the record unreadable -> outcome (c)) or if
no join arrives at all (check joincapture first - input gate).

## ABSENCE NEGATIVES (both kinds)
- zero pktdump + zero join_type0a: the relay didn't deliver this boot
  (join_relay result=none / peers=0 -> timing; read the whole boot first).
- zero inst_nonce lines with joins flowing: the getter is inlined or bypassed
  on this path - the retwatch's silence becomes the instrument's defect log.

## GRAPHICS DELTA (U12)
Expected new rendered models: 0 (read-only instruments; no behavior change).

## SETUP
  1. Server unchanged (4f1dfced4f5a9e9e running; reset claims at the boot
     boundary - backgrounded, hangs after succeeding).
  2. Clients deployed BOTH (80a9475f88b8a29e; preflight PASS recorded).
  3. rig ssh control socket up.
  4. Both clients land; NO in-game actions.

## ADVERSARIAL PASS: the retwatch/pktdump gates are change/novelty-gated
## (the p2-181 lesson applied); hook RVAs verifier-passed; the outcome tree
## covers the instrument's own failure ((c)/(d)). The one unreviewed
## assumption: the OOB consumer builds a NEW record per datagram (if it
## reuses a per-connection record, pktdump's novelty gate still fires once
## and the dump answers the question).

## DO NOT
  - do not read the machinery lines before join_relay=sent (input gate)
  - do not ship any nonce-patching change this boot (measure first - U2)
  - do not launch the server from anywhere but the repo root
  - do not modify the client beyond the declared instruments
