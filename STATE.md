# STATE - living snapshot (the single source of "where we are")

Updated: 2026-08-26 ~18:10 (**BOOT #9 RESULT: THE MAC ACCEPTED THE FOREIGN PEER
ROW - acked rev 5 with zero fixups, zero type-14s, no privacy-mode.** The
delivery-gap fix worked. Remaining gap = both clients still self-host; neither
takes GUEST role toward the other's instance. Member keys proven boot-scoped.
Next: guest-role mechanism. FINDINGS 20.77.) READ THIS WHOLE HEADER before any
deploy.

>> THE PEER BOOT RAN (20.64). The client named its reason for the first time:
>> **`tried-to-join-self`** - BOTH MACHINES ARE PLAYING THE SAME ACCOUNT.
>> NEXT ACTION: give the rig a genuinely separate account. Everything downstream
>> of "is this peer foreign" is untestable until then. DISARM the peer row first:
>> `membership_sweep_pin: 5`.
>> **"Separate accounts" can no longer be treated as a settled goal** - Steam and
>> BAP sign-on separate correctly, the published activity identity does not.

READ FIRST, IN THIS ORDER (for any session taking over):
  1. AGENTS.md at this root - lessons 13-16 + THE PRE-BOOT CHECKLIST are binding.
  2. INCIDENT_2026-08-25_false-loops.md - why those lessons exist; all three traps recur.
  3. FINDINGS_2026-08-25.md entries 20.40 -> 20.62 (today's whole arc, newest first).
     20.62 supersedes 20.61 supersedes 20.59/20.60 on the schema registry. Read
     20.62 FIRST: it corrects 20.61's reading of node+0x14 and carries the
     encoder transcription.
  4. Lane deliverables: RE_output/claims/transport-relay-design.md (Lane T),
     RE_output/claims/client-steam-vtable-names.md (Lane V),
     RE_output/claims/msg12-parser-read.md (Lane M, main session).
  5. RE_output/claims/s1-accept-contract.md stays the BAP contract reference.
  6. RE_output/claims/msg12-schema-decoded.md - the type-12 schema, with
     per-link evidence marks. The ONE inference in it is flagged in the file.

OPERATIONAL FACTS:
  - Fork repo: RE_build/Sunrise-fork-inventory, branch upstream-gameplay-scoped.
    HISTORY NOTE: TWO COMMITS CLAIM p2(39) - f2d0995 (Claude, shape sweep) and
    9639aa4 (opencode, revision advance). Next number is p2(41); do not renumber.
  - Build: cd RE_build/Sunrise-fork-inventory/build && make -j8 (src/steam/** compiles
    ONLY into steam_api64.dll).
  - Deploy server: bash RE_scripts/deploy_p2d6_gameplay.sh (drops clients; gates inside;
    stages from build output and asserts deployed==built).
  - Deploy client DLL: bash RE_scripts/deploy_client_dll.sh <mac|rig> "<literals...>" -
    hash assert + literal grep IN the deployed file; never skip.
  - Logs: server RE_output/s1_accept/Sunrise/logs/sunrise.log; each client
    <game>/Sunrise/logs/sunrise.log. Grep ev=steamnet / ev=activity / peers valid /
    ev=relay stage=register.
  - Rig: ssh master ~/.ssh/cm-rig to rasla@192.168.1.136 (reopen per
    FINDINGS_2026-08-24.md:1476; needs the USER's password). Rig game dir:
    C:\Users\rasla\Downloads\destiny-preservation\dcv build\bin\x64\.
  - Identities: Mac default steamId ...861; rig authors ...862 in its Sunrise/settings.json.

## HEADLINE: BOOT #9 - THE MAC ACCEPTED THE FOREIGN PEER ROW (acked rev 5, 41 ms
## after push, ZERO fixups / type-14s / privacy-mode). THE p2(54) DELIVERY FIX
## WORKED. MEMBER KEYS PROVEN BOOT-SCOPED (mac key changed across boots; rig's
## stable that day but both are session-scoped by design). REMAINING GAP: BOTH
## CLIENTS SELF-HOST; NEITHER TAKES GUEST ROLE AGAINST THE OTHER. NEXT: guest-role
## mechanism (FINDINGS 20.77).

DEPLOYED RIGHT NOW:
  server exe   `1babdb0c18d3978e` (p2(54): peer-advertisement delivery + ws503 authority;
               seven gates rc=0)
  client DLLs  `e957951643ed987a` on BOTH machines (p2(54): region writer accepts
               two advertisements - own + peer citizen in per-session slots)
  fork         `upstream-gameplay-scoped` @ `04276f0` (p2(54)), clean
  settings     rig `state.local_account_key: 1`;
               `membership_sweep_pin: 0` (ARMED, packed_masks), cap 2
  identities   mac memberKey boot-scoped (6F52AA… this boot), acct …100100 char …101;
               rig memberKey 846C…, acct …110100 char …103
  instruments  keepalive names slot=; svc-24 logs answered soid; ws503 logs
               proposed vs answered; type-13/14 payloads logged raw;
               stage=body_capture dumps peer-bearing type-12 heads (160 B)

NEXT BOOT = re-test #5 target: the GUEST-ROLE mechanism. Both clients now
establish and accept rows; what remains is one client joining the other's
instance instead of self-hosting. Investigate: advertisement timing during
setup:matchmaking, or explicit host/guest role negotiation our flow never runs.
Instrument candidates: managed_session creation triggers, posse role selection.

TO MAKE THE PEER ROW IMPOSSIBLE AGAIN: set `membership_sweep_pin: 5` (solo).
  settings: `membership_sweep_pin: 5` (= solo, publishes NO peer row),
            `membership_peer_retry_cap: 6`, `membership_sweep: false`
  client DLLs `eb893d2b1b6d8534` on BOTH machines (unchanged all day)
  fork `upstream-gameplay-scoped` @ `aefdcd1` (p2(46)), clean

**Leave the pin at 5 until a peer row is worth sending again.** A peer row the
client refuses freezes it: six bodies was enough to hard-freeze the Mac.

### The day's three real results

 1. **The self-peer bug (20.54).** `foreign_member_identity` excluded only the
    caller's SESSION ID, and one client holds several sessions, so a client was
    served ITSELF as its fireteam member and rendered a second copy of the local
    guardian named "You". Same mistake 20.37 fixed for matchmaking. Fixed in
    p2(45) by excluding candidates sharing the caller's member key.
    **20.53's "two guardians" milestone is RETRACTED**, and every trailing-field
    verdict measured before p2(45) is VOID.
 2. **The protocol census (20.55).** 59 client message types; we dispatch 17,
    accept-with-no-work 14, and emit 6. The gap's shape is *requests we accept
    and never answer*: `request_activity_host` -> 9/10, `request_peer_reservation`
    -> grant/45, `keepalive_request` -> 17. `kAcceptedMessages`' own comment
    states the wrong assumption: "carry no work for this host ... one-way".
    AND: the client sent `release_peer_reservation` 56 ms after our first peer
    body, twice. We accept that message and discard it.
 1a. **THE PEER BOOT (20.64) MOVED THE FRONT.** Message 14's payload decodes as
    `{u64 reason BE, u64 memberKey LE}` - keys byte-exact against both identities.
    The reason indexes the client's own peer-link failure enum (image `.rdata
    0x141c9e2f8`, contiguous strings so index == order):
      the RIG said **1 = `tried-to-join-self`** about the MAC
      the MAC said **5 = `privacy-mode`** about the RIG
    And it is right to: both machines publish `acct=0x9EAA300100100100`, differing
    only in character (...0101 Mac, ...0103 rig). `acct` is the CLIENT's own claim
    from its type-23 identity, not our label. Account 1's band
    `0x9EAA30010011....` appears ONCE in the whole boot log - the startup listing.
    **It was never served to anybody.**
      Steam identity     SEPARATED (...861 / ...862)
      BAP svc-25 sign-on SEPARATED (matched=slot0 served=0 / slot1 served=1)
      activity identity  **NOT SEPARATED** - both account 0
    Open question, not yet investigated: what collapses the rig onto account 0's
    third character between "svc-25 served account 1" and "the client publishes
    its identity". Candidates: account 1's characters never provisioned into its
    own band; the rig client caching a character selection; the character list
    served to slot 1 being account 0's.
    **The trailing-field verdict is VOID for the third time** - the refusal lands
    on the peer's IDENTITY and never reaches what `peer_and_player_counts` means.
    Same trap as 20.54 in a new costume: a peer that is not genuinely foreign
    cannot test anything downstream of being foreign. DO NOT re-pin and re-run
    the sweep; it cannot produce a valid result yet.
    **Cheap build that would have caught this before a single peer body shipped:**
    `foreign_member_identity` (activity_session_lookup.cpp:130) excludes a
    candidate sharing the caller's `memberKey` and checks nothing else - it never
    compares `accountSoid`. 20.37 fixed this level for matchmaking on session id,
    p2(45) for membership on member key; the ACCOUNT is the level neither reached.

 3a. **p2(47) BOOTED AND PASSED (20.63).** `membership_ack result=ok` at
    revisions 2, 3, 4; client loaded into `city_tower_social_d2`, state=3, and
    held revision 4 for the rest of the run. No encode_fail, no hang.
    Body provenance is in the number itself: every push read `type=12 body=3882`,
    which only the new encoder produces - (30,032 + 1,024)/8 = 3,882 against
    p2(46)'s 3,874 (1,024 bits = the 128-byte citizen descriptor, present all
    run). The client acknowledged a body that demonstrably carried four fields.
    **LIMIT, stated plainly (lesson 11):** this proves the four-field body is not
    REJECTED. It does NOT prove the client READS fields [6]/[7] - they sit at the
    END, so a parser that stops early accepts both forms. And all four carried
    the value 1 by design, so no semantics were tested. Consumption only becomes
    visible with a second member, where a mask (3) and a count (2) differ.
    RESIDUAL, unexplained and recorded: the user's FIRST launch reached the tower,
    took four bodies and acknowledged NONE before being quit; the second acked
    three times. Read as a quit (every line stops on one tick, then 122 s of
    silence and fresh svc-25 handshakes), but `membership_ack` is one boot old and
    has no baseline. Check the next boot against it.

 3b. **THE TRANSCRIPTION LANDED, AND p2(47) SHIPPED WHAT IT FOUND (20.62).**
    `node+0x14` is the PRESENCE BITMAP size, not the wire width - 20.61 said
    otherwise and is corrected (verified across 6,709 of 6,765 nodes; the 56
    exceptions are named and none is in the roster spine). With that fixed:
      - the roster AGREES with our encoder exactly - 32 slots, and an absent
        member row costing 3 bits IS the row's 3 presence flags. The member-row
        shape was never the problem.
      - the top level declares **FOUR** presence-flagged 32-bit fields (presence
        indices 996-999). **We have always published TWO.** Lane M's field
        registry names four in that position: peer_and_player_counts,
        peer_updates, player_updates, player_seq_number - so `player_updates`
        and `player_seq_number` have never been sent at all. Lesson 17.
    p2(47) publishes all four. +64 bits: 29,968 -> 30,032; 3,746 -> 3,754 bytes.
    All four carry the historical value, which is 1 in a solo body - where mask,
    count and packed counts are the same number - so **the boot commits to no
    semantics and tests only the shape.**
    NEXT = boot ONE client on the Mac (BOOT_BRIEF_p2-47.md). Rig stays off.

 3. **The schema registry is OPEN and the type-12 schema is DECODED
    (20.57-20.61).** 20.60 extracted **31 genuine runtime packed keys** - every
    one `0x808xxxxx`, including the type-12 membership key **0x808086A8** read
    out of the membership orchestrator's own pointer chain (global 0x141FA4180).
    That part stands. **20.60's "dump-time-state wall" does NOT** - 20.61 traced
    it to three further bugs in `schema_walk.py` (sign-fill mask six bits too
    wide; no 64-bit wraparound on the adjustment subtract, which made every live
    node read as "not mapped"; and the field count read off the message's total
    bit size). Fixed, **all 31 keys resolve in the 08-15 dump**, each verified
    against the packed key the node stores at `+0x08`.
    The type-12 shape: a **fixed 32-slot** roster (0x808086A9) of **31-bit**
    member rows (0x808086AF = identity block + 28-bit block + 5-bit field), then
    a trailer 0x808086AC at bit 992 and four presence-flagged 32-bit fields.
    Full tree + evidence marks: RE_output/claims/msg12-schema-decoded.md.
    **Do not run 20.60's live-capture boot.** The dump serves this fine, the
    dump is LOCAL, and any other message type is now one command away.
    NEXT = transcribe 0x808086BC/0x808086B1 against our encoder, then resolve
    the accepted-and-dropped types 9/10/17/45 the same way.
    Registry census: **6,765 self-verifying nodes, ALL in buckets 1024-1028**;
    buckets 0-23 hold NONE (20.60's census said the opposite). The whole
    registry is enumerable offline whenever we want it.

### Method rules earned today (AGENTS.md, binding)

  - lesson 17: **nothing in a shipped protocol is optional.** An unimplemented
    type is a missing requirement, not a deferred feature.
  - the ONE-MACHINE CONTROL: boot a single client and confirm zero peers, FIRST,
    before any two-machine peer test. It is what caught the self-peer bug and it
    costs sixty seconds.
  - a null from a mechanism whose syntax already failed in this session is not
    evidence (three grep/PowerShell censuses were wrong today; each was caught
    by re-asking through a mechanism that could not fail the same way).
  - **a model fitted on N points and tested on the same N points has not been
    tested** (20.62). 20.61's reading of node+0x14 matched the four numbers it
    was derived from and was refuted by the whole-registry pass that costs one
    minute. Check a model against the population, not the sample, BEFORE it
    ships into a finding.
  - **an instrument nobody has seen fail is not an instrument** (20.62). The new
    `--membership-wire-test` gate was run against a deliberately broken encoder
    and confirmed to return rc=1 before it was trusted to pass.
  - **lesson 13 covers OFFLINE instruments too** (20.61). A Python script
    reading a static dump produced a null that got written up as a property of
    the game ("the registry instance is phase-dependent"). It was three bugs in
    the script. Give every reader an ORACLE IT CAN FAIL AGAINST before trusting
    its nulls - here, the node stores its own key at +0x08, so a resolution can
    be checked rather than merely looking plausible.

### The peer front - BUILT AND ARMED (p2(48)/p2(48b)), see BOOT_BRIEF_p2-48.md

  - The sweep now drives ALL FOUR trailing fields, and its readings are ordered
    LIKELIEST-FIRST rather than control-first: a peer row can freeze the client
    before a late reading is reached, so the historical all-masks reading (the one
    already known to freeze) sits near the END. `solo` stays last.
      0 packed_masks     0x00020002 / 3 / 3 / 1   <- PINNED for this boot
      1 count_masks      2 / 3 / 3 / 1
      2 packed_masks_seq 0x00020002 / 3 / 3 / 3
      3 count_masks_seq  2 / 3 / 3 / 3
      4 all_mask         3 / 3 / 3 / 3            (historical; it froze)
      5 solo             no peer row              (terminal positive control)
  - Gate invariant added: no peer-bearing reading may carry a ZERO in any field.
    The encoder reads a zero override as "keep the historical value", so such a
    reading would silently publish the mask it was written to replace while
    reporting its own name - a sweep step that measures the control.
  - Retry cap 6 -> 2. Two unacknowledged peer bodies withdraw the peer row
    (sticky), a solo body follows, the client should carry on. The budget is a
    guess against an unknown freeze threshold; if it freezes anyway, RECORD HOW
    MANY `peer=1` BODIES PRECEDED IT - that number is the finding.
  - Lesson 17 lead still open and UNANSWERED, but no longer unrecorded: p2(48b)
    logs the payload of BOTH `request_peer_reservation` (13) and
    `release_peer_reservation` (14). Neither has ever fired, because both need a
    peer body to exist - this boot is the first that produces one. We still do
    not ANSWER 13 with a grant/45; that is the competing explanation for the
    freeze and the next front if the counts reading fails.
    Every message type's schema is now one `schema_walk.py --tree` away.

DEAD ENDS - DO NOT RESUME:
  - MEMBER ROW SHAPE **BY BLIND SWEEP**. Six shapes swept, none informative.
    NOTE (20.61): the row no longer has to be guessed - the client's own schema
    says 32 fixed slots x 31-bit rows. Reading it off the schema is not a resume
    of the sweep; do not start another sweep.
  - TRAILING-FIELD VALUES (counts vs masks). Every verdict predates p2(45) and
    was measured against a self-peer. NOTE (20.77): foreign rows are now
    ACCEPTED (mac acked rev 5 with the peer row) - the acceptance barrier this
    entry guarded against is partially gone; treat trailing fields as testable
    against an EST-Y peer pair only after guest-role convergence lands.
  - "SYMMETRIC FIXUP-RELEASE" claims. Boot #8 disproof: rig=reason 1, mac=reason
    5, asymmetric timing (rig MEM-1 immediate, mac MEM-5 +112 s). Never average
    the two hosts' verdicts again.
  - PASSIVE SEARCH RESULTS AS THE JOIN TRIGGER; the svc-43 contents lane; the
    peer-subnet egress relaxation; the physics gates.
    NOTE (20.74): search results DO get served (served_descriptor=1 twice in
    boot #8) but no client acted - the failure is downstream of serving, not in it.

--- everything below predates 2026-08-25 evening; treat as history ---

## HEADLINE: THE CLIENT NOW APPLIES A PEER-BEARING MEMBERSHIP BODY - AND DOES
## NOTHING WITH IT. NO STEAM SURFACE FIRES, NEITHER GUARDIAN IS VISIBLE. THE
## ROW SHAPE IS ANSWERED AND CLOSED. PRIME SUSPECT: peer_and_player_counts.

Deployed: server exe `427766a2456f493a` (p2(41), five harness gates rc=0 incl. the new
`--membership-sweep-test`); client DLLs `eb893d2b1b6d8534` on both machines. Fork branch
`upstream-gameplay-scoped` @ `e8eae58`-era HEAD (see git). Opencode PAUSED during the sweep;
ready to resume - see RESUME_OPENCODE_LANE_M.md at this root.

WHAT THE SWEEP SETTLED (20.49 -> 20.51):
 - The blocker was never the row SHAPE, it was the REVISION. The client applies one update
   per revision and drops every repeat (opencode Lane M). Every earlier peer row reused an
   already-applied revision, so shape variation was never evaluated.
 - With each shape on its own revision, BOTH sessions acked a peer-bearing body - session A
   under `key_account`, session B under `key_only`. **memberKey alone is sufficient.**
 - And it changes NOTHING: zero `ev=steamnet` lines after the peer bodies, no
   `send_rendezvous` ever, and neither player saw the other at a shared spawn.

PRIME SUSPECT (inference, marked): Lane M's field registry names a separate
`peer_and_player_counts` field upstream of the two valid-masks, and notes our body does not
distinguish counts from masks. Our encoder writes `masks = 0b11` twice
(activity_replicate_membership_encoder.cpp:12,28,35-36) and no plain count. If the count
still says one member, the client parses our slot-1 row into a slot it ignores - which fits
every observation simultaneously: body parses, revision acks, peer never appears, shape
irrelevant, no connection attempted.

SECOND LEAD: the ~44-entry peer-link failure-reason enum at .rdata 0x141c9e2f8. Surfacing
which reason fires makes the client name our cause instead of us inferring it. Three
parallel registries, no direct xrefs - Lane M flagged it as a follow-up.

DEAD ENDS - DO NOT RESUME THESE:
  - MEMBER ROW SHAPE. Swept six shapes under distinct revisions; key_only and full_mirror
    behave identically because the row is not read. Answered - do not sweep it again.
  - PASSIVE SEARCH RESULTS AS THE JOIN TRIGGER. Proven twice.
  - the svc-43 search-result contents lane. Serving works; contents changes change nothing.
  - the peer-subnet egress relaxation (p2(28)). Moot - no IP in the advertisement.
  - the physics gates (physicsHostSession / serverDefaultEntity / gameplayExternalBody).

TOOLING ADDED: `--membership-sweep-test` (pure decision logic, drives a full pass, asserts
open-on-key_only / no skips / no early retire / one advance per shape). It is in the deploy
gate list and was VERIFIED TO FAIL before being trusted (`||` for `&&` -> failures=6, exit 1).

PROCESS: two agents on one checkout collided mid-boot-test (opencode deployed over a live
run; duplicate p2(39) numbers). Nothing was lost, but a boot was confounded. Only one writer
at a time on this tree, or give the other a worktree.

--- everything below predates the sweep; treat as history ---

## HEADLINE: ACKNOWLEDGEMENT IS CONTENT-GATED - THE PEER ROW ITSELF IS REFUSED,
## NOT THE REVISION NUMBER (Claude's sweep, 20.49). SIX-SHAPE SWEEP EXISTS; FOUR
## SHAPES STILL UNSHIPPED. opencode's revision-advance suspect WAS REFUTED BY
## THAT SWEEP, AND ITS 17:01 DEPLOY OVERWROTE THE SWEEP BUILD - COORDINATE
## BEFORE THE NEXT DEPLOY.

DEPLOYED RIGHT NOW: server `1b5a5a56fadec5ba` = HEAD (sweep p2(40) + opencode flip-fix);
gates rc=0. Client DLLs `eb893d2b1b6d8534` both machines. If Claude's sweep binary
`7496f5e6e9904f8b` is required instead, rebuild from commit `111ba17` (no backup kept).

ESTABLISHED BY EXECUTION TODAY (FINDINGS_2026-08-25.md):
  - identity split end to end (20.41/20.42); all three Steam surfaces instrumented,
    none initiates joins (20.44); id=1298 consumed by BOTH clients => Lane T delivery
    viable; comparator fix live - slot 1 ships carrying the peer (20.45/20.48);
    acknowledgement CONTENT-gated: full_mirror ack=0 across nine transmissions under
    ADVANCING revisions while solo acks immediately (20.49).

opencode's refuted suspect: repeat-revision drop (20.48 reading) - refuted by the sweep.
Its flip-fix stays deployed as hygiene, not as the fix.

NEXT (Claude's front): run the remaining four sweep shapes (key_only, key_account,
key_account_join, key_account_join_opaque); p2(40) fixed the anchoring bug, opens on
key_only. First shape to draw an ACK names the missing field; then mirror that shape.

LANE M ADDENDUM (~17:45, main session - msg12-parser-read.md section 6): the msg-12
parser IS the documented schema walker (INVENTORY-W1). Field layout is RUNTIME SCHEMA
DATA (0x28-byte entries through DAT_142439c70); statics cannot produce the entry bytes -
three lanes converged on that independently. Correction recorded: 0x1404c72e0 (once
mis-dismissed by this lane) is a schema-walk entry variant. Q1 route: capture the packed
type-12 schema key at 0x1404c72e0's entry during a live boot (one hook/breakpoint),
resolve the node per W1 CLAIM 1, transcribe entries per CLAIM 3 (+0x28 bits / +0x31
presence / +0x3C width), diff against our encoder's emitted sequence - the first
divergence names what peer_and_player_counts needs. Q2 ack likely falls out of the same
read (mirror walk, W1 OPEN #7).

opencode statics that stand regardless (msg12-parser-read.md): type table [12]/[23]/[38];
field registry incl peer_and_player_counts vs peer_updates/player_updates; 44-entry
peer-failure reason enum; "view signature mismatch, no replication" gate @ 0x1416eb9a2;
self-key offset 0x6C30 cluster; simulation_queue_activity_client_membership_insert anchor.

DEAD ENDS - DO NOT RESUME THESE:
  - PASSIVE SEARCH RESULTS AS THE JOIN TRIGGER. Filed twice, never acted on.
  - full_mirror AS-IS: ack=0 x9 under advancing revisions (20.49). Its isolated
    sub-shapes are the live question.
  - REVISION-ADVANCE-ONLY AS THE FIX: refuted by execution.
  - the svc-43 search-result contents lane; peer-subnet egress relaxation (p2(28));
    physics activation gates (see 20.38/20.44).


--- everything below predates the p2(38) verdict; treat as history ---

## HEADLINE (superseded): P2(37) STAGED - REASON INSTRUMENT. EXECUTED AS PLANNED.

Committed not deployed: fork @ `3c5ab39` - server build has slot-1 + wire_snapshot reason
instrument (`ev=activity stage=wire_snapshot session=N peer=0|1 reason=none_joined|
identity_missing|destination_mismatch`); client DLLs have the callback-registration-id log
(`ev=relay stage=register id=N`, p2(36)). Deployed right now: server `1cf5243e2fa1c398`
(p2(35)), client DLLs `a248109eaeeedc71` (p2(34)).

WHY THE FIRST PASS COULD NOT TEST THE CLAIM: type-12 bodies ship only while
`regionChanged || !acknowledged()` during a load burst; after both clients settled, no
membership body shipped at all, so foreign_member_identity was never consulted. The rig's
orbit trip DID rebuild its session server-side (t=905381, state=1) with still no inclusion -
ambiguous between query-failure and no-msg-12-built, which is why the reason instrument
exists now.

NEXT SEQUENCE (one deploy window, user-gated):
  1. User closes both games. I deploy: server p2(37) via script + both client DLLs
     (deploy_client_dll.sh Mac / scp+assert rig).
  2. User boots BOTH into the Tower (Mac first), then ONE orbit trip on either machine.
  3. Read: ev=relay stage=register ids (is 1298 consumed? D4); stage=wire_snapshot lines
     (did any msg-12 build post-settle?); membership_peer inclusion or reason code;
     peers-valid masks in both dumps. Every branch pre-named in FINDINGS 20.44/20.45/20.47.

LANES: Lane V LANDED (20.46). Lane T LANDED - RE_output/claims/transport-relay-design.md:
carriage = new minimal shim-owned link to the server's existing plaintext listener;
delivery = synthesize inbound via queue_callback(id=1298 = k_iSteamNetworkingCallbacks(1200)
+98, gbe_fork RecvP2PRendezvous_t, 528 B) - HARD GAP: ring payload cap is 32 B
(callback_registry.h:22, verified) and must rise >=528; addressing = authored steamId
registered per link. Binding order per lesson 2: registration-id log boot FIRST (now part
of step 2 above); blob contents + native BAP rendezvous service id stay Ghidra opens (O3/O4).

DEAD ENDS - DO NOT RESUME THESE:
  - PASSIVE SEARCH RESULTS AS THE JOIN TRIGGER. Two boots prove a served result sits filed.
  - the svc-43 search-result contents lane. Serving works; contents changes change nothing.
  - the peer-subnet egress relaxation (p2(28)). Moot.
  - the physics gates (physicsHostSession / serverDefaultEntity / gameplayExternalBody).

--- everything below predates the p2(35) deploy; treat as history ---

## HEADLINE (superseded): P2(35) DEPLOYED - PEER AS MEMBER SLOT 1. FIRST PASS
## INCONCLUSIVE (see 20.47).

Deployed: server exe `1cf5243e2fa1c398` (p2(35), four harness gates rc=0, 30976 bound);
client DLLs UNCHANGED `a248109eaeeedc71` on both machines (server-only change - no DLL
push needed). Fork branch `upstream-gameplay-scoped` @ `cae9ca9`. Identity: Mac default
(...861), rig authored ...862. Rig ssh master at ~/.ssh/cm-rig (rasla@192.168.1.136;
reopen per FINDINGS_2026-08-24.md:1476 - needs user password).

THE CHANGE: state query foreign_member_identity() (same destination, joined, identity
published); wire slot 1 = mirrored local row shape (+673 bits; layout-derived and probed
offline across all four shapes with the solo bodies byte-exact); masks bit 1 set;
liveness lines `ev=activity stage=membership_peer result=included key=0x..` (server log)
and `stage=membership result=encode_fail` on refusal. FINDINGS_2026-08-25.md 20.45.

NEXT BOOT READS (both client logs): `peers valid: 0x3` + a `peer # 1` row = the claim
holds and the client has a peer to dial - all three Steam tables remain camera'd, so any
contact attempt gets caught on whatever surface it uses. Negatives pre-named: dumps stay
0x1 => membership is client-authored => Ghidra lane on the join path; peer row but no
contact => the row lacks dialer fields (likely platform identity).

IN FLIGHT (background lanes, zero-boot):
  - Lane T (transport design): rendezvous relay carriage/delivery/addressing ->
    RE_output/claims/transport-relay-design.md - STILL RUNNING
  - Lane V (vtable naming): LANDED, FINDINGS 20.46. Friends 3=count(0x404)/4=by-index/
    5=persona-state(1..6) = a designable enumeration triple; 43=UNKNOWN predicate (risk);
    mm27 chat entries are fixed 1040-byte blobs. Fallback trigger (fabricated one-friend
    roster naming the peer's SteamID64) is now designable if the membership boot fails.

DEAD ENDS - DO NOT RESUME THESE:
  - PASSIVE SEARCH RESULTS AS THE JOIN TRIGGER. Two boots prove a served result sits filed.
  - the svc-43 search-result contents lane. Serving works; contents changes change nothing.
  - the peer-subnet egress relaxation (p2(28)). No IP in the advertisement; moot.
  - the physics gates (physicsHostSession / serverDefaultEntity / gameplayExternalBody).
    Not on the critical path - see 20.38.

--- everything below predates the p2(35) deploy; treat as history ---

## HEADLINE: THE SEARCH RESULT ENCODES AND SHIPS (140 B, client's own schema).
## THE SOLO BOOT WAS STRUCTURALLY INCONCLUSIVE. p2(27) DEPLOYED
## (9bd8a78036a18048) - NEXT BOOT IS THE FIRST TWO-CLIENT ONE.

p2(26) boot: `kind=session_search served_descriptor=1 encoded=1 bytes=140`.
The lane's shape encodes and ships. Client stayed PRIVATE - but this boot could
not have succeeded, for two structural reasons:
 1. with ONE client the only advertised session is its own, and p2(26) served a
    SYNTHETIC self-descriptor named by nothing;
 2. setup:activity_session_creation (16) runs BEFORE setup:matchmaking (17), so
    the client already owns a session when it searches.
DO NOT read that boot as evidence against the field-3 shape.

THE BEST INSTRUMENT ON THIS FRONT, found in the client's own log:
    networking:session:membership:dump: peer # 0 ... s=_established
    peers valid: 0x1, non-dormant: 0x1; players valid: 0x1
`peers valid` is a bitmask and the state machine is exactly group_host.cpp's.
**SUCCESS = `peers valid: 0x3` with a `peer # 1` row.** Exact, client-side, and
it replaces every inferred flag we have been chasing.

p2(27) (deployed, gates rc=0, both targets clean):
 - `foreign_advertisement()` - the first cross-context read here; a searcher is
   served a session ANOTHER client published, never its own.
 - the element carries its field-6 IdPair, so the descriptor is named.
 - sizing bug caught BEFORE deploy: the IdPair reaches 164 B at a maximal
   uint64, past the 148 ceiling - which is the worst case for the FIELD-7 shape,
   not a client limit (real buffer 256 KiB). Field 3 now has its own derived
   bound of 164.

NEXT BOOT - BOTH MACHINES, and it is the first two-client test on this front:
Mac first (advertises), then the rig (searches). Read `peers valid` in BOTH
client logs.
PRE-NAMED NEGATIVES: rig sees served_descriptor=0 => the Mac's advertisement is
not reaching State (server-side lookup bug, cheap). served_descriptor=1 but both
rosters stay 0x1 => delivered, named, still not actionable; the omitted element
fields (2,3,5,7) become the suspects - bounded, not a new front.

## HEADLINE: THE LANE CRACKED svc-43 FIELD 3 AND WE NOW ANSWER THE SESSION
## SEARCH WITH A REAL RESULT (p2(26) 91157a0, DEPLOYED 03660b61d53fbddd).
## BOOT IT - THIS IS THE FIRST BOOT THAT CAN PLACE A CLIENT IN OUR INSTANCE.

THE LANE SUCCEEDED, and it vindicated the do-not-guess rule exactly: the
client's matchmaking parser is DATA-DRIVEN, its field tables were read straight
out of .rdata, and field 3 turns out to be a CONTAINER, not a bare repeated
field - the symmetry guess we refused to ship was wrong by one nesting level.

    3: SearchResults { 1: repeated SearchResult { 1: DescriptorWrapper {
                                                    1: bytes[128] } } }

Calibrated against TWO independent wire-proven chains (svc-43 f7 locate,
svc-42 advertisementUpdate). The DescriptorWrapper table 0x141C38BE0 is the SAME
one both of those already use, so the innermost two levels are proven by
production paths. NOT virtualised - no .vmp0 on this surface.
Full evidence: RE_output/claims/lane-svc43-field3.md.

p2(26): sessionSearch now emits one real result whose descriptor is built by
`gameplay::descriptor::build` pointing at THIS server's gameplay endpoint - the
same constructor the citizen advertisement uses, whose output p2(24) already
proved builds and ships. No bound endpoint or no identity falls back to the old
empty-but-present body, which is the correct "no sessions" answer.

DEPLOYED: exe 03660b61d53fbddd, four harness gates rc=0, both targets clean,
backups *.bak_p2d6_20260825_101937, endpoint bound on 30976.

THE BOOT - MAC ALONE FIRST. The matchmaking instrument now runs AFTER the encode:
    ev=matchmaking stage=request kind=session_search served_descriptor=1
                   encoded=1 bytes=<N>
served_descriptor=1 and encoded=1 mean we built and shipped a result; bytes must
be <= 148 (kMaximumResponseBodySize). Then watch the CLIENT for
`activity_host_changed` leaving `instance=PRIVATE CURRENT`, ah-sid filling, and
`public AH instance ready`.
PRE-NAMED NEGATIVES: encoded=0 => our own sizing is wrong, read bytes= and fix
locally, no RE needed. encoded=1 but the client still PRIVATE => the shape is
right but something else in the element is required (the schema defines fields
2,3,5,6,7 we deliberately omit); that is a bounded next step, not a new front.
STILL ONE CLIENT - the rig only after the Mac acts on a result.

## HEADLINE: THE svc-43 FIELD-3 LANE IS OPEN AND TOOLED. ANCHORS VERIFIED,
## AND IT LANDS ON A WALL bap-dispatch.md ALREADY NAMED
## (brief: RE_output/claims/lane-svc43-field3.md).

TOOLING BUILT, COMMITTED, PARSE-CHECKED + SMOKE-RUN, and it is Mac-local -
no Ghidra, no rig, no password (the 08-23 direction-codec precedent):
  RE_scripts/pe_reader.py   PE map, VA->offset, runtime->static translation
  RE_scripts/disasm_fn.py   capstone disassembly annotating protobuf TAG bytes

THE FACT THAT UNBLOCKS ANYONE TOUCHING THIS IMAGE:
destiny2_unpacked_full.exe is a PROCESS DUMP. Headers keep the static base
0x140000000 but .data holds LIVE pointers. The dump's runtime base is
0x7FF6AF7F0000 - derived empirically, 19,990/20,000 sampled .data pointers land
inside the image with it. Without it every .data pointer reads as garbage.

ANCHORS VERIFIED THIS SESSION: registry 0x141FBF418 (svc-42 req) and
0x141FBF430 (svc-43 rsp) -> two ADJACENT 64-byte descriptor objects in .rdata
at 0x141C2E748/0x141C2E788. Layout: [0] type-id getter (mov eax,0x2a / 0x2b),
[1] class getter, [2..7] SHARED base-class helpers. So the descriptor object is
metadata only - THE DECODE IS NOT THERE.

THE WALL, pre-existing and documented: bap-dispatch.md maps request types 0..36
to per-type records at 0x141C3CB88 + k*0x60. Type 42 is not in that map - it
falls to a class-default descriptor, and that doc already calls this "the one
open question the data cannot close". Matchmaking parsing is class-default or
data-driven, not a per-type function.

NEXT, in order: (1) disassemble the shared helpers 0x140E74B30 / 0x140E74450 /
0x140E74C00 hunting a tag loop (and eax,7 / shr eax,3 / jump-on-tag);
(2) find the ENCODER instead - the client encodes svc-42 including a 128-byte
descriptor, and encoders read easier; (3) search .rdata for a field-schema
table; (4) NAMED HAZARD - several functions tail-jump into .vmp0, so if the
decode is virtualised, static analysis ends and the fallback is a live
instrument plus the client's retail log.

DO-NOT: guess the field numbers. A wrong tag parses, matches nothing, and looks
exactly like every previous negative on this front.

## HEADLINE: THE SHORTCUT IS DEAD AND MY OWN REVIEW IS PART-REFUTED. TWO
## ACTIVITY SESSIONS IS THE *CORRECT* SHAPE. THE ONE REMAINING UNKNOWN IS A
## SINGLE PROTOBUF LAYOUT (FINDINGS 20.35).

RISK SIZING KILLED SHARED-SESSION PLACEMENT. The join commit does
`heldEntitySlots = mask; memberKey = ...; membership = {}; bubbleAuthority = {}`
and `select_free` picks slots ascending from zero consulting only the server
reserve - so a second client joining one session takes the SAME slots and wipes
the first client's lease, key, membership mirror and bubble grants. The
SessionRecord models exactly ONE ActivityClient. UPSTREAM IS BYTE-IDENTICAL.
Doing it would be a data-model change on the scale of the P2 keying front.

CORRECTION, and it must not be inherited: my overnight review read 20.21's "two
activity sessions" as the defect's signature and proposed an invariant against
it. BOTH ARE WRONG. One activity session per client IS the architecture. Two
players share a WORLD, joined at the gameplay/physics layer - exactly what
p2(23)/p2(24)/p2(25) built. That work was never the wrong layer.

WHAT SURVIVES AND UNIFIES THE FRONT: the client asks `session_search` ONCE and
we answer an empty list (20.34, wire-confirmed). A search result carries a
128-byte JOIN DESCRIPTOR - and it is the SAME descriptor the citizen
advertisement carries (matchmaking kJoinDescriptorSize = 128;
gameplay kDescriptorSize = 128; replicate_membership.h includes the gameplay
header and derives its size from it). Two delivery channels, one currency: a
pointer to a gameplay host. The citizen advertisement may simply be the wrong
CHANNEL - `setup:matchmaking` is where the client actually asks.

GOOD NEWS: we need no round-trip of the client's bytes.
`gameplay::descriptor::build(JoinEndpoint, out)` already constructs this
descriptor and p2(24) proved it builds and ships.

THE ONLY UNKNOWN LEFT: the layout inside svc-43 field 3. Upstream does not
implement it either, so there is no reference. Everything else exists -
storage, descriptor builder, endpoint, group host, bind path, membership
publisher.
NEXT: Ghidra on the client's svc-43 matchmaking response parser, using the
RE_scripts PyGhidra pattern. Scoped question: "how does the client parse field
3". DO NOT GUESS THE FIELD NUMBERS - a wrong guess parses, matches nothing, and
looks exactly like today.

## HEADLINE: WE ARE ONE LAYER TOO DEEP. TWO CLIENTS NEVER SHARE AN INSTANCE
## BECAUSE MATCHMAKING RETURNS AN EMPTY SEARCH, ALWAYS. FOUR BOOTS OF
## PEER-VISIBILITY WORK SIT BELOW THE LAYER THAT IS ACTUALLY BROKEN.
## FULL ANALYSIS: RE_output/claims/architecture-review-2026-08-25.md

    matchmaking_response_encoder.cpp:46
        case RequestKind::sessionSearch:
            return encode_empty_message(kSearchResultsField, output, written);
    matchmaking_route.cpp:42-48
        sessionSearch / locateSession -> `return true;`  no State lookup, ever

THE CLIENT'S OWN STATE MACHINE SAYS SO: setup:matchmaking (17) runs BEFORE
setup:activity_host_setup (18). Placement first, then the instance's host.
Everything since 20.27 lives at 18 and 23.

THE PROOF WAS ALREADY IN OUR RECORDS: FINDINGS 20.21, logged as a milestone,
observed "Two activity sessions, both dest=city_tower_social_d2". Two clients,
one destination, TWO SEPARATE INSTANCES - the exact signature of a search that
always returns empty. We read it as a success on 08-24 at 11:1x.

WHAT IS STORED vs SERVED: advertisementUpdate IS State-backed and stores the
client's own 128-byte session descriptor (VariantRecord, 8 contexts).
sessionSearch never reads it back at all. locateSession DOES - but only from
the CALLER'S OWN context (latest_snapshot), so a client is handed back its own
advertisement. The plumbing is complete; the lookup never crosses contexts.

WHY THIS IS TRACTABLE: we do NOT have to reverse-engineer the descriptor.
Client A hands us its own bytes; we store them verbatim; serving them to client
B is a round trip. No Ghidra, no format guessing.

NEXT, cheapest first:
 0. DONE AND DEPLOYED (exe f2ceb5267e428399, gates rc=0): the matchmaking
    route now logs the REQUEST KIND, whether a descriptor was served, and the
    advertisement id - `ev=matchmaking stage=request kind=...`. THE MORNING'S
    FIRST BOOT NEEDS NO CODE CHANGE: just boot the Mac and read that line.
    Expect to see `advertisement_update` (we store it) and, decisively, whether
    `session_search` / `locate_session` are ever asked for. If the client never
    asks either, this whole model is WRONG and the next front is elsewhere.
 1. locateSession: resolve the requested advertisement id ACROSS contexts
    instead of the caller's own latest_snapshot. Everything else already
    works end to end. This is the
    "join a specific session" path, i.e. almost certainly the FIRETEAM path
    the upstream video showed.
 2. sessionSearch: iterate the 8 contexts, return descriptors that are not the
    caller's. Needs a real results-list encoder.
 3. Only then does layer 2 matter - and p2(23)/p2(24)/p2(25) become testable
    for the first time.
NEW STATE API NEEDED (the only new surface): a cross-context read. State
exposes latest_snapshot() per-context only; the storage is already one array of
8, so this is an accessor, not a redesign.

THE TRAP PATTERN, recorded because it is the real lesson: 20.28 unbound-not-
absent, 20.31 bound-to-a-stub, 20.32 timing-refuted, today wrong-layer. Three
of four are "a thing that reports success while doing nothing". Every fix was
locally correct and globally irrelevant, and each returned green.
RULE: before optimising a layer, prove the layer above it is delivering.
CONCRETE INVARIANT TO ADD: two clients in one destination must not produce two
activity sessions. /ladder already prints this; make it a check, not a note.

THE LAST FOUR COMMITS ARE KEPT AND ARE NOT WASTED - they are layer-2 work that
was premature, not wrong.

## HEADLINE: MY WINDOW THEORY IS REFUTED. THE CLIENT HOLDS THE DESCRIPTOR FOR
## 20 SECONDS, ENTERS `activity:physics_join`, WAITS 6 s, SENDS NOTHING, AND
## FALLS THROUGH TO `in_world` (FINDINGS 20.33). CONTENT IS NOW THE SUSPECT.

    client t=101930  activity_host_changed -> PRIVATE (its CURRENT instance)
           t=106919  first membership_replication = our descriptor
           t=127624  enters activity:physics_join      <- 20,705 ms later
           t=133676  enters activity:in_world          <- after 6,052 ms
    server ev=gameplay stage=receive   ZERO, every boot

So a late descriptor was never the problem: the client had ours for twenty
seconds before the state that would consume it, and still never sent a single
datagram to UDP 30976. `activity_host_changed -> PRIVATE` at join time is the
client reporting its current instance, not a decision that closes a window.

p2(25) (eager host row) IS KEPT - it removes a 5 s stall from every region
change and the gap halved, 9,975 -> 4,989 ms - but it is NOT the fix and must
not be recorded as one. 20.32's mechanism was the wrong target.

WHAT IS NOW ESTABLISHED: delivery is proven (3 advertise=ok each followed by a
type-12 push, 24 bodies counted client-side, advert=ready on 14 keepalives).
The real decision point is named: `activity:physics_join`, where the client
waits ~6 s and concludes there is nothing to join.

NEXT, cheapest first:
 1. SETTINGS ONLY, NO REBUILD: set
    server.activation.physics_host_session = true and restart. The client sits
    in a state called physics_join; our physics host is gated off. Upstream
    says the bridge "produces no wire output either way", so this may be a
    negative - but it is minutes and it targets the exact state.
 2. IF THAT CHANGES NOTHING, the front moves to the DESCRIPTOR BYTES: dump what
    middleware::gameplay::descriptor::build emits and compare against the
    client's msg-12 citizen-block parser. Ghidra work, and the honest next
    front rather than another server-side guess.

EXONERATION DIRECTIONS (rule 11): timing cleared ONLY for
"descriptor before physics_join"; delivery proven; CONTENT untested and now the
prime suspect; p2(23)'s bind path and public-membership publisher still
untested, both downstream of a descriptor never acted on.

## HEADLINE: THE HOST ROW IS NOW CLAIMED AT ACTIVITY-SESSION COMMIT, A WHOLE
## REQUEST BEFORE THE JOIN. DEPLOYED (p2(25) e3443af). BOOT - MAC ALONE.

20.32 measured the real problem: the descriptor SHIPS (p2(24) works) but ~10 s
late, and the client decides its activity host 43 ms after the join reply and
never re-evaluates. Ordering inversion, not a contract problem - the row was
claimed lazily by the first advertisement query, but the descriptor is needed IN
the frame that makes that query, and the burst is STAGED before the commit that
could fill it (encrypted_runtime.cpp:198 vs :214, by design).

p2(25): claim + fill the row when the ACTIVITY SESSION commits. That happens in
an EARLIER request than the join (activityHostManagerResponse vs
activityMessageRequest), so the join burst should now find the advertisement
already `ready`. Legal against upstream's constraint (allocation must not run
inside a staged push): the staged frame is already encoded bytes, this branch's
prepare/commit pair closed a line above, and nothing after it commits State -
verified, no commit() survives in the post-staging path. Fail-safe: if the claim
declines, the row stays lazy and behaviour is unchanged.

DEPLOYED 2026-08-25 00:56: exe 226b8659dda06c8b, four harness gates rc=0, both
targets clean, backups *.bak_p2d6_20260825_005637, endpoint bound on 30976.

THE BOOT - MAC ALONE, and the falsifiable claim is now about TIMING:
  the client's FIRST inbound activity message (the join burst) must carry a
  descriptor. Read it in the CLIENT log, not ours:
    - `activity_host_changed` stops saying `instance=PRIVATE CURRENT`
    - `ah-sid=` fills in
    - `public AH instance ready` appears
  Server side: `advertise result=ok` must appear BEFORE the join burst's push,
  and `stage=membership result=held reason=no_host_session` should NOT appear
  at the join. Then bind result=public_target, then ONE public_membership ok.
PRE-NAMED NEGATIVE: if the descriptor now rides the join burst and the client
STILL says PRIVATE, timing is exonerated and the descriptor CONTENT becomes the
question for the first time - which is a new front, not a repeat.
Still one client; the rig would confound the read.

## HEADLINE: THE ADVERTISEMENT NOW SHIPS AND IS ~10 SECONDS TOO LATE. THE
## CLIENT DECIDES ITS ACTIVITY HOST 43 ms AFTER THE JOIN REPLY, ONCE, AND
## NEVER RE-EVALUATES (FINDINGS 20.32).

p2(24) WORKED: advertise result=ok x3, delivered (type=12 push after each; 24
membership_replication counted client-side), advert=ready on 14 keepalives,
host budget 2 of 8. Step 1 of the ladder is green.

BUT THE WINDOW HAD ALREADY CLOSED:
  client t=89011 enters setup:activity_host_setup
         t=89211 first inbound activity message (the join burst)
         t=89254 activity_host_changed -> PRIVATE, blank ah-sid   DECIDES
         t=90006 leaves the setup state
         t=99229 first membership_replication carrying our descriptor
  => 9,975 ms late, and activity_host_changed fires exactly ONCE all log.

ROOT CAUSE - AN ORDERING INVERSION, not a contract problem:
the host row is claimed LAZILY by the first advertisement query, but the
descriptor is needed IN the frame that makes that query. Server-side:
held(no_host_session) -> keepalive ships without the body -> allocated 2 ms
later -> next advertise +5,011 ms (one kKeepaliveIntervalMs). The `pending`
hold is doing its job; the row simply is not ready when the join burst ships.

NEXT: make the host row ready BEFORE the join burst is staged, so the
descriptor rides the frame the client reads. transactions::commit() runs before
notification staging, and upstream's only constraint is that allocation must
not run inside a staged push - commit is not one. Bounded change.
DO NOT just shorten the keepalive: saving 5 s lands at t~94229 and the window
shut at t=90006.

STILL UNTESTED, NOT EXONERATED (rule 11): the descriptor's CONTENT, p2(23)'s
bind path, and the public membership publisher. All three sit downstream of a
descriptor the client has never consumed in a window where it mattered.

## HEADLINE: THE ADVERTISEMENT WAS BOUND TO A FAIL-CLOSED STUB SINCE f68f230.
## FIXED AND DEPLOYED (p2(24) b4ac691). BOOT AGAIN - MAC ALONE.

THE 08-25 00:34 BOOT FAILED AT STEP 1 OF 5, NOT AT THE NEW CODE:
`ev=gameplay stage=advertise result=skip reason=no_source` on every region,
where 20.28 read `result=ok`. So the client was never told a host session
exists, never sent the second join, never bound public - instance stayed
`PRIVATE CURRENT`, ah-sid blank, zero public_target binds. Everything p2(23)
built is correct and sits downstream of a message that was never sent.

CAUSE: upstream's reworked advertisement ships TWO overloads - the real one
taking a SessionBinding source, and a source-LESS stub ("TODO: no caller yet")
whose whole body clears the output and reports Skip::noSource. Our four BAP
publishers passed no source, so adopting that subtree in f68f230 silently
bound them to the stub. Valid overload => clean build, no warning, descriptor
dead for three commits. Nothing surfaced it because no boot ran in between;
20.28's advert=ready was the OLD code.

FIX (p2(24)): all four publishers pass this link's own committed record as the
source. advertisement_state releases its own generation internally; the
membership publisher releases the one build_advertisement hands out rather than
threading a generation through six call sites - the row stays claimed, only the
LRU pin is dropped, and the next advertisement re-claims it. Every retain
balanced. Recorded as a deliberate simplification, not parity with upstream.
AND THE STUBS ARE DELETED, so this mistake is now a COMPILE ERROR - the same
treatment the defaulted AccountKey got in 20.22, for the same reason.

DEPLOYED 2026-08-25: exe af9cbb1d2c4387df, four harness gates rc=0, both
targets build clean, backups *.bak_p2d6_*. Endpoint bound on 30976; 0 sessions.

NEXT BOOT - MAC ALONE AGAIN, and the ladder is unchanged:
 1. ev=gameplay stage=advertise result=ok        <- THE fix's own gate
 2. ev=activity stage=bind result=public_target
 3. ev=activity stage=public_membership result=ok appended=1
 4. client: activity_host_changed stops saying PRIVATE CURRENT, ah-sid fills,
    `public AH instance ready`
STILL ONE CLIENT - the admission path aliases two peers onto one session record
(20.29 3), so the rig would confound the read. Rig only after step 4 lands.
If step 1 is ok but step 2 never fires, the client is ignoring a descriptor it
now receives, and that is a DIFFERENT question from the last three boots.

## HEADLINE: THE DUAL-LINK MODEL IS BUILT, GATED, AND DEPLOYED. A BOOT IS NOW
## WORTH RUNNING - IT IS THE FIRST ONE THAT CAN EXERCISE NEW BEHAVIOUR
## (p2(23) 829aef5, opencode; reviewed by Claude).

DEPLOYED 2026-08-24 17:37: exe e7493386ddb6b9fd (33,032,704 B), backups
*.bak_p2d6_20260824_173700. Builds clean both targets; four harness gates rc=0
in the deploy window. settings.json carries
server.activation.activity_public_membership = true and the gameplay block
(0.0.0.0:30976). Endpoint bound: ev=gameplay stage=endpoint result=ok.

WHAT LANDED (option B from claims/upstream-strategy-2026-08-24.md - hand-ported
SHAPES, not upstream's BAP layer, whose chain closes onto our keying front):
 1. ActivityClientRole on Session (privateCurrent / publicTarget).
 2. prepare_join ACCEPTS a join naming a session this server advertised
    (host_session_for_activity + binding_matches) instead of refusing it -
    refusing is what kept every instance PRIVATE (20.28).
 3. The bind publishes the role and logs
    ev=activity stage=bind result=public_target.
 4. The public link owes exactly ONE membership body, gated, carrying the
    PRIVATE link's member table verbatim (live_region_session / join_identity /
    prepare_refresh, read-only - this link must never move the private
    session's revision). Latched on DELIVERY, not encode.
REVIEWED: gating, once-only, read-never-commit, SecureZeroMemory, and the
delivery latch are all correct; branch ordering matches upstream's.

NO BOOT HAS RUN YET. /ladder shows 0 sessions, zero public_target binds, and
the client log is stale (16:15, before the 17:37 deploy). THE BOOT IS THE NEXT
ACTION and it is the user's to launch.

SUCCESS IS NAMED BY THE CLIENT, NOT BY US: in the client log,
`activity_host_changed` must stop reading `instance=PRIVATE CURRENT`, `ah-sid=`
must stop being blank, and `public AH instance ready` should appear. Server
side expect ev=activity stage=bind result=public_target then exactly ONE
ev=activity stage=public_membership result=ok appended=1.
ONE CLIENT FIRST - the admission path still aliases two peers onto one session
record (20.29 3), so two clients would confound the result.
Pre-named negative: no second join at all => the descriptor contract is wrong,
not the binding; go back to 20.28's ladder.
Watch ev=gameplay stage=activityhost held=N (cap 8 of a 16-slot table).
Rollback: server.activation.activity_public_membership = false, no rebuild.

FOUND WHILE REVIEWING, not a blocker: `activityJoinedForeignSession` has ZERO
assignment sites tree-wide yet still guards an early return that precedes the
publicTarget branch, and is read by the roster burst/region logic. It has been
dead since fe11228 (long before this front) so it is pre-existing debt, not a
regression - but it is a live branch on a permanently-false field and should be
retired deliberately.

## HEADLINE: PEER VISIBILITY NEEDS THE **FULL** UPSTREAM INTEGRATION - THE
## SCOPED CUT DOES NOT EXIST, PROVEN BY BUILDING IT (FINDINGS 20.30).
## THE PHYSICS STACK IS IN AND GREEN; NO BOOT IS WORTH RUNNING YET.

Tried the BAP activity-layer adoption. The chain closes back onto our own P2
front, each link forced by a compiler error:
  public-membership gate -> ActivityClientRole dual-link session model
  -> transactions/ServiceOutcome variant -> membership transactional forms
  -> activity receipts -> middleware activity_message -> CACHE FORMAT v44
  (upstream's roster snapshot reads bubbleGroups/slotIndices; ours is v24)
  -> queuez ServiceOutcome (EquipmentSwap/SubclassSelection/ItemAcquisition)
     = OUR P2 KEYING FRONT.
There is no cut line between "upstream's public membership" and our queuez
work: they are the same objects. Two retreats were tried; both closed.

STATE OF THE TREE: reverted by hard reset to f68f230. Clean, BUILDS CLEAN
(exit 0, exe 33,041,408 B). That commit keeps the whole 20.29 win - physics/
replication stack, source-bound advertisement, activation gates, SessionBinding
port. integration is untouched and still runs the deployed system.
Rollback tag pre-upstream-0188841.

WHY NO BOOT: with the gates unread in our tree, a boot of f68f230 exercises no
new behaviour at all - physics host off, membership gate inert. A green boot
would prove only "no regression"; a red one would be pure cost.

NEXT, and it is a dedicated front, not an afternoon:
 1. SETTLE FIRST, cheap and blocking: can the STANDALONE server regenerate a
    build_data.bin at a new format version? Extraction lives under
    client/content/**; our server reads a prebuilt cache. A server that cannot
    rebuild its cache does not boot, so this gates the whole plan.
 2. Then the full integration in staged commits: queuez/ServiceOutcome variant
    model -> cache v44 -> ability model + state.db migration, each with its own
    harness run.
MERGE RULE ADDED (20.30): after a 3-way merge of a restructured function, diff
the RESULT against upstream's version of that function. merge-file exited clean
on arm_repushes while silently mangling it and dropping upstream's banner block.

## HEADLINE: UPSTREAM'S PHYSICS/REPLICATION STACK IS IN AND BUILDS CLEAN
## (SCOPED, commit f68f230, FINDINGS 20.29). NEXT: DEPLOY + FLIP THE
## activityPublicMembership GATE - THE ONE 20.28 NAMED.

VERIFIED FIRST (rule 1): upstream master is STILL 0188841 (2026-08-21), live
from GitHub, and master is its only branch - so today's two-player fireteam
video is NOT public upstream code. 0188841 is the newest thing adoptable.

SCOPED, NOT FULLY MERGED, and the reason is specific: a real trial merge is 63
files / 108 hunks, and it drags in upstream 7846599 moving ability picks from
the character to the subclass ITEM, which stops our persistence.cpp compiling
and forces a state.db migration. That would put a schema migration and the
peer-visibility front in one boot. Owner chose scoped; the ability-model
reconcile is now its own front.

TAKEN WHOLE (163 files, zero conflicts - our divergence in the whole gameplay
subtree was five lines): world coordinator, replication planner, interest
manager, actor store, bubble host, combat kernel, motion validator, external
entity codec, the source-bound advertisement rework, and the activation gates.
PORTED BY HAND: SessionBinding + retain/release onto our process-wide
g_activity (20.24), with the release/eviction guards that make a retain mean
anything; entity_slots lease_masks; and the group-host allocation NAMED
kLegacyAccount - upstream's unkeyed call was a COMPILE ERROR thanks to the
20.22 sweep, which has now paid for itself twice.
KEPT OURS: ability model + persistence, queuez/P2 keying, datagen, build_data,
client tree. Verified intact after adoption.

BUILDS CLEAN, exit 0. Binary 27.1 -> 33.0 MB. Provisioned hash UNCHANGED
(0xAC65559674A52DD8). Candidate: sunrise-server.exe.MERGED_candidate.
NOT harness-gated yet (gates need the server stopped - that is the deploy
window). Branch upstream-gameplay-scoped; integration untouched and still
running. Rollback tag pre-upstream-0188841.

NEXT, two steps, one variable each, and the second needs NO rebuild:
 1. deploy merged build with gates OFF -> confirm no regression.
 2. set server.activation.activity_public_membership = true -> restart -> boot.
    That gate is "Membership on a public-target link, so the client binds a
    world container to it", and 20.28's client reported
    instance=PRIVATE CURRENT with a blank ah-sid.

## HEADLINE: P2-D6 BOOT - THE GAMEPLAY PLANE IS LIVE AND CORRECT; THE CLIENT
## DECLINES IT BECAUSE ITS ACTIVITY INSTANCE IS *PRIVATE* (FINDINGS 20.28).
## THE FRONT IS NOW PUBLIC-INSTANCE MEMBERSHIP, AND UPSTREAM HAS BUILT IT.

BOOT RESULT (Mac, one client, Tower): endpoint bound on UDP 30976;
advertisement built and PUBLISHED 3x across regions 48 and 56 with
advert=0 (ready) and the type-12 membership push carrying it; host-session
budget healthy (held=2 of 8); no crash, no regression. But ZERO
stage=receive - and zero egress denials in the client log (which logs
denials at warn, and client is at info), so the client never ATTEMPTED a
datagram. Its own log says why: activity_host_changed fired ONCE at
t=94436 with instance=PRIVATE CURRENT and a BLANK ah-sid, and never again
through t=383641. A private instance has no activity host to bind, so the
citizen advertisement has nothing to attach to.
TARGET STATE IS NAMED BY THE CLIENT ITSELF: the string pool carries
'public AH instance ready' / 'public bubble' / 'public_activity_host_mismatch'.
UPSTREAM HAS THE MACHINERY AND WE DO NOT: b8ccfb9 adds the
activityPublicMembership gate ('membership on a public-target link') and
reworks the advertisement to source its host session from a
state::activity::SessionBinding whose destination the target copies -
SessionBinding does not exist in our tree, and our host session is
allocated bare with no destination.
NEXT: (1) desk-read what flips PRIVATE -> PUBLIC (may be a field we already
encode); (2) only then size the reconcile. Do NOT repeat this boot
unchanged - it is fully characterised. AND THE 2100 HASHES ARE BUBBLE HASHES, NOT ABILITY
## PLUGS (2026-08-24 ~15:4x, FINDINGS 20.27, Claude session holds the pen).

GAMEPLAY WIRING (peer-visibility front, item #1). The sizing was wrong by an
order of magnitude in our favour: every gameplay source was ALREADY compiled
into sunrise-server.exe and `server::service()` ALREADY called
`gameplay::service(now)` every 10 ms - only `gameplay::initialize()` was
missing, so the endpoint never bound and every citizen advertisement returned
Skip::notReady. Two files changed plus a settings block.
BUILT CLEAN (llvm-mingw, exit 0). Candidate staged:
RE_output/s1_accept/sunrise-server.exe.NEW_candidate sha8 d3a7bd3f477e0c40.
--print-provisioned-hash on the live settings = 0xAC65559674A52DD8 UNCHANGED
(new settings block parses; no equipment drift). Restamp dry run: imageSize
UNCHANGED, only the timestamp moves.
DEPLOYED ~16:0x: all four harness gates rc=0, exe d3a7bd3f477e0c40, cache
restamped (eqHash unchanged, checksum matches), backups
*.bak_p2d6_20260824_155954. `udp4 *.30976` is bound and the log carries
`ev=gameplay stage=endpoint result=ok mode=embedded port=30976` - the line
20.11a said did not exist in any form. AWAITING THE CLIENT BOOT: the open
question is whether the client acts on the citizen advertisement at all
(watch for `ev=gameplay stage=receive`).
HISTORICAL NOTE on the gates: all four harness flags run
after log+persistence init, so they return rc=1 while the server is live - the
DEPLOYED exe fails identically as a control, so this is environmental and not a
regression. `RE_scripts/deploy_p2d6_gameplay.sh` stops the server, runs the
gates in that window, ABORTS if any fails, then backs up, deploys, restamps,
relaunches and verifies the listeners. RUNNING IT IS THE NEXT ACTION and it
needs an approved `kill` (the classifier declined mine).
PRE-STATE FOR THE DIFF: no UDP 30976 listener (20.11a's finding, re-confirmed).
ROLLBACK IS ONE WORD: server.gameplay.topology = "disabled".

2100 (opencode's lane 1, advanced from the desk). The two client hashes are
NOT in an undecoded table: 622 = sizeof(ScenarioRecord), and both values are
scenario BUBBLE NAME HASHES at bubbleHashes slots. 0xAB28899E = 'court' (a
bubble of city_tower_social_d2 and 10 sibling Tower scenarios; hashNames
resolves the string); 0x841B4EF7 = bubbleHashes[3] of 'orbit_d2'. They name
where the players WERE. INFERRED: the 2100 parser
(web_service_runtime.cpp:240) takes payload[0..3] BE with no shape validation
and calls it a definition hash, so apply_ability_change searches plug space for
a region identifier and cannot ever match. The deployed diagnostic will confirm
the symptom, not the cause; it was left untouched. New desk tool:
RE_output/scripts/resolve_cache_hash.py (self-checking - refuses to print if
the cache model drifts). NOT ESTABLISHED: what 2100 actually is.

MANAGER KEY (opencode's lane 2, E1 partly run). E1's documented LE byte pattern
is WRONG (`00 01 00 01 00 30 aa 9e`; correct `00 01 10 00 01 30 aa 9e`) and
would have produced a false negative that skipped E2. Corrected scan, Mac leg:
344 files, every hit is our own settings.json - and the prefix has NO retail
user-data directory at all (45 files, all crash folders). So on the Mac there
is no artifact behind "retail persists an identity". RIG LEG NOT RUN (no public
key on the rig; needs an interactive password). E3 deliberately NOT implemented:
it is a second unproven variable and must not ride the gameplay boot.

## HEADLINE: 2100 MUTATE NEVER WORKED (HASH-SPACE MISMATCH) + MANAGER-KEY
## MODEL SOLVED: RETAIL PERSISTS IDENTITY, WS-503 MIRRORS IT (2026-08-24 ~15:1x,
## FINDINGS 20.26, claims/p2-managerkey-map.md).

2100: apply_ability_change scans plugSource; client hashes live in a different
identifier space (present in raw caches as LE u32 in repeating records, absent
from all extracted domains). No result=ok ever recorded. Diagnostic deployed
(backups *.bak_p2d5diag_*): unmatched hash now logs equipped list, all entries'
plug/group/kind, and whether the hash resolves as an item def. One live click
completes the mapping evidence.

MANAGER KEY: retail persists an account identity across boots client-side;
presents it in ws-503; server adopts+echoes; manager keyed from the 503
exchange (first subscribe landed 64us after it). The 10:23 hang = settings edit
moved OUR identity while retail presented ITS OWN persisted value. Fix ladder
E1-E4 in the claims doc: locate/rewrite retail's stored identity and/or make
ws-503 server-authoritative for provisioned slots; success = request, roots,
producer, and slot identity all reading ...110100 with fast sign-in.

## HEADLINE: THE DUAL-LINK PUBLIC/PRIVATE ACTIVITY MODEL IS COMPLETE,
## DEPLOYED, GATES GREEN - ONE-CLIENT BOOT P2-D7 IS THE NEXT ACT (2026-08-24
## ~17:3x, FINDINGS 20.31, commit 829aef5).

Steps 1-4 landed on upstream-gameplay-scoped: role enum, session fields, the
prepare_join branch that accepts a join naming a session we advertised, the
bind publication, and step 4 - one membership body on the public link gated on
server.activation.activity_public_membership, carrying the PRIVATE link's
member table verbatim (read-only prepare_refresh; latched on delivery).
Deployed exe e7493386ddb6b9fd via deploy_p2d6_gameplay.sh; all four harness
gates rc=0 in the window; eqHash unchanged 0xAC65559674A52DD8; UDP 30976 bound;
settings gate ON (backup settings.json.bak_p2d7_*). integration untouched.
NEXT: P2-D7 boots ONE client (Mac) into the Tower. Success = the CLIENT's own
lines: activity_host_changed off PRIVATE CURRENT, ah-sid populated, "public AH
instance ready". Server: ev=activity stage=bind result=public_target + exactly
one membership push. Pre-named negative: no second join => descriptor contract
wrong => back to 20.28's ladder. Watch stage=activityhost held=N (cap 8/16).
Rollback: restore *.bak_p2d6_* exe+cache pair, or set gameplay topology
disabled for plane-only rollback.

## EARLIER TODAY - SUPERSEDED HEADLINES (newest first, kept for the arc)

## HEADLINE: "FULL END-TO-END DIFFERENT ACCOUNT SUPPORT" IS CLOSED AND
## BOOT-PROVEN (P2-D4, 2026-08-24 ~14:3x, FINDINGS 20.25). NEXT: PEER VISIBILITY.

Both clients relogged after a server restart: Mac hunter kept its arc subclass,
rig warlock kept its void subclass - pulled from state.db, which now carries
accounts ...0100100 + ...110100 with 61 items each and all nine slot-1
subclass instances. Rig menu shows all three subclasses; rig family-4 objects
49 -> 55 (Mac parity); reader CLEAN on both legs; ensure/seed correctly silent
on the second boot. TOP OPEN ITEM: opcode-2100 ability-change mutate failures
(6x this boot, BOTH peers; apply_ability_change refuses; pre-existing but it
blocks verifying ability-PICK persistence). Then the manager-key map (ws-503
echo suspect) gates the distinct-guardian identity front. THEN peer visibility:
two guardians in ONE shared instance needs the gameplay/entity plane wired into
server_main (20.11a).


## HEADLINE: THE THREE DIFFERENT-ACCOUNT BLOCKS ARE CLOSED AND DEPLOYED. THE RIG
## IS A FULL FIRST-CLASS ACCOUNT IN THE DATABASE NOW (2026-08-24 ~14:2x, 20.24).

Commits 3e6ea14/82135be/ecd8ad6; server exe rebuilt + deployed (backups
*.bak_p2d4_20260824_141507), cache restamped ts 0x6A8CB3A7 size 0x2CFC000,
eqHash UNCHANGED 0xAC65559674A52DD8.

- MISSING SUBCLASSES ROOT CAUSE CORRECTED (supersedes 20.23's data-scope read):
  Parser::character() had no "inventory" handler - every account's built State
  carried zero storage items. Fixed (+ optional flags field, ceiling 32->64).
- PERSISTENCE: seed_from_settings seeds every provisioned slot under its
  authored band; idempotent ensure adds missing slots to existing DBs.
- ACTIVITY: sessions relocated to process-wide runtime::storage::g_activity
  (world state is not account-scoped); prepare_session names its owning slot;
  per-slot rebuilds can no longer drop live sessions. Matchmaking keeps the old
  pattern (adjacent debt).
- IDENTITY UNTOUCHED BY DESIGN: rig stays legacy band; peers share rebased
  soids. Manager-key map recorded - mapping it is the FIRST task of the
  distinct-guardian front. Do not re-band the rig before that.
- HARNESS: 17 new gates; ensure-path 499 checks exit 0; fresh-seed path seeds
  both accounts. Known debt: accounts[0] authored defs are stale-capture
  (29 fresh-env failures, predates this front).

## HEADLINE: THE KEYING FRONT IS CLOSED AND BOOT-PROVEN. WHAT BLOCKS TRUE
## MULTI-ACCOUNT IS NOW ARCHITECTURAL: THREE SUBSYSTEMS ARE SINGLE-ACCOUNT
## BY CONSTRUCTION (2026-08-24 ~12:4x, FINDINGS 20.23).
THE OWNER'S SYMPTOM ROOT-CAUSED: on the rig only the equipped subclass appears
in the menu. state.db holds **one account** - `accounts` 1 row, `characters` 3
rows, `items` 61 rows, `items bucket_id=16` 3 per character, ALL slot 0. There
are NO slot-1 rows. The rig's account lives only in memory from
settings.json accounts[1], which authors the equipped subclass and not the
spares. Data scope, not protocol. It also explains the family-4 object counts
(Mac 55/56 vs rig 49).
=> The keying sweep fixed everything that WAS a keying problem. "Full end-to-end
distinct accounts" now needs three architectural changes, not arguments:
  1. PER-PEER ACTIVITY STATE - both prepare_session overloads read
     `g_states[kLegacyAccount].activity` outright (20.22).
  2. PER-ACCOUNT PERSISTENCE - the DB schema/rows are single-account; slot 1 is
     never written or loaded, so its 801/2100 changes almost certainly do not
     survive a restart (untested).
  3. A MULTI-ACCOUNT SEED - seed_from_settings reads slot 0 only.
Then peer visibility (the gameplay plane is still absent from server_main).
ALSO: identity is still shared (ws-503 rebases slot 1 onto slot 0's soid band),
and re-banding the rig's settings alone splits the client and hangs sign-in
(20.18/20.22) - the queuez manager-key source must be mapped first.
MAC STABILITY: three crashes today (prepare_for_orbit, activity_world_transition,
Tower transition), no crash reports, no server anomaly, DLL untouched
(83345d39, Aug 23). The parked ship-render/black-screen intermittent reproduced
again and was cleared by a subclass swap - third data point, Mac-only. Consider
unparking.


## HEADLINE: TWO PROVISIONED ACCOUNTS, TWO DIFFERENT GUARDIANS, BOTH IN THE
## TOWER AT ONCE (2026-08-24 ~11:1x, FINDINGS 20.21). THREE DEFECTS OF ONE
## FAMILY CLOSED THIS SESSION.

/ladder: 4 authenticated sessions (Mac conn 1+2 slot0, rig conn 3+4 slot1).
Two activity sessions, both dest=city_tower_social_d2, players ...0101 (Mac)
and ...0103 (rig) - DIFFERENT characters, each with its own inventory band
(slot0 6000.., slot1 4100..) and its own channel keys. 435 seals, zero off-key,
ZERO invalid signatures, zero family-4 refusals, zero move_selection failures.
Reader CLEAN, exit 0. The rig's 'character:signin' took 5,188 ms and exited
cleanly - it was 82,477 ms and a timeout before the 20.20 fix.
THE ARC: 20.17 the staging reset the mirror's accountKey (second peer served
the FIRST peer's account) + refused-but-sent manifests; 20.20 the web-service
select handler called an unkeyed setter (every peer's pick moved slot zero's
selection). All three are one family: a provisioned-slot argument defaulted or
dropped, correct for slot 0 and only slot 0.
NOT ESTABLISHED: the two peers still SHARE an account soid (both activity
identities read acct=0x9EAA300100100100 - ws-503's rebase plus the unkeyed
session_soid_base()), so DISTINCT-GUARDIAN cohabitation is still untested; and
peer visibility is not wired (neither client sees the other - the gameplay
plane is still absent from server_main, 20.11a). Standing in the same named
destination is not sharing a world.
DONE SINCE (2026-08-24 ~11:4x, FINDINGS 20.22, commits c3450c4 + cdbde8c,
BUILT AND HARNESS-VERIFIED BUT **NOT YET DEPLOYED** - the running server is
still e93d08c3906b317b): all 29 defaulted `AccountKey = kLegacyAccount`
parameters DELETED, so every call site must name a slot and this defect class
is now a COMPILE ERROR. The compiler immediately found what the hand census
could not: `prepare_item_republish` was being passed `after.accountKey` in the
`bool clearedSockets` POSITION at both call sites - AccountKey is a uint8_t, so
slot 0 read false and worked by accident while slot 1 read TRUE and published
the synthetic socket-RESET frame built from the legacy account (opcode 801 and
2100, every non-legacy peer). Also fixed: prepare_subclass_selection ignoring
its own key, unkeyed prepare_ability_change, and the activity seed/roster pair
(now keyed off session.accountKey).
BIGGEST FINDING, and it resizes the next front: THE ACTIVITY PLANE IS
SINGLE-ACCOUNT BY CONSTRUCTION. Both prepare_session overloads read
`g_states[kLegacyAccount].activity` outright - one activity state shared by
every peer. The census called this an unkeyed accessor; it is not, it is a
design limitation. Per-peer activity state is what distinct-guardian
cohabitation actually requires.
NEXT: deploy + boot-test the sweep (nothing about it is boot-proven); then peer
visibility / per-peer activity state.
Census (partly superseded by 20.22): RE_output/claims/p2-defaulted-account-key-census.md.

## HEADLINE: THE BLACK SCREEN AT CHARACTER SELECT IS ROOT-CAUSED AND FIXED -
## AN UNKEYED SETTER MOVED THE OTHER PLAYER'S SELECTION (FINDINGS 20.20).
## THIRD INSTANCE OF ONE DEFECT FAMILY. DEPLOYED, BOOT UNTESTED.

`select_character()` called `state::set_selected_character(soid, changed)` with
no slot, and that parameter is DEFAULTED to kLegacyAccount - so every peer's
character pick moved SLOT ZERO's selection. The keyed `prepare_selection_move`
then read its own slot, found the selection unmoved, and refused:
`family4 stage=prepare result=fail step=move_selection` -> `queuez stage=select
result=fail` -> no Family-4 move frame -> the peer sits in 'character:signin'
until it times out, black screen with a live cursor. Invisible with one client
because slot zero IS the default; and it silently moved the MAC's selected
character while the Mac stood in the Tower. Fixed as a SWEEP (commit 8307a74,
exe e93d08c3906b317b): every unkeyed accessor on the web-service and
outcome-staging paths where the key was already in scope. Harness 480/480 with
a gate that drives the real opcode-504 handler; negative control fails.
THE WALL HAS MOVED TWICE: pre-20.17 the rig died at the cross-account serve
before ever reaching a select (0 move_selection failures in those captures);
post-20.17 it reaches select and dies there (2 failures in each of the last two
boots). 20.18's identity-split mechanism is WITHDRAWN as the cause - boot 3 ran
with no split and failed identically.
STILL UNKEYED AND DEFERRED (inert only while the peers share a rebased soid):
activity_keepalive_seed.cpp:34, activity_roster_snapshot.cpp:47,
server_http.cpp:31 sign_on(), persistence.cpp:619. Sweep them BEFORE the
distinct-guardian front, because that front is exactly what arms them.

## HEADLINE: THE ACCOUNT-KEY DEFECT IS FIXED AND WIRE-VERIFIED UNDER TWO
## CONCURRENT CLIENTS (20.17 + 20.18). THE REMAINING BLACK SCREEN AT PICK IS
## A CLIENT IDENTITY SPLIT THE RESOID CAUSES - RIG REVERTED, RESOID RE-OPENED.

P2-D1 boot, 2026-08-24 ~10:3x: `p2d1_boot_read.py` reports CLEAN, exit 0.
Every client subscribe stayed keyed to its own slot all session (Mac key=0,
rig key=1), zero family-4 refusals, and each connection's item payload stayed
pinned to its own soid band (slot0 6000.., slot1 4100..). The C4 mid-burst key
flip is gone. ATTRIBUTION: `family4_resubscribe result=adopt` never fired, so
defect 1 (the key wipe) was the whole story and defect 2 (refused-but-sent)
was latent - the policy is still correct, just not yet load-bearing.
THE BLACK SCREEN AT PICK IS SEPARATE AND I CAUSED IT: re-banding the rig's
local legacy block splits the client's own account identity (...110100) from
its queuez MANAGER key (...0100100, what every subscribe roots on and what
retail's sign-on path feeds). The game's own family-zero producer then never
emits an entry - proven by A/B against the Mac in the same boot, where the
producer emits at t=68832 and sign-in completes in 3.1 s, versus the rig
stalling 82.5 s in 'character:signin' and leaving 'unavailable'. Rig REVERTED
and verified. 20.16's "the revert kills the resoid theory" is WITHDRAWN (rule
11: that revert failed for the cross-account reason, so it never tested the
resoid's own mechanism). Do not re-apply the resoid until the manager-key
source is mapped.

Reading the queuez ladder before touching it found a second defect in the
same expression as the assigned one, and it is the one that explains the
wall: `stage_family4_snapshot` built its after-image from a SCRATCH
SessionState, so publishing it reset every field family four does not own -
including `accountKey`, which is stamped exactly once at svc-25 and never
re-stamped. The FIRST family-4 manifest a session recorded therefore
re-pointed that session at the legacy slot. Proven on ONE connection's wire
(C4, conn=3 = the slot-1 rig, 52 ms): `subscribe_in family=3 key=1` with item
soids 4100.. -> `companion family=4 recorded=1` -> `subscribe_in family=4
key=0` with item soids 6000... The rig was handed the MAC's account under its
own root. Single-client boots never saw it: slot 0 over slot 0 is a no-op.
The assigned defect (refused-but-sent) is real and also fixed, by policy: a
subscription is answered with the full-snapshot flag at the initial version,
which REPLACES the peer's store, so the mirror now ADOPTS what it delivered
(the measured family-three rule, same client-side parser). Commit e17cf3e;
harness 476/476, negative control fails exactly the six new gates.
NEXT: the dual-client boot. Nothing about this is boot-proven yet.

## PRIOR HEADLINE: SECOND PROVISIONED ACCOUNT IN THE TOWER - THE P2 TOWER
## BLOCKER WAS ONE UNKEYED SEAL SITE (FINDINGS 20.14)

The Season-of-Arrivals fork boots and plays solo end to end on the private
server, AND a second machine provisioned into slot 1 now signs on, reaches
orbit, and STANDS IN city_tower_social_d2. The Tower blocker that killed
P2-B1 was a single line: the activity-push path sealed with state::bap()'s
legacy default key instead of the peer's own channel keys - proven by the
svc-25 identity + crypto-fingerprint instruments (keyfp F0EF.. vs 2B7A.. on
the fatal frame), fixed in activity_keepalive_push.cpp:102. Identity was
never broken: both links matched slot 1 (matched=slot1 served=1). Next:
second client simultaneously (G1 two sessions / G3 cross-talk / G4 restart
persistence), then peer visibility (entity front).

The Season-of-Arrivals fork boots and plays solo end to end on the private
server (destination loads, full inventory/equipment persistence, subclass +
ability swapping, preferences publishing). Docs/community layer is DONE and
PUBLIC. 2026-08-23: a second machine (Windows gaming rig, 192.168.1.136)
connected to the Mac-hosted server (192.168.1.164), passed sign-on AND
content_check, and loaded the Tower (FINDINGS_2026-08-23.md 20.1). The fix
was ONE settings string per machine (manifest config_guid is install-
local, not portable); zero source changes. Next multiplayer gates: guest
accounts (P2), then peer visibility (entity front).

## THE DEPLOYED STACK RIGHT NOW (verified 2026-08-24 ~09:4x)

  server exe  446feb2ae6944b2e (27,178,496 B)  pid 1593, board empty
              RE_output/s1_accept/sunrise-server.exe, launched via
              mac-port/launch-server-macos.sh (GPTK wine, own prefix)
  cache       ts 0x6A8C742C size 0x02CFC000 eqHash 0xAC65559674A52DD8
              (SizeOfImage moved 0x2CFB000 -> 0x2CFC000 this build; older
               STATE/handoff lines quoting 0x2CFB000 are stale)
  instruments LIVE: stage=identity, stage=arm, stage=crypt, stage=subscribe_in
              (now the trustworthy key= column), stage=family4_refusal
              (+key=), stage=family4_resubscribe result=adopt (new).
              All marked "strip when the dual-account front closes".
  invariants  17/18 green pre + post (DETAIL_COVERAGE red = expected/inert).
              FAMILY4_MONOTONIC now accepts a drop to EXACTLY the initial
              version as the designed re-subscribe reset; any other decrease
              is still a rollback.
  admin       binds 192.168.1.164:8099 - NOT 127.0.0.1. A curl to loopback
              returns EMPTY with exit 0 and reads exactly like a dead server.
  clients     DLLs UNTOUCHED (mac 83345d39, rig 162972c7). The staging file
              also compiles into steam_api64, but BAP is answered by the
              standalone server here, so the in-process copy is off-path.
  backups     *.bak_p2d1_20260824_094250 (exe + cache)
  HAZARD      Sunrise/src/server/runtime/server_main.cpp (the
              --print-provisioned-hash flag) is IN the deployed exe and STILL
              UNCOMMITTED. Pre-existing; owner call.

## THE PRIOR DEPLOYED, WORKING STACK (verified 2026-08-22 ~23:1x)

  server exe  04a3a1caf9fdc923   RE_output/s1_accept/sunrise-server.exe
              (Lane C dashboard + /events + seq ring + bind_address,
               + collector fixes: 3 compile breaks, SO_REUSEADDR on admin
               AND https, dashboard filter, /flags bounds clamp)
  client dll  67f3d0531a543b91   Game/bin/x64/steam_api64.dll
              (Lane E protocol tape, boot-validated; item_gate uninstalled)
  cache       build_data ts=0x6A8A90A5 size=0x02C4F000 (restamped per rebuild)
              eqHash 0xA8E1DA67DFA2118F - DRIFTED from 0xE8683B305DA99CD7 by
              the 22:46 play session (LIVE state; server self-restamps @20)
  flag bank   5,255 rows curated (account 4,931 / char 5 / profile 142 /
              char_obj 177); runtime bank lengths 12,300 / 256 / 512 / 4,096
  invariants  17/17 GREEN (RE_output/scripts/check_invariants.py)
  client log  core.logging.levels.client = "info" (retail + tape visible;
              item_gate still installed -> ~114k lines/boot)
  dashboard   http://127.0.0.1:8099/  (survives client death - proven)
  PRIOR ARTIFACTS backed up as *.bak_preobs_20260822_224433

## THE OBSERVABILITY PROGRAM - ALL 5 LANES LANDED + VERIFIED (2026-08-22)

Purpose: make system state legible to the USER, not only to an AI reading
8 MB of log; and a prerequisite for multiplayer, where nobody can read races
out of a static file. All five deliverables verified by the main session
against disk, not accepted from report-backs.

  A cockpit        DONE. lane_cockpit.md. Tools: live_console.py (Mac paths,
                   item_gate suppressed), live_client/server_tail.sh,
                   retail_view.py.
  B queryable boot DONE + VERIFIED. lane_boot_record.md. boot_diff(A4,B4)
                   names EXACTLY world_population_carrier 7->8, nothing
                   spurious; boot_diff(A4,R4) CLEAN. Records in
                   RE_output/boots/.
  C dashboard      DONE + FIXED. lane_dashboard.md. Landed 3 compile breaks
                   and 2 runtime bugs (below); all fixed and verified.
  D invariants     DONE + VERIFIED. lane_invariants.md. 17/17 green live;
                   RED at 12,549 on the saturated backup with char_obj
                   correctly staying green.
  E protocol tape  DONE + VERIFIED ON THE WIRE. lane_protocol_tape.md.

THE VALIDATION BOOT (2026-08-22 ~22:46, all four gates PASSED):
- Dashboard served during the boot AND after the client was force-quit.
- 114 tape=1 rows; predicted sign-on sequence reproduced exactly
  (svc=123 queue_update on PRIMARY session=0, then svc=9 activity_message
  on FAH session=1). Every kind named, zero unknowns, max type=54 inside
  the 0..58 registry.
- CROSS-CHECK: server and client type histograms IDENTICAL
  (58 auth_sense / 23 global_activity_state / 12x10 membership_replication /
  1 each bubble_host_table, join_result, entity_slot_notification), counts
  94 == 94, sizes differ by a CONSTANT 28 bytes (len=601 <-> size=573;
  len=234 <-> size=206) = the BAP frame header the server counts and the
  client dispatcher does not. => the handbook's p46 envelope layout is now
  INDEPENDENTLY CONFIRMED AGAINST LIVE TRAFFIC.
- 352 ev=retail lines returned at client=info.
- 115,572-row two-sided record captured (closes Lane B's last open item).

## OPEN ITEMS (ranked; none block solo play)

1. ~~item_gate source fix~~ **CLOSED 23:2x**: install commented out
   (client_hook_activation.cpp, 6a63d9a treatment); DLL rebuilt + deployed
   (steam_api64 67f3d0531a543b91). Runtime confirmation = the NEXT client
   boot (expect the client log to fall from ~114k lines to ~1.2k with retail
   + tape intact). The f4dump diagnostics in family4_object_staging /
   roster_snapshot are the SAME closed-front class ("strip when the
   weapons/model front closes", 261 rows/boot) - not yet retired.
2. ~~Multiplayer M1 - remote connect~~ **DONE 2026-08-23 ~12:4x**: rig
   (192.168.1.136) signed on against the Mac server and loaded
   city_tower_social_d2; family-4 join snapshot ACTIVE on the wire. The
   blocker was NEVER TLS - the rig client answered SignOn + manifest GET
   in-process all along and died at content_check on a manifest GUID
   mismatch (guid hashes pkg mtimes -> install-local, not portable). Fix =
   per-machine config_guid from RE_output/scripts/manifest_guid_from_cache.py.
   Full chain: FINDINGS_2026-08-23.md 20.1. Next: guest accounts (P2),
   then entity front for peer visibility.
3. **Guest accounts (P2) + two-client M3**: identity/keying GREEN under two
   concurrent clients; distinct-guardian cohabitation = NEW WALL
   (2026-08-23 ~23:1x, FINDINGS 20.14/20.15).
   TOWER BLOCKER CLOSED (20.14): one line - activity-push/keepalive path
   sealed with `state::bap()`'s legacy default key instead of
   `state::bap(session.accountKey)`; fixed + wire-verified (C2: Tower loaded
   on slot-1 rig, roster ok, zero invalid signatures).
   M3 DUAL SIGN-ON (G1): Mac=slot0 / rig=slot1, distinct channel keys,
   zero off-key seals across 520 seals, zero signature failures. Rig local
   state RE-STAGED into the slot-1 soid band (...110100/01/02/03; backup
   settings.json.bak_m3g1_resoid); family-4 snapshot records under the new
   root (objects=49 recorded=1).
   NEW WALL - NOW A NAMED DEFECT (2026-08-23 ~23:3x, FINDINGS 20.15/20.16):
   when a second client signs on, the FIRST client's presence-driven
   family-4 re-subscribe carries a CHANGED manifest (55->56 objects), which
   stage_family4_snapshot refuses (replay_mismatch) while the caller still
   SENDS the frame -> client applies version N+1 content while the server
   mirror stays at N -> mirror/client desync -> downstream kicks (PONY /
   black screen / marionberry on whichever side touches the desynced state).
   subscribe_in instrument data corrects the earlier attribution: the
   refused legacy-root subscribes were the MAC's refresh, not the rig.
   The rig REVERTED settings still failed (C4), which also EXONERATES the
   resoid as the cause; rig is back on legacy band (backup
   settings.json.bak_m3g1_resoid holds the ...110 variant for later).
   QUEUEZ MIRROR-DESYNC FRONT: CODE DONE 2026-08-24 ~09:4x (FINDINGS 20.17,
   commit e17cf3e, deployed exe 446feb2a). Two defects, one expression:
   (1) the staging wiped the mirror's `accountKey` (and the family-zero
   ladder) because its candidate was scratch-built - the second peer was
   served the FIRST peer's account from its first family-4 record onward,
   proven on one connection's wire; (2) the assigned refused-but-sent desync,
   now resolved by POLICY: a subscription answer carries the full-snapshot
   flag at the initial version and REPLACES the peer's store, so the mirror
   ADOPTS the delivered manifest (the measured family-three rule; both
   families share the client-side parser). Still refuses in ONE window:
   family3Phase != normal (character change mid-flight). The unsolicited
   re-push guard in consume_deferred is untouched. Harness 476/476;
   negative control against the old staging fails exactly the six new gates
   and no others. 20.16's "the refusals are the MAC's (key=0)" is WITHDRAWN -
   key=0 was the wiped mirror. Its open questions 1/2/3 are answered in
   20.17; question 2's front=0x32D7B974 is a DEFINITION id, not a soid.
   RIG IS NOW ON THE ...110 BAND (2026-08-24 ~10:2x, done + verified from the
   rig's own parse): state.account.primary_soid = 0x9EAA300100110100 and its
   three characters ...110101/02/03, matching server slot 1; state.accounts[]
   and config_guid untouched. Rig backup settings.json.bak_p2d1_20260824_1024.
   CORRECTION: the documented backup `settings.json.bak_m3g1_resoid` does NOT
   hold the ...110 variant - it is BYTE-IDENTICAL to the legacy-band live file
   (sha AD3341439F93C2CD). It is a PRE-edit copy that the C4 revert restored;
   the ...110 variant never survived. The edit was re-done with
   RE_scripts/rig/resoid_settings.py. Rig install lives at
   C:\Users\rasla\Downloads\destiny-preservation\dcv build\bin\x64\Sunrise
   (one tree only; NOT the Desktop path the handoff implies).
   WHY IT MATTERED (20.17): ws-503 ADOPTS the client's presented
   primary_soid into that peer's slot and rebases its character soids
   (web_service_runtime.cpp:199 -> set_primary_soid). The rig is currently on
   the LEGACY band, so signing on rewrites server slot 1 onto slot 0's account
   + character soids - both slots then share identity keys with different
   inventories. That is also why the C4 companion recorded instead of hitting
   front_ne_root. Restore the rig's settings.json.bak_m3g1_resoid (the ...110
   band, = server slot 1 0x9EAA300100110100) before the distinct-guardian
   boot. Does NOT reopen the resoid-as-cause question (still cleared).
   NEXT: the dual-client boot (brief at the end of 20.17 - watch that the
   rig's subscribe_in stays key=1 all session, that family4_refusal is gone,
   and whether family4_resubscribe result=adopt ever fires). Then G3/G4 from
   orbit-parked clients, then P4 gameplay-plane wiring for cohabitation.
   Ship-render/black-screen-on-entry: INTERMITTENT, parked (two data
   points). Open questions list in 20.16.
   EVIDENCE: RE_output/boots/20260823_m3_g1r_resoid_retry/ and
   .../20260823_p2c1_identity_crypt/. Server exe lineage tonight:
   4f2685e6 -> bcd76e88 -> cc62e95a (instrumented). Backups
   *.bak_p2b2_20260823_213659.

4. **Release engineering**: adapt .github/workflows/build.yml to attach
   sunrise-server.exe per tagged release (+ checksums; NO pdb).
5. **Attribution bisect**: which saturated flag scope broke rendering (~3
   boots, zero graphics delta). Input preserved (.bak_preflagrevert, verified
   12,549 rows). Closes the 15.9 attribution gap.
6. **Entity front W1-W8** (static enemies): emission deployed, flag OFF
   (`world_population`). Prerequisite for multiplayer P4 peer visibility.
   Ladder: RE_output/claims/lane_entity_scope.md.
7. **Upstream reconcile**: fresh fetch 2026-08-23 = **45 behind, 94
   ahead** of stanuwu/Sunrise:master (upstream tip 0188841, 2026-08-21).
   21 conflict-risk commits identified incl. upstream's own opcode-801
   subclass lane (parallel invention of our swap front - do NOT blind-merge)
   and a 273-file tree-wide refactor. Full triage:
   RE_output/community/intel-sweep-2026-08-23.md.
   Policy pending; divergence intentional until then.
8. ~~/flags response-budget overflow~~ **CLOSED 23:2x**: it was an
   out-of-bounds WRITE, not just an over-read - (kResponseCapacity - used)
   underflows as size_t once snprintf's would-be length pushes `used` past
   the buffer. Now clamped with a reserved tail and a "truncated" flag.
   Verified with a 1 KiB test build against the real 4 KB response: stayed
   in bounds, stayed VALID JSON, reported truncated=true + true run_count,
   server survived.
9. **Research repo publish decision**: origin still points at tigercli.git
   (wrong project).
10. **Shader-cache persistence** (Mac QoL): no MoltenVK/DXMT cache persists;
    every launch compiles cold; new equipped models crash-prone at pick.
11. Helmet front: RESOLVED-PARKED (16.4) - control is vestigial, no consumer.
12. Parked unchanged: verb layer; vendor storefront loop (scoped 18.2);
    bucket-builder strictness; ForcedDestination wiring.

## HAZARD: THE SHARED WORKTREE IS DIRTY (lanes C and E commit into it)

RE_build/Sunrise-fork-inventory (branch `integration`) carries UNCOMMITTED
work from 2026-08-21 ~22:15 that predates this program: CMakeLists.txt,
Sunrise.vcxproj, client_hook_activation.cpp, character_record_encoder.{cpp,h},
family4_object_staging.cpp (+40), roster_snapshot.cpp (+47), and the ENTIRE
UNTRACKED src/client/hooks/item_gate/ directory. A blanket `git add -A` in
that worktree sweeps ~100 lines of unrelated S2/datagen work into an
observability commit. Lane C confirmed it commits only its own files and does
NOT touch CMakeLists (headers only). Owner decision still outstanding: is the
08-21 work still wanted, or superseded by the 18.3 MSVC line?

## WHAT IS PUBLIC VS INTERNAL

PUBLIC: github.com/aslaniar/Sunrise, master @ **c30a72d** (docs set +
SERVER-SIDE-SPEC.md rev 2026-08-22 + scripts/{launch-server-macos.sh,
server-settings.template.json, restamp_build_data.py}; the 18.3 MSVC line:
windns_compat shipped in-tree, sln builds both targets, egress signatures
aligned to the Windows SDK; CI green). d2-unlock-index-tables repo (CC0).
Knowledge dump as PDF via Discord.
INTERNAL ONLY: knowledge dump md/pdf sources + handbook digest & text
(RE_output/{community,dumps}), claims/ (380+ files), RE_scripts tooling,
RE_output runtime artifacts (never ship: game-derived caches/DBs, live
tokens, oo2core proprietary DLL).

## CORRECTIONS TO THE RECORD (supersede older text; do not re-derive)

- 20.16's "the revert failing KILLS the resoid-causes-it theory" is WITHDRAWN
  (20.18). The C4 revert failed for the CROSS-ACCOUNT reason (the key wipe,
  since fixed), so that boot never tested the resoid's own mechanism. Rule 11
  again: an exoneration is only valid in the direction it was tested.
- 20.15's "family-4 companion RECORDS under the new root" was an INFERENCE:
  the companion log line does not print a root, and the refusal lines in that
  same boot carry root=...0100100. No rig subscribe has ever carried the ...110
  root, resoid or not.

- 20.16's "every legacy-root family-4 refusal belongs to the MAC's presence
  refresh (key=0)" is WITHDRAWN (20.17): `key=` reads `before.accountKey`,
  and that field was the thing being corrupted. The refusals arrived on the
  RIG's own connection, 16 ms after its own key=1 subscribe. An instrument
  column is only as trustworthy as the field it reads.
- 20.16's `front=0x32D7B974` is a family-4 ACCOUNT-OBJECT DEFINITION ID, not
  a soid: the refusal line prints `objects.front().id`, and queuez `Object`
  is {u32 id = definition id, u64 version = soid}. It is identical on every
  family-4 snapshot. Nothing "presence/group-shaped" to hunt.
- A family-4 re-subscribe now RESETS the mirror's family-4 version to zero by
  design (the full-snapshot answer replaces the peer's store). FAMILY4_
  MONOTONIC was taught this; a drop to any OTHER value is still a rollback.

- UPSTREAM DELTA: STATE's earlier "~115 commits behind" was WRONG, and so was
  an intermediate "2 behind" read (taken from a STALE remote-tracking ref).
  Fresh fetch 2026-08-22 22:0x: **45 behind, 98 ahead**. Always fetch before
  quoting a divergence count.
- "Silencing item_gate leaves ~1-2k readable lines" is WRONG: retail is
  Level::info too, so client=warn leaves only the warn/error floor (~0-100
  lines this boot: 2 warn, 0 error). Corrected by Lane A.
- The BAP service names were NOT missing: src/middleware/bap/frame.h already
  carries RequestService/ResponseService/NotificationService enums, and Lane E
  verified they are NUMERICALLY IDENTICAL to the handbook registry (27/24/2,
  programmatic cross-check). They were simply never wired into the log line.
- handle_message_observer's `type=%u` column is the BAP SERVICE NUMBER, not
  the activity-message wire type (Lane E, verified against two incidents).
- 14.17 "flags fully exonerated" INVALID (one-directional test) - superseded
  by 15.8/15.9.
- 15.2 "silently seeded nothing" WITHDRAWN -> 15.4: server REFUSES to boot
  with state.characters present (ordering defect; publisher is client-only).
- ONE repository (RE_build/Sunrise-fork) with linked worktrees; inventory tree
  = worktree of it.
- SocketPolicy authored==nativeDefaults byte-identical on wire (15.5);
  entryList=0 on gear correct (refuted x4); no equippability flag exists in
  the family-4 object (greyed = client derivation).
- helmetMode has NO consumer in this build (16.2-16.4).
- Preferences are one-way (no write-back path); in-game changes die at boot.
- Deadorbit: local/embedded HTTP branch does NOT serve ticket_drop; external-
  mode URL rewrite intercepts it fine.
- M1 BLOCKER RECLASSIFIED (2026-08-23, supersedes the 19.x/handoff text):
  the remote-rig failure was NOT wine-TLS and NOT silent. SignOn POST and
  the manifest GET were answered IN-PROCESS all along; the kill was
  bootflow:content_check "guid mismatch", and the "15 s silent gap" was the
  cleanup state's task timeout after that kick. Evidence:
  RE_output/boots/20260823_m1_remote_rig/rig_client_log.txt lines 257-268;
  full chain in FINDINGS_2026-08-23.md 20.1.

## HARD-WON TRAPS (each cost a real failure; do not re-learn)

- A DEFAULTED PROVISIONED-SLOT ARGUMENT IS THE RECURRING HAZARD (three
  instances: a9d1cbc `state::bap()`, 20.17 the scratch-built mirror, 20.20
  `set_selected_character`). Twelve state APIs carry
  `AccountKey key = kLegacyAccount`; the default compiles silently at every
  unkeyed call site and behaves CORRECTLY for slot 0, which is the only slot a
  single-client test exercises. When touching any multi-account path, grep for
  the call sites, not the declarations.
- A GATE IS WORTHLESS UNTIL ITS NEGATIVE CONTROL RUNS (twice in one session,
  2026-08-24). Both first drafts passed against the broken code: one exercised
  a code path the defect did not live on, the other asserted against the State
  setter when the defect was the CALLER. Run every new gate against the
  pre-fix build before trusting it.

- RE-BANDING THE RIG'S LOCAL SOID SPLITS THE CLIENT IN TWO (2026-08-24,
  20.18): `state.account.primary_soid` moves the client's PUBLISHED identity,
  but the queuez MANAGER key - what every family subscribe roots on - is fed by
  retail's sign-on path and does NOT move. The game's own family-zero producer
  then emits nothing, the seed hook fights it 36x/second forever, and sign-in
  hangs ~82 s before leaving 'unavailable' (a black screen with a live cursor).
  Distinct-guardian testing needs BOTH to move; map the manager-key source
  first (in-process ws-503 echo is the prime suspect).
- AN INSTRUMENT'S conn COLUMN IS STALE DURING A DEFERRED RE-PUSH (2026-08-24):
  a re-push runs on the connection's own timer, so no inbound transport frame
  precedes it and "last seen conn" belongs to whoever last spoke. This produced
  a false "key flip" that read as a live defect. p2d1_boot_read.py now detects
  re-push blocks and prints conn=repush; the real fix is to print the session
  id in the subscribe_in line itself.

- A BACKUP'S NAME IS NOT ITS CONTENT (2026-08-24, cost: nearly booting the
  confound we set out to clear). `settings.json.bak_m3g1_resoid` was recorded
  in three places as "the ...110 variant"; it is byte-identical to the
  legacy-band live file. In this repo `bak_<label>` usually means "taken
  BEFORE <label>". Hash a backup before trusting what it holds.
- SSH TO THE RIG NEEDS A LIVE ControlMaster (2026-08-24): the handoff's
  `-o ControlPath=~/.ssh/cm-rig` form has no credentials of its own and the
  socket dies with rig sleep / session end. Re-open with
  `ssh -M -S ~/.ssh/cm-rig -o ControlPersist=8h -N -f rasla@192.168.1.136`
  from a plain shell with nothing appended - a duplicated host token makes the
  master refuse sessions AND its own -O exit. ping proves nothing (ICMP is
  blocked); use the ssh handshake as the liveness test.
- ADMIN BINDS THE LAN ADDRESS, NOT LOOPBACK (2026-08-24): the log says
  `ev=admin stage=listen result=ok port=8099 bind=192.168.1.164`. A curl to
  127.0.0.1:8099 returns an EMPTY body with exit 0 - indistinguishable from a
  dead server. Always query the bound address.
- A SCRATCH-BUILT AFTER-IMAGE IS A SILENT FIELD WIPE (2026-08-24, cost: the
  whole dual-client wall, and a boot to find the same bug in family three
  earlier - the boot-G roster refusal). Any staging that builds `Struct x{}`
  and fills only its own fields resets everything else in that struct when
  published. Build after-images from the BEFORE-image and overwrite only what
  the operation owns. Grep the queuez/staging tree before adding another.

- DXMT cold-compile pick-crash: changing an EQUIPPED item's definition forces
  cold shader compiles at pick (no persistent shader cache on macOS) ->
  silent death, no SEH/minidump. State every experiment's GRAPHICS DELTA.
- Truncated log trap: build_data identity warn prints expected_eq SHORT with
  NUL+garbage mid-line. NEVER read expected values from logs; compute
  (RE_output/scripts/bootL_eqhash_exact.py, validated).
- eqHash is LIVE state: ability/equipment commits drift it; the server
  self-restamps offset 20 itself. Compute before comparing.
- CROSS-PROCESS ANCHOR TRAP (new, Lane B): same-name core events on the two
  sides are NOT the same real moment - the client's core lines come from the
  in-process DLL, the server's from the standalone wine server that booted
  minutes earlier (observed disagreement ~5.3 s). Only WIRE events (transport
  accept / bap) are true shared moments. merge_logs.py's PRIMARY anchor has
  ZERO client-side hits on every capture currently on disk.
- SNAPSHOT IS A VALUE TYPE (new, Lane C): core::log::snapshot::Snapshot is
  std::array<Entry,128> (~134 KB) returned BY VALUE. Enlarging the ring to
  4096 makes it ~4.3 MB in any caller's frame - the admin thread's default
  1 MB stack cannot hold it. Gate capacity per-target and raise the thread
  stack before enlarging.
- STALE CONFIG DECOY (new, Lane C): RE_output/s1_accept/settings.json (root
  level, https_port 443, Windows paths) is IGNORED. The live file is
  RE_output/s1_accept/Sunrise/settings.json. Do not read the decoy as config.
- Use /usr/bin/python3 for sqlite3 work (miniconda python has broken _sqlite3).
  Sandbox also cannot open state.db.bak_* in place - copy to scratch first.
- Cache surgery: details SORTED by definitionIndex; itemDetailCount u32 @36;
  payload checksum two-segment recipe; eqHash @20 OUTSIDE checksummed region.
- One-directional negative != exoneration. Record the test DIRECTION.
- NO settings write-back exists: published once from settings.json; in-game
  changes cannot survive a boot.
- Git EPERM curse (hit twice): reads via cat work, git gets EPERM on
  .git/config. FIX: copy .git to scratch, verify, swap fresh copy into place
  at identical path. If instance #3 appears, budget a real diagnosis session.
- ADMIN PORT / TIME_WAIT (new, 2026-08-22): the dashboard polls 8099 every
  second, so its own just-closed connections sit in TIME_WAIT and a quick
  server restart could not rebind - and admin bind failure is FATAL
  (ev=admin result=fail reason=bind -> initialize stage=admin result=fail ->
  server exits). FIXED by setting SO_REUSEADDR on the admin listener,
  matching bap_listener.cpp. Verified with 9 TIME_WAIT sockets present at
  relaunch. https_listener now carries the same option (the client holds
  8443 for a whole session and would fail identically once it has live
  connections; not reproducible on THIS Mac because the hybrid architecture
  answers config/SignOn in-process so 8443 never sees client traffic).
  discovery_listener is UDP - TIME_WAIT is TCP-only, so it is not exposed.
- Flag banks must stay CURATED: blanket saturation -> client discards part of
  the family-4 join snapshot while all server-side checks stay green.
- CONTENT-MANIFEST GUID IS INSTALL-LOCAL (2026-08-23, cost: the whole M1
  blocker misread as TLS): the guid = SHA256 over pkg stems/ids/patchIdx/
  sizes/lastWriteTime. Two machines with the SAME build produce DIFFERENT
  guids (mtimes) while serving byte-identical manifest sizes - never copy a
  config_guid between installs; derive per machine via
  RE_output/scripts/manifest_guid_from_cache.py (validated against the Mac
  cache first).
- INLINE MULTI-LINE POWERSHELL OVER SSH SILENTLY NO-OPS (2026-08-23): exit 0,
  no output, NO effect on disk. Write a .ps1, scp it, run with -File, then
  VERIFY the edit landed before building on it.
- ADMIN /ladder AND /state EMIT INVALID JSON WHEN ANY SESSION EXISTS
  (2026-08-23, FINDINGS 20.2): leading comma before the first row. FIXED,
  DEPLOYED, WIRE-VERIFIED 2026-08-23 ~13:1x (commit 2a0da29) - board is
  17/17 green with a live session. Kept as the pattern: empty-board reads
  hid this bug all day; a serializer must be proven with DATA present.

## DEPLOY RULES (binding)

Kill old server first. Restamp build_data identity after any exe rebuild
(offsets 12/16; scripts/restamp_build_data.py). Recompute eqHash after
equipped items/levels/policy/plugs changes (flags do NOT feed it). Content
JSONs override cache at boot. Verify observer call volume BEFORE deploying a
hook. Verify THE WIRE changed before accepting a negative. One destiny2.exe
per boot. Byte-exact settings copies. No debuggers. Restart the server before
blaming state. BOOT BRIEF RULE: purpose/payoff, falsifiable claim, what it
does NOT test, GRAPHICS DELTA. NEW: run check_invariants.py before and after
a boot - it seeds the monotonic baselines and catches the saturation class.

## MAC PORT ESSENTIALS (stable)

Client rides Game/bin/x64/steam_api64.dll in Whisky bottle "Sunrise"
(DllOverrides winemetal=b, d3d10core=n,b per-app required). Server =
llvm-mingw cross-compile under GPTK wine 7.7, own prefix,
mac-port/launch-server-macos.sh. Hybrid architecture: config-manifest GET +
SignOn answered IN-PROCESS by the client DLL (wine inbound TLS impossible -
permanent); BAP/discovery/admin external on 30975/3074/3075/8443/8099;
gameplay ~30976 UDP even ports. Build -- -j 8.

## MILESTONES

S0 standalone-server extraction DONE (+Mac port). S1 persistence +
content-driven datagen DONE (+swap front). S2 static world population
STARTED (scoping done, emission deployed flag-off, W1-W8 ladder ready).
S3 combat / S4 missions / S5+ NOT STARTED (handbook + playbook now exist
externally; estimates revised down for early missions).
TWO-BUG FRONT DONE (2026-08-22) => FIRST SHIPPABLE BASELINE.
M3 DUAL-CLIENT COHABITATION (partial) DONE 2026-08-24: two provisioned
accounts, two DIFFERENT guardians, both in city_tower_social_d2 at once, with
isolated per-slot data and keys (FINDINGS 20.21). Peers cannot yet SEE each
other, and they still share an account soid - both are the next front.
COMMUNITY PUBLICATION ARC DONE (2026-08-22, FINDINGS 18.1).
MSVC BUILD FRONT DONE (2026-08-22, FINDINGS 18.3, CI green on c30a72d).
OBSERVABILITY PROGRAM IN FLIGHT (2026-08-22 ~21:3x, lanes A-E; D verified).
Next natural fronts: finish A-E -> multiplayer P1 bind-address -> guest
accounts; entity front W1-W3; attribution bisect as a cheap warm-up.
