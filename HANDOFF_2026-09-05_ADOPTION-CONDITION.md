# HANDOFF 2026-09-05 — THE RESERVATION ADOPTION FRONT (post-drumbeat: landing solved, relay tested, theory corrected)

STATUS: live (2026-09-05 ~19:0x). Written for a fresh session taking over the
peer-record front. Read STATE.md first; this file owns the arc's detail and the
next steps. Supersedes nothing — it BANKS the 2026-09-05 session and points forward.

## THE ONE-PARAGRAPH STATE OF THE WORLD

Both clients now LAND and hold the Tower with a sustained peer row (the duty-cycle
gate fixed the paired-load hang — 20.307: the client's re-landing needs a ~12-18 s
quiet window after each peer-row composition change; at body cadence it never got
one). The peer's reservation record, however, is STILL born containerless —
(3,4)/mask=0/touch=-1 in every boot — and that birthright is the precondition for
every link after it: the sweep's claim, the ladder's connected rung, the guard, the
receiver object, the codec, the entity, the render. The message-grant theory (relay
the join) was implemented, shipped, and REFUTED: the relay delivers the bytes but the
reservation handler never fires from session-plane input (calls=0, 20.310) — the
reservation plane is PER-TICK MACHINERY inside the obfuscated keyed family. The front
is now the per-tick ADOPTION CONDITION: what session state makes the machinery adopt
the peer's record into a container.

## READ ORDER (do not skip)

1. STATE.md — verdict trail, DEPLOYED, NEXT (items 1-2 are this front).
2. FINDINGS 20.302-20.310 — this arc, newest last. 20.307 (the hang mechanism),
   20.309 (the ident decode: the record's identity IS the peer's endpoint), 20.310
   (the relay refutation + the per-tick finding) are the load-bearing three.
3. RE_output/claims/establishment-decode.md — the writer map: the second state
   field's writer (0x1417C0260), the 3->4 gate (ladder==5), the state machine
   (0x1418025B4) and its three transition sites.
