# BOOT_BRIEF_p2-190 — RETARGET ARM 3: THE RELAYED JOIN NAMES THE RECIPIENT'S OWN JOINID
STATUS: live (2026-09-06).
FRONT: session-lookup-identity

INSTRUMENTS + FIX, ONE CONTRACT: the relayed join is retargeted (arm 3) so its
sessionId equals the RECIPIENT's CURRENT JOINID — the first arm whose key value
is PROVEN inside the gate's walked records on BOTH machines (p2-189: binder2's
stack args = the machine's own joinId, byte-exact vs each admit line; binder ctx
pointers = walk_map's walked slots; cof_soid granted that key index 2; p2-187
census: key=joinId vs blob=joinId, match=1). The client ships ONLY the
instrument fix that makes the boot's own readout alive (the per-caller sesscmp
budget), no behavior change.

## INSTRUMENTS (declared; literals pre-checked in the DEPLOYED binaries)
- sess_cmp per-caller budget: literal "budget_exhausted" (deploy_client_dll.sh literal ok, BOTH machines).
- walk_map tag alignment: literal "stage=walk_map" (deploy_client_dll.sh literal ok, BOTH machines).
- preflight --record: manifest written; deployed==built 617841ee43bd7a37 (clients) / 7164333c337cd674 (server).

## MODEL REVIEW (REQUIRED - session-lookup-identity carries third-branches)
BANKED (p2-187 brief, carried): the dead assumption was that the state's idB
flows into the live blob via the membership machinery — it does not; the live
writer is the session-to-connection binding path. THIS BOOT'S additional dead
assumption (banked, HANDOFF_INSTRUMENT-WIDTH + the p2-189 close): that the
gate's walked slots hold the RECIPIENT's OWN joinId-named session — this was
MEASURED (binder2/walk_map/cof_soid, both machines), not assumed; the arm-3
value follows from that measurement, which is why this is not "a retarget value
by assumption" (the STATE dead-rule).

## PRIOR ART (required field)
q.sh terms: arm3 / peer_join_id / walk_map / binder2 / cof_soid / joinId.
Read in full: connection-layer-join-delivery.md (the CONSEQUENCE section +
binder decode); FRONT_peer-render-chain.md row 5 + "current blocker";
HANDOFF_2026-09-06_SESSION-BINDING.md; HANDOFF_2026-09-06_INSTRUMENT-WIDTH.md
(the instrument spec + per-caller sub-budget note); p2-188b + p2-189 captures.
Verdicts: arm 1 REFUTED by measurement (p2-188b - the gate refused the machine
id, join processor never ran); the connect-family handlers DECODED pure
transport (20.320, do not re-decode); the parameters road CLOSED (20.319).
None of this boot's terms is a re-opened closed front.

## PURPOSE (ONE CONTRACT)
Does the relayed join, retargeted to the recipient's current joinId, PASS the
connection-layer join gate's session lookup (refusal absent -> join_processor
runs)? If it does not, the refusal-walk readout (alive per the replay
acceptance) names the gate's walked container directly and decides the next
arm without another value-arming boot.

## THE CHANGE
- server 7164333c337cd674: relayJoinTargetIdentity now selects the recipient's
  OWN joinId (peer_join_id, recorded per endpoint from each client's own join
  at answer_join, before admission; arm 1's peer_machine_id accessor REMOVED —
  dead code). Rewrite machinery unchanged (wire-proven p2-188b: the client's
  refusal NAMED the retargeted value). settings.json
  relay_join_target_identity=true (backup settings.json.bak_p2-190_arm3).
  Log field renamed machine= -> retarget= (it is no longer a machine id).
