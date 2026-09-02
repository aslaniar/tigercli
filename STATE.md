# STATE - living snapshot

STATUS: live (2026-09-01). Verdict + deployed + next + reading order only.
FINDINGS holds the dated entry stack; front detail lives in FRONT_*.md and the
HANDOFF; operational facts live in ENVIRONMENTS.md.

Updated: 2026-09-02 15:1x PDT. *** 20.259 (p2-161): cond5 IS NOT THE RENDER GATE.
The bit was FORCED SET on the peer record (throwaway client diagnostic, reverted), all
conditions the probe tracks passed for 294 consecutive walks, and NOTHING RENDERED and
NOTHING was constructed - not one new event class. With 20.258 R6 (the RENDERED self
record has +0x38 = 0x00, bit4 clear), the +0x38 front is DEAD: ~10 boots hunted a writer
for a byte that changes nothing when set. DO NOT RESUME IT.
HONEST LIMITS (settle offline before anyone reopens the byte): pgate's ALL-PASS is OUR
model, not the game's decision; THERE IS NO cond2 IN THE PROBE (cond1/3/4/5 only, so
"all conditions pass" has always meant "all we implemented"); and the decider may read
the STAGING IMAGE, whose +0x38 stayed 0x00 - we poked the table only.
NEXT (offline, no boot): the local player RENDERS and 20.258 R6 showed its record is
structurally identical to the peer's - so the difference is NOT in the participant record.
Find what actually renders the local player, then ask what SERVER INPUT drives that path
for a second participant. Also open: 20.256 R4a (case-12 -> 0x1416E6250 never walked).
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

## NEXT (per 20.259 - ALL OFFLINE; the +0x38 front is closed)
  1. THE POSITIVE-REFERENCE METHOD, which has now produced results twice: the local
     player RENDERS and its record is structurally identical to the peer's (20.258 R6).
     The difference is therefore NOT in the participant record. Find the path that
     actually renders the LOCAL player, then ask what SERVER INPUT would drive that same
     path for a second participant. Offline, no boot.
  2. Settle 20.259's two honest limits before anyone reopens +0x38 on a hunch:
     (a) WHAT IS cond2? The probe implements cond1/3/4/5 and no cond2 exists anywhere in
         it, so every "all conditions pass" in the record has been partial.
     (b) does the construction check read the STAGING IMAGE rather than the live table?
         We poked the table only; the image's +0x38 stayed 0x00 throughout.
  3. 20.256 R4a: the router's case-12 -> 0x1416E6250 link was never walked (vtable group
     .rdata 0x141C9F6F0-0x141C9F728).
  DEAD, DO NOT RESUME: the +0x38 / cond5 writer hunt (20.259); the femu type-12 byte map
     (20.258); membership_peer_row_flags as a lever (20.258 - wrong byte ranges).
 SETTINGS NOW: mac client gate_poke REVERTED TO 0 (diagnostic retired per the governing
 constraint). pool_c4_mark_push TRUE and HARMLESS. DO NOT MARK SELF (20.249). DO NOT
 RAISE the retry cap (20.247 R8).
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
