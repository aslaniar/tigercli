# BOOT_BRIEF_p2-188 — THE JOIN LOOKUP RETARGET, ARM 1 (the relayed join's sessionId = the recipient's join machine id)
STATUS: live (2026-09-06).
FRONT: session-lookup-identity

INSTRUMENTS: none new. Clients UNCHANGED (a3e75d564ed58832, 58/58, preflight
PASS 13/0/0 — sess_cmp/join_type0a/join_processor/sess_state/inst_nonce all
live). The change this boot measures is SERVER BEHAVIOR, not a probe.

## MODEL REVIEW (REQUIRED - the front carries 2 third-branches: p2-185, p2-186)
THE CAUSAL ASSUMPTION THAT DIES (banked, p2-187 brief): the state's idB flows
into the live blob via the membership machinery — it does not; the live writer
is the session-to-connection binding path. THIS BOOT DOES NOT re-assert that
assumption: it stops predicting the live blob and instead CHANGES THE VALUE THE
RELAYED JOIN CARRIES, so the lookup's outcome is measured directly against
whatever the slots hold. The arm (join machine id) is pre-named as arm 1 of
two; arm 2 (the real account key) is named in the setting's comment and the
boot's readout decides — no third prediction is patched onto this mechanism.

## PRIOR ART (required field)
q.sh terms: join_relay_target / sess_cmp / 0x14177A0B0 / refusal. Read in
full: connection-layer-join-delivery.md (20.319 section: the registry, the OOB
switch id map, the gate walk, the identity-form distinction, the refusal
timing), p2-187's archive (the refusal line + the sesscmp pairs), STATE NEXT
items 1-4. The retarget's bit offset (109) is byte-verified vs the p2-182
admit decode and fixture-replayed (only the 64 sessionId bits change).

## PURPOSE (ONE CONTRACT)
Turn the relayed join's "unknown session" refusal into a lookup match — or
produce the pair evidence that names the slot blobs' real arm. ONE change:
relay_join_target_identity=true on the server; the clients' instruments read
the consequence.

## THE CHANGE
- server: NEW build (the 20.319 source: PeerMachineId table +
  remember_machine_id at answer_join + rewrite_join_session_id + the
  per-target relay loop). Settings: relay_join_target_identity=true added to
  the server's settings.json (all other keys unchanged from af414e390a97808b:
  relay_peer_join=true, duty 30000, retry_cap=10, transport_identity=true,
  profile=true, world_population=true, self_peer_row=false, sweep=false).
- clients BOTH: UNCHANGED (a3e75d564ed58832; no rebuild, no redeploy).
- The hook set is untouched: verify_hook_rvas state carries over; preflight
  --record re-run after the server deploy (server hash changes).

## READOUT TRIGGER (required field)
- stage=join_relay_target: NEVER-OBSERVED (new server line) — its appearance
  (result=sent, machine=<target's id>) IS the retarget running. result=verbatim
  reason=parse means the rewrite refused — a defect, not an outcome.
- The greppable verdict: the mac's client line
  "networking:messages:join-request: received message for an unknown session"
  — for the RELAYED copy, its session field names the RETARGET value now.
  Absence of the refusal for the relayed join = the lookup matched.
- sess_cmp: novelty-gated as deployed; NEW (key,blob) pairs after the relay are
  the lookup's live sides (the instrument's budget: 24 pairs, as p2-187).

## PRE-NAMED OUTCOMES
  (a) NO refusal line for the relayed copy + join_processor fires on the mac
      (the relayed join's recipient) -> THE ARM WORKS: the join flow enters the
      processor; rows 6-7 (reserve/admit, ladder) are next.
  (b) refusal again, and the refused session field reads the RECIPIENT'S JOIN
      MACHINE ID -> the recipient's gate slots do not hold its own join id
      either. Arm 2 (the real account key) is next; the sesscmp pairs log which
      blob values the walk saw.
  (c) refusal still names the FORK's sessionId -> the retarget did not apply
      (setting unparsed / no recorded id / parse-fail fallback). Read
      stage=join_relay_target: absent = the setting or the id table; present
      result=verbatim reason=parse = the captured container failed validation.
  (d) refusal gone but join_processor never fires -> the lookup matched and the
      processor's own gates refused (capacity [pkt+8], flags [pkt+4], state
      6..9) — decode the processor's gates next; the retarget arm is vindicated.

## ABANDON OUTCOME (empty-mask #7)
If (b) reproduces with join_relay_target=sent, arm 1 is dead: revert the
setting to false (byte-verbatim relay restored, no rebuild needed) and decode
the connect-family handlers (ids 5/6/7/9) — the binding publisher — before
arm 2. No retries of arm 1.

