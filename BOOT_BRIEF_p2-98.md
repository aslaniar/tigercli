# BOOT BRIEF p2-98 (2026-08-28) - WHICH CALLER CREATES A PEER SLOT? The one probe that
# decides whether the fix is server-side or client-side.

STATUS: live (2026-08-29 ~00:0x). Client-DLL-only, LOGGING-ONLY. The p2(97) injection is
still in the tree and still switched OFF. Server unchanged from p2(96).

## PURPOSE
20.159 resolved the 0x1417692E0 collision: it is ONE function, it is the PEER-SLOT
CREATOR (it writes the slot machine id at +0xc8 that p2(97)'s census reads), and it has
five callers. Two of them sit inside fn 0x141781800 - the message-30 membership apply,
the handler for the bodies THIS SERVER PUBLISHES - and both pass kind 0xa, the same
"type-0x0A" the roster-caller lane attributed to a client-to-client join.

That is the fork in the road, and it is a big one:
  - if the message-30 apply ever reaches the creator FOR A PEER, the fix is SERVER-SIDE,
    in a body we already send every keepalive;
  - if only the join gate (fn 0x141772440) ever does, the DLL injection is the road, and
    20.158 says it must create the SLOT, not just the member record it currently writes.
One observer answers it, because the caller's return address names the path.

WIN: `ev=admission stage=slot_create` lines carrying caller RVAs. Caller 0x1782C9E or
0x1782D36 = the apply path (server-side road). Caller 0x1772A99 = the join gate. Caller
0x1769295 / 0x17ABC90 = the two small callers, unclassified so far.
LOSE: no slot_create lines at all - see ABSENCE; the creator is reached some way the
caller scan missed, and 20.159 CLAIM 3 needs re-reading.

## GRAPHICS DELTA
Zero. No new rendered models, no rendering change: one detour that calls the original
untouched and logs its caller. Both clients load the same Tower as p2(93)-p2(97). Boot
minimized where possible; the result is read from the logs.

## FALSIFIABLE CLAIM
Each client emits at least one `ev=admission stage=slot_create` line with
`machine_after` equal to that machine's OWN slot-0 machine id (mac 0x2A2A21C73725326F,
rig 0x65556BF27BB8602 as measured in p2(97)), because p2(97) proved slot 0 exists and is
populated on both - so something creates it, and this observer sits on the only function
that writes that field.

CONTENT NEGATIVE: slot_create lines whose caller is ONLY 0x1772A99 (the join gate) mean
the message-30 apply never reaches the creator in a real session. That CLOSES the
server-side road opened by 20.159 and commits us to the DLL injection - a real result.
SECOND CONTENT NEGATIVE: an apply-path line (0x1782C9E / 0x1782D36) that creates a slot
for the LOCAL machine only tells us the apply CAN create slots but our bodies only ever
describe self - which makes the fix "publish a peer row the apply accepts", a body
change, and moves the question to the guard at byte[rsp+0x51] (20.159 CLAIM 4).
THIRD CONTENT NEGATIVE: `machine_before == machine_after` on every line means the
creator was called but wrote nothing - it was a lookup, not a create, and CLAIM 2 needs
re-reading.

## ABSENCE NEGATIVE
- `ev=admission stage=install` prints on every attach with its reason and now echoes the
  slot RVA. `result=fail why=attach_slot` or `why=range_slot` = the observer did not
  attach and the absence of slot_create lines means NOTHING.
- p2(97) proved slot 0 is populated on both machines, so a boot with install=ok and ZERO
  slot_create lines is a real anomaly, not an empty result: it would mean the slot is
  created before our DLL attaches, or by a path the caller scan did not find.
- Slot creation is not a per-tick event, so every call is logged up to a 48-line cap
  rather than only changes. A handful of lines is expected.

## CHAIN MARKS
- 0x1417692E0 derives the 0xb8 slot array, a 0x38 array and the peer states (+0x1758,
  stride 0x120) from ONE base, matching both lanes' geometry exactly -
  verified-by-reading (20.159 CLAIM 1).
- It writes the slot machine id at +0xc8 - verified-by-reading (store at 0x1417695bc).
- It has exactly five direct callers, two inside fn 0x141781800 - verified-by-execution
  (call-site scan over .text; no indirect/lea reference exists).
- Both apply call sites pass kind 0xa - verified-by-reading (0x141782c84, 0x141782d19).
- Slot 0 exists and is populated with self on both machines - verified-by-execution
  (p2(97) census, ok=1).
- The ABI (RCX obj, EDX index, R8D kind, R9D flag, four stack args) - verified-by-reading
  off both apply call sites; the observer mirrors all eight arguments.
- The return type - ASSUMED. Declared u64 and passed through, which is correct for an
  int/bool return and harmless if the function returns void.
- That the apply path can be made to create a PEER slot - assumed, and NOT tested here.
  This boot only names which callers fire.

## ADVERSARIAL PASS: waived: solo main-session boot prep, no second reviewer available
in-session (B-checkpoint exception). Adversarial surface: this hooks a function on the
membership-apply path, which runs on every membership body - potentially often. It is
bounded by a 48-line cap, calls the original first, formats nothing past the cap, and
SEH-guards its two field reads. The p2(97) census hook on the adoption arm ran clean in
the same build, on a comparable path.

## INSTRUMENTS:
  "ev=admission stage=slot_create"
  "ev=admission stage=install"

## SWITCH POSITIONS FOR THIS BOOT
  client.admission_census    TRUE   (unchanged; its census also re-runs)
  client.admission_inject    FALSE  <- MUST stay false; 20.158 showed it has no target
  client.admission_member_index 0
  client.admission_xuid      0
  join_roster_observer       FALSE  both clients
  slice_set                  56     both clients
  server: unchanged from p2(96); gameplay switches as p2(93)

## ROLLBACK
Client DLL only, all halves observation. Prior DLL `4951f587da240dba` (p2(97)). Server
needs no rollback.
