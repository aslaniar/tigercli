# HANDOFF 2026-08-28 - ROAD C IS CLOSED. L9 RENDER IS THE FRONT.

STATUS: live (2026-08-28 ~15:2x). Supersedes HANDOFF_2026-08-27_ROAD-C.md, whose
question - what must be true for two clients to share one host - is ANSWERED.
Read with FINDINGS 20.132-20.144 (newest-first) and STATE.md.

## WHAT HAPPENED (the one-paragraph version)
Two clients now stand in ONE public Tower instance: identical session-description,
region and activity host, each naming the other's xuid, peer channel connected and
HELD, 0 errors and 1 region rebind on both machines (20.140). Three defects fell to
get there, each hiding the next: the server never answered the client's SECOND BAP
link (20.137); the source for that link must be per-ACCOUNT because the two links do
NOT share a member key (20.138); and `kBapConnectionCount` was 4 while a client needs
3 links - a ceiling only survivable while the third link kept dying, so fixing the
starvation is what exposed it (20.139). Deployed: server p2(89) `2997d2810f11b1ab`,
fork d721435. Client DLLs UNCHANGED (`4831be3cb85db735`) and must not be redeployed.

## THE ONE THING THAT IS STILL MISSING
The other guardian does not RENDER. The session layer knows both players; nothing
turns the second into a character in your world. Co-location and render are now
CLEANLY SEPARATED for the first time - every earlier render observation was
confounded by the clients being in different instances, so treat pre-20.140 render
notes as suspect.

## WHERE THE STATIC HALF IS NOT (all measured, do not re-derive)
1. NOT on the peer channel (20.144, pcap). Steady state is 552 distinct 34-byte
   packets at ~4 Hz symmetric, DTLS-encrypted; ~26 bytes of payload per tick. Too
   small for appearance BY SIZE - the player row's identity block alone is 264 bytes.
   The establishment burst is plaintext and carries session id + endpoints only.
2. NOT reachable by subscribing to the peer's root (20.142). Each client subscribes
   families 0/2/3/4 to its OWN root, and - decisively - `familyRootSoid` plays no part
   in choosing whose data is served: the snapshot path reads
   `state::account_snapshot(before.accountKey)`, and NO root->account resolution
   exists anywhere in `state/` or `server/`. A foreign-root subscription would return
   the subscriber's own records.
3. NOT produced by the physics plane (20.141). ~1,800 lines under
   `server/gameplay/physics/*` never execute (`ev=physics` etc. all zero), gated on
   `server.activation.physicsHostSession`. DO NOT FLIP IT: its own doc says "It
   produces no wire output either way." Neighbouring gates `gameplayExternalBody` and
   `serverDefaultEntity` say outright "nothing reads this gate."

## WHERE IT PROBABLY GOES - THE CHOSEN TARGET
The GROUP-SESSION PLAYER ROW (20.143). `middleware/gameplay/group/session_messages.cpp`:
    /** A clear flag ends a player row after its identity group. The profile block it
     *  would gate has no writer here, so no row carries one. */
    constexpr std::uint64_t kPlayerProfileAbsent = 0;
    /** This host publishes no 264-byte identity block ... */
and `write_player_delta` closes EVERY row with `kPlayerProfileAbsent`. So the format
has a 264-byte identity/profile slot, the consumer already parses the row, both
clients already consume this channel - and we have never written one. Every player we
publish arrives with an identity and nothing to draw.
Supporting (INFERRED, not verified): `pc=` in the client's membership dump is
plausibly "profiles carried" - it reads 0 on every group_target row INCLUDING our own
player, and 1 on the client's own row in the client-built fireteam session. Consistent
with the two constants above. NOT promoted without the emitting function.

## THE NEXT ACTION, AND THE RULE THAT GOVERNS IT
STEP 3 = write the profile block. It is BLOCKED on one question and only one:
**WHAT DO THE 264 BYTES CONTAIN?** Nothing in the fork writes or decodes them; no
claims doc covers them. DO NOT GUESS THE LAYOUT - a guessed 264-byte struct is exactly
the class of guess this project has already paid for (a measured call outranks a
published header).
Two ways to source it, cheapest first:
  (a) TCP capture of a CLIENT-HOSTED session's membership push. Group membership rides
      BAP on TCP 30975, so a `tcpdump ... tcp port 30975` during a client-hosted
      fireteam/session run should carry a row that DOES set the profile flag (the
      fireteam `pc=1` row is the existence proof). NO code, NO client change.
  (b) Caller capture on the membership dump line (LESSONS 18c +
      `RE_scripts/pdata_bounds.py`) to reach the client's own encoder. Client-DLL
      change and a boot.
FALLBACK CARRIER if the player row proves wrong: the BAP root->account route (20.142),
which needs new server code - a root->account resolution plus a decision to serve one
account's family-0/3 records to another account's connection.

## OPERATIONAL NOTES EARNED TODAY (they cost real time)
- **Run `bash RE_scripts/boot_verdict.sh` FIRST after any paired boot.** It reads BOTH
  client logs over the ~/.ssh/cm-rig control socket. It was never run for hours while a
  RIG failure was diagnosed from mac+server logs alone (20.139).
- The rig's shell is Windows cmd; POSIX tooling is absent and plain `cmd /c` mangles
  the space in "dcv build". Use `powershell -NoProfile -Command` with single-quoted
  paths - or just use boot_verdict.sh.
- `reset_lobby_claims.sh` hangs AFTER succeeding and an interrupt leaves the server
  DEAD. A plain detached relaunch (`nohup bash mac-port/launch-server-macos.sh
  >/dev/null 2>&1 </dev/null & disown`) clears the in-memory claim table just as well.
- Do not deploy between the two clients' joins: it restarts the server, kills both
  links, and doubles the lobby claim counts.
- Peer-channel pcap needs NO sudo (this user is in `access_bpf`) and MUST filter on
  BOTH ports: `src port 3097 and dst port 3097`. Registered in TOOLS.md.
