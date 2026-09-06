# ESTABLISHMENT DECODE — what advances the peer's connection record, and where it stalls (2026-09-05)

STATUS: live. Static, no boot, every address pdata-anchored. Extends 20.272/20.273/
20.276/20.277. Answers 20.272 R4's question to the second state field's writer
inclusive; the fork-side vocabulary check (20.276 R5 phase 3) remains the one-boot
discriminator. Tooling: field_xref (the T1.3-corrected build), callers.py,
lane_svc43_disasm_range, pdata_bounds.

## CLAIM 1 — the second state field (rec+0x30E8) is written by 0x1417C0260, the connection
## state machine's advancer (VERIFIED)
- addr: 0x1417C0260 (39 B primary + 0x1417C0287..0x1417C07C7 fragment, 1344 B);
  the write site 0x1417C07B0; the predicate-2 check 0x1417C07CC
- claim: 0x1417C0260(container rcx, idx edx, code r8d) ends with
  `eax = [rsp+0x40]; [r14+0x3040] = eax; cmp dword [r14+0x3040], 4` — and on ==4 it
  SETS bit r12 in a manager-level mask at [r13+0x1005C0] (bts/btr), clearing a word at
  +0x3090 and storing a qword at +0x3048. r14 = rec base (the +0x3040 spelling IS
  rec+0x30E8 via the conn-object base alias — 20.276 R2's lesson applied to the
  SECOND field; 20.273's rec-base census could never see it).
- evidence: the disassembly above; the three call sites all pass (container=r13, idx=r12d,
  code in r8d).
- confidence: high

## CLAIM 2 — the advancer is called from ONE state-machine function at exactly three
## transition sites: code 2, code 3, and a COMPUTED state+1 gated on the ladder == 5
## (VERIFIED)
- addr: 0x1418025B4 (7227 B, pdata 0x1418025B4..0x1418041EF; primary 0x141802540,
  116 B — rsi = rcx+0xA8+idx*0x41F0 = THE CONNECTION OBJECT; r15 = [rsi+0x3150])
- claim: the three sites:
    0x141802E81: (container, idx, r8d=2)  — preceded by vtable+0xD0 on [rcx]
    0x1418032F5: (container, idx, r8d=3)  — preceded by vtable+0x80 on r15; the
                 CONNECTING transition; immediately followed by the vtable+0x50
                 dispatch on [rsi+0x3150] (see CLAIM 4) and
                 0x1416D2710(conn, snapshot, -1) — the channel-driving arm (the
                 same family 20.276 R2 named as the ladder state-3 writer).
    0x141803F2B: the 3→4 site — guarded: `[rsi+0x3040]==3` AND `[rsi+0x1D18]==5`
                 (THE EMBEDDED LADDER MUST BE CONNECTED), then
                 `and byte [rsi+0x3068], 0xFD; lea r8d,[rcx+1]` → call (container,
                 idx, 4). THIS is the establishment gate: state 4 on the second
                 field requires the connection ladder at CONNECTED(5).
- evidence: disassemblies of the three sites (in-session).
- confidence: high

## CLAIM 3 — the state machine is driven by five call sites in four functions, one in
## the registered-message-handler family (VERIFIED structure, events UNNAMED)
- addr: callers of 0x141802540: 0x1417CA237 (0x1417CA1F0, 114 B),
  0x1417CCF81 jmp (0x1417CCEC0, 198 B), 0x1417E698E (0x1417E6920, 150 B — adjacent
  to the connected-rung's registered handler 0x1417E5A10/decoder 0x1417E6140),
  0x14180BDFF + 0x14180BE16 (0x14180BDA0, 162 B)
- claim: the machine runs on events from the reservation core AND the session-plane
  handler family. WHICH event maps to WHICH transition is not statically named here.
- evidence: callers.py output.
- confidence: high for the edges; the event semantics = OPEN.

## CLAIM 4 — the +0x50 dispatch inside the state machine is the CONNECTION OBJECT'S OWN
## fifth interface, NOT the four receive blocks (VERIFIED — a near-miss recorded)
- addr: 0x14180332D dispatch; the writer 0x1417C0E5C (in 0x1417C08F0, 1949 B); the
  outer ctor 0x1417BF040
- claim: [conn+0x3150] = an INTERIOR pointer (&conn+0x3158/+0x31C0/+0x3190,
  mode-selected at 0x1417C0E42-0x1417C0E5C); the sub-object's vptr is written by the
  record ctor 0x1417BF040 as 0x141CAF2B0 (lea rip+0x4f0250 → stored at conn+0x3158).
  Its vtable slot 10 (+0x50) = 0x1417D0880 — a per-connection SNAPSHOT BUILDER
  (zeroes 0x1B0 at [rdx+0x88], checks a global byte +0x96 and [conn+0x30]==2, walks
  an 18-bit mask at [rdi+0x80], copies 16 B/entry from conn+0x18). So the 20.302 R7
  "call [reg+0x50]" shape exists HERE too — a near-miss for the dispatcher hunt, and
  a second lesson that slot-10 dispatches are a pattern in this codebase, not a
  unique fingerprint.
- evidence: disassemblies + the vtable dump (0x141CAF2B0 slot 10 = 0x1417D0880).
- confidence: high

## THE STALL, RESTATED WITH THE WRITERS IN HAND
The peer's record in p2-164 reached (3,4): second field=3 (connecting), ladder=4
(established). To advance: the ladder must reach 5 — the connected-rung, message-fed
from the session-plane chain (0x1417E5A10 → pump → 0x1416D56C0: event type 4, subtype
!= 8 → 0x1416BCFC0) — and THEN the state machine's 3→4 site fires. 20.277 R2: the
peer's record stopped receiving updates when its mask bit was cleared at the fork
payload's landing (pre-W4). Post-W4 (20.284: the card lands on the guard's field)
the disown should no longer fire — so the ladder may now climb to 5. THE CHEAPEST
DECISIVE READ: a resv-probe line (state fields) from any post-W4 boot - if one
exists in the p2-176+ archives, the ladder's current value answers whether the
establishment now completes without any further change.

## MEASURED (p2-180, post-W4 + post-duty-cycle): THE STALL PERSISTS
The resv probe's state dumps in the p2-180 archive (mac table, 12 lines):
    rec=0 (the fork-session connection): s30e8=4 s1dc0=5, mask flickering 0x0020
         - the guard's predicates SATISFIED, as in every boot.
    rec=1 (the peer's record, ident 0xFF000C198801A8C0): s30e8=3 s1dc0=4,
         mask=0x0000, touch=-1 - the SAME (3,4) stall as p2-163/164, now measured
         post-W4 (the card lands on the guard's field) and post-duty-cycle (the
         rig landed, the transition completed).
=> The ladder's connected rung still does not mirror for the peer's record, and
the record is still not being touched (the disown/quiet state persists). The
establishment decode's gate (CLAIM 2) explains what is blocked; the remaining
question is WHY the connected event does not mirror - the two live threads:
  (a) the mirror subscriber's connected arm (routed through the event pump:
      event type 4, subtype != 8 - 20.276 R3);
  (b) the disown: the admit family (0x1417AA4F0/0x1417AA610 -> bit-clear
      0x1417C4810) compares SLOT identity vs RECORD identity - 20.277 R3's
      "two different compositions" warning. The W4 card feeds slot+0x142; the
      record's own identity blob is rec+0x3144. IF the disown compares those two
      compositions and they differ byte-wise, the claim fails forever and the
      record goes quiet regardless of the card. NEXT DECODE: the admit family's
      claim check - which fields it compares (static, no boot).

## OPEN (next steps)
1. Check the post-W4 archives (p2-176/178/180) for resv-probe lines: the peer
   record's current (second field, ladder) values. If the probe is not in the
   deployed clients, this needs the one-hook boot (20.276 R5's hook A/B design,
   both pdata-exact and detour-safe).
2. The event→transition mapping for 0x141802540's five callers (which wire event
   drives code 2/3/4) — likely resolvable by one more caller hop up from
   0x1417E6920 into the message dispatch.