- clients BOTH 617841ee43bd7a37: sesscmp per-caller sub-budgets (12 slots x 16
  triples, per-caller first-seen pair cache + one budget_exhausted marker per
  caller) replacing the flat 64-triple budget that the landing drained before
  the relayed join (p2-189's one instrument defect); stage tag aligned
  walkmap -> walk_map. Hook count UNCHANGED 64/64 (verify_hook_rvas PASS 112
  RVAs 0 bad; 11 not-code data addresses incl. kEqHelperRva - the banked gap).
- No behavior change in the clients: read-only observers.

## READOUT TRIGGER (required field)
- the refusal line ("join-request ... unknown session ... refusal"): PRIOR-LOG
  CITE p2-187/p2-188b/p2-189 (fires on every value-arm failure; its session
  field renders as two reversed dword groups - decode before comparing).
- stage=join_relay_target retarget=<joinId> result=sent: PRIOR-LOG CITE
  p2-188b (the retarget applied end-to-end); arm 3 = new VALUE, same machinery.
- stage=join_processor enter FROM A RELAYED JOIN: NEVER-OBSERVED (measured
  never-ran in p2-188b/189) - its first firing IS the event.
- stage=join_reserve (0x14178EA73 caller, not the self-reserve sites), stage=
  admit from the join-handler caller: NEVER-OBSERVED for a relayed join.
- stage=sesscmp per-caller triples AT the refusal window: the gate's own
  comparisons - the p2-189 gap, now budgeted alive (see acceptance below).
- stage=budget_exhausted: NEVER-OBSERVED (emits only on a caller's 16th+1 new
  pair; ABSENCE is the expected case and is explained, not a null result).

## PRE-NAMED OUTCOMES
  (a) refusal ABSENT + join_processor enter + reserve/admit fire from the
      join-handler caller -> THE BLOCKER FALLS: the join flow runs; watch the
      adoption chain (resv mask gains the container bit, records leave (3,4),
      ladder (4,5)) as row 6-8 evidence. Front moves to establishment.
  (b) refusal PRESENT but NAMES the recipient's joinId + walk_map captured at
      the refusal + sesscmp gate-caller triples at that window -> the retarget
      landed but the walked slots still don't hold that value at refusal time:
      the triples' blob set IS the container readout; decide arm 2 (the real
      account key) vs the binding decode from the same capture. NO new value
      boot without reading these triples.
  (c) refusal PRESENT and sesscmp emits NO gate-caller triples in the refusal
      window despite budget alive -> the walk never reached the compare
      (version gate regression or walker-not-on-path) -> re-derive the gate,
      do NOT re-arm values.
  (d) NO join_relay_target result=sent (all verbatim, or retarget=0) -> the
      relay fired BEFORE the recipient's own join was recorded (ordering) ->
      the fix is server-side sequencing, not a new arm. Readout void until a
      retarget=sent line exists.

## ABANDON OUTCOME (empty-mask #7)
If arm 3 is refused (b) AND the refusal-walk triples show the walked blobs are
only {0, the machine's own joinId, the machine's own account key} with no
peer-naming form in any walked slot, the binding is not populated by ANY wire
message we currently deliver: the road narrows to the landing-session blob
writer (the copier walk 0x1416E2350, the open site; the session-apply is
excluded by apply_stamp) as the last publisher candidate. No further value
arms, no binder retries.

