# BOOT BRIEF - p2(57), the unique-lobby-id boot (2026-08-26 ~19:55)

## THE POINT

The client's join-gate table (FINDINGS 20.83) carries
`target_fireteam_is_not_ours`, and both machines were publishing the **identical**
fireteam platform id (`0x109000000000002`) because our `create_lobby` derived it
from a per-process counter. That gate could never pass, and the rig has said
`tried-to-join-self` about the mac in every capture we hold.

p2(57) makes the id unique per machine. **One variable.**

## THE PREDICTION (falsifiable, and the whole reason to change one thing)

The rig should STOP saying peer-link reason 1 and START saying reason 5, because
gate [27] `target_fireteam_privacy_is_not_closed` is untouched and the session is
still created `as_private=1` with `friend-only=1`.

- **Both machines converge on reason 5** -> the fix landed, gate 28 now passes,
  and privacy is the next single gate. Best realistic outcome.
- **The rig still says reason 1** -> the id is not what gate 28 compares. The
  gate-table correspondence (marked INFERRED in 20.83) is wrong and must be
  retracted; go back to locating the evaluator.
- **A new reason appears** -> best case. It names the next gate directly.
- **No type-14 at all** -> read `peers valid` and the `peer_advert` lines before
  concluding anything; it may mean the peer condition never held.

## PRE-BOOT CHECKLIST

### 1. Provenance - ASSERTED
```
client DLL  63f5fbda6b83e0b4  on BOTH machines
            hash re-checked AFTER copy on the machine that runs it
            literals confirmed IN each deployed file:
              "stage=lobby_create"   "account=0x%08X"
server exe  1991b3da6f518165  UNCHANGED (steam shim compiles into the DLL only)
fork        dd6ac7d, clean
```

### 2. Liveness - a line that MUST appear whatever happens
```
ev=steamnet stage=lobby_create type=3 max=32 result=N lobby=0x... account=0x........
```
Emitted twice per client at startup, before anything else can go wrong, and it
now prints the account field the fix derives the id from. **The ids are
predicted exactly**, so this line is also the content check:
```
mac  0x010900000CC46DB7  and  0x01090000EA0CF3EE
rig  0x010900000CC46DB4  and  0x01090000EA0CF3ED
```
If the two machines print the same lobby id, the fix did not take and nothing
downstream in this boot means anything.

### 3. Both negatives pre-named
- **CONTENT**: ids differ but the rig still releases with reason 1 -> gate 28
  does not compare this field; retract the 20.83 correspondence.
- **ABSENCE**: no `lobby_create` lines at all -> the DLL did not load; check the
  deployed hash before reading anything else.

### 4. Chain marks
| link | mark |
|---|---|
| peer row ships, client accepts and parses it | verified-by-execution (boot #10) |
| client reads the peer and looks it up by machine id | verified-by-execution |
| tracking data comes from managed-session membership | verified-by-reading |
| the fireteam platform id was identical on both machines | **verified-by-execution** (boot #10 capture) |
| gate 28 is what reason 1 reports | **INFERRED - this boot tests it** |
| gate 27 (privacy) blocks after 28 passes | inferred; the prediction above |
| a group TARGET is ever set | assumed-false, untouched |
| Steam P2P transport carries a join | assumed-false, untouched |

### 5. Graphics delta
**ZERO.** No item, loadout or model change. Renderer compiles exactly what it
compiled last boot.

### 6. Known hazard carried forward
The Mac black-screened during boot #10 shortly after its peer body (20.81). The
suspect is the second region record in membership update 5, which is UNCHANGED
here. **Expect it may happen again.** It is a render hang, not a crash - the
process stays alive and keeps logging, so the log is still good. If it goes
black, let it sit ~60 s, then quit normally; the capture is still valid.

## THE RUN
1. Boot the Mac into the Tower, let it settle.
2. Boot the rig into the Tower.
3. Both standing ~60 s, then have one player walk a short distance (different
   bubbles make the peer endpoint deliverable).
4. Quit both.

## WHAT I READ
`ev=steamnet stage=lobby_create` (both, ids must differ), the type-14
`release_peer_reservation` payloads (reason byte), `stage=peer_advert`,
`stage=push type=12 body=` (3882/3967/4095), `peers valid`, and any
`[AC ... TARGET ...]` line - a group TARGET appearing would be the first ever.

**Grep every capture with `grep -a`.**
