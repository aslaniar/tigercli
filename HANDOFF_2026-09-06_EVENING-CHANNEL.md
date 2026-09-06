# HANDOFF 2026-09-06 (EVENING) — THE CHANNEL FIX + THE INSTRUMENT FREEZE, FOR CLAUDE CODE

STATUS: live (2026-09-06 ~15:10 PDT). Written under the user's "bank everything"
directive. Read STATE.md first; this file banks the evening's front progress,
the four instrument defects (all mine), and the EXACT next moves. Companion:
docs/postmortems/POSTMORTEM_2026-09-06_THE-BLIND-GUARD.md (all four defects,
R1-R8); FRONT_peer-render-chain.md (the pinned chart, current).

## THE ONE-PARAGRAPH STATE OF THE WORLD

The session-binding front (FRONT_peer-render-chain row 5) moved further tonight
than in the prior week, and every step is measured. THE CHAIN NOW VERIFIED:
(1) the relayed join must arrive on the association whose client-side
connection object holds the bound session containers — the ENGINE association,
not dtls (the join gate walks [ctx+0x28] of the packet's OWN connection,
disasm-verified 0x1416E0460; the fix = relayJoinEngineChannel=true, SHIPPED,
wire-proven channel=engine); (2) with the channel fixed, the gate's LOOKUP
MATCHES — key=forkSession vs blob=forkSession, match=1, on the gate chain,
measured TWICE (p2-193a/b, client 572ca7c2fc02ada3); (3) the gate STILL
refused — the found-path carries a SECOND check the decode had missed:
[found_slot+0x1AEF8] must be in {6,7,8,9} (the session-state window; 6 = LIVE
HOSTED) or the SAME "unknown session" refusal text fires (the join gate's
disasm, read line-by-line tonight); (4) the remaining ambiguity — the matched
slot's +0x1AEF8 value contradicts the sessstate probe's state=6 reading — is
ONE instrument from resolution: a leave-probe on the walker.

## THE CURRENT MESS I AM HANDING OVER (own it, do not repeat it)

The LAST TWO builds broke the mac's landing (3d95a375dc164972 and
d5ed2ae3f12e42fb both: "won't load into the tower"), while 0687f90187e3dd97
(the build the user called "you fucked up") DID let the mac land (the rig
froze on it instead). The mac currently has 572ca7c2fc02ada3 restored (the
proven-landing build, backup .bak_d5ed2ae3_150906 holds d5ed2ae3); the rig is
on d5ed2ae3f12e42fb with backups .bak_p2d7_20260906_144204 (5313eb03) and
.bak_p2d7_20260906_150906-era rows. THE BISECTION THE NEXT SESSION MUST RUN
FIRST (one boot or two): deploy 572ca7c2 on BOTH (the proven-landing pair),
confirm both machines land; then bisect 3d95a375's delta — the SUSPECT is the
leave-probe routing change (emit_walkleave via the walk_map row's leave
dispatch on 3d95a375+ vs the walk_leave SECOND ROW on 0687f, which the mac
landed on). The leave-probe's own dedup loop (a 16-entry linear scan on a hot
path called from 35 consumers, possibly multi-threaded) and the
sesscmp_reset_seen's global g_sessCmpEmits.store(0) are the two new hot-path
behaviors the failing builds introduced and 0687f did not have (0687f's leave
ran as its own row).

## THE FOUR INSTRUMENT DEFECTS OF 2026-09-06 (all mine, all documented)

1. emit_sesscmp's qword-alignment guard refused the gate's own misaligned blob
   pointers for ~5 boots (THE BLIND-GUARD postmortem DEFECT 1; fixed p2-190c).
2. the XOR-of-fields novelty hash erased every MATCH (DEFECT 2; fixed 9cd3f23b,
   then hardened d5ed2ae3 — the synthetic collision arm caught key=all-ones).
3. the walk_leave second target row on the same RVA = dual detours = the rig
   frozen at the loading loop (DEFECT 4; fixed 3d95a375 — leave routed onto the
   walk_map row's leave dispatch, 64 targets).
4. the state reads added to emit_walkmap's hot path stalled the mac's landing
   (DEFECT 5; reverted hot path, states moved behind the change gate,
   d5ed2ae3f12e42fb) — and the mac STILL won't land on it, so there is an
   UNRESOLVED 5th defect in the 3d95a375/d5ed2ae3 lineage (see the bisect
   above). FOUR SHIPPED INSTRUMENT DEFECTS IN ONE SESSION: every one was an
   instrument change made under boot pressure without its negative test. The
   closing lesson in the postmortem stands: instrument changes need the same
   gates as shipped code.

## WHAT IS BANKED AND PROVEN (do not re-derive)

- THE CHANNEL FIX: relay_join_engine_channel=true (settings,
  .bak_p2-192_dtls) — the relayed join delivered on the ENGINE association,
  channel=engine logged, server acbb62af4a3ca133. The join gate walks
  [ctx+0x28] of the packet's own connection (disasm-verified: mov
  rcx,[rdi+0x28] at 0x1416E04A4 before call 0x14177A0B0 at 0x1416E04AC).
