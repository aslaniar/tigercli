# BOOT_BRIEF_p2-189 — THE WIDE BINDING CAPTURE (the binders + the walk map + the widened compare)
STATUS: live (2026-09-06).
FRONT: session-lookup-identity

INSTRUMENTS: clients ONLY (the server is unchanged from 4b94d56a063c9534,
relay_join_target_identity=false — byte-verbatim relay). +6 hooks, 58 -> 64
targets: binder1, binder2, cof_index, cof_soid, walk_map, apply_stamp; and
sess_cmp WIDENED to the (caller RVA, key, blob) TRIPLE (budget 24 -> 64).
No behavior change: all hooks are read-only enter/leave observers.

## MODEL REVIEW (REQUIRED - the front carries third-branches: p2-185, p2-186, p2-188)
THE CAUSAL ASSUMPTION THAT DIES (banked, p2-187 brief): the state's idB flows
into the live blob via the membership machinery. Plus the NEW dead instrument
assumption this boot replaces (banked, HANDOFF_INSTRUMENT-WIDTH): that
(key, blob) pairs describe the GATE's walk. They describe the UNION of every
caller of the shared helper. This boot does not predict which container the
gate walks - it OBSERVES the walk (walk_map reads the six slots' binding
fields at the walk itself) and the binding events (the binders) side by side.

## PRIOR ART (required field)
q.sh terms: binder / 0x141772440 / walkmap / cof_soid / walk_map. Read in
full: connection-layer-join-delivery.md section 8 + the binder decode (this
session's reply, banked in the chat record until written up);
HANDOFF_2026-09-06_INSTRUMENT-WIDTH.md (the three instrument gaps + the
caller-discrimination spec); FRONT_peer-render-chain.md row 5; p2-188b's
capture (the blob census + the refusal timing).

## PURPOSE (ONE CONTRACT)
Map the session-to-connection binding end to end in ONE landing: which
machine contexts exist, which session each is bound to ([ctx+0x1C7C0]), when
and with what key the binders bind, what the apply stamps into each record's
blob window, and which (caller, key, blob) triples the shared equality
helper sees during the relayed join's gate. No value arms are tested - the
retarget setting is OFF and stays off.

## THE CHANGE
- clients BOTH: rebuilt DLL (64 targets; the 6 new are .pdata-backed function
  starts: 0x141772440/0x141773200/0x141795A40/0x1417951A0/0x14177A0B0/
  0x1416C5280; verify_hook_rvas PASS 112 RVAs 0 bad; hook_targets 64/64).
- server: UNCHANGED (4b94d56a063c9534; relay off).
- No behavior change of any kind: the observers never write game state.

## READOUT TRIGGER (required field)
- stage=walk_map: NEVER-OBSERVED - its first line IS the gate's walked map
  (six bind fields + the key). Change-gated on the (key, six-index) fingerprint.
- stage=applystamp: NEVER-OBSERVED - every firing is a blob stamping, with
  the soid and the destination's pre-state. Change-gated on (dst, soid).
- binder1/binder2 enter lines + stackargs: NEVER-OBSERVED - each firing is a
  binding event (ctx, flags, key/index, stack args, caller_rva).
- cof_index/cof_soid ret= lines: NEVER-OBSERVED - the returned session index
  (or -1) per create-or-find.
- sess_cmp: WIDENED (caller_rva= now in every line; budget 64 triples) - the
  gate's own comparisons separate from the shared helper's other callers.
- pktdump/inst_nonce/join_type0a/join_processor/sess_state/resv/admit: as
  p2-187/188b.

## PRE-NAMED OUTCOMES
  (a) walk_map's six binds include a slot bound to a session whose blob holds
      the fork's sessionId at the moment the relayed join's key is compared,
      and sesscmp shows the GATE's caller RVA with match=0 against some other
      blob -> the gate walks a DIFFERENT container than the matching one;
      the binding exists but is in the wrong slot set -> decode which message
      binds the gate's container.
  (b) walk_map's binds never include the fork's session at all (all zero or
      self-values) through the relayed join's refusal -> the binding was
      never APPLIED to the gate's container -> the binder triggers (stack
      args + caller_rva) name what DID bind, and the missing trigger names
      what the fork must publish.
  (c) cof_soid/cof_index fire with the fork's sessionId as the key but the
      returned index is -1 (not found) -> the client NEVER created the
      fork's session in the binding table -> the create path is the fix.
  (d) applystamp shows a destination whose soidA/soidB = the fork's session
      identity while the gate still refuses -> the blob was stamped into a
      record the gate does not walk (the p2-188b "match=1 outside the gate"
      case, now attributable by dst pointer vs walk_map's slot pointers).

## ABANDON OUTCOME (empty-mask #7)
If the walk_map line shows the six slots' bind fields ALL identical to
p2-188b's pre-binder values and no binder/cof line fires during the whole
landing, the binding happens outside these two binders - the road narrows to
the obfuscated ring's other writers (field_xref had exactly 7 write sites;
the -1 clearers are the fallback targets). No binder retries.

