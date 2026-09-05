# BOOT_BRIEF_p2-174 — C3: THE CRAFTED SELF-PEER ROW WITH AN OVERRIDDEN CHARACTER

STATUS: READY (2026-09-04 ~13:0x PDT) — change BUILT (server 3f0496a9ebcf744c); clients
p2-171 a96a6a70f578fc40 BOTH (rolled back 2026-09-04 12:40, hashes asserted on both
machines); adversarial pass ses_f91ffb20fffeDIYU6rTyQBxIvU: GO-WITH-CONDITIONS, 5
conditions ALL APPLIED (see ADVERSARIAL PASS). IMPLEMENTATION boot (the server sends a
row it has never sent, to provoke a specific client behavior). Ancestor: 20.53/p2(42)
(the positive control), p2(45)'s same_client fix (bypassed by this knob BY DESIGN).

## PURPOSE

The character-data question closed with one residual (character-data-lookup-brief.md C3,
FINDINGS 20.294 R5): does the client's body-builder consume a server-named CHARACTER, or
only the locally loaded one? The positive control is 20.53: a full membership row naming
the LOCAL player rendered a second guardian server-only ("You" clone) — the row's
character field then named the local player's ACTIVE character, so the test could not
distinguish "row-driven" from "local-state-driven".

THIS BOOT: the fork publishes a CRAFTED self-peer row (the local identity in member
slot 1 — the 20.53 condition, settings-gated bypass of same_client/same_account) with
the row's character-carrying field REPLACED by a DIFFERENT character soid of the same
account (0x9EAA300100100100 + 1..3). The fork's row fields mirror the client's own
type-23 identity; among field3/field5/field6 exactly one is expected to carry the
active character soid. The replacement is SELF-LOCATING (the encoder matches the field
holding the active soid) and logs the field name, pre, and post.

## THE CHANGE (server only, two knobs, all client builds unchanged)

`RE_build/Sunrise-fork-inventory/Sunrise/src/.../activity_membership_push.cpp`
(make_wire_snapshot): settings-gated crafted peer row + character override, with
`ev=membership stage=crafted_peer` and `stage=crafted_character` log lines.

**THE CHARACTER FIELD IS KNOWN, NOT GUESSED**: the fork's own membership route maps
`parsed.field5 -> identity.opaqueSoid` and logs it as `character=`
(activity_membership_route.cpp:33/77-83). The override replaces field5 directly, with a
sanity check against the account's FULL character list (the server's selected character
can diverge from the client's played one - 20.64's lesson). A field5 outside the list
logs `result=field5_not_known_character` and the row publishes UNCHANGED - a
locator-negative to record, NOT a C3 answer by itself (adversarial finding 3).
Settings knobs: `membership_self_peer_row` (bool), `membership_row_character_override`
(u64 via unsigned_value - quoted hex accepted). Server build 3f0496a9ebcf744c.

## VARIANTS (pre-named; settings flips between runs; reset_lobby_claims.sh between)

  V-1  override = "0x9EAA300100100103" (the LAST character; the active is LIKELY the
       first, so this maximizes the visible delta: class/gender/race visible in render).
  V-2  override = "0x9EAA300100100102" (the middle character) — only if V-1's crafted_
       character line shows pre==0x...0103 (i.e. the active IS the last character).
  V-3  (pre-authorized, adversarial finding 2) `membership_peer_same_region_advert=true`
       — the self-peer row's peerAdvertReason is DETERMINISTICALLY `same_region` (the
       local key resolves the local binding), so the row ships CITIZEN-LESS and may be
       fixup-released (20.74.4: "a peer with no address is not joinable"). If the client
       shows no second member and the logs show same_region, flip this TRUE as the next
       run - it is the branch's own switch, not a new instrument.

## INSTRUMENTS: crafted_peer, crafted_character
## (the client rides the p2-171 build's proven observers - resv_rec/pgate/ent census -
## no new client instrument)
## LITERAL TARGETS:
## RE_output/s1_accept/sunrise-server.exe: crafted_peer, crafted_character

