# BOOT BRIEF p2-104 (2026-08-29) - WHAT GOES ON THE PEER CHANNEL WHILE THE CLIENT
# WAITS ON A PEER THAT CANNOT ANSWER?

STATUS: live (2026-08-29 ~0x:xx). Behaviour change, MAC ONLY (admission_inject=true,
same build as p2(103)); rig is the control. Server unchanged p2(96).
The NEW instrument this boot is the WIRE: tcpdump on en0, udp 3097, started BEFORE
client launch, running through the stall + 60 s. No client or server code change.

## PURPOSE
p2(103) left the client alive and rendering at `setup:orbit`, "waiting on a peer that
cannot answer" - and we have never once read the peer channel (the only path the clients
talk to each other on directly, 20.144) during that wait. p2(96) proved admission does
not ride the server. This boot asks the wire directly: when the forged peer makes the
client believe it has a peer, does the client ATTEMPT anything peer-directed on the
peer channel - and does the rig answer?

WIN: the pcap shows, after the inject and through the setup:orbit stall, mac->rig
peer-channel traffic beyond 20.144's baseline (a new establishment burst, or a
steady-state cadence/size change) that the rig does NOT answer symmetrically. That
means admission IS attempted client-to-client and refused - the fix is making the RIG
side real (symmetric record or true admission), and the plaintext establishment burst
may name what the client expected to exchange.

DECISION RULE (pre-named, per U6/U9 - each outcome maps to exactly one next action):
  - D1 NEW mac->rig BURST, no symmetric reply  => admission attempted + refused.
       Next: decode the plaintext establishment phase; instrument the rig's
       refusal/drop point. Do NOT resume record-content guessing.
  - D2 NEW SYMMETRIC exchange (both sides burst)  => an admission conversation IS
       happening. Next: decode plaintext portions; then field_xref the record's
       other readers. (This is the branch nobody expects.)
  - D3 BASELINE ONLY (34 B ~4 Hz symmetric + keepalives, nothing new, through
       stall + 60 s)  => the client never even attempts admission on the peer
       channel despite believing it has a peer; the wait is CLIENT-INTERNAL.
       Next: instrument the record's other readers (the handoff's fallback), not
       the wire.
  - STALE-ID WATCH (runs inside every outcome): the establishment burst is
       plaintext and carries session-form machine ids (20.144). Compare the rig's
       announced id against the injected constant's session form
       E622D0F738836C84 (= value 0x846C8338F7D022E6). Ids rotate (20.163), so a
       DIFFERENT announced id confirms the stale-a7 mechanism as a co-cause and
       goes in the finding regardless of D1/D2/D3.

## GRAPHICS DELTA
Zero new rendered models. Identical build to p2(103); the known failure mode is a
black screen with moving frames (renderer active, no new models) and the known win
renders nothing new either. No loadout change. Boot otherwise minimized.

## FALSIFIABLE CLAIM
With admission_inject=true on the mac and the capture running from before client
launch, decision rule D1 holds: new mac->rig peer-channel traffic appears during/after
the inject and through the setup:orbit stall, unanswered by the rig - because the
client tries to USE the peer it now believes it has, and the rig has no matching state
to answer with.

CONTENT NEGATIVE 1 (D3): baseline-only traffic. The incompleteness theory is already
dead (20.165); if the wire is also silent, the stall is not a wait on ANY network
answer.
CONTENT NEGATIVE 2 (D2): symmetric new exchange - an admission conversation exists
and this boot cannot see enough of it; escalate to decode + reader instrumentation.
CONTENT NEGATIVE 3: `stage=inject` reports member=1 members_now=1, roster names the
peer, and the client nevertheless reaches `activity:in_world` - that SPLITS the
admission and z-leg (+0x524) hypotheses bundled since 20.157 and hands the swap back
to fn 0x140E1D400.

