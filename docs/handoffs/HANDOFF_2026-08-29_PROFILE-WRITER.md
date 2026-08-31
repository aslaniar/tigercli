# HANDOFF 2026-08-29 - THE PROFILE WRITER (Claude Code -> opencode)

STATUS: SUPERSEDED (2026-08-29 ~23:5x) by FINDINGS 20.178-20.185 and
HANDOFF_2026-08-29_STAGE-TRAY.md. THIS HANDOFF'S JOB IS DONE: the writer shipped
bit-exact at p2(115) (commit 2e11e4a) and the boot ran - the flag-on body is delivered,
acked, and decoded, but the client's apply skips it at the STAGING OBJECT (uninitialized
pointer, 20.183-20.185) - a layer this handoff could not have named. The traps below
remain true and were all respected. Read this only for the argument maps and the
what-not-to-redo list; the live job is in STAGE-TRAY.

## THE ONE-PARAGRAPH STATE OF THE WORLD

The networking stack is DONE. Both clients reach the Tower, hold `peers 0x7 / players
0x3` at real endpoints, land in ONE instance, and run a direct client<->client channel.
Two guardians do not appear for exactly one reason: our server writes a hardcoded 0 into
the player row's profile-present bit, and the profile block that bit gates has never had
a writer. The block's wire encoding is now fully read. A minimal, decoder-correct writer
is specified bit for bit in 20.177 RESULT 5. Write it, gate it OFF by default, boot it.

## WHAT NOT TO REDO (each cost a boot or a day)

1. **The admission forge is CLOSED (20.170/20.172).** Its premise - "the mac's member
   table never names the rig" - was false the whole time; 20.129 had already measured the
   symmetric state. The injection poisons the mac's OWN bdNAT structures, which is what
   produced every "NAT Type: UNKNOWN" and forge black screen. Do not forge a peer record.
2. **Do not raise `membership_peer_retry_cap`.** p2(111) took it 2 -> 6, produced 146
   peer bodies, and BLOCKED the mac's Tower load. It is a tuned brake. It is back at 2.
3. **Do not enable `physicsHostSession`.** Its own doc: no wire output either way, and it
   runs on the render thread (a frame stall). Not the render path.
4. **`serverDefaultEntity` is dead** (20.174 R5) - 3 references, all settings parsing.
5. **`foreign=` is not a peer count** - it is `activityJoinedForeignSession`, never
   assigned anywhere in the tree (20.171 R1). Ignore it.
6. **Do not hook 0x1417AF2D0.** `pdata_bounds` proves it is not a function start.

## THE THREE INSTRUMENT LIMITS THAT PRODUCED FALSE FINDINGS - ALL STILL LIVE

- `handle_message_observer.cpp:118` HARDCODES `dir=down`. Any "the client never sends X"
  read off that tape is an instrument limit, not a finding.
- `bapdecode.py` only decrypts s2c. The c2s direction needs the nonce's LAST BYTE
  XOR 0x01 (`kReceiveDirectionMask`, plaintext.cpp:218). With it: 571/571 frames, 0 fails.
  Tools: `RE_output/captures/p2-114_grand_capture/c2s_decode.py` + `c2s_services.py`.
  bapdecode.py should absorb a `--direction` flag.
- `Adding player [xuid=...]` only ever fires on the fireteam/posse sessions, never on
  `group_target`. Its absence for a peer proves nothing (20.172 RETRACTION 1).

## MANDATORY BEFORE ANY BOOT THAT SHIPS A HOOK

`python3 RE_scripts/verify_hook_rvas.py` - exit 1 on any RVA that is not a .pdata
function START. It caught two real errors on its first day: p2(112)'s dropped digit
(0x1A6040 for 0x17A6040, which cost a whole boot because a wrong address still passes a
module-range check) and 0x1417AF2D0 being a mid-function fragment.
Also: `gate_boot.py <brief>` on the brief, and `deploy_client_dll.sh` for its literal
grep IN the deployed file.

## THE JOB, IN ORDER

