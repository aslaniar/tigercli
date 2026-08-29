# HANDOFF 2026-08-28 EVENING - THE GATE REVIEW (for Claude Code)

STATUS: superseded-by FINDINGS 20.153 (2026-08-28 ~21:3x). The REVIEW WAS DONE and its
answer retracts this document's CURRENT LEAD: the peer-properties asymmetry is a misread
of whose steamid each `peer-properties accepted` line names (every one names that
machine's OWN peer #0), and the mac's "world never instantiates" is not what the logs
say - both clients ran the identical ladder and both stall at the PUBLIC slice-set switch.
The relay IS absent but symmetrically, and is not the blocker. STILL VALID HERE: the
DEPLOYED STATE, ENVIRONMENTAL and TOOLING STATE sections. Original status line follows.

ORIGINAL STATUS: live (2026-08-28 ~22:0x). Continues HANDOFF_2026-08-28_L9-RENDER.md (render
milestone still open). This is the review handoff: a fresh reviewer is asked to
audit today's chain and the current lead. Read with FINDINGS 20.145-20.152
(newest-first in FINDINGS_2026-08-25.md; NOTE 20.150 is double-assigned - bapdecode
entry + gate entry renumbered 20.151; walk both).

## WHERE THE MILESTONE STANDS (one paragraph)
Two clients are CO-LOCATED in one shared public Tower instance - proven at the session
layer (same group target id both sides, `players valid: 0x3`, peer channels established
both ways). The RIG renders in the shared Tower. The MAC renders its solo Tower, then
its citizen join into the shared instance succeeds at the session layer (EST-Y on the
public row, membership acked, Tower precached) but the world never instantiates: it
waits forever at `Waiting for managed-session-start for all peers` - black screen,
menus alive. Three static lanes + two switch-gated experiments today mapped the gate
and its neighborhood; the current lead is the PEER-PROPERTIES / WORLD-START RELAY (below).

## TODAY'S CHAIN (each step verified; walk FINDINGS 20.145-20.152 for detail)
- 20.145: the appearance/profile block in player rows is an opaque self-hashed ~396B
  blob; cannot be authored, only replayed. Capture route prepped (runbook:
  RE_output/claims/route-b-fireteam-runbook.md; instrument: RE_scripts/capture_bap30975.sh;
  decoder: RE_scripts/bapdecode.py, registered in TOOLS.md).
- 20.146-20.147: the rig's join failures decoded - region-56 record WAS on the wire
  (224/224 bodies); the defect was the rig's own region never reaching 56 after churn.
- 20.148/20.149: p2(90) fixed it (region seed on session re-creation) - co-location
  achieved, rig clean, mac stalls at the gate.
- 20.150/20.151 (gate lane): the gate is the world controller's per-peer activity-setup
  wait, machine-id-keyed (fn 0x140C17E40, scan 0x140C17FCD, stride 288). The 4-bit state
  ladder is wire-fed and satisfied - NOT the lever.
- 20.152 (map lane + two experiments): member fields 11/12 ARE the setup-complete flags
  (client descriptor 0x141ca68e0; record bytes +181/+183 - the +0xED/+0xEF readers use a
  different base). Experiments p2(91) all-rows=1 and p2(92) all-except-self=1 BOTH broke
  the mac's citizen join ('session disappeared', retry loop); switch-off restored it both
  times. OVERRIDING FACT: the rig crossed the gate with ZERO flags - the flags are not
  the gate's lever.

## THE CURRENT LEAD (what the reviewer should scrutinize first)
The p2(90) differential: the rig RECEIVED the mac's world-start status ('fireteam req.
peer update ... peer-properties accepted, map status=_precached, progress=100') and
rendered; the mac NEVER accepted the rig's status (its last world line: the peer fixup
'Could not find tracking data for peer 1 ... adding it to fixup' in its private session,
then silence). Hypothesis: the mac's gate waits on the RIG'S world-start status arriving
through the managed session's peer-properties relay - and our server's group host
(server/gameplay/group/group_host.cpp) may not RELAY client-sent peer-properties between
members of the shared session at all (it composes its own server-authoritative
snapshots; client->client relay is unverified). REVIEW QUESTIONS:
1. Does the fork's group host relay client-sent peer-properties/world-start updates to
   other members? If not, where must the relay be built, and is the p2(90) rig-render
   consistent with it (the rig may have crossed via a timeout path the mac misses)?
2. Is the flags conclusion (20.152) sound - i.e. could the flags still matter post-relay?
3. The p2(90) rig-vs-mac post-precache flows deserve a line-by-line diff
   (mac: Game/bin/x64/Sunrise/logs/sunrise.log vs rig copy - rig logs need ssh fetch:
   ssh over ~/.ssh/cm-rig ControlPath, host rasla@192.168.1.136, log at
   'C:\Users\rasla\Downloads\destiny-preservation\dcv build\bin\x64\Sunrise\logs\sunrise.log').

## DEPLOYED STATE (exact, for reproducibility)
- Server: p2(92) `535b918` deployed (RE_output/s1_accept/sunrise-server.exe), with
  activity_member_setup_flags=FALSE in settings.json (the p2(91)/p2(92) flag publishing
  is IN THE TREE but switch-gated OFF - both shapes broke the citizen join). Region seed
  (p2(90) activity_region_survives_churn=TRUE) is LIVE and required.
- Client DLLs: `ae4d41f76b5202a5` BOTH machines (type=/asid= capture restore, fork
  6d9f0ec; logging-only). settings BOTH: join_roster_observer FALSE, slice_set 56.
- Boot briefs: BOOT_BRIEF_p2-90/91/92.md (all gate-PASS; 90 = baseline win, 91/92 =
  the two negative flag experiments).
- ENVIRONMENTAL: the mac is dual-homed (en0=192.168.1.164 server + en13 USB LAN
  192.168.1.7); a host route pins the rig to en0 (`route get 192.168.1.136` -> en0) -
  KEEP IT. bdNAT 'ignored request' lines are a confirmed red herring (20.146).
- ROSTERS: both clients' roster UI names only self (PEER xuid=0) - pre-existing open
  question (20.104), same managed-session member-table carrier family.

## TOOLING STATE (use these - do not re-derive)
- Logs: INDEX FIRST (/usr/bin/python3 RE_scripts/logindex.py LABEL=PATH ...; miniconda
  python3 has broken sqlite - use /usr/bin/python3), query with logq.py (<db> positional,
  --stage/--grep/--source/--tail/--aligned). bapdecode.py for pcap->type-12.
- Boot discipline: brief -> gate_boot.py --literals -> deploy_p2d6_gameplay.sh ->
  launch-server-macos.sh; boot_verdict.sh FIRST after any paired boot.
- Capture: capture_bap30975.sh <seconds> (en0+lo0); bapdecode.py --pcap to decode.
- Indexes of today's boots exist under RE_output/logindex/ (index_20260828_*.db).

## SUGGESTED ORDER FOR THE REVIEWER
1. Read FINDINGS 20.145-20.152 + the three claims files (l9-profile-layout,
   ms-start-gate, ms-start-gate2, ms-start-gate3, gah-region-decode).
2. Audit the relay hypothesis against group_host.cpp + the p2(90) logs (the reviewer's
   independent angle is the point - today's session may be tunnelled).
3. If the relay is confirmed missing: design it server-side (we own group_host.cpp),
   one rebuild, one boot - the mac's Tower should render.
4. Then the render milestone: route-B fireteam capture (runbook ready) -> appearance
   blob relay -> two guardians visible.
