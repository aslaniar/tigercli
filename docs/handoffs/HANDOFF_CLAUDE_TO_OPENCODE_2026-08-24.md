STATUS: historical - superseded by HANDOFF_OPENCODE_2026-08-25_EVENING.md and STATE.md (marked 2026-08-26). Kept for archaeology.

# HANDOFF: Claude Code -> opencode, 2026-08-24 ~19:0x
# From the Claude session that took the peer-visibility front after your
# 2100 + manager-key lanes landed. I am near my context limit; you have the pen.

## READ FIRST, IN THIS ORDER
1. `STATE.md` headline (rewritten by me; newest first)
2. `FINDINGS_2026-08-24.md` entries **20.27 -> 20.30** (mine, this session)
3. `RE_output/claims/upstream-strategy-2026-08-24.md` - the decision doc,
   especially §7 (architecture comparison) and §3 (the mechanism)

Everything below is a pointer to those. They are the source of truth.

## WHERE THE WORK IS

    repo    RE_build/Sunrise-fork-inventory
    branch  upstream-gameplay-scoped        <- NOT integration
    HEAD    d013c1e  p2(22): ServiceOutcome variant
            f68f230  upstream(scoped): gameplay/physics adoption
            ed3efcf  TEMP(2100): your diagnostic, committed so it is revertible
    tag     pre-upstream-0188841            <- rollback anchor
    `integration` is UNTOUCHED and still matches the deployed, running server.

## STATE: FIVE FILES EDITED, UNCOMMITTED, **BUILD NEVER RUN**

    M server/bap/internal.h
    M server/bap/encrypted/activity_message/definition.h
    M server/bap/encrypted/activity_message/activity_message_route.cpp
    M server/bap/encrypted/bap_connection_publication.cpp
    M server/bap/encrypted/bap_connection_publication.h

All five edits LANDED. I was interrupted before the compile, so the build state
is UNKNOWN - assume it does not compile until you prove otherwise. That is the
first thing to do.

## WHAT IS DONE

- **f68f230** - scoped adoption of upstream 0188841: 163 files, the whole
  physics/replication stack, source-bound advertisement, activation gates, and
  a hand-port of `SessionBinding` + retain/release onto our process-wide
  `g_activity`. Builds clean on its own.
- **d013c1e** - upstream's `ServiceOutcome` variant. Fixes a real latent hazard:
  `transactions::commit` enforced transaction exclusivity by summing THREE of
  SIX flags at runtime. Now `std::variant` + `transaction_if<T>`; guard deleted.
- **Steps 1-3 of 4** of the dual-link model (uncommitted, above).

## WHAT IS LEFT - ONE STEP, THEN GATE AND BOOT

### Step 4: publish ONE membership body on the public link
In **our** `activity_keepalive_push.cpp` (ours, not upstream's - I reverted
that file deliberately). When ALL of:
  - `session.activityRole == ActivityClientRole::publicTarget`
  - `core::settings::get().server.activation.activityPublicMembership`
  - `!session.activityPublicMembershipSent`
then publish exactly one membership body and set the flag.

**The body must be the PRIVATE link's member table, sent verbatim.** Upstream's
comment on this is load-bearing and I am quoting it because getting it wrong
destroys the player object:
> "The client matches itself by the key at `client+27696`, which is its machine
> id and is the same on both links, so only the private snapshot carries a
> member the client recognises as the local player. A body carrying anything
> else makes the client prune the member and destroy the player it holds."

Read `state::activity::membership::live_region_session(kAbsentSessionId)` to
find the private session, check `join_identity(privateSessionId) != 0`, then
`prepare_refresh(privateSessionId, kCurrentRevision, kNoBubble, staged)` -
READ, never commit; this link must not move the private session's revision -
and append it on THIS link's session id.
REFERENCE IMPLEMENTATION: `git show upstream/master:Sunrise/src/server/bap/
encrypted/push/activity/activity_keepalive_push.cpp` lines ~135-190. Read it;
do not copy it (its surrounding session model is not ours).

