# STATE - living snapshot

STATUS: live (2026-09-01). Verdict + deployed + next + reading order only.
FINDINGS holds the dated entry stack; front detail lives in FRONT_*.md and the
HANDOFF; operational facts live in ENVIRONMENTS.md.

Updated: 2026-09-02 14:4x PDT. *** 20.258 (p2-160, 3 launch cycles): THE STAGING IMAGE
WAS CAPTURED IN BOTH SHAPES (solo + peer, same src/call site, complete). TWO VERDICTS:
(1) NOTHING the type-12 peer row carries reaches +0x38 - the row writes record 1
contiguously +0x08..+0x37 and STOPS DEAD at the gate byte; 2154 differing bytes, ZERO on
any record's +0x38. The femu byte-map lane (20.256 R2/20.257) is CLOSED - do not resume.
(2) *** THE RENDERED SELF RECORD ALSO HAS +0x38 = 0x00 AND FAILS cond5. *** Self and peer
records differ in 31 of 10,944 bytes and are structurally identical; the ONLY byte set in
self and zero in the peer is +0x00 (self 0x05, peer 0x00). cond5 may not be the render
gate at all - 20.251's "cond5-gated receiver REQUIRED to render a peer" is now in tension
and must be re-read before anything is built on it.
NEXT: (a) re-read 20.251's basis; (b) chase +0x00, the one structural gap; (c) 20.256 R4a
re-check of the type-12 attribution. ALL OFFLINE - no boot until a question needs one.
POSTMORTEM: the p2-160 addendum in docs/postmortems/POSTMORTEM_2026-09-01_INSTRUMENTATION.md
(3 cycles, 2 spent on the instrument; the rule: replay a probe's trigger over the previous
boot's own recorded lines BEFORE deploying).
VERDICT TRAIL (one line each; full text in FINDINGS):
  20.255 p2-159 cancelled: rig crash + mac machine freeze -> DR watch RETIRED (3/3
    boots abnormal, LESSONS U18); pubrest retained (plain detour) and delivered the
    lever: message-driven publish (0x1416E6250) fires right after type=12
    membership_replication, image carries per-member identities; restore is
    obfuscated-direct (bypasses 0x1403CB340).
  20.254 the write-back is real: p2-158 hit geometry proves a full-table restore
    (dest=table) at landing through an obfuscated thunk; 20.246's "no writer" is
    superseded in KIND (bulk SSE copy from obfuscated code).
  20.253 the image is a staging snapshot: ctor PUBLISHES (direction corrected), gated
    by the 20.220 authority predicate; 21 consumers; manager 0x140C21FE0 flattened.
  20.252 the gate-byte writer captured live: bulk copier 0x1404DF6A0 (0xB24 x 0x80
    SSE, .pdata gap) via 0x1403CB340 / pool ctor 0x1404F77D0 (image at [rsp+0x70]).
  20.251 open question (3) answered: the cond5-gated receiver is REQUIRED to render
    a peer (replication cluster single-entry; local loop self-only by design).
Standing behind them: 20.250 c4 front dead (tracking cluster exonerated); 20.246
cond5 closed as a wire front statically (bit4 never set: 384/384 dumps + 904 live);
20.245 row lifecycle by-design; 20.242 tracking feed exists; 20.239 citizen advert
works; 20.219 slot supply closed. THE USER'S FRAMING GOVERNS (20.238): unmodified
retail rendered peers on server input alone - every missing writer is gated on server
input the fork does not send. Full narrative: FINDINGS 20.238-20.257.

## DEPLOYED (2026-09-02 11:5x - p2-159 cancelled after solo; safe build 159c0140a02fe996)
   clients        BOTH: 159c0140a02fe996 - pubrest (retained, the behavioral-boot
                  verifier) + wwatch RETIRED (install emits result=retired; no VEH/DR/
                  suspend-sweep anywhere). History: b241ecda (sweep-fix) crashed the rig
                  in Tower and froze the mac -> postmortem 09-02, LESSONS U18.
                  Rollbacks: rig .bak_p2d7_20260902_115445, mac .bak chain 20260901_233724.
   server exe     4f51581cbd3561c7 - RUNNING (p2-154 deploy, built==deployed). The
                  type-45 PEER-CONTACT push behind pool_c4_mark_push (harmless, 20.250).
                  Rollback: settings .bak_p2d8_c4mark_20260901_145236; exe+cache .bak_p2d6_*.
   dumps          p2-146 and p2-150 (rig, verified-paired, PROVENANCE.txt inside), in
                  RE_output/dumps/. p2-149 DELETED (superseded, analysis banked).
   index          RE_output/logindex/p2150.db + drift json (p2-150 evidence).
   capture        RE_scripts/capture_gameplay_plane.sh (UDP 3097/3074/3075/30976,
                  en0+en13+lo0; smoke-tested). BOOT HYGIENE: deploy client DLLs BEFORE
                  the user boots (a running process never re-reads its image); restart
                  the server with reset_lobby_claims.sh backgrounded; logindex/logq.

## WHERE WE ARE
Session/membership/identity: DONE. Slot supply CLOSED (20.219); row lifecycle
CLOSED (20.245); contactable byte DEAD (20.250); gate-byte writer FOUND
(20.252/20.254); write-back conduit MESSAGE-FED (20.255); DR watch RETIRED
(U18). Peer rendering remains the wall.

## NEXT (per 20.257 - the behavioral boot)
  1. OFFLINE (this lane): finish the femu type-12 map. (a) Resolve 20.257 R6 -
     what index does key resolver 0x1404C7BC0 walk with (rig.trace)?
     (b) Graft its entry or bypass it (0x140351D90/0x14034C290 then
     0x1404C74B0(INDEX,&stream,&id,&id,0) directly). (c) A/B probe bodies
     (scratch/femu_type12_map.py) -> the byte map; plant the 0x2AC0 record
     layout (identity +8, gate +0x38) - EITHER ANSWER at +0x38 closes a front.
  2. BEHAVIORAL BOOT (settings-gated) per 20.256 R3, but read 20.257 R2 first:
     pushes are SOLO bodies - if the gate byte is unsourced from the solo
     field set, check citizen-advert fields / the 4095 peer-row variant first.
  3. pubrest f38src verifies bit4=1 at the publish; pgate reports cond5; the
     20.223 receiver vtable group appears or the front moves. Brief follows.
 SETTINGS NOW: pool_c4_mark_push TRUE and HARMLESS (peer-only). DO NOT MARK SELF
 (20.249). DO NOT RAISE the retry cap (20.247 R8).
 TOOL DEBT: reset_lobby_claims.sh cries wolf; c4query derefs before dedupe.

## SUPERSEDED (20.221 gate-2 framing; dump pointer lives in DEPLOYED)
 Scenario-scoped, not time-scoped (20.221 R5): Tier-1 code/tables reusable until
 the GAME binary changes; Tier-2 roster/manager state only valid for THIS scenario.

## HARD RULES (earned; each cost a boot or a day)
  - RESET THE SERVER BETWEEN RUNS (reset_lobby_claims.sh, backgrounded).
  - NO .text patching; NO guessed interface ordinals. Census FIRST.
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
 RETIRED 20.219: the whole entity-index/slot-supply front (also dead: type-28 as
    the missing message, assignment-unlocks-fill, ordering/race reading).
 UN-RETIRED 20.221: entity-replication cluster - RECEIVER candidate, see above.
 RETIRED: router-flags gate (20.218) | type-20 teardown (20.217 am2) |
    assignment VALUE semantics (20.217) | PEER CHANNEL as appearance carrier
    (pcap-refuted 20.196, 20.208 R5 - HARD, still constrains 20.221 reading (a))
    | region A appearance fields (20.202) | admission-forge (20.170) |
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