1. **Write the minimal writer** exactly as 20.177 RESULT 5 specifies - 150 bits, nothing
   guessed. Put it in `middleware/gameplay/group/session_messages.cpp`
   (`write_player_delta`), behind a NEW server setting `publish_player_profile`,
   **DEFAULT FALSE**. Keep `kPlayerProfileAbsent` as the else-branch.
   WATCH: the region-A presence bits go out in WIRE order (1, 2, 4, 8, 0x100, 0x10, 0x20,
   0x40, 0x80) - NOT bit order. Chunks 4 and 5 are `read(6) - 1`, so write 1 to store 0.
   The tail's 5-bit field must have bit 0x10 CLEAR.
2. **Boot it paired**, both clients unarmed, server flag ON. The success line is `pc=1`
   on a `group_target` row in either client's `membership:dump`. The failure mode to
   watch is a desynced body: the client refusing/refreshing membership, `players valid`
   dropping, or the local player being destroyed. Flip the setting off to recover - no
   rebuild.
3. **If pc=1 lands and nothing breaks**, the scaffold is proven and the remaining work is
   the payload encodings of region-A chunks 2, 6, 7, 8, 9 (0x140A496E0, 0x1416D3B20,
   0x1404C74B0, and chunk 9's 0x1416BE1E0 pair) plus region B's body (0x1416D3C30) -
   all static, all unread.

## THE CLIENT-SIDE OBSERVERS ARE ALREADY BUILT AND DEPLOYED

DLL `45ef17f93b901db9` on BOTH machines. Two read-only observers, both settings-gated,
both DEFAULT FALSE, both currently ARMED:
  - `profile_harvest` -> 0x1417A6040, the registry commit. Gives a real region A.
  - `profile_ingress` -> 0x1417AF360, which runs ONLY when a profile block is applied
    from ANY path. `caller_rva` separates the wire apply (RVA 0x1781800..0x17834CE) from
    the local registry commit (~0x17A6101).
**`ev=ingress stage=apply` with a caller_rva in the 0x178xxxx range is the direct proof
that a written block reached the client.** That is your success instrument for step 2;
it fired 8x per machine in p2(114), every one from the registry, zero from the wire.

## DEPLOYED STATE AS OF THIS HANDOFF
```
  client DLL   45ef17f93b901db9  BOTH machines (profile_harvest + profile_ingress armed)
  server exe   b9b0f3823f74d1bf  UNCHANGED; membership_peer_retry_cap = 2 (reverted)
  mac client   admission_inject FALSE; region_public FALSE; all log levels debug
  rig client   same; settings verified byte-clean (no BOM, LF, 229 keys)
  captures     RE_output/captures/p2-114_grand_capture/ (logs, en0+lo0 pcaps, c2s tools)
  harvest      RE_output/captures/p2-113_profile_harvest/ (real region A + tail .bin)
```
Both clients were in the Tower when this was written; nothing is armed that writes.

## THE HONEST CAVEATS, SO YOU DO NOT INHERIT MY MISTAKES

- The harvested region A is UNVALIDATED. The commit hash is NOT an oracle - it is
  computed over the PREVIOUS cached copy (20.173 R4). Do not treat those bytes as proven.
- Region A is IDENTITY, not appearance (20.173 R3: xuid, SOIDs, a 1060.0f power value,
  -1 sentinels, zero gear hashes). The minimal writer will NOT render a guardian. Where
  appearance actually lives is still unproven; region B (136B, wire-fed only, never
  written by anything) is the remaining candidate and its body is unread.
- The delta buffer is NOT proven to be zeroed before decode. That is exactly why the
  minimal writer sends chunks 1/4/5 rather than an all-absent region A - see 20.177 R4.
- I was wrong three times in one day (the co-presence render hypothesis, the retry cap,
  and `Adding player` as an instrument), each time by asserting a mechanism from a
  filtered or truncated view before running the census this project's own rules demand.
  CENSUS BEFORE FILTER. It is now a hard rule in STATE.md.
