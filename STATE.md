# STATE - living snapshot

STATUS: live (2026-09-01). Verdict + deployed + next + reading order only.
FINDINGS holds the dated entry stack; front detail lives in FRONT_*.md and the
HANDOFF; operational facts live in ENVIRONMENTS.md.

Updated: 2026-09-03 2x:xx PDT. *** 20.277 (p2-164 LOG RE-READ, no boot): the peer
channel COMPLETED to connected (t=330639, "WITHOUT RELAY") - transport exonerated. The
peer's reservation record stalled at 3/4 BEFORE that and its mask cleared at t=328727,
the exact moment the fork's membership payload landed (peer row _established). Every
LOGGED ent_gate evaluation (25 of 898; emit budget) predates the peer record and bailed
predicate 2 on a non-peer record; bail-5 ret is record-independent (cannot say which
record matched). The fork composes TWO DIFFERENT identity byte-sets: the participant
slot blob (session bytes, +0x14 in the 0x2AC0 table, matches the ingress payload tail)
and the reservation record's NetAddr identity ({IP,port,flags}) - the peer's endpoint
bytes appear in only the latter. FRONT = two stacked server-side walls: W-A (slot blob
wrong format -> predicate 1 can never select the peer's record) and W-B (record stalls
3/4 + mask cleared on membership arrival -> predicate 2 would fail anyway). NEXT: pin
the guard's exact blob source from its disassembly, then read the fork's two composition
paths and diff against rec=0's known-good pair; boot only as fix verification.
VERDICT TRAIL (full text in FINDINGS):
  20.279 red-team: chain holds; required mask bit 7/6 not 5; old boot unwinnable.
  20.278 guard blob = slot+0x142, all-zero, cursor-composed. 20.277 log re-read:
  channel COMPLETED, record stalled pre-completion, mask cleared on membership arrival.
  20.276 ladder writer map (setter 0x1416D82A0 + connected-rung 0x1416BCFC0; record
  embeds connection obj at rec+0xA8). 20.271-273: reservation input = session-join
  layer; failing check = predicate 2. 20.252-255: gate-byte writer, staging publish
  lever. 20.238 USER'S FRAMING GOVERNS: every missing writer is gated on server input
  the fork does not send. Full narrative: FINDINGS 20.238-20.279.

## DEPLOYED (2026-09-02 23:5x - p2-162 W1 build deployed; boots NOT yet run)
   clients        BOTH: acb81df8478143bf - W1 + ent_pass fall-through hook (mac deployed
                  and literal-verified; rig DEPLOYED-OK acb81df8478143bf via ssh 23:58).
                  Rollbacks: *.bak_p2d7_20260902_2356* (mac) / ..._235842 (rig); earlier
                  chain 20260902_14*.
   server exe     b10c7c205b75f547 - W1 server: roster_peer_participation setting
                  (DEFAULT OFF = bit-identical body), --sensor-auth-peer-test as the
                  harness's 8th gate, PASS. RUNNING, listeners verified. Rollback:
                  *.bak_p2d6_<stamp> in RE_output/s1_accept.
   NST            --sensor-auth-peer-test: off path byte-identical to pre-change encoder
                  (frozen fixture), peer path = local key then peer key 315 bits apart,
                  +224 bits (one participation body). Frozen in-tree test, runs in wine.
   settings       PAIRED BOOT RAN (2026-09-02 ~23:5x-00:2x): state.activity.
                  roster_peer_participation=true LIVE; backup settings.json.bak_w1_20260903_000338.
                  RESULT (p2-162): EMISSION PROVEN (type-5 body 556->584 B = +28, both
                  connections); digestion clean (no reject/freeze); type-13/38 = 0;
                  ent_gate/ent_pass/ent_reg ALL 0 - THE GUARD WAS NEVER REACHED because
                  cond5 never passes without the poke (20.230). The tree's (b)/(c) split
                  is UNOBSERVABLE without the poke - the pre-named tree missed this.
                  Registration invariant HELD (memidx_alloc 8 mac / 7 rig) - no entity.
                  The 43 "failed to create 'player_broadcast'" lines = known pb_create
                  load-burst churn (p2-160 boots 41-46; solo control today 0). ARCHIVE:
                  RE_output/logs/20260903_002841_p2_162_paired (rig log unreachable).
   next boot      p2-164 (2026-09-03) WIDE-NET: notifier never fired (0/16,740);
                  peer rec=2 born WITH mask=0x0020, climbed 1/1->3/4, mask cleared to
                  0x0000 exactly at the stall. 20.274 R3(b)/R4 CORRECTED by 20.275
                  (re-read of p2164.db): predicate 1 WAS satisfiable during the climb;
                  the empty-slot-blob suspect is demoted. FRONT = 20.272 R5's
                  channel-mirror subscriber (fired connecting->established, never
                  established->connected). Builds MATCHED 540d61a2; gate_poke armed
                  (revert after); notifier_hook=true mac / absent rig (20.274 R1).
   images/dumps   p2-160 staging pair (RE_output/dumps/p2-160_staging_images/,
                  PROVENANCE.txt inside) remains the positive reference; p2-146/p2-150
                  dumps still on disk.
   index          RE_output/logindex/p2161b.db newest; new boots index to p2162*.db.