3. The fork-side vocabulary (20.276 R5 phase 3): does the fork send the
   connected-marking message for the PEER connection — hook A (0x1417E5A10)
   captures the message vocabulary in one paired boot.

---

## THREAD 2 (2026-09-06, STATIC, NO BOOT): THE PARTICIPANT MASK - WHAT WAS FOUND,
## AND WHERE IT STOPPED

Question taken: the peer record's `mask=0x0000` and `touch=-1` - who should be
touching rec=1, and was the mask bit ever set?

### FOUND (solid)

1. **The mask has exactly ONE direct-displacement writer in the whole binary,
   and it only CLEARS.** field_xref +0x3112: 7 accesses, 1 write. That write is
   0x1417C4841, inside 0x1417C4810..0x1417C4861:

        0x1417C4810(_, edx=bitIndex, r8d=recordIndex):
            rax = 0x1417CF0E0()             ; the table base
            r8  = rax + recIdx*0x41F0       ; the record
            ax = [r8+0x3112] ; btr ax, di ; [r8+0x3112] = ax    ; BIT TEST AND RESET
            ax = [r8+0x3114] ; btr ax, di ; [r8+0x3114] = ax
            ret

   This is the DISOWN function 20.277 R2 inferred. It has 5 callers:
   0x1416FFEF3, 0x1417022CD, 0x1417AA565, 0x1417AA66D, 0x1417B3D4A.
   The sibling word +0x3114 likewise has no setter by displacement (its only
   other "write" is a stack write at 0x14075C198, SIB base rsp).