## ABSENCE NEGATIVE
- ZERO packets with src port 3097 AND dst port 3097 in the pcap => the CAPTURE
  INSTRUMENT failed (wrong interface, tcpdump not running, filter error). That is an
  instrument fact, not a system fact - rerun the capture before concluding anything
  (L13). The 20.144 baseline guarantees this traffic exists during a paired dwell.
- No `stage=install ... inject=1` line on the mac => the settings did not parse or
  the guard chain refused; the boot tested nothing.
- Any `stage=inject` line on the RIG => the rig is NOT disarmed; boot invalid as a
  control. Zero expected (verified pre-boot by reading the rig's settings.json).

## CHAIN MARKS
- Slot + member record makes the client believe it has a peer (roster names the
  peer) - verified-by-execution (p2(102), reproduced p2(103)).
- The p2(103) outcome (black screen, moving frames, stall at setup:orbit) -
  verified-by-execution.
- Peer channel: DTLS established BOTH directions, baseline 34 B @ ~4 Hz + keepalive,
  establishment burst STRUCTURED PLAINTEXT carrying session-form machine ids -
  verified-by-execution (20.144).
- The client ATTEMPTS peer-channel traffic toward a believed peer - UNKNOWN (this
  boot's test).
- The rig answers or refuses - UNKNOWN (expected: cannot).
- Injected a7 equals the rig's CURRENT session machine id - KNOWN STALE (a settings
  constant across boots; real ids rotate within a boot, 20.163). Deliberately NOT
  changed this boot: one variable per boot, and the capture is the new instrument.
- Both clients on build ba6013a2d08cbd46 after alignment - verified at deploy
  (hash assert inside deploy_client_dll.sh).
- Server p2(96) b9b0f3823f74d1bf unchanged and alive - verified (lsof + hash
  pre-boot).
- Solo-control rule (p2(59)): this exact build has already booted on BOTH machines
  tonight (mac ARMED in p2(103), rig as control). Solo control waived on that basis;
  the only new variable this boot is the settings flip + the passive capture.

## ADVERSARIAL PASS: waived - solo main-session prep (B-checkpoint exception); the
adversarial review of the 20.153-20.165 chain was performed this session and its two
actionable flags are encoded here as the decision rule (D1/D2/D3) and the stale-id
watch. Main residual risk: arming re-creates the p2(103) stall - accepted, it is the
phenomenon under test, recovery is a settings flip with no rebuild, and the rollback
DLL is on disk.

## SWITCH POSITIONS FOR THIS BOOT
  MAC  admission_inject TRUE (params retained: member_index 1,
       xuid 76561198776753862, peer_steam_id 76561198776753862,
       peer_machine/a7 9542145991190258406), admission_census TRUE
  RIG  admission_inject FALSE (control; no admission keys on that machine)
  Server unchanged p2(96) b9b0f3823f74d1bf.

## CAPTURE
  mkdir -p RE_output/captures/p2-104_peer_admission
  tcpdump -i en0 -s0 -U -w RE_output/captures/p2-104_peer_admission/peer_<ts>.pcap 'udp port 3097'
  Started BEFORE client launch; stopped after the stall + 60 s. Analysis filters
  `src port 3097 and dst port 3097` (3097->3074/30976 are NOT the peer channel,
  TOOLS.md); steady state is DTLS-encrypted - read by SIZE and CADENCE, contents
  only where 20.144 showed plaintext (establishment burst).

## INSTRUMENTS:
  "ev=admission stage=inject"
  "ev=admission stage=census"
  "ev=admission stage=install"

## LITERAL TARGETS:
  Game/bin/x64/steam_api64.dll: ev=admission stage=inject, ev=admission stage=census, ev=admission stage=install

## ROLLBACK
Flip mac admission_inject to false - no rebuild. Write-free p2(98)
`5d7e6bd61e078c24` is on disk on the mac as steam_api64.dll.bak_p2d7_*; the rig is
untouched (control). Server unchanged; DO NOT BOOT p2(71).