- THE MATCH: on the engine channel the relayed join's key (the verbatim fork
  sessionId) MATCHED a walked slot's blob twice (client 572ca7c2, the p2-193a/b
  boots; the gate-chain +0x57C site 0x17944FA).
- THE SECOND CHECK: [found_slot+0x1AEF8] must be 6..9 (the join gate's disasm,
  tonight: 0x1416E04B6 add ecx,-6 / cmp ecx,3 / ja 0x1416E04D7 — the SAME
  refuse block as not-found, hence the identical "unknown session" text).
- THE STATE PROBE'S AMBIGUITY: the sessstate instrument (change-gated, early
  boot) read slot objects 0x45A2C18 (st=6 sid=0), 0x4631748 (st=0 sid=-1),
  0x45DBD60 (st=6 sid=1); the extended walk_map's +0x1AEF8 reads on the
  landing walk AGREED (st0=6 st2=6). The contradiction stands: match + state=6
  + join_processor calls=0 (hooked at 0x17806C0 = the gate's found-path callee,
  verified same function).
- THE WALKER'S CONSUMER MAP: 35 callers, all in the connection-layer receive
  region (0x1416CD300..0x1416E13DA) + 0x14175B8F0; the receive pump climbs into
  the VMP ring (0x140B5xxxx) — the framing/reachability question ends there.
- the binders bind slot objects' [+0x1C7C0] via the init-time context manager
  (0x14175E520) + the VMP ring; container objects are per-connection and can
  differ between the client's associations.

## THE NEXT STEPS (in order)

1. BISECT THE MAC'S LANDING FAILURE: restore 572ca7c2fc02ada3 on BOTH machines
   (the mac already has it; the rig needs its equivalent backup restored or a
   redeploy), confirm both land. THEN rebuild the walk-return instrument ONE
   CHANGE AT A TIME, each with its negative test (R1-R8 are in ENFORCEMENT.md
   and the postmortem) and a LANDING VERIFICATION before deploying: the probe
   cost on the walker's hot path is the suspect - do the first test WITHOUT
   any walk_map change (the leave-probe alone, on its own row is PROVEN
   dangerous; the walk_map-row routing is SUSPECT - try the leave emission
   budgeted to the join-packet window only, or attribute via femu instead).
2. THE WALK-RETURN READOUT (the last instrument the front needs): the walker's
   leave = (ret slot ptr | 0=MISS, [+ret+0x1C7C0] bind, [+ret+0x1AEF8] state,
   outcome=MISS/FOUND-LIVE/FOUND-STATE-OUT). Implemented in
   emit_walkleave (3d95a375dc164972 and later) but NOT YET VERIFIED SAFE for
   the mac's landing - that verification is step 1.
3. WITH THE OUTCOME: MISS -> the gate's walk uses a different container than
   the rich one (attribute via the container-id log lines, now live);
   FOUND-LIVE -> the refusal comes from deeper (the processor's own validation
   - decode 0x1417806C0's body); FOUND-STATE-OUT -> the fork-side fix is
   making the forkSession-named session reach state 6+ (the session machinery
   progression - p2-182 proved sessions reach 6 organically).
4. THE CHART: rows 1-4 DONE/RUNNING; row 5 = two of three checks pass. Do not
   re-walk: the value arms (all refused against the empty dtls container),
   the stamp-timing theory (retracted), the connect-family re-decode (pure
   transport), the parameters road (closed), the +0x818/+0x38 hunts (dead).

## THE TOOLING DEBT (for the fix session, from tonight)

- loggrep.sh: not executable + GNU-stat flags on macOS - unusable; sgrep.sh is
  the standing path.
- reset_lobby_claims.sh: fired its pre-registered defect TWICE tonight (executed
  as python, SyntaxError); the manual pkill + mac-port/launch-server-macos.sh
  path was used; its real-restart path is STILL untested.
- callgraph.py: `callgraph.py --callers-of X` (without the `query` subcommand)
  dumps the whole doc and exits 1 - needs a usage line.
- hook_targets.py / verify_hook_rvas.py: verified table arithmetic but did NOT
  flag the duplicate-RVA rows (the freeze) - add the duplicate-RVA reject.
- /usr/bin/bash does not exist on this mac (zsh host) - background watchers
  must not hardcode it.
- emit_walkmap's silent early-returns (unreadable slots) hid the relayed
  join's walk twice - the first-reject markers now exist (3d95a375+) but the
  whole walk_map/leave layer needs the R1-R8 audit on a workflow session.
- THE SESSION'S OWN PROCESS DEBT: four instrument iterations shipped under
  boot pressure, each breaking a different invariant of the same function;
  U7 (escalate after 2 failures) was violated in spirit for hours. The next
  session must verify instrument changes with femu/replay and cost checks
  BEFORE touching the user's machines.

## THE USER-FACING RULE THIS SESSION EARNED (verbatim)

"the dog doesn't clean up its own mess" - when an instrument change breaks a
client, the immediate response is RESTORE THE USER'S PLAYABLE STATE FIRST and
bank the debugging for a session with the proper gates - not a fourth live
iteration. This handoff exists because that rule got its teeth tonight.