4. RE_output/claims/full-walk.md — the whole chain wire->render with the walls.
5. RE_output/claims/ent-receive-contract.md + payload-bodies.md +
   carrier-type-table.md — the entity-message contract (complete except the outer
   wire type; a guardian's payload = 8 raw bytes).

## THE BANKED ASSETS (do not re-derive)

- THE LANDING FIX: the duty-cycle gate (server, settings-gated
  membership_peer_duty_cycle_ms=30000). Deployed and verified (p2-180: both
  machines land, clean transitions). A global (cross-session) window is a small
  refinement, not needed yet.
- THE ENTITY CONTRACT: ent-receive-contract.md (four receive interfaces, the 0x84
  record, the header bit grammar, the MSB-first/BE-word reader) + payload-bodies.md
  (kind 2 = 8 raw bytes, femu-validated) + carrier-type-table.md (the 93-wire-byte
  router census; the "network extract" decode chain shares the entity storage).
- THE WRITER MAP: establishment-decode.md (the ladder's two write paths, the
  advancer, the state machine, the connection object's embedded fifth interface).
- THE RESV PROBE: deployed in both clients; its state dumps (s30e8/s1dc0/mask/
  touch/ident) are the front's outcome meter. The ident = the record's endpoint:
  bytes {IP(4), port(2 LE), tag(2)}.
- THE DUMP INSTRUMENT: rig-side scan scripts (_rig_vptr_scan.py /
  _rig_identity_diff.py patterns — scp a generated .py to the rig, run with the
  rig's python, mmap-scan the dump file locally on the rig). NEVER pull 7 GB dumps
  (tar corrupts 2/2). The dump freeze kills the session (2/2) — dump only where
  losing the session is acceptable.
- THE OUTCOME LEDGER: p2-179 (third-branch), p2-180 (hypothesis-survived, front
  rig-paired-landing), p2-180-secondary + p2-181 (third-branch / hypothesis-wrong,
  front receiver-conversion / peer-record-birthright).

## THE OPEN FRONT — THE PER-TICK ADOPTION CONDITION

What is known:
- The peer's record is born (when the fork's membership payload lands) with mask
  bit 5 = container-field(-1)+6: NO container owns it. The guard requires bits 6/7
  (container fields 0/1). The mask's only clean-code writer is the bit-CLEAR
  (0x1417C4810); the set is creation-time bulk work. Once disowned, never re-set.
- The identity compositions MATCH (the record's 86-byte blob and the slot's card
  agree byte-for-byte in the p2-180 dump — the 0x56-prefix and three-array copies
  are in the rig dump). The disown is not a content mismatch.
- The reservation plane is per-tick machinery: join_gate 0x14175C7C0 (13k calls,
  r9=0xF08BF267 - the keyed family), join_msg 0x1417E5A10 (the receive tick's pump,
  caller 0x16CCAAD). The reserve's real caller is 0x1417B3B90-family (r8=0xA, kind
  10, twice per machine at startup).
- The join relay (relay_peer_join) is DEPLOYED and INERT: it forwards join bodies
  correctly but nothing consumes them (the handler calls=0). Leave the code; do not
  shape it further until the adoption condition is decoded.

Next steps, in order:
1. (static) Decode the reserve's real caller: 0x1417B3B90 (480 B, pdata-exact) —
   what state drives the kind-10 reserve, and what the adoption/claim condition
   reads. The container field the disown reads ([container-shared-object]+0x850)
   has a source in this family's context.
2. (static) Decode the adoption/claim: the sweep that clears the mask (the admit
   family 0x1417AA4F0/0x1417AA610 are the RELEASE arms; the sweep that CALLS them
   reads slot-vs-record identity — the compositions match, so find WHY the claim
   still fails: ordering, a second field, or the container field).
3. (one instrumented pass, after 1-2) Frequency-class-aware hooks: change-gated
   emit (NOT fixed-N enter budgets - the p2-181 budget lesson) on the reserve's
   real caller + the sweep, plus a trace of whether the container field is ever
   non-(-1) for the peer's record.
4. Then the ladder/(4,5), the guard, the receiver vptr scan (rig-side), the entity
   message (the encoder is spec-complete; the outer wire type may fall out of the
   adoption decode), the render.

## THE RULES THIS ARC EARNED (full text in FINDINGS/ENFORCEMENT.md)

- Hook budgets by MEASURED call-frequency class; a fixed-N enter budget on a
  per-tick function burns out in seconds (p2-181 R3).
- The full-dump freeze kills the session (2/2); the tar pull corrupts (2/2) —
  rig-side generated-script scans are the standing dump instrument.
- The build tree's client source is AHEAD of the deployed client — client deploys
  are deliberate acts; preflight catches the drift (it did, p2-180).
- Re-read what produces a probe field before it enters a conclusion (the BABOON
  was my dump's freeze, not the loop's — 20.306 R1).
- The empty-manager trio is NORMAL (the landed boot has 96k of them).
- disasm_fn's "protobuf tag" annotations are a heuristic misnomer on the
  reservation/reservation-adjacent code — edx=8 is an 8-bit WIDTH, not a wire tag.
- A field's xref is only complete after its BASE ALIASES are enumerated (rec+0x30E8
  = conn+0x3040; the alias scan found the writer 20.273's census missed).

## ARTIFACTS INDEX

- Archives: RE_output/logs/20260905_183210_p2-181-relay (latest),
  ..._172534_p2-180-duty, ..._160811_p2-179-hang, 20260904_195444_p2-175
  (THE LANDED CONTROL), 20260904_220846_p2-176-runA, 20260905_112354_p2-178.
- Indexes: RE_output/logindex/p2175_{mac,rig,server}.db, p2176_runA.db, p2178.db,
  p2179.db, p2180.db, p2181.db.
- Dumps: RE_output/dumps/p2-180-transition (7.1 GB, RIG-SIDE ONLY - the local copy
  is corrupt), p2-179-hang (same). The rig file: C:\Users\rasla\dump_*.dmp.
- Scripts: RE_output/scratch/hang_census.py (the landing census),
  RE_output/scratch/dutycycle_replay.py, RE_output/map/fixtures/
  join_relay_trigger.py + rearm_ack_trigger.py (replay_trigger.py fixtures),
  RE_output/.rig_vptr_scan.py + .rig_identity_diff.py (the rig-side dump patterns).
- Claims: establishment-decode.md, full-walk.md, ent-receive-contract.md,
  carrier-type-table.md, payload-bodies.md, sobject-carrier.md (the 08-16 base),
  schema-walker-grammar.md (the reader grammar).
- Ledger: RE_output/map/boot_outcomes.jsonl; decision D-001 (closed,
  hypothesis-wrong); instruments.json (preflight --record, current).

## UNSOLVED / PARKED (do not re-chase without a new fact)

- The +0x818/+0x38 writer hunts, the creation-loop framing, the queue-event
  carrier, type-17, cap=0, transition-alone conversion, the join-relay message
  grant — all refuted/retired with evidence (STATE DEAD list).
- The mac's co-presence render-black: recorded signature, process alive, session
  held. Parked.
- The image_set hang: worked around, not understood.
- The fork's fork-tree git state: UNCOMMITTED (the relay + the duty cycle + the
  pre-existing p2-178-era edits). Committing is the user's call — the deployed
  binaries are the source of truth until then.