## EFFECT CLAIM (empty-mask #5)
Not a behavior claim. The EFFECT: the first direct observation of the
binding layer (who is bound to what, when, by which key) and the gate's
walked container, in one landing - the measurements that decide between the
binding fix and arm 2 without another value-arming boot.

## STATE READERS (empty-mask #1)
- the gate's walked slots: DIRECT = walk_map (six [+0x1C7C0] values + key).
- the binding events: DIRECT = binder1/binder2 enter (+stack args, caller
  rva) + cof_index/cof_soid ret values.
- the blob's writer: DIRECT = applystamp (src soid + dst + pre-state).
- the comparison's both sides AND caller: DIRECT = sesscmp (widened).

## FIX SURFACE: server
No behavior change this boot (instruments only). SERVER-SIDE GAP: the fix
surface is whichever wire message drives the runtime binder (inside the
obfuscated ring) - this capture names it by correlating binder firings with
the fork's published message stream (joincapture/membership lines).

## WIDE NET
joincapture / stage=identity / stage=join result=admit|completed /
join_relay (server) / join_type0a + pktdump / inst_nonce / walk_map /
binder1 / binder2 / cof_index / cof_soid / apply_stamp / sess_cmp / resv /
sess_state / add_candidates / bootflow / the refusal line.

## INPUT GATE (hard rule)
Do not read gate-side lines before the server's join_relay result=sent.

## OBSERVER BUDGET / CALL FREQUENCY
- walk_map/apply_stamp/cof_*: 16 each (cold paths; change/ret-gated, so a
  steady state is silent).
- binder1/binder2: 24 (bindings are rare; init may spend a few).
- sess_cmp: 64 triples (the widened gate; several consumers, each distinct
  (caller, key, blob) emits once).
- every other target: unchanged from p2-187/188b.

## HOOK COUNT: 64 (58 + 6; hook_targets declares=64 initializers=64)
## INSTRUMENT SOURCES: RE_build/Sunrise-fork-inventory/Sunrise/src/client/hooks/milestone_trace/milestone_trace_observer.cpp
## INSTRUMENT LIVENESS
the names ("walk_map", "apply_stamp", "binder1", "binder2", "cof_index",
"cof_soid", "sess_cmp") must appear in BOTH clients' attach lines.

## FALSIFIABLE CLAIM
With both links up: at least ONE stage=walk_map line AND at least ONE
binder1-or-binder2 stage=enter line appear on at least ONE machine during
the landing (the walker and the binders are on the join path / the binding
path - measured directly). REFUTED if walk_map is absent while join_type0a
fires (the gate does not walk 0x14177A0B0 in our environment -> the gate
decode itself is wrong and gets re-derived).

## ABSENCE NEGATIVES (both kinds)
- zero walk_map with join_type0a firing: the walker is not on the relayed
  join's path (outcome class (d) of p2-187) - re-derive the gate's lookup.
- zero binder/cof lines: the runtime binding never happens client-side in
  this landing - the slots are init-time only, and the binding question
  moves to "what changes [ctx+0x1C7C0] per message" (the -1 clearer sites).

## GRAPHICS DELTA (U12)
Expected new rendered models: 0 (read-only instruments).

## SETUP
  1. Server UNCHANGED (4b94d56a063c9534 running; relay_join_target_identity
     false; claims cleared).
  2. Clients deployed BOTH (the 64-target build; preflight --record after).
  3. rig ssh control socket up.
  4. Both clients land; NO in-game actions.

## ADVERSARIAL PASS
- All six new RVAs are pdata-backed function STARTS (verified 0 bad); the
  helpers they call from the probe (safe_read only) are the proven pattern.
- walk_map dereferences SIX slot pointers per firing - all reads gated on
  the 0x10000/alignment guard; a fault returns, never crashes.
- The stackargs probe is the proven shape (the p2-147a consumer pattern).
- sess_cmp's widened gate cannot flood: 64 triples cap, and a repeated
  triple by the SAME caller is silent by design (documented).
- The instrument literals are new strings in the deployed DLL - preflight
  checks them post-deploy.

## DO NOT
  - do not read gate-side lines before join_relay result=sent (input gate)
  - do not flip relay_join_target_identity (one contract per boot)
  - do not modify the client beyond the declared instruments
  - do not launch the server from anywhere but the repo root
  - NO SLEEP in shell chains (background + notify)

## CHAIN MARKS (L16)
  L1-L7 as banked (p2-180..184: landing, transition, identity, candidates,
       OOB delivery, nonce gate)
  L8 the session lookup matches             unknown - measured DEEPER this boot
       (the walk map + the binders + the widened compare: verified-by-execution
       once the lines land; assumed until then)
  L9 the ladder climbs to (4,5)             unknown
  L10 guard/receiver/codec/entity/render    unknown