## EFFECT CLAIM (empty-mask #5)
The relayed join names a value the RECIPIENT's own gate can match. The
measurable effect: the "unknown session" refusal for the relayed copy
disappears (or its named session changes to the retarget value — outcome (b)).

## STATE READERS (empty-mask #1)
- the relay's per-target behavior: DIRECT = stage=join_relay_target
  (result/machine) + stage=join_relay (retargeted=N).
- the recipient's gate outcome: DIRECT = the mac's client refusal line
  (absence is the positive signal) + join_processor/admit lines.
- the lookup's comparisons: DIRECT = sess_cmp (novelty-gated) — with the
  caller-discriminating upgrade NOT shipped this boot (clients unchanged);
  the pairs still distinguish arms by their VALUES.

## FIX SURFACE: server
The relay's per-recipient copy only. No client change. SERVER-SIDE GAP: the
retarget value's arm is open (join id vs account key) — this boot measures
arm 1; the p2-186 identity publishing stays.

## WIDE NET
joincapture / stage=identity (machine= decoded per join) / stage=join
result=admit / join_relay + join_relay_target (server) / join_type0a +
pktdump / sess_cmp / join_processor / admit / resv / sess_state / bootflow /
the refusal line on BOTH clients.

## INPUT GATE (hard rule)
Do not read any client-side join lines before stage=join_relay
result=sent appears in the server log — a relay that never sent proves
nothing about the gate.

## OBSERVER BUDGET / CALL FREQUENCY
unchanged from p2-187 (the client build is untouched): sess_cmp 24 distinct
pairs; the server lines fire per join (a handful per boot).

## HOOK COUNT: 58 (unchanged; verify_hook_rvas state carries over)
## INSTRUMENT SOURCES: RE_build/Sunrise-fork-inventory/Sunrise/src/client/hooks/milestone_trace/milestone_trace_observer.cpp
## INSTRUMENT LIVENESS
the p2-187 liveness test carries: sess_cmp/inst_nonce/join_processor/
sess_state names must appear in BOTH clients' attach lines (unchanged build).

## CHAIN MARKS (L16)
  L1-L7 as banked (p2-180..184: landing, transition, identity, candidates,
       OOB delivery, nonce gate)
  L8 the session lookup matches             THIS BOOT (the retarget, arm 1)
  L9 the ladder climbs to (4,5)             unknown
  L10 guard/receiver/codec/entity/render    unknown

## FALSIFIABLE CLAIM
With relay_join_target_identity=true and both links up: after the second
client's join is admitted (stage=join result=admit) and relayed, the mac's
log contains NO "unknown session ... refusal" line whose session field equals
the RETARGET value logged by stage=join_relay_target — i.e. the relayed copy
is either accepted or refused under a DIFFERENT named session. REFUTED if a
refusal appears naming the fork's own sessionId again (outcome (c): the
retarget never applied).

## ABSENCE NEGATIVES (both kinds)
- zero stage=join_relay_target lines with join_relay result=sent: the setting
  did not reach the server (parse) or both targets had no recorded id — the
  relay's own lines name which (retargeted=0 with peers=1 = no id recorded).
- zero NEW sesscmp pairs on the mac with the relay delivered: the gate's walk
  compared only pre-seen (key,blob) pairs — the refusal/no-refusal verdict
  still stands via the refusal line itself (the greppable outcome).

## GRAPHICS DELTA (U12)
Expected new rendered models: 0 (server-side message content only; the
clients' binaries are byte-identical to p2-187's).

## SETUP
  1. Server: NEW build deployed; settings relay_join_target_identity=true;
     claims cleared; launched from the REPO ROOT, backgrounded.
  2. Clients BOTH: unchanged (a3e75d564ed58832); rig ssh control socket up.
  3. Both clients land; NO in-game actions.
  4. Wait for both joins admitted + the relay; capture per boot_record.

## ADVERSARIAL PASS
- The retarget preserves the container's framing bit-exact (fixture replay
  proved: only the 64 sessionId bits differ from the verbatim bytes).
- The client build is UNCHANGED — no hook risk, no new RVAs, no verify run
  needed beyond preflight's carry-over check.
- The refusal line's session field is printed by the client in reversed
  byte groups ("1B1A9EEC:4822430D" = the fork's sessionId) — readouts must
  decode that form before comparing it to the retarget value.
- The mac's join decode failed in p2-187 (identity result=absent) — if that
  recurs, the MAC's id may be missing from the table and the relay to the
  rig falls back verbatim while the relay TO the mac still retargets (the
  rig's id decoded fine in p2-187). Both directions' lines are read
  separately.

## DO NOT
  - do not read machinery lines before join_relay result=sent (input gate)
  - do not touch the client binaries (the client is never modified)
  - do not launch the server from anywhere but the repo root
  - do not flip arm 2 mid-boot; one arm per boot (U10)
  - NO SLEEP in shell chains (background + notify)
