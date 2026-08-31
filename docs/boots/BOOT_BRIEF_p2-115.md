# BOOT BRIEF p2(115) - THE MINIMAL PROFILE WRITER

STATUS: live (2026-08-29 ~15:4x). Author: opencode session (pickup of
HANDOFF_2026-08-29_PROFILE-WRITER job item 1-2; see also 20.177 RESULT 5).

Build under test: SERVER ONLY. New server exe from fork commit 2e11e4a
(p2(115)): `write_minimal_profile` in
`middleware/gameplay/group/session_messages.cpp`, behind the new server setting
`publish_player_profile` (DEFAULT FALSE; flipped ON in the deployed
settings.json for this boot - a settings flip, no rebuild, is the rollback).
Also in this build: `membershipPeerRetryCap` code default 6 -> 2 (the deployed
settings value was already 2; the code default now matches the tuned brake).
CLIENTS UNCHANGED: DLL `45ef17f93b901db9` on both machines, both observers
armed, no rebuild, no settings change on either client.

## PURPOSE

The profile block's wire encoding is fully read (20.176/20.177) and the
decoder-correct MINIMAL writer is now implemented and bit-exact smoke-tested
(+177 bits, region A mask builds 0x109, tail 0x10 clear, state hash unchanged).
This boot answers whether setting the profile-present gate on the peer's player
row - with an EMPTY but decoder-correct profile - reaches the client's apply
path and flips the peer row's profile state, WITHOUT desyncing the membership
body (20.177 R4's hazard is discharged by construction; this boot tests that
construction against the real client).

WHAT THIS BOOT DOES NOT TEST. It does not test appearance: the minimal block
carries no name, no gear, no appearance content (region A is identity-only,
20.173 R3), so NO guardian should render from it. It does not test the full
region A/B payload encodings (chunks 2/6/7/8/9 and region B's body are still
unread). It does not test the forge lane (closed) or the retry cap (tuned, and
its code default now agrees with the deployed value).

## GRAPHICS DELTA  (L12)

Expected ZERO. The minimal block sets the profile-present state with an empty
profile: no name string, no gear hashes, no appearance data (20.173 R3), and
20.177's own contract says it "will NOT render a guardian".
ACCEPTED RISK, named: a present-but-empty profile is a state no real client has
ever received from us, and nothing proves the client's appearance resolver
treats it as inert. If the client DOES attempt a peer render from the empty
profile, that is one new model load attempt against the co-presence render
class parked at 20.110/20.111. Rollback is the settings flip; a render death
here would be information, not a surprise.

## FALSIFIABLE CLAIM  (L6)

CLAIM: with `publish_player_profile=true`, each client's
`networking:session:membership:dump` for the `[group_target:...]` session shows
`pc=1` on the PEER's player row (not on the client's own row), while membership
stays fully healthy: `peers valid` and `players valid` unchanged from p2(110)'s
baseline (0x7 / 0x2 at the group session), no membership refusal, no refresh
loop, local player intact. Direct wire proof: `ev=ingress stage=apply` with
`caller_rva` in the 0x178xxxx range fires on EACH client (the wire-apply
caller), in addition to the 8x registry-path calls (~0x17A6101) already seen in
p2(114).

PRE-NAMED CONTENT NEGATIVE 1 (dump healthy, gate dead):
  If both clients stay healthy but `pc` stays 0 on the peer row for the whole
  boot, then the dump's `pc` field does not read the store the gate bit drives.
  Target: the dump instrument's source field - NOT the writer (the smoke proved
  the bits; if the wire carried them, the encoding is not the suspect).

PRE-NAMED CONTENT NEGATIVE 2 (desync - the hash question):
  If either client refuses/refreshes membership, drops `players valid`, or
  destroys its local player, FIRST suspect is the client's trailing state hash
  covering profile bytes the apply writes into the hashed replica - the one
  failure mode 20.177 R4 could not discharge by construction, because our hash
  was only ever validated against profile-absent bodies. Response: flip
  `publish_player_profile` off (no rebuild), confirm recovery, then target the
  client's hash input region around the apply.

PRE-NAMED CONTENT NEGATIVE 3 (apply never sees the wire block):
  If `ev=ingress stage=apply` fires ONLY at the registry caller_rva and never
  in 0x178xxxx while membership delivers (server logs `result=built` with the
  new exe), then the block reached the client but not the apply - target the
  delivery/parse step upstream of 0x141781800, not the encoding.

