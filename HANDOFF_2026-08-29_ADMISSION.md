# HANDOFF 2026-08-29 - ADMISSION: the roster is solved, the forge is not

STATUS: live (2026-08-29 ~02:2x). Supersedes HANDOFF_2026-08-28_EVENING_GATE-REVIEW.md
(itself already marked superseded-by 20.153). Read with FINDINGS 20.153-20.166, newest
first in FINDINGS_2026-08-25.md. NOTE 20.166 (the p2(104) mac-only boot): the stall
needs NO peer and the client sends NOTHING on the wire while stalled - the forge-stall
reading below is refined, the paired capture remains the gate (D3 leading).

## READ THIS FIRST - THE MACHINES ARE ON DIFFERENT BUILDS
This is the one thing that will waste your first boot if you miss it.
```
  MAC client DLL  5d7e6bd61e078c24  = p2(98). WRITE-FREE. No injection code at all.
  RIG client DLL  ba6013a2d08cbd46  = p2(103). Injection code PRESENT, disarmed by
                                      settings default (the rig has no admission keys).
  SERVER          b9b0f3823f74d1bf  = p2(96). Unchanged since; all gameplay switches
                                      as p2(93) incl. slice_follows_region=1.
```
Both are SAFE and neither injects today, but they are not the same binary. To align
before booting (run each as its own shell call - the rig one touches ssh):
```
  bash RE_scripts/deploy_client_dll.sh mac "ev=admission stage=inject"
  bash RE_scripts/deploy_client_dll.sh rig "ev=admission stage=inject"
```
That puts both on the current build (injection present, `admission_inject=false` on the
mac, absent-and-defaulted-false on the rig). The mac's settings still carry the working
injection parameters; flipping `admission_inject` to true re-arms with NO rebuild.

## WHAT THIS SESSION SETTLED (do not re-derive any of it)
- **20.104 IS CLOSED.** The mac's roster named the RIG's xuid, reproduced on two boots
  (p2(102), p2(103)). Slot + member record is what the adoption path needs; it has no
  self/peer filter and never did.
- The slot creator 0x1417692E0 is fully characterised: ABI, all eight arguments, the kind
  that creates (5, not 10), and the whole slot layout. The "mystery 0x50 blob" is an ASCII
  identity string (20.162).
- A FABRICATED per-session machine id (a7) is accepted at creation AND by the adoption
  consumer (20.163/20.164). It does not have to be the peer's real value.
- The server road for admission is CLOSED BY MEASUREMENT: the type-0x0A join never reaches
  the group-host pump (20.157, zero fallthrough across a full boot), and the message-30
  apply's slot-creator call sites never execute (20.160).
- The public world swap is NOT the managed-session-start gate. Both clients cross it. The
  z-leg (`normal_z_leg`, transition type 3) is never polled for its phase - by design, the
  constructor covers types {2,4,5,6,7} only (20.156). Its poll path rejects on
  `dword[obj+0x524] == -1` (20.157). The phase branch is CLOSED; do not resume it.
- PROVENANCE TRAP, still live: destiny2_unpacked_full.exe was dumped from a HOOKED process,
  so at hooked call sites its first bytes are OUR patch, not the game's (20.155).

## WHERE IT STOPPED, AND WHY
The injection works and is insufficient. It makes the client believe it has a peer; the
client then tries to USE that peer during activity setup, and a forged peer cannot answer.
p2(102) hard-froze at `setup:orbit`; p2(103), with a verbatim copy of a live record,
black-screened with moving frames at the same place - alive, rendering, waiting.
20.164's "the record was incomplete" inference is REFUTED by p2(103). The record also
carries SELF's address block (a documented approximation), so anything routing on it sees
two records claiming one address.

Two forge attempts, two broken clients, one boot each. U7 says stop.

## THE RECOMMENDED NEXT STEP
Capture the PEER CHANNEL. The clients have had DTLS channels established both directions
since 20.144 - they are already talking to each other - and we have never once read that
conversation for this question. p2(96) proved the admission join is not on the server
path, so if a real admission exchange exists it is there.
```
  tcpdump -i en0 -s0 -U -w <out> 'udp port 3097'      # TOOLS.md; no sudo needed
```
Filter BOTH directions (`src port 3097 and dst port 3097`); the payload is DTLS-encrypted,
so read it by SIZE and CADENCE, not contents (20.144 did exactly this successfully).
This reframes the question from "how do we forge a peer good enough to survive" to "what
does real admission look like and why does it not complete" - no client memory writes, no
risk to either machine.

## IF YOU DO RESUME THE FORGE ANYWAY
The one named suspect is the SELF address block. Do not guess at record contents again -
two inferences died. Instrument the record's other READERS (who reads member index 1
between the roster and setup:orbit) and let that name the field.

## HARD-WON PROCESS NOTES FROM THIS SESSION
- A call site that does not run cannot tell you the shape of one that does. p2(99) crashed
  both clients because the argument ABI came from apply-path call sites that p2(98) had
  just proven never execute (20.161).
- SEH (`__try/__except`) inside a `noexcept` detour does NOT make a bad dereference
  survivable. It did not catch it.
- Replay-with-substitution has succeeded twice; partial synthesis has failed twice. Prefer
  copying a live structure and changing one field.
- "Write only what is read" is safe only while nothing else can SEE the record. Setting the
  present bit removes that protection.
- `gate_boot.py --literals` requires every literal in every named binary, so it cannot gate
  a two-binary boot. Take the structural pass plus an explicit per-binary check. A
  per-target mapping would close the gap.

## STILL OPEN, IN DEPENDENCY ORDER
1. Make admission REAL rather than forged (peer-channel capture above).
2. The world swap: `dword[obj+0x524]` is -1 and never populated; its one in-range writer is
   fn 0x140E1D400, guarded on a predicate and on `byte[obj+0x208]`. Whether admission also
   unblocks this is UNPROVEN - the two were bundled in 20.157 and nothing has separated
   them yet.
3. The public bubble reservation reads 0 slots (20.132); the research doc's #4 says it is
   downstream of the member table - re-check once admission is real.
4. The appearance blob (20.145 + the profile-builder lane): route decided (client-memory
   harvest via our DLL, NOT the pcap route), design ready, never executed. This is the last
   mile to two VISIBLE guardians and is independent of everything above.

## INSTRUMENTS ADDED THIS SESSION (all registered / in-tree)
- RE_scripts/field_xref.py - struct-field xref with a 4-case oracle. TOOLS.md registered.
  LIMIT: disp32 forms only; "0 writes" is never proof of none.
- client/hooks/phase_probe - the transition phase query + the two type-3 pollers.
- client/hooks/admission - the adoption census, the slot-create observer with caller
  capture and argument dump, and the switch-gated injection (both halves).
