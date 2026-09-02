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
input the fork does not send. Full narrative: FINDINGS 20.238-20.258.

## DEPLOYED (2026-09-02 14:2x - p2-160 attempt 3 ran and delivered; see 20.258)
   clients        BOTH: 3b4e5cfcda66df7d - pubrest with the p2-160 corrections (dump not
                  gated on role; anchor from pgate's self record; 8 records scanned;
                  baseline anchored; no stability gate; bytes= clamped) + wwatch RETIRED
                  (install emits result=retired; no VEH/DR/suspend-sweep anywhere).
                  Rollbacks: mac/rig .bak_p2d7_20260902_1426*; earlier chain 20260902_11*.
   server exe     4f51581cbd3561c7 - RUNNING, UNCHANGED through p2-160 (p2-154 deploy).
                  A build carrying membership_peer_row_flags (default 0) is STAGED, NOT
                  deployed: RE_build/staged/sunrise-server.exe.p2-161-rowflags
                  (1e7cefc6f9c4af25). 20.258 makes it low-value; do not deploy for it.
   images         p2-160 staging pair (solo + peer, complete, PROVENANCE.txt inside):
                  RE_output/dumps/p2-160_staging_images/. THE positive reference.
   dumps          p2-146 and p2-150 (rig, verified-paired, PROVENANCE.txt inside).
   index          RE_output/logindex/p2160c.db (p2-160 attempt 3); p2150.db (p2-150).
   capture        RE_scripts/capture_gameplay_plane.sh. BOOT HYGIENE: deploy client DLLs
                  BEFORE the user boots (a running process never re-reads its image);
                  restart the server with reset_lobby_claims.sh backgrounded; logindex/logq.
                  AND: replay a probe's trigger over the PREVIOUS boot's recorded lines
                  before deploying it (p2-160 cost 3 launch cycles for want of this).

## WHERE WE ARE
Session/membership/identity: DONE. Slot supply CLOSED (20.219); row lifecycle
CLOSED (20.245); contactable byte DEAD (20.250); gate-byte writer FOUND
(20.252/20.254); write-back conduit MESSAGE-FED (20.255); DR watch RETIRED
(U18). Peer rendering remains the wall.

## NEXT (per 20.258 - ALL OFFLINE; no boot until a question needs one)
  1. RE-READ 20.251's BASIS. It says the cond5-gated receiver is REQUIRED to render
     a peer. 20.258 R6 measured the RENDERED self record at +0x38 = 0x00, bit4 clear.
     Both cannot be right as stated. Settle which before any further +0x38 work -
     this is the load-bearing question now, and it is free to answer.
  2. CHASE +0x00. In 10,944 bytes, the only structural difference between a rendering
     record and a non-rendering one is +0x00 (self 0x05, peer 0x00), and self's moved
     0x03 -> 0x05 when the peer arrived. Find its writer and its meaning. Note pgate's
     cond4 ALREADY reads this byte on the NEXT record (logged as next0=), so the
     condition set has been looking at it all along.
  3. 20.256 R4a: re-check the type-12 -> 0x1416E6250 attribution (the router's case-12
     handler link was never walked; vtable group .rdata 0x141C9F6F0-0x141C9F728).
  DO NOT RESUME: the femu type-12 byte map (20.256 R2 / 20.257) - answered by 20.258.
  LOW VALUE, DO NOT BOOT: membership_peer_row_flags - it moves bytes inside the member
     row, whose fields land in ranges 20.258 shows do not include +0x38.
 SETTINGS NOW: pool_c4_mark_push TRUE and HARMLESS (peer-only). DO NOT MARK SELF
 (20.249). DO NOT RAISE the retry cap (20.247 R8).
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