## SETUP

  server   3f0496a9ebcf744c (deploy_p2d6_gameplay.sh default source). Settings:
           membership_self_peer_row=true,
           membership_row_character_override="0x9EAA300100100103",
           world_population=FALSE (the eventType question is closed, 20.294 R4 - off to
           reduce confounds), membership reseed OFF, transport identity ON, roster
           participation ON, **pool_c4_mark_push=FALSE** (adversarial finding 1: with a
           self-peer row live, the type-45 path would mark the CLIENT'S OWN machine id -
           the 20.249 crash shape; the deployed file had it TRUE, now set false - VERIFY
           in the deployed file before launch). gate_poke=0 both clients.
           NEW INSTRUMENT LITERALS to grep-assert in the DEPLOYED server exe (U14):
           "crafted_peer", "crafted_character"; and the settings echo must show
           membership_self_peer_row / membership_row_character_override before launch.
  clients  p2-171 a96a6a70f578fc40 BOTH (deployed + asserted 2026-09-04 12:40). Their
           observer set: resv_rec, pgate, ent census, mtrace WITHOUT resv_claim/
           image_set (those are the parked-defect build's hooks - absent here).
  rollback p2-173 server (3bc9a3b922b398bb) + settings bak_p2-173_pre; clients unchanged
           (already p2-171).

## GRAPHICS DELTA (THE TEST ITSELF)

A SECOND GUARDIAN is the expected render (the 20.53 positive control) — and its
CLASS/GENDER/RACE is the measurement: if the clone renders as the OVERRIDE character
(V-1: character 3) rather than the active one, the client's body-builder consumes
server-named character data (C3 = YES, a crafted-row lever exists). If it renders as
the ACTIVE character (identical to the player), C3 = NO (the body follows local state;
the row's character field is not consumed). No second guardian at all = the crafted row
was dropped upstream (the citizen/endpoint path) — the log's peerAdvertReason line
names which cause.

## FALSIFIABLE CLAIM

After `ev=membership stage=crafted_peer result=ok` and (if the override matched)
`stage=crafted_character result=ok field=<name> pre=<active> post=<override>` on the
server, the CLIENT's roster/ent census shows the second member row, and the rendered
clone's visible class matches EITHER the override character (C3 YES) or the active
character (C3 NO). The user's visual report + resv_rec/ent census decide it. ZERO
client-side peer-row evidence after a clean crafted_peer line = the claim fails (the
row was dropped; peerAdvertReason names the cause).

## CONTENT NEGATIVE

  (1) `stage=crafted_character result=field5_not_known_character` → the row's field5
      does not match ANY soid in the account's character list: a LOCATOR-negative -
      record the logged f5 value and the account's character soids, and STOP; do not
      conclude C3 from it (adversarial finding 3: the client's own type-23 names its
      played character in field5, so a mismatch means the account snapshot diverged,
      not that the row names no character).
  (2) crafted_peer ok but the client log shows no second member → the row was dropped:
      peerAdvertReason + the client's own roster lines say which cause. EXPECTED value
      for this branch is `same_region` (deterministic: the local key resolves the local
      binding) - that is NOT a failure signal, it is the citizen-less row shipping; if
      the client then drops it, that is 20.74.4's fixup-release by construction, and
      V-3 (`membership_peer_same_region_advert=true`) is the pre-authorized next run.
  (3) The client refuses the crafted row or freezes (the 20.64 shape). SCOPE NOTE
      (adversarial finding 4): 20.64's refusal fired on a FOREIGN member key of the
      same account; this row carries the LOCAL key - the 20.53 shape that RENDERED -
      so the refusal is not expected. A freeze OR a tried-to-join-self line is the
      negative: record, stop, NO retries.
  (4) pre==post in the crafted_character line (the active IS the override character) →
      void run; run V-2 (pre-authorized).

## ABSENCE NEGATIVE

  - ZERO stage=crafted_peer lines → the push path or settings regressed; check the
    deploy hash + settings echo before any client conclusion.
  - resv_rec/ent census absent → install census first (the p2-171 build's observers
    are execution-proven across p2-170/171, so silence would be a real negative).

## CHAIN MARKS  (L16)

1. Row encode layout (write_member_row/write_player_identity) — verified-by-reading
   (the fork's own encoder; the byte map cross-checks 20.258 R3's record write-set).
2. Identity fields mirror the client's type-23 — verified-by-reading (the parser +
   make_wire_snapshot's field mapping; the field VALUES' meaning unverified - this boot
   logs them).
3. Active character soid accessor (account_snapshot + find_character_index) —
   verified-by-reading (the family4 push paths use exactly this pair).
4. The client renders a body from a self-named full row — verified-by-execution
   (20.53/p2(42), one machine, zero peer contact).
5. The client consumes the OVERRIDE field — **unknown: THE LINK THIS BOOT RESOLVES**.
6. p2-171 client build reaches the Tower and runs full sessions — verified-by-execution
   (p2-170/171 boots, 20.284-20.286).
7. The crafted row survives the peer-row delivery chain (endpoint/revision) — unknown,
   pre-named as content negative (2).

## ADVERSARIAL PASS: ses_f91ffb20fffeDIYU6rTyQBxIvU — verdict GO-WITH-CONDITIONS, 5
## conditions ALL APPLIED: (1) pool_c4_mark_push pinned FALSE in deployed settings
## (the 20.249 self-mark crash shape - the deployed file had it TRUE); (2)
## peerAdvertReason=same_region pre-named as the branch's deterministic value + V-3
## (membership_peer_same_region_advert=true) pre-authorized; (3) the character field
## resolved from the fork's own route code (field5=opaqueSoid, logged as character=)
## + the locator-negative reclassified (not a C3 answer); (4) the 20.64 refusal scope
## noted (foreign key, not local) + freeze pre-named as record-and-stop; (5) the new
## literals grep-asserted in the deployed exe + settings echo required pre-launch.

## DO NOT

  - Do not run this paired before the solo mac shows the crafted_peer + character line
    (the 20.53 control was solo; adding the rig before the mechanism shows adds a
    variable). Solo first even though the user waived solo for p2-173 — here the waive
    was not requested; default to the hard rule unless told otherwise.
  - Do not touch the client. gate_poke=0. Do not turn world_population back on for
    this boot (its question is closed; it is a confound here).
  - Do not chase a 20.64-freeze with retries: if the client cites tried-to-join-self,
    that is content negative (3) - record and stop.
