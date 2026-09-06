# HANDOFF 2026-09-06 — THE SESSION-TO-CONNECTION BINDING (the lookup's live blocker)

STATUS: live (2026-09-06 late). Written for a fresh session taking over the
peer-record front. Read STATE.md first; this file banks the arc and points
forward.

## THE ONE-PARAGRAPH STATE OF THE WORLD

The join delivery chain is verified end-to-end at the mechanism level: the
fork relays each client's join container byte-verbatim on the OOB datagram
channel (p2-183), the client's connection-layer join gate RUNS (join_type0a
fires — p2-183), the gate's first check is the PROTOCOL VERSION and passes
(p2-184 — the "instance nonce" was retracted), and the identity publishing is
hash-valid at the walk-derived offset +152 (p2-186 — p2-185's +144 diverged
the hash, outcome (c) as pre-named, reverted). p2-187's instrument
(sess_cmp on the lookup's one-qword equality helper 0x141A83C00) measured
the failing comparison LIVE: the join's sessionId IS compared (10 firings,
byte-exact against the fork's own admit decode) — and the blobs compared
hold the RECEIVING MACHINE'S OWN identity (its account key, its joinId),
NOT the fork's sessionId. The game's own refusal is now greppable in our
logs: "networking:messages:join-request: received message for an unknown
session ... sending back a refusal". A session whose blob DOES hold the
sessionId exists (match=1 during the landing) — outside the gate's
ctx+0x28 container. THE BLOCKER: the session-to-connection binding.

## READ ORDER (do not skip)

1. STATE.md — the 20.318 headline + NEXT.
2. FRONT_peer-render-chain.md — THE PINNED CHART (update after every boot).
3. RE_output/claims/connection-layer-join-delivery.md — the full decode
   chain (the record, the gates, the copier walk, the blob decode, the
   lookup measurement) — every link carries this arc's evidence tokens.
4. BOOT_BRIEF_p2-187.md — the MODEL REVIEW for session-lookup-identity is
   BANKED there (the dead assumption, named).

## THE BANKED ASSETS (do not re-derive)

- THE OOB JOIN RELAY (server, settings-gated): relay_join_body forwards the
  captured join container byte-verbatim via send_transport. PROVEN p2-183+.
- THE IDENTITY FIX (server): membership field 8 (idB) = the fork's sessionId
  on every row; the state model writes it at member-entry +152. HASH-VALID
  (both joins completed). PROVEN p2-186.
- THE INSTRUMENT SET (58/58, both clients): join_type0a (pktdump),
  join_processor, admit, add_candidates, sess_state (change-gated),
  inst_nonce (retwatch), sess_cmp (novelty-gated), join_gate/join_reserve/
  join_handler/join_msg/resv probe — all live and proven.
- THE GREPPABLE VERDICT: every future boot's readout includes the game's own
  "join-request: ... unknown session ... refusal" line — the lookup's outcome
  is visible without any decoding.
- THE PINNED CHART: FRONT_peer-render-chain.md — update after every
  boot/static verdict (the user reads it to track the project).

## THE OPEN FRONT — THE SESSION-TO-CONNECTION BINDING

Measured facts (p2-187):
- The join's lookup walks the sessions bound to the receiving connection's
  context (ctx+0x28) — the walker's per-slot compare uses the one-qword
  equality helper; the join's sessionId IS the key (10 firings).
- The compared blobs hold the receiving machine's OWN identity (account key
  0xD3DABDA3AF16F99E, joinId 0xACBE7AA8CBE8B2D4) and zeros — NOT the fork's
  sessionId.
- A session whose blob holds the fork's sessionId exists (match=1 during
  the landing, t=132645+) — outside the gate's container.
- The client's own refusal: "unknown session" → transport close, silent at
  the transport level.

Next steps, in order:
1. (static) Decode the session-to-connection binding: what populates the
   ctx+0x28 container's sessions' identity blobs (+0x57C/+0x94E). The
   client's parameter-application machinery (the named parameters —
   parameter_registry.cpp holds the 25 names) is the prime suspect.
2. (server) Publish the session identity through the decoded path. The
   p2-186 publishing stays (it is model-correct; the live path is what is
   missing).
3. Any boot on this front carries the banked MODEL REVIEW (the dead
   assumption is in the p2-187 brief).

## THE RULES THIS ARC EARNED

- The "instance nonce" is the PROTOCOL VERSION check — named by measuring
  both sides (p2-184), not by static reading. Absence-of-close in the fork's
  logs is NOT evidence of no-close (the transport close is silent).
- The record = the decoded message struct, not a wire window — the "packet
  record" fields are the parsed fields, verified numerically against the
  fork's own decode.
- The descriptor copier's walk: field address = walker + entry[8] +
  entry[9](signed); advance by size (x count; count=0 LEN = skipped
  entirely in the STATIC template — the runtime counts are set at registry
  construction).
- Hook budgets by novelty/change gates only (proven three boots running).
- NO SLEEP in shell chains (the user's hard rule, this arc): background +
  notify, never blocking sleeps.

## ARTIFACTS INDEX

- Archives: RE_output/logs/20260905_220623_p2-187-sesscmp (latest),
  ..._215008_p2-186-idb152, ..._212248_p2-185-idbfix, ..._202538_p2-182-sessbase.
- Indexes: auto-named index_20260905_*.db per archive (logq/logindex are
  BROKEN — merge_timeline.py line 286 IndentationError; the user is fixing
  it; raw /usr/bin/grep -a is the standing readout).
- Claims: connection-layer-join-delivery.md (the master claim),
  adoption-condition.md, establishment-decode.md, full-walk.md.
- Ledger: RE_output/map/boot_outcomes.jsonl (p2-179..p2-187; two
  third-branches on session-lookup-identity — the review is banked).
- Decision log: D-001..D-015 (all closed; D-015 = this boot's measurement).
- Instruments: RE_build/Sunrise-fork-inventory/Sunrise/src/client/hooks/
  milestone_trace/milestone_trace_observer.cpp (58 targets).

## UNSOLVED / PARKED (do not re-chase without a new fact)

- The +0x818/+0x38 writer hunts, the creation-loop framing, the queue-event
  carrier, type-17, the SESSION-plane join delivery, Road 3's client-host
  premise, the nonce-mismatch diagnosis, idB at entry+144 — all refuted/
  retracted with evidence.
- The mac's co-presence render-black: recorded, parked.
- The image_set hang: worked around, not understood.
- The fork-tree git state: UNCOMMITTED (committing is the user's call).
- TOOLING: logq/logindex broken (the user is fixing); q.sh false-null on hex
  addresses (Tier-2 row, to log).
