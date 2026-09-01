# HANDOFF 2026-08-31 - THE GATE-FEEDER LANE (blocker 3)

STATUS: live. Supersedes HANDOFF_2026-08-31_POOL-PROTOCOL.md (whose entity-index premise
was closed by measurement at 20.219). Read this + FINDINGS 20.219-20.233.

## THE ONE-PARAGRAPH STATE OF THE WORLD

Membership/identity/session: CLOSED and symmetric. Slot supply: CLOSED, never a blocker
(20.219). The local build loop is CORRECT - it builds only what the client owns, so it was
never the peer path (20.221). Peers must therefore ARRIVE, and the receiver for that is an
object that IS NEVER CONSTRUCTED - zero instances of any of its four secondary vtables
across 6.49 GB of live memory (20.223). Its construction chain is fully mapped, call-only,
dual-encoding verified (20.225), and IS invoked - it stops at a five-condition
per-participant gate (20.228/20.229). p2-148 measured which condition: **bit 4 of
byte[table + i*0x2AC0 + 0x38] is clear for every participant, 904/904 readings, solo and
paired** (20.230). What writes that bit is the whole remaining question.

## THE GATE, IN FIELDS (20.229, measured live 20.230)

    table = [rcx] + 0x6C38          rcx = 0x141702580's argument (= 0x1417021C0's)
    records at table + i*0x2AC0
    1. i = first set bit of [table+0x5924C]           (maskB)   -1 -> bail
    2. i != self index                                 <- SELF IS FOUND BY IDENTITY:
       0x1404DD640 walks maskB comparing [record+8] against a reference qword (20.232 R1)
    3. bit i of [table+0x59248] SET                    (maskA)
    4. byte[table + (i+1)*0x2AC0 + 0] == 0
    5. bit 4 of byte[table + i*0x2AC0 + 0x38] SET  -> CONSTRUCT   *** THIS IS THE BLOCKER ***

## WHAT HAS BEEN ELIMINATED AS THE FEEDER (do not redo these)

- All 21 handled activity-message types on the pool dispatcher (other session's decode):
  none writes the gate bitmasks or +0x38. Type 30 touches only +0x602b4, already proven
  insufficient.
- Every encoding field_xref covers (20.232 R2): disp32 [reg+0x59248] = 2 reads/0 writes;
  disp8 byte writes to [reg+0x38] intersected with the 29 participant-table functions = 0;
  no-displacement SIB writes intersected with the same = 0 real (1 false positive).
- The record CONSTRUCTOR itself: 0x1404F7240, the only pool-cluster function that indexes
  by 0x2AC0, initialises -0x10/+0x00/+0xB0 and NOT +0x2C or +0x38 (20.233 R3).

## WHAT REMAINS, IN ORDER

1. Decomposed-base writes (`lea rax,[rcx+0x59000]; mov [rax+0x248],..`) - NO tool covers
   this. Needs a small dataflow-aware pass over the pool cluster, or acceptance that it is
   not statically findable.
2. The obfuscated second .text: 3 SIB byte-writes to [reg+reg+0x38] there
   (0x144FB54C1, 0x1454FC96B, 0x146D853BB), unexamined.
3. The 14 scattered single stride sites from 20.233 R2, unexamined.
4. THE PROBE-ADDRESSED DUMP (the fallback, and the highest-value single action): ptable
   already logs the table address live. One paired run with ptable armed AND a full dump
   taken at that moment makes every participant record - and whether bit 4 of +0x38 is EVER
   set for anyone, in any state - a permanent offline question. Method:
   RE_scripts/rig_full_dump.sh (dbghelp MiniDumpWriteDump; the comsvcs route FAILS on the
   rig, do not retry it). A dump is SCENARIO-SCOPED, not time-scoped (20.221 R5).

## THE THING TO SAY OUT LOUD ABOUT "BEHAVIOURAL CHANGE"

Three independent eliminations now point the same way: the gate fields are probably NOT fed
by anything the server sends. If that holds, the fix is a CLIENT-SIDE WRITE (the STAGE-TRAY
populate-at-apply mechanism - its premise was retracted but the mechanism is sound and
already designed), not a fork wire field. That is still a behavioural change and still a
real boot - but it is a different shape from "send a new message", and the lane should stop
expecting a wire fix.

## PRE-NAMED FOR THE FIRST SUCCESS (20.125 precedent, other session)

When the gate passes, expect a second body with DEFAULT/identity-level appearance, moving
from the already-flowing dynamic stream. Correct armour is a separate, still-unidentified
carrier and is its own later front. A default-looking second guardian is the construction
path WORKING - do not read it as a failure.

## STANDING, UNTESTED (carried since 20.208, marked in every chain-marks block)

Does a constructed receiver render a peer AT ALL? The local guardian renders while
ent_recv/ent_create log ZERO calls, so guardian rendering demonstrably does not require
this path. This assumption underwrites the entire lane and has never been tested.

## INSTRUMENT STATE

Deployed: client a83f02c8e0e671ab (both machines), 34 targets incl. ptable 0x1417021C0
(the whole gate in one line: table, three masks, per-participant record bytes + verdict).
Server a9d033e2487b9cbe, settings entity_index_* all FALSE, reserve 8 / join_grant 4088.
NEXT PROBE FIELD, one line, prevents a wild goose chase: log the SELF INDEX beside the
per-participant verdict. Without it, "FAIL-cond3 on i=0" cannot be told apart from "self,
correctly excluded" (20.232 R1) - and solo data makes both readings survivable.

## TOOL DEBT RAISED THIS SESSION

- field_xref --sib-scan lacks the boundary validation --disp8 gained; its hits must be
  disassembly-confirmed (20.232 R3). Reported.
- .pdata attribution must sanity-check range size: 0x1405B9260's entry is 4.3 MB and is a
  catch-all, not a function (20.233 R4).
- Constant hunts: byte-prefilter then decode. The naive full-image capstone sweep and a
  per-address subprocess loop were both killed for hanging (20.233 R1).