## ABSENCE NEGATIVE  (L13)

- Zero `ev=ingress stage=apply` lines on a client means the OBSERVER did not
  run, not that no block arrived. Liveness: the same line fired 8x per machine
  in p2(114) from the registry path with the identical DLL - silence on THIS
  boot with the same DLL means the client ran the OLD dll or its settings
  changed; verify the deployed DLL hash and `profile_ingress` in the client's
  settings.json before any encoding conclusion.
- Zero `membership:dump` lines: the dump instrument is known-live on both
  machines at `client: debug` (p2(109)/p2(110)); silence = instrument/config
  problem first (L13).
- Server liveness: `ev=gameplay stage=membership result=built` fired 100+ times
  in prior boots; zero such lines with the new exe means the server did not
  start or the settings file was refused (a malformed settings.json refuses the
  whole file - check the server log for the parse failure).

## CHAIN MARKS  (L16)

  L1  server exe deployed == built (commit 2e11e4a)   VERIFIED-BY-EXECUTION
      (deploy_p2d6_gameplay.sh: candidate a7a7a1cfd4e26abb, all 7 harness
      gates ok, deployed exe a7a7a1cfd4e26abb, 2026-08-29 ~15:3x)
  L2  publish_player_profile=true in the served       VERIFIED-BY-READING
      settings.json; server restarted 15:3x and        + VERIFIED-BY-EXECUTION
      accepted the file (ev=initialize result=ok; a    (server alive on new exe)
      malformed settings file refuses startup)
  L3  membership_peer_retry_cap=2 unchanged            VERIFIED-BY-READING
      (settings.json, this session; code default now also 2)
  L4  client DLL 45ef17f93b901db9 on BOTH machines,    VERIFIED-BY-HISTORY
      unchanged this boot (deployed 08-29, hash-asserted at that deploy)
  L5  both client observers armed (profile_harvest +   VERIFIED-BY-HISTORY
      profile_ingress true on both machines)           (armed at that deploy)
  L6  both clients' log levels still all-debug         VERIFIED-BY-HISTORY
                                                       (unchanged since p2(110))
  L7  hook RVAs in the built client tree pass          VERIFIED-BY-EXECUTION
      verify_hook_rvas.py (0 bad; exit 0, this session) - client DLL unchanged,
      re-run not required for THIS boot; recorded for chain completeness
  L8  writer bit-exactness (+177 b, mask 0x109, tail   VERIFIED-BY-EXECUTION
      0x10 clear, hash unchanged)                      (smoke, this session)

## ADVERSARIAL PASS: ses_fb06b8cffffezsJEMVuh9yOxfJ

Q: Is the +177-bit delta itself the bug? A: No - the gate bit (1) REPLACES the
   absent flag (1), so the delta is block-after-gate = 177; total block 178.
   The smoke measures the delta directly off the encoder, both paths.
Q: Could the writer desync when a session has MULTIPLE players? A: The block is
   self-contained per row and every width is fixed; the smoke exercised one
   row, but row encoding is stateless (no carry between rows; the reader walks
   per-entry). Capacity: +178 b/row x 32 = +712 b, body cap 1024 B, worst case
   today ~200 B - fits.
Q: Does the new code change the profile-ABSENT path? A: Byte-for-byte no: the
   absent branch writes the same single 0 bit it always did (smoke compares the
   OFF body bit count and content).
Q: Why believe the client will accept an empty profile at all? A: We do not -
   that is exactly what the boot tests, and negatives 1-3 name the three ways
   it can fail and where each one points.

## INSTRUMENTS

Server (new build, this deploy):
  publish_player_profile - settings key, parsed by server_settings_parser.cpp
LITERAL TARGETS (pre-deploy: the staged build output; deploy_p2d6_gameplay.sh
asserts deployed==built by hash, and the gate is re-run on the deployed path
after deploy to close L14 on the live file):
  RE_build/Sunrise-fork-inventory/build/sunrise-server.exe: publish_player_profile, membership_peer_retry_cap
Client (unchanged, for the absence negative only):
  ev=ingress stage=apply / caller_rva - already shipped in 45ef17f93b901db9.
