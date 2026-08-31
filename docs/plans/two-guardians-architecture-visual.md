# Two Guardians in the Tower — Architecture & Gap Map (rev 3, road C live)
Plan-mode artifact, 2026-08-27 late. Supersedes rev 2 (20.109-era). Sources: STATE.md
(~18:3x), FRONT_public-host-chain.md (live), HANDOFF_2026-08-27_ROAD-C.md, 20.110–20.122.

## THE VERDICT (20.113–20.122)
The client does not trust BAP declarations: it walks its OWN managed-session member
table and tracks only members at state 10 (ESTABLISHED); anything else is warned and
released. The entire wire-shaping class is RETIRED (STATE DEAD ENDS, 20.113).
The peer layer NOW WORKS (verified-by-execution, 20.118): stage=receive 0 -> 37..64;
DTLS/establish/group join/membership/player-added/join result=completed; reserve fires
for a SECOND MACHINE at memb=10; peers valid 0x1 -> 0x3; PUBLIC TARGET role taken;
tracking-data warning + peer-reservation release no longer fire.
Three changes opened it: p2(75) serve own endpoint as search answer; p2(78) force
Tower region public (slice set 56, settings-only); p2(79) application-ready gate.
CORRECTION (20.125): that evidence is MAC-SOLO, delivered via BAP/Steam-emulation —
the rig has NEVER dialed the gameplay endpoint; see LADDER 4b.

## ROAD C CHAIN (server = group-session host) — updated 2026-08-28 ~18:xx
L1-L8 ✅ verified-by-execution (co-location: 20.140, p2(89)) | L8b ✅ resolved via
second-BAP-link fixes (20.137-20.139) | L9 render ⏸ the remaining lane —
re-scoped twice: peer channel = dynamic-only (20.144); the carrier is the
group-session player row's 264-B identity/profile slot (20.143), whose blob is
opaque+self-hashed and must be REPLAYED from capture (20.145). Current gate:
rig GAH link never advertised (20.146) — static read, no boot.

## TWO LIVE BLOCKERS — RESOLVED/SUPERSEDED 2026-08-28 (history below kept for context)
1. PARAMETER 21: verdict UNSETTLED — 9-byte grammar found (param21-body-grammar.md),
   framing bit gated on VMP-suspected envelope parser (param21-msg38-parser.md).
   Clear-root stays; possibly MOOTED by L8b (0-slot reservation was downstream of
   MEM-0, 20.132).
2. L8: RESOLVED — built (20.124), row drop fixed via real machine ids (20.128/20.129),
   co-location landed (p2(87)/20.131). NEW GATE: L8b, see LADDER STATUS 5c.

## OPERATIONAL LANDMINES (handoff §6)
- reset_lobby_claims.sh is a PRECONDITION (public region with no search = hard stall).
- Only force slice set 56 (Tower); 24 orbit / 48 initial — do not force (p2(76) stall).
- p2(80) keepalive = proven no-op, inert; do not cite as fix.
- Render death follows CO-PRESENCE not entry order; parked render lane.
- U1 corollary: grep the local corpus (handbook dumps) before naming an RE question.
- L13 corollary 2: census stages first (uniq -c), then filter; match event prefixes.

