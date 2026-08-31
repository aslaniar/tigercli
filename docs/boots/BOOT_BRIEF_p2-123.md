# BOOT BRIEF p2(123) - REAL CONTENT: DOES A NAME SURVIVE THE WIRE?

STATUS: live (2026-08-30). Reads with FINDINGS 20.194 (the plumbing, symmetric) and
20.179 R1 (the name cipher).

## PURPOSE - what this boot learns, win or lose

p2(122) proved the profile block reaches both clients and applies, in both directions -
but the block is EMPTY by construction (region A = 232 zero bytes). Everything so far
proves SHAPE. This boot is the first that publishes CONTENT: region A chunk 1, the name,
obfuscated with the cipher derived in 20.179 R1 and inverted for the writer.

Each row carries a DISTINCT name - the configured text with the player's slot digit
appended - so a client that applies two rows says WHICH row it applied. That turns
"a peer's row was applied" into "a peer's NAME arrived intact".

## GRAPHICS DELTA

ZERO new rendered models expected. A name in the membership profile is not a character
model; appearance is the character_record family (20.173). Nothing new is drawn.
Minimization: this changes bytes inside a body both clients already receive and apply.

## FALSIFIABLE CLAIM (the one contract under test)

CLAIM: the client's stored region A begins with the name, in UTF-16LE, exactly as written.
PRE-REGISTERED PREDICTION (computed before the boot, RE_scripts/name_codec.py):
    slot 0 -> "SUNRISE0"  stored hex 530055004e0052004900530045003000c2c4
    slot 1 -> "SUNRISE1"  stored hex 530055004e0052004900530045003100c2c4
    wire words slot 0: D9BD 9964 7B93 A54C DE6B 3BC5 45FB 605F 0000
    wire words slot 1: D9BD 9964 7B93 A54C DE6B 3BC5 45FB A4B0 0000
The trailing c2c4 is the TERMINATOR word stored as key16(8)=0xC4C2 - the reader writes the
deobfuscated word back BEFORE testing the wire word for zero, so a nonzero stored
terminator is CORRECT and is not corruption. An observed `ev=ingress stage=dump tag=regionA
off=0` line on either client must begin with one of those two strings.

CONTENT NEGATIVE (pre-named): region A off=0 is nonzero but does NOT match either
prediction. Then the cipher's WRITER direction is wrong even though the reader direction
was derived correctly - most likely the index-0 special case or the mod-31 rotation. The
codec's oracle (name_codec.py --selftest, 10/10) only proves self-consistency, never that
our inverse matches the client's forward transform. This boot is that check.

SECOND CONTENT NEGATIVE: region A off=0 is still ALL ZERO. Then the name chunk was not
written - suspect `profile_name` not reaching the writer (check the setting parsed) rather
than the cipher.

THIRD: the decoder returns ok=0 again. The name adds 16 bits per character, so the body
grew ~144 bits per row; a size or fragment limit we have not met before would show here.
20.188's instrument reports it directly.

## ABSENCE NEGATIVE (L13)

- Zero `stage=install` on either machine: that DLL did not load.
- `staging_populate=1` anywhere: the detour is armed and the boot is void (20.191).
- Zero `ev=ingress ... path=WIRE`: the profile path did not run; compare with p2(122),
  where it ran on both machines. Suspect the new server build before the clients.
- Zero `tag=regionA` dump lines with a WIRE caller: the per-class dump budget
  (4 per class) was spent on local commits - but that CANNOT happen now, because dumps are
  budgeted per (path,index) since 20.193 R5. If it happens anyway, the budget fix is wrong.

LIVENESS: `ev=dtrace stage=install result=ok staging_populate=0 ...` on BOTH machines.

## CHAIN MARKS (L16)

| Link | Mark |
|---|---|
| Profile block reaches and applies on both clients, both directions | VERIFIED-BY-EXECUTION (20.194) |
| Server composes two-row bodies | VERIFIED-BY-EXECUTION (20.193 R1, 655 bodies) |
| Name cipher, READER direction | VERIFIED-BY-DISASSEMBLY (20.179 R1, 0x1416D3460) |
| Name cipher, WRITER inverse | VERIFIED-BY-SELFTEST only (name_codec.py 10/10, self-consistent) - THIS BOOT tests it against the client |
| A published name survives to the client's stored buffer | UNKNOWN - THIS BOOT |
| Appearance (character_record; peer's record unservable) | VERIFIED-BY-READING (20.173) - not this boot |
| Render / co-presence | UNKNOWN (parked) |

## INSTRUMENTS

INSTRUMENTS:
  ev=dtrace stage=decoded
  path=%s

## LITERAL TARGETS

LITERAL TARGETS:
  Game/bin/x64/steam_api64.dll: ev=dtrace stage=decoded, path=%s

## ADVERSARIAL PASS

ADVERSARIAL PASS: waived: content-only change inside an already-working body; rollback is a settings clear

waived: no new hook RVAs, no client change (same DLL as p2(122)). The server writes 16 more
bits per name character into a body both clients already accept. Clearing `profile_name`
publishes the empty name again and reproduces the p2(122) bytes exactly, with no rebuild.

## DEPLOYED FOR THIS BOOT
  server exe     `515e437f0ce1bed2` - name encoder in region A chunk 1; all seven deploy
                 gates passed (sweep-test, wire-test, local-account-test all failures=0).
  MAC client DLL `cadb28325fb3e7cf` (unchanged from p2(122))
  RIG client DLL `cadb28325fb3e7cf` (unchanged from p2(122))
  settings       server publish_player_profile TRUE, profile_name "SUNRISE";
                 both clients staging_populate FALSE, decoder_trace TRUE, ingress TRUE.
                 settings.json edited by TEXT INSERTION only (trap 18); backup
                 settings.json.bak_claude_p2d123.

## AFTER THE BOOT - REQUIRED
`bash RE_scripts/capture_boot.sh p2-123` - pulls both client logs plus the server log.