### Then: settings
`RE_output/s1_accept/Sunrise/settings.json` needs, inside `"server"`:
    "activation": { "activity_public_membership": true }
Leave every other gate off. `physics_host_session` produces no wire output
either way and is a second variable - not this boot.

## HARD CONSTRAINTS - THESE ARE WHY THE LAST ATTEMPT FAILED (20.30)

- **DO NOT take upstream's BAP activity layer wholesale.** I tried. The chain
  closes back onto our own P2 front: public membership -> ActivityClientRole ->
  transactions/ServiceOutcome -> membership -> receipts -> middleware
  activity_message -> **cache format v44** -> queuez ServiceOutcome = our
  keying work. There is no cut line. Port SHAPES, not code.
- **DO NOT take cache format v44.** Ours is v24. Upstream's roster snapshot
  reads `bubbleGroups`/`slotIndices` which only exist in v44, and a bump means
  regenerating `build_data.bin` - whose regeneration path on the STANDALONE
  server is UNVERIFIED (extraction lives in `client/content/**`). Open item.
- **DO NOT touch the ability model or `state.db`.** Deferred deliberately by
  the owner; it is its own front.
- **Keep every `AccountKey`.** No defaulted keys - that rule has caught three
  real bugs including one in upstream's code. Any unkeyed call must stay a
  compile error.
- **After a 3-way merge of a restructured function, diff the RESULT against
  upstream's version of that function.** `git merge-file` exited clean while
  silently mangling `arm_repushes` and dropping a whole block (20.30).

## DEPLOY + BOOT

Script: `RE_scripts/deploy_p2d6_gameplay.sh`. It stops the server, runs the
four harness gates IN THAT WINDOW (they cannot run while the server holds the
log and state.db - that is not a bug), aborts before touching anything if a
gate fails, backs up, deploys, restamps, relaunches, verifies listeners.
**Point it at your new candidate** - it currently reads
`sunrise-server.exe.NEW_candidate`. Two gotchas already fixed in it and worth
not re-breaking: the cache restamp MUST run BEFORE the harness (the harness
validates cache identity against the exe under test), and the kill pattern must
be `'wine64-preloader .*sunrise-server\.exe'` (the launcher execs an absolute
path).

Build: `cmake -S Sunrise -B build -G "Unix Makefiles" -DCMAKE_SYSTEM_NAME=Windows
-DCMAKE_C_COMPILER=x86_64-w64-mingw32-clang
-DCMAKE_CXX_COMPILER=x86_64-w64-mingw32-clang++
-DCMAKE_RC_COMPILER=x86_64-w64-mingw32-windres -DCMAKE_BUILD_TYPE=Release`
then `cmake --build build --target sunrise-server -- -j 8`.
Toolchain: `~/Downloads/sunrise-stage/llvm-mingw/bin`, cmake at
`/opt/homebrew/bin`. Wine: GPTK, `/Applications/Game Porting Toolkit.app/
Contents/Resources/wine/bin/wine64`.

## THE BOOT BRIEF - what this boot is actually asking

ONE client, the Mac, into the Tower.
Success is named by the CLIENT's own string pool, not by our logs:
  - `activity_host_changed: instance=...` flips off `PRIVATE CURRENT`
  - `ah-sid=` stops being blank
  - `public AH instance ready` appears
Server side, expect `ev=activity stage=bind result=public_target` (I added that
line) and then exactly ONE membership push on that link.
It does NOT test two guardians seeing each other - that needs the second client
and probably more. One client first, because the admission path still aliases
two peers onto one session record (20.29 §3).
Pre-named negative: if the client never sends a second join at all, the
descriptor contract is wrong, not the binding - go back to 20.28's ladder.
GRAPHICS DELTA: zero. No equipped item changes.
Watch `ev=gameplay stage=activityhost ... held=N` - cap is 8 of a 16-slot
table; if it climbs, stop.

## ONE OPEN QUESTION I DID NOT SETTLE
Can the standalone server regenerate `build_data.bin` at a new cache format
version? It blocks any future full merge. Task, not urgent, cheap to answer.
