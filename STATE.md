# STATE - living snapshot

STATUS: live (2026-09-01). Verdict + deployed + next + reading order only.
FINDINGS holds the dated entry stack; front detail lives in FRONT_*.md and the
HANDOFF; operational facts live in ENVIRONMENTS.md.

Updated: 2026-09-03 2x:xx PDT. *** 20.276 (static, verified; callers.py added): the
reservation record EMBEDS a real connection object at rec+0xA8 (idx=(obj-table-0xA8)/
0x41F0, proven in 3 reservation-core fns). The ladder's .text writers are FULLY mapped:
setter 0x1416D82A0 states 0-4 + connected-rung 0x1416BCFC0 state 5 (20.273's "no
writers" was a base-alias artifact: writers spell the field +0x1D18 from the obj base,
not +0x1DC0 from the rec base). The connected-rung is MESSAGE-FED via registered handler
0x1417E5A10 -> pump 0x1416D4A30/0x1416D4B00/0x1416D56C0 (event type 4, subtype!=8).
The peer's record reached 4 (the advancers' events work for it) and never 5 - the
connected message is the missing input. Mask +0x3112's only writer = bit-CLEAR routine
0x1417C4810 (admit family + ent-gate region callers). NEXT: ONE boot - hooks on
0x1417E5A10 (message captures) + 0x1416BCFC0 (rung fires + caller RVA) + resv change-gate
widened to +0x3112; then cross-reference the fork's server send vocabulary.
VERDICT TRAIL (one line each; full text in FINDINGS):
  20.271-20.273: no activity type feeds the reservation subsystem - its input is the
    SESSION-JOIN layer; the reservation record IS a connection entry (ladder named by
    the binary's own strings); p2-163 named the failing check = predicate 2 (+0x30E8==4
    "established"); the state writer is behind the obfuscated family (femu-proven).
  20.255 message-driven publish lever | 20.254 write-back real (bulk SSE copy) |
  20.253 staging snapshot ctor PUBLISHES | 20.252 gate-byte writer captured live |
  20.251 cond5-gated receiver REQUIRED to render a peer. Behind them: 20.250 c4 front
  dead; 20.246 cond5 closed as a wire front; 20.245 row lifecycle by-design; 20.219
  slot supply closed. THE USER'S FRAMING GOVERNS (20.238): unmodified retail rendered
  peers on server input alone - every missing writer is gated on server input the fork
  does not send. Full narrative: FINDINGS 20.238-20.275.

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
Session/membership/identity: DONE. Slot supply CLOSED (20.219); row lifecycle
CLOSED (20.245); contactable byte DEAD (20.250); gate-byte writer FOUND
(20.252/20.254); write-back conduit MESSAGE-FED (20.255); DR watch RETIRED
(U18). Peer rendering remains the wall.

## NEXT (per 20.276 - ONE boot, then fork-side cross-reference)
  The connected rung is MESSAGE-FED: handler 0x1417E5A10 (registered; parses via
  0x1417E6140) -> 0x1417E5B20 -> pump 0x1416D4A30 -> 0x1416D4B00 -> 0x1416D56C0
  (event type 4, subtype != 8) -> connected-rung 0x1416BCFC0 -> setter(obj,5).
  The fork-session connection reached (4,5) so the message EXISTS on that wire; the
  peer's record stuck at (3,4) - the advancers (0x1417D1FC0/0x1417D4590/0x1417D3010,
  all -> state 4, identity-checked) worked for the peer, the connected message did not.
  BOOT (p2-165): hook A = 0x1417E5A10 (log parsed message head: type/len/bytes);
  hook B = 0x1416BCFC0 (log obj identity + old state + _ReturnAddress); resv probe
  change-gate widened to +0x3112. All read-only, settings-gated, verify_hook_rvas.
  PRE-NAMED OUTCOMES: (a) hook A fires for the fork session only -> the peer-connected
  message is missing from the wire entirely -> find it in the fork's server vocabulary
  (group_host.cpp / bap_peer_session.cpp) and emit it peer-addressed; (b) hook A fires
  for the peer too but hook B never follows -> the identity lookup
  (0x1417CE430/0x1417C3920) fails on the peer's identity -> the fork's published
  NetAddr/identity blob is the lever; (c) hook B fires for the peer and the record
  still stalls -> the write lands but the guard's OTHER predicate (+0x30E8 snapshot)
  lags -> chase the snapshot writer. (d) hook A silent for both -> the pump arm
  (type 4) is not the only connected path -> fall back to iterator hook 0x1417C53B0.
  DO NOT: hook the notifier 0x1417FFA20; resume the slot-blob suspect (demoted 20.275);
  write any client code beyond read-only observation.
  ALSO OPEN: 20.256 R4a (the router's case-12 -> 0x1416E6250 link was never walked).
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
 RETIRED 20.241 R4: static naming of the tracking-feed dispatch type - the
    dynamic discriminator is the 20.241 R5 probe (add-site caller RVA).
 RETIRED 20.234: the +0x38 writer under every covered static encoding - accessor
    family all readers; disp8/SIB/decomposed-base x participant fns = 0; 59 stride
    sites; second-.text SIB unattributable (bounded, not proven).
 RETIRED 20.220: slot SUPPLY as the blocker (loop stops at its GATES; two real
    allocators, different jobs).
 *** RE-OPENED 2026-09-02 (postmortem THE-WRONG-QUESTION) *** 20.219: the entity front
    was closed on a SUB-QUESTION. Genuinely dead: slot supply as SCARCITY (~145 free),
    type-28 as the missing message, assignment-unlocks-fill, ordering/race. What its own
    RESULT 4 measured and nobody acted on: "the client NEVER ASKS. Creation is not
    reached." What 20.219 R5 retracted WITHOUT meeting its control: 20.208 R6 (arming
    world_population -> type=7 sobject + type=52 epoch made the client ATTEMPT
    player_broadcast creation, vs ZERO in four prior runs) and 20.213 R1 (a SERVER
    setting - lease size - switched the attempt ON, firing on type-12 pushes; failure
    localised between "roster member exists" and the index request). THAT IS THE ONLY
    KNOWN SERVER-SIDE LEVER ON ENTITY CREATION, AND IT IS THE FRONT.
 UN-RETIRED 20.221: entity-replication cluster - RECEIVER candidate, see above.
 RETIRED: router-flags gate (20.218) | type-20 teardown (20.217 am2) |
    assignment VALUE semantics (20.217) | PEER CHANNEL as appearance carrier
    (pcap-refuted 20.196, 20.208 R5 - HARD FOR APPEARANCE/BULK ONLY: it never tested
    continuous POSITION/STATE, which is small and flat - the exact shape it measured.
    Do NOT extend it to "the peer channel is irrelevant to rendering". Still constrains
    20.221 reading (a)) | region A appearance fields (20.202 - correctly closed, all
    232 B decoded field-by-field on two accounts) | admission-forge (20.170) |
    road C (20.113-20.144) | staging population (20.191/2) | svc21=pool request.
    Full list: FINDINGS dead-end blocks.
 PARKED: mac black screen (Ubuntu server move is the clean test) | rx-decode |
    reason hunts | posse fabrication.

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