## EFFECT CLAIM (empty-mask #5)
The join gate PASSES for a relayed join for the first time in the project
(row 5's blocker). Not a cosmetic log effect: join_processor running is the
precondition for rows 6-10 (reserve/admit/adoption/ladder/guard/entity).

## STATE READERS (empty-mask #1)
- the game's own verdict: the refusal line (greppable every boot).
- the retarget: join_relay_target result=sent retarget=<value> (DIRECT).
- the walked container: walk_map (six [+0x1C7C0] binds + key, DIRECT).
- the gate's own comparisons: sesscmp triples at the refusal window, gated by
  caller rva (DIRECT, budget alive).

## FIX SURFACE: server
The fix IS server-side (the retarget value + setting). No client behavior
change exists to excuse; the client build is instrument-only (the
SERVER-SIDE GAP rule: the missing wire item arm 3 publishes is the joinId
form under which the recipient's own binding names its session - now
delivered by rewrite, not a new message).

## WIDE NET
joincapture / stage=join result=admit|completed / join_relay +
join_relay_target / join_type0a + pktdump / inst_nonce / walk_map / binder1 /
binder2 / cof_index / cof_soid / apply_stamp / sesscmp (per-caller) /
join_processor / join_reserve / admit / resv / sess_state / add_candidates /
bootflow / the refusal line / stage=identity.

## INPUT GATE (hard rule)
Do not read gate-side lines before the server's join_relay_target shows
result=sent retarget=<non-zero> for the relayed join.

## OBSERVER BUDGET / CALL FREQUENCY
- sesscmp: 16 triples PER caller rva (12 slots) + 1 budget_exhausted marker
  per caller; global hard bound 192. The p2-189 replay of the new gate over
  the recorded candidates: 9 distinct triples (vs 64 flat emissions), and at
  BOTH walk_map markers every caller had 11-14 triples left - the refusal
  window's readout survives the landing's noise.
- every other target: unchanged from p2-189.

## HOOK COUNT: 64 (unchanged; hook_targets declares=64 initializers=64)
## INSTRUMENT SOURCES: RE_build/Sunrise-fork-inventory/Sunrise/src/client/hooks/milestone_trace/milestone_trace_observer.cpp
## INSTRUMENT LIVENESS
- "sess_cmp" attach lines in BOTH clients (unchanged name).
- "walk_map" (the NEW tag) present; the OLD tag "walkmap" ABSENT from the
  client logs (absence = the new build is live; presence = stale build).
- "budget_exhausted" ABSENT is expected (never-observed marker; explained).

## FALSIFIABLE CLAIM
With the relay retargeting ON and both links up: the relayed join either (i)
is NOT refused (join_processor enter fires - hypothesis), or (ii) IS refused
with the refusal line naming the RECIPIENT's joinId (retarget= value) while
walk_map + at least one gate-caller sesscmp triple emit in the refusal window
on at least one machine. REFUTED if the refusal names any OTHER value than the
retarget= line's (the rewrite did not ride the wire -> re-derive the relay),
or if walk_map is absent while join_type0a fires (the walker not on the
relayed join's path -> the gate decode gets re-derived).

## ABSENCE NEGATIVES (both kinds)
- zero join_relay_target result=sent lines: the retarget never happened
  (ordering/membership gap, outcome (d)) - the gate-side readout is VOID.
- zero refusal AND zero join_processor with join_type0a firing: the join body
  died before the gate (framing/transport) - the p2-183(b) class, re-check
  framing before touching anything else.

## GRAPHICS DELTA (U12)
None. No graphics-affecting change. KNOWN RISK (banked, not attributed): the
mac's parked co-presence render-black (client alive, no fade_release in
segment 2) recurs intermittently; the rig spawned fine on the identical
build at p2-189. If the mac render-blacks this boot, the readout is taken
from the RIG's log and the boot is not voided.

## SETUP
- server: deployed 7164333c337cd674, RELAUNCHED (transport listen ok port
  30975, UDP 30976/3074/3075 bound, TCP 8443/8099; reset_lobby_claims --check
  = healthy no-op, claims=0). Launch: nohup bash mac-port/launch-server-macos.sh
  (from the repo root; the first relaunch failed - the mac was off ethernet;
  restored).
- clients: BOTH deployed 617841ee43bd7a37 (mac bak_p2d7_20260906_112558; rig
  bak_p2d7_20260906_112733); preflight PASS 13/0/0 (manifest recorded).
- rollback: settings .bak_p2-190_arm3; client .bak_p2d7_20260906_*; server
  .bak_p2d6_20260906_111620.

## CHAIN MARKS (L16 - evidence mark per link)
- fork publishes the peer; both clients land + hold the row: VERIFIED-BY-EXECUTION (p2-180).
- live hosted session exists (state 6, sids 0/1, both machines): VERIFIED-BY-EXECUTION (p2-182).
- join delivery on the connection layer + version gate passes: VERIFIED-BY-EXECUTION (p2-183/p2-184).
- identity published hash-valid at +152: VERIFIED-BY-EXECUTION (p2-186).
- the lookup's one-qword compare measured live: VERIFIED-BY-EXECUTION (p2-187).
- the retarget machinery rides the wire end-to-end: VERIFIED-BY-EXECUTION (p2-188b - the refusal named the retargeted value).
- the gate's walked slots bound to small-index sessions, one NAMED BY THE RECIPIENT'S OWN JOINID: VERIFIED-BY-EXECUTION (p2-189: walk_map/binder2/cof_soid, both machines).
- arm 3's key = the recipient's current joinId: VERIFIED-BY-READING (connection-layer-join-delivery.md CONSEQUENCE + p2-189).
- this boot proves: the relayed join's retargeted key MATCHES a walked slot -> the lookup passes. NOT YET (this boot).

## DEAD-END AUDIT (prior art cites closed findings - the escape check)
- arm 1 (the join machine id): CLOSED BY MEASUREMENT p2-188b - the gate refused it, the join processor never ran. This boot does NOT re-test it; its accessor is deleted. Escape: the arm-history comments name it refuted.
- the connect-family handlers (OOB ids 5/6/7/9): DECODED PURE TRANSPORT 20.320 - no session binding rides it; OOB id 8 is default-dropped. This boot does not re-decode; the binder decode (p2-189) superseded the "next decode" pointer.
- the parameters road (OOB id 38): CLOSED 20.319 - the client's OOB receive switch silently drops it. Not touched.
- the SESSION-plane join delivery: RETRACTED 20.182 (the relay delivered to the wrong layer). Not touched.
The prior-art citations are cited as CLOSED PREMISES this boot builds PAST, not roads to re-walk; each has a measured refutation recorded in FINDINGS/claims.

## ADVERSARIAL PASS: ses_f882ff186ffeIGc0ofsy65C5k1
The retarget MACHINERY is wire-proven (p2-188b: the client's refusal named the
retargeted value - the rewrite rode the wire end-to-end); this boot changes
only the VALUE source (peer_join_id) and the instrument's budget shape. The
sesscmp change was replay-accepted BEFORE deploy over the p2-189 capture
(replay_trigger, fixture sesscmp_percaller_budget.py: fires>0, both callers
visible, per-caller cap binds, budget alive at both walk_map markers). The
hook set is verifier-passed (112 RVAs, 0 bad, 64/64 table). The one
un-replayed surface: the server's peer_join_id recording ORDER (identity is
recorded at answer_join before admission - if a peer's own join is missed,
its relayed copy falls back to VERBATIM, which is outcome (d), loud on the
wire, not silent).

## DO NOT
- re-decode the connect-family handlers (pure transport, 20.320).
- re-arm arm 1 (the join machine id - refuted p2-188b).
- spend a boot on any value arm not named by the refusal-walk triples.
- read any gate-side line before join_relay_target result=sent.
- sleep in shell chains (background + notify).