## WHERE WE ARE
Session/membership/identity DONE; slot supply, row lifecycle, contactable byte,
gate-byte writer, staging publish lever all CLOSED (mechanism in FINDINGS). Peer
rendering = the wall, now decomposed into the four-wall stack W1-W4 (see NEXT).

## NEXT (implementation spec: RE_output/claims/BOOT_IMPL_peer-rendering-walls.md)
  Four-wall stack to a rendered peer, all server-side (20.275-20.279 + red team):
   W1 identity: guard compares slot+0x142 (86 B) - all-zero, cursor-composed from a
      body field the fork never sends. Fix = emit the peer's transport identity there.
   W2 mask: guard requires bit (remote-slot+6) = 7 MAC / 6 RIG; rec2 never carried it.
   W3 record stall: peer rec stuck 3/4; predicates 2+3 demand 4/5; the final rung
      comes from the session-join flow, not the channel.
   W4 instruments: first-seen-key emit gating on the leave probes (else the
      informative bail-3 outcome is invisible - the p2-164 lesson).
  PREREQUISITES before encoder code: (i) pin the runtime bit value; (ii) full
  86-byte identities in resv lines; (iii) schema-walk the t12 identity node + exclude
  0x808086F8; (iv) hunt the +0x3112 SET path (cascade gate). Then: fork encoder
  (settings-gated, size-consistent, NST fixture) -> solo control -> ONE paired
  verification boot (poke pre-named + reverted). Outcome tree 0/L/a-e in the spec.

 SETTINGS NOW: mac client gate_poke REVERTED TO 0 (both clients, post-162b).
 pool_c4_mark_push TRUE and HARMLESS.
 DO NOT MARK SELF (20.249). DO NOT RAISE the retry cap (20.247 R8).
 TOOL DEBT: reset_lobby_claims.sh cries wolf; c4query derefs before dedupe.

## SUPERSEDED (20.221 gate-2 framing; dump pointer lives in DEPLOYED)
 Scenario-scoped, not time-scoped (20.221 R5): Tier-1 code/tables reusable until
 the GAME binary changes; Tier-2 roster/manager state only valid for THIS scenario.

## HARD RULES (earned; each cost a boot or a day)
  - RESET THE SERVER BETWEEN RUNS (reset_lobby_claims.sh, backgrounded).
  - THE CLIENT IS NEVER MODIFIED - THE SERVER MUST ACCOMPLISH EVERYTHING (user,
    2026-09-02; full statement in AGENTS.md). No .text patching AND no client-side
    writes into game data. Client writes are throwaway DIAGNOSTICS only, reverted at
    the end of the boot. NO guessed interface ordinals. Census FIRST.
  - EVERY hook RVA through verify_hook_rvas.py before a boot (it catches
    added/dropped digits - both have happened).
  - Bundle OBSERVATION freely; BEHAVIOUR only behind a settings switch.
  - CENSUS BEFORE FILTER. BUDGET OBSERVERS PER EVENT CLASS.
  - SCAN AFTER THE WRITE. PREFER LANDMARKS OVER ARITHMETIC.
  - Wire fields: raw fields keep byte order, VALUE fields are MSB-first.
  - One long-running/ssh action per shell call; it hangs AFTER succeeding.
  - Solo control boot before any two-machine run.
  - Boot-test scope is fixed at brief approval; instrument tweaks wait.

## DEAD ENDS - DO NOT RESUME (mechanism in FINDINGS)
 RETIRED: tracking-feed dispatch naming (20.241) | +0x38 writer encodings (20.234) |
    slot SUPPLY as scarcity (20.220) | router-flags gate (20.218) | type-20 teardown +
    assignment VALUE semantics (20.217) | PEER CHANNEL as appearance/bulk carrier
    (20.196/20.208 R5 - NOT for continuous position/state) | region A appearance
    fields (20.202) | admission-forge (20.170) | road C (20.113-144) | staging
    population (20.191/2) | svc21=pool request. Full list: FINDINGS dead-end blocks.
 RE-OPENED (postmortem THE-WRONG-QUESTION): 20.219 entity front - the client NEVER
    ASKS; creation not reached. The only known server-side lever on entity creation =
    20.208 R6 (world_population -> type-7 sobject + type-52 epoch) + 20.213 R1 (lease
    size setting fired the attempt on type-12 pushes). THAT IS THE FRONT after the
    walls fall. UN-RETIRED 20.221: entity-replication cluster RECEIVER candidate.
 PARKED: mac black screen | rx-decode | reason hunts | posse fabrication.

## READ FIRST (any session taking over)
  0. FINDINGS 20.238-20.257 (the verdict stack; 20.252-20.256 = the
     gate-byte writer, staging layer, type-12 lever; 20.257 = femu lane). BOOT BRIEFS
     p2-158/p2-159 carry the watch-era discipline; postmortem 09-02 (U18).
  1. AGENTS.md conditional triggers; boot work loads LESSONS pre-boot checklist
     and runs gate_boot.py on the brief.
  2. ENVIRONMENTS.md before ANY deploy/capture/settings edit (trap 18: settings
     edits are format-sensitive; RIG<->MAC transfers = tar-over-ssh, never scp).
  3. Log evidence: RE_output/logindex/p2150.db; logq.py --aligned. Captures have
     NUL bytes (grep -a); logindex/logq over grep chains.