2. **A SETTER NEVERTHELESS EXISTS AND RUNS** - the internal control: rec=0 (the
   fork's own connection) shows `mask` flickering 0x0000 <-> 0x0020 within a
   single boot, so bit 5 is set repeatedly on that record. The setter is
   therefore real; it simply is not a +0x3112 / +0x3114 displacement write, and
   it is not in the reservation commit pair (0x1417C4200, 0x1417C35F0 - neither
   contains a 0x3112/0x3114 reference or a bts/btr).

3. **The peer record's mask has NEVER been set.** `ident=0xFF...` records read
   `mask=0x0000` in EVERY archive checked back to 2026-09-05 (17 boots,
   including the p2-190 baseline landing and p2-195).

4. **The four mask PREDICATE sites** (all `test [base+idx+0x3112], reg`) resolve
   to: 0x1417C08F0..0x1417C108D, **0x1417C40F0..0x1417C4176** (the reservation
   LOOKUP this document already named), 0x1417CE7B0..0x1417CE84A, and
   **0x1417E56C0..0x1417E5725** - which sits just below the connected-rung's
   registered handler 0x1417E5A10. So the mask is a predicate on BOTH the
   reservation lookup and the connected-rung handler family: the same bitmap
   gates the rung this front is stuck on.

### NOT FOUND (the thread's failure, stated plainly)

The SETTER. A displacement scan cannot see a store through a computed base
(`lea rcx,[rec+0x3112]` then `mov [rcx],ax` appears as a write to `[rcx+0]`),
and field_xref's `--sib-scan` mode is a whole-binary mod=00 dump with no
displacement at all, so it cannot be targeted at this field. Per the project's
scan-negative hygiene rule this is a COVERAGE LIMIT, not a world-fact: point 2's
control proves a setter exists and runs.

### WHAT THIS LEAVES FOR THE NEXT INSTRUMENT

The cheapest decisive read is now a RUNTIME one with a live positive control
already identified: rec=0's bit 5 is set repeatedly every boot. Any instrument
that catches that write catches the setter. Options, cheapest first:
  (a) hook the 5 disown callers to see whether the peer's bit is cleared after
      ever being set (distinguishes "never set" from "set then disowned" - 20.277
      R2 assumed the latter and it has never been measured);
  (b) walk backward from the two predicate sites that matter
      (0x1417C40F0's lookup and 0x1417E56C0's connected-rung test) to whoever
      populates the bitmap they read;
  (c) a write-watch on rec=0's mask address - but that is the U18 invasive class
      the 09-02 wire-watch postmortem retired, so (a)/(b) come first.