## LADDER STATUS (updated 2026-08-28 ~14:4x — CO-LOCATION ACHIEVED, L9 re-scoped)
MAIN PATH:
  1. param-21 ◐ verdict UNSETTLED (9-byte grammar; framing bit gated on
     VMP-suspected envelope parser, param21-msg38-parser.md). Parallel lane.
  2. ⏸ clear-root stays (may be mooted; peer channel HELD post-p2(89)).
  3. ✅ 4. ✅ 4b. ✅ (rig wedge: resolver self-address + jr-observer, p2(84))
  5. ✅ row drop CLEARED (real machine ids 20.128/20.129 — 3 members
     _established both sides, peers valid 0x7).
  5b. ✅ activity-host co-location (region-bound AH, churn dead, 20.131).
  5c. ✅ L8b CLOSED via deeper root: second BAP link never served (GAHN
      starvation 20.137) -> per-account link source (20.138) ->
      kBapConnectionCount 4->12 (20.139) -> p2(89) 2997d2810f11b1ab.
  5d. ✅ CO-LOCATION ACHIEVED (20.140): ONE public Tower instance (identical
      session-description D9AED900:EBB92CF2, region PUB56.56, AH 00200003,
      both 'public AH instance ready'), each names the OTHER's xuid (prior
      runs read PEER=0), peer channel connected4 HELD, 0 errors / 1 rebind.
  5d. ✅ CO-LOCATION ACHIEVED (20.140): ONE public Tower instance (identical
      session-description D9AED900:EBB92CF2, region PUB56.56, AH 00200003,
      both 'public AH instance ready'), each names the OTHER's xuid (prior
      runs read PEER=0), peer channel connected4 HELD, 0 errors / 1 rebind.
  6. ★ CURRENT GATE (20.146): the rig's GAH link NEVER OPENS — no GAH endpoint
      advertised — so it never learns the public region, never gets a
      citizen-join task, hangs at 'waiting for managed-session-start'.
      Boot-1 split instances + boot-2 hung load = ONE defect. Mac gets 3 links
      (PRIMARY/FAH/GAH), rig 2 (GAH properties unset). Suspect: p2(89) per-
      account second-link lookup fails for the SECOND account's window
      ([5..12] vs [0..7]). Wire evidence already captured (bap30975 captures
      20260828_155846/_1615) — static read names the defect, NO boot. Mac now
      DUAL-HOMED (en0 .164 + en13 .7 owning default route; host route pinned) —
      environmental drift to watch. bdNAT red herring closed (LAN peer setup
      does not depend on bdNAT rendezvous).
  7. ✅ pc= DECODED (20.143): the group-session player row carries an OPTIONAL
      264-byte identity/profile block; this host has NO WRITER for it (writes
      profile absent). The carrier L9 builds on — same channel both clients
      consume, slot defined, consumer parses it.
  8. ◐ PROFILE BLOB ANATOMY (20.145, claims/l9-profile-layout.md): opaque,
      self-hashed ~396 B (8+232+136+20); client apply fn 0x141781800 verified
      field-for-field; ONE profile-present flag (byte +0x21) gates all of it;
      region A carries its OWN lookup3 hash (0xdeadbfd6, distinct from session
      hash 0xdeae2f4e). Session layer TRANSPORTS, NEVER PARSES -> writer must
      REPLAY real bytes (self-hash validates the replay). Open: wire bit-reader
      decode unlocated; 8-B table-base discrepancy (0x3b58 vs fork's 0x3b50) —
      audit before any hash-matching write.
  9. ⬜ SOURCE a real blob: route B capture — client-HOSTED fireteam (mac hosts),
      capture_bap30975.sh (TOOLS.md); fireteam self-row pc=1 = existence proof
      of a row that sets the flag.
  10. ⬜ replay the blob into the shared session's player rows (server-side
      writer, hash-validated).
  Phase 3 ⬜ firsts (leadership/properties/tracking x2) — capture-and-park.
  Phase 4 ⬜ render-death class + remaining render specifics.
  12. 🎯 two guardians one tower.
L9 MEASUREMENTS (20.143-20.145): W-A ANSWERED — peer channel = 26-byte ~4 Hz
  ENCRYPTED dynamic stream + establishment plaintext (session desc/addresses);
  appearance NOT on it (by size: 26 B vs 264 B identity block). Static half
  genuinely missing from every measured carrier; third-carrier possibility
  stated but unexamined. W-B CLOSED: no root->account resolution exists
  anywhere. Do NOT flip physicsHostSession / gameplayExternalBody /
  serverDefaultEntity (no wire output / unwired). Do NOT start at W-C.
L9 REFRAME (20.141/20.142): peer channel ALREADY replicates (250 pkts/summary,
  0 lost — likely dynamic state: position/motion, cf. 20.131 phantom movement);
  missing = peer's STATIC character records (which guardian, which armour).
  Do NOT flip physicsHostSession (produces no wire output), gameplayExternalBody
  / serverDefaultEntity (unwired). Do NOT start at W-C (lane_entity_scope W1-W8
  scoping predates co-location). One 08-22 blocker already gone (per-account
  soids distinct); shared-space placement closed by 20.140.
PHASE 3 — SESSION LEARNS IT HAS TWO PEOPLE (observe first):
  6. Leadership resolves (delegate-leadership 0x20 / desired-leader-address;
     client must accept outcome incl. non-peer leader)
  7. Property exchange settles (0x1F / 0x25 — answer if asked, Phase-1 pattern)
  8. Tracking table holds BOTH members (0x140C17E40 lookup at state 10 x2;
     no warning, no release)
