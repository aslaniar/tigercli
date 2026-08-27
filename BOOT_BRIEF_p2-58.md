# BOOT BRIEF - p2(58), the reason-decision instrument (2026-08-26 ~20:30)

## THE POINT

Every peer-link refusal we have ever read arrives as a number - reason 1
`tried-to-join-self`, reason 5 `privacy-mode` - and we have never known what the
client compares to pick it. 20.85 located the naming accessor but the static
walk above it ends in a 27-arm observer fan-out with `.vmp0` beyond.

This boot hooks `reason_name(int)` and reports **who asked**. The return address
IS the deciding call site. One boot converts an open-ended RE walk into an
address.

**This is an INSTRUMENT boot. It changes no behaviour and fixes nothing.**
Expect the same refusal as boot #11; the point is the site, not the outcome.

## PRE-BOOT CHECKLIST

### 1. Provenance - ASSERTED
```
client DLL  9bba721d961c0869  BOTH machines, hash re-checked after copy
            literals confirmed IN each deployed file:
              "ev=peerlink stage=reason"   "stage=lobby_create"
server exe  1991b3da6f518165  UNCHANGED (no server change in p2(58))
fork        p2(58), clean
```
Signature verified UNIQUE in `.text` offline (exactly one match, at
`0x1416E1620`) before the hook shipped.

### 2. Liveness - fires on EVERY reason lookup, boring path included
```
ev=peerlink stage=reason result=ok                        <- install line
ev=peerlink stage=reason value=N name=<enum-name> site_rva=0x........ static=0x14........
```
The install line appears at startup regardless of anything. If it says
`result=fail reason=target`, the signature missed and nothing else in the boot
means anything.

### 3. Both negatives pre-named
- **CONTENT**: lines appear but every `static=` address lands in the observer
  fan-out we already mapped (`0x1416Dxxxx`/`0x1416E1250`) -> the decision is
  further up still, and the next move is hooking the printer at `0x141785E90`
  to capture its arguments instead.
- **ABSENCE**: zero `value=` lines with `result=ok` present -> the reason is
  named through a path that does not call this accessor (e.g. the release
  encoder formats it elsewhere), which retires this route and points at the
  type-14 send path in `0x1404Fxxxx`.

### 4. Chain marks
| link | mark |
|---|---|
| the reason enum indexing | verified-by-execution, TWO independent routes (20.64, 20.85) |
| the five printer sites take reason as a parameter | verified-by-reading |
| the decision is above the observer fan-out | verified-by-reading |
| **which call site decides** | **THIS BOOT resolves it** |
| what that site compares | one disassembly after this boot |

### 5. Graphics delta
**ZERO.** No item, loadout, model or renderer change.

### 6. Known hazard
The Mac may black-screen again (20.81 suspect unchanged). It is a render hang,
not a crash - the process stays alive and keeps logging, so the capture stays
good. Let it sit ~60 s, then quit normally.

## THE RUN
Same as the last two: Mac into the Tower, then the rig, both standing ~60 s,
walk one player a short distance, quit both.

## WHAT I READ
`ev=peerlink stage=reason` lines from BOTH clients - the `static=` address of
the site that asked for reason 1 and reason 5 - then disassemble those addresses.

**Grep with `grep -a`.** The server log also still spans earlier boots; filter by
the new session ids.