PHASE 4 — MAKE THE SECOND GUARDIAN EXIST (render lane):
  9. Character records cross the wire (family-0/family-3 — server owns family-3)
  9b. Per-identity appearance replication (NEW, 20.125: duplicate-hunter visual
      proved the client renders BAP-carried members with LOCAL appearance)
  10. Position stream (mesh vs relay — decided by step 6's outcome)
  11. Render death diagnosed (already fired on co-presence, no client trace;
      hypothesis: renderer handed a member with no char/pos data)
  12. TWO GUARDIANS IN THE SAME TOWER 🎯 (L9 closed)
Caveat: complete for everything nameable today; ladders sprout sub-steps when
climbed (2b exists because of that). One step per boot, pre-named negatives.

## AFTER STEP 12 — GENERALIZABILITY MAP (2026-08-28, added post-co-location)
TIER 1 — transfers free: hosting chain L1-L8 (region/slice set is a parameter:
48 initial / 24 orbit / 56 Tower); L9 profile replay (guardian bytes are
destination-agnostic); peer channel dynamic state; multi-client provisioning
(per-account links, distinct soids — 20.141 confirmed identity-collision
blocker resolved); instruments + offline wire-decode method (works on any BAP
body family).
TIER 2 — transfers with configuration: full fireteam <=6 (composer capped 6
peers / 988 B worst case, measured + static_asserted; kBapConnectionCount 12
= 4 clients x 3 links — scale for more; party layer party_start_join->... still
the one untouched join plane); other social spaces; orbit is its own no-host
flow (p2(76) precedent).
TIER 3 — genuinely new lanes: (1) combat authority — physics-host election/
arbitration (delegate-leadership 0x20 / desired-leader-address have never
fired; unknown whether clients elect among themselves or the server must
arbitrate); (2) mission scripting — Truman's Activity Host runs mission script
logic; the fork is session/membership authority only; Tower masked this
entirely; size unknowable until physics-host answered; (3) population — patrol
bubbles with strangers = the server fabricating NPC/stranger state (fireteam-
only instances avoid it); (4) combat event traffic — 26-B channel is a motion
budget; shots/damage carrier unknown until pcap'd in a combat space.
SLEEPER GENERALIZATIONS: the BAP account/family backbone (family-4 equip proof
chain; families 0/2/3 subscription live) is the plane for vendors/inventory/
progression; L9's conditional root->account resolution (W-C) is the exact
primitive cross-account anything needs — building it for L9 pays forward.
BOTTOM LINE: Step 12 is the proof the method works on any wall; remaining
risk concentrates in physics-host authority + mission-script hosting, both
unanswerable until co-located guardians exist where shooting matters.

## Method rules that keep paying (history proof)
Complete far-end implementation + offline byte-exact verification before boots; one
variable per boot; pre-named negatives; observation bundles free, behaviour switched.

## HISTORICAL: the rev-2 prediction and how road C resolved it
Rev 2 predicted the observation boot would show "nobody knocks" (client-to-client
transport dead: peers valid 0x1 forever, send_rendezvous a log-only sink, SDR creds
absent, relay never carried traffic — all verified). The prediction was CORRECT for
the client-to-client direction, and road C won precisely by refusing that frame:
instead of making clients dial each other, the SERVER became the complete group
host (the "full far-end implementation" style that produced every prior win), and
the client dialed IT. The falsifier fired only after three deliberate environment
changes (p2(75)/(78)/(79)) — i.e., the mechanism was never broken; the environment
was incomplete. Same lesson as 20.93, now proven at the session layer.

## HISTORICAL: GDC cross-reference (still-valid corroboration)
Truman GDC 2015 / Aldridge GDC 2011 / Butcher 2013 / Genova 2015 — nothing
contradicts the static map. Points that remain live: reservations consume capacity
(now literally parameter 21's subject); host election vocabulary (delegate-
leadership 0x20 / desired-leader-address) still unexplored; reconcile-as-house-style
explains sustained-feed requirements; membership-update 0x1E (0x7980) remains the
host-migration full-roster snapshot; thread discipline is an engine-wide invariant.
Frame GDC material as corroboration + capture targets, never as a substitute for
binary evidence (20.82->20.105 precedent).

## RUNG PROTOCOL (how the ladder enters a session without scope explosion)
- The ladder is a MAP in one doc, never pasted into working context. A session
  receives ONE rung: "You are on Step N. Done looks like X. Do not work on
  Step N+1. Notice something outside the rung -> one line, park it."
- Never paste raw conversation fragments across architecture areas — distill
  to a FINDINGS/claim entry first, cite by number, target session pulls on demand.
- Close the rung with a ritual (marks updated, finding written), then FRESH
  session for the next rung. Long-lived sessions accrete stale considerations.
- Use lane-brief-template.md (OUTPUT-FIRST) as the rung carrier.
- The USER moves the rung pointer; the session never advances itself.

## Hard constraints (unchanged, still binding)
- NO one-shot writes into +0xC8 — reconcile loop computes removals unless the
  source keeps asserting. Sustained feed or nothing.
- NO .text patching; no guessed-ordinal vtable slots; census first (LESSONS 18).
- No new Steam bindings for this goal (pipeline never touches Steam, 20.107).
- Observation bundles freely; behaviour only behind no-rebuild switches.
- Caller capture (LESSONS 18c), not string xrefs — log strings not in binary.
- DO NOT GUESS parameter body layouts (policy-31 fatal decode; p2(80) precedent).
