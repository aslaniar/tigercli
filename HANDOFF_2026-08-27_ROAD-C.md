# HANDOFF: road C is open. The peer link works; one parameter blocks the session.

STATUS: live (2026-08-27 ~21:0x, Claude Code -> next session). STATE.md outranks this
file when both are current. Read STATE "THE VERDICT" first, then
FRONT_public-host-chain.md, then FINDINGS 20.113 -> 20.122 newest-first.

## 1. THE ONE THING TO UNDERSTAND

**The client does not trust anything we declare over BAP.** It walks its OWN
managed-session member table and tracks only members that reach state 10
(ESTABLISHED); anything else it warns about and releases (20.112/20.113). Twenty
boots of wire-shape work aimed one layer too high. That whole class is retired - see
STATE "DEAD ENDS".

The only route to state 10 is the game's own peer layer, and **that route now works**.

## 2. WHAT CHANGED TONIGHT (all verified by execution)

- `ev=gameplay stage=receive` went from ZERO on every boot in project history to
  37-64. The client dials the gameplay endpoint (20.118).
- Full stack: DTLS, establish, connect, link bound, group join, membership built,
  player added, `join result=completed`, and the peer's parameter request ANSWERED.
- Client side: `reserve` fires for a SECOND MACHINE at `memb=10`; `peers valid`
  went 0x1 -> 0x3; the activity client took the **PUBLIC TARGET** role after reading
  PRIVATE CURRENT on every line of every previous boot.
- The tracking-data warning and the peer-reservation release - the two lines that
  ended every peer's life for weeks - **do not fire at all** any more.

Three changes did it, in order: serve OUR OWN gameplay endpoint as the session-search
answer (p2(75), 20.114); force the TOWER's region public at the native decision point
(p2(78), slice set 56, 20.117/20.118); gate membership publication on the
application-ready boundary (p2(79), 20.119).

## 3. WHERE IT STOPS, AND IT IS ONE PARAMETER

Every ~22.8 s the peer rebuilds its channel and redoes a completed join. Cause:
    stage=parameters result=request  names=public-session-reservations
    stage=parameters result=ambiguous walked=0x00000000 stopped=21 tail=8039
Registry index 21 IS `publicSessionReservations`. Our ANSWER for it is a deliberate
clear root bit - "no value, keep your own" - because its body layout is unrecovered.
The client then logs "Updating public bubble reservation peer request ... to '0'
SLOTS" and recycles the session. A public bubble with room for nobody.

The client's request body is EMPTY (`0804 00..00`, 20.121): it is ASKING us for the
value, not telling us one.

## 4. THE NEXT MOVE, ALREADY SCOPED (static, no boots, no machines)

20.122 found the client's parameter registry builder: **fn 0x1417A9820**, called from
0x14178CD4D, located from the name string `public-session-reservations` @
0x141CA8648. Record layout, class markers, and the fact that 21/23/24 share a marker
the others lack are all in 20.122.
The grammar is NOT in the builder. Every record shares one object at `[rbx+0xB958]`,
stored at `rec+0x18`. That object is the common owner and is where a codec or vtable
lives. Steps:
  1. Read fn 0x1417A9820's prologue for what fills `[rbx+0xB958]`, and its caller
     0x14178CD4D for what rbx is.
  2. If it has a vtable, read the slots - expect an encode/decode pair keyed by the
     class marker at rec+0x24.
  3. Only then encode parameter 21's answer body.
**DO NOT GUESS THE LAYOUT.** Handbook 16.5 makes a wrong nesting a policy-31 FATAL
decode, and p2(80) already cost a boot to a guess this session (20.120).

## 5. AFTER THAT: L8, AND IT IS THE LAST STRUCTURAL PIECE

Both clients name the SAME group session. `claim()` (group_host.cpp:147) is keyed by
session and REBINDS its single record to whichever endpoint joined last - written for
one client reconnecting from a new port. With two clients they steal it from each
other and every snapshot stays `members=2 players=1`.
L8 = `Admitted` holds an endpoint LIST; `publish_snapshot` builds host + N peers with
N players; each peer's own entry carries ITS OWN join id and ITS OWN address blob
echoed byte-exact. All three constraints are already stated in group_host.cpp's own
comments. `kSnapshotMemberCount = 2` is where it starts.

## 6. OPERATIONAL FACTS THAT WILL BITE YOU

- **`reset_lobby_claims.sh` before a run is a PRECONDITION, not hygiene** (20.121). A
  public region with no search is a HARD STALL: one boot forced the region, never
  searched, never dialed, and froze on spawn-in with the game alive.
- `region_public_slice_set: 56` is the Tower. **24 is orbit and 48 is the initial
  slice set - do not force those.** p2(76) forced all three and stalled on orbit,
  which has no host to connect to.
- p2(80)'s keepalive is a **proven no-op** (fired zero times). It is left in place,
  inert. Do not cite it as a fix.
- The render-death class is still unexplained and still parked: it follows
  CO-PRESENCE, not entry order (20.111 corrected 20.110).
- One long-running or ssh-touching action per shell call. A frozen client holds the
  DLL open and blocks its own redeploy - taskkill it first.

## 7. TWO METHOD RULES THIS SESSION PAID FOR (both now in LESSONS)

- **U1 corollary**: the oracle you already hold counts. "The only remaining unknown is
  one protobuf shape" was carried for three days while the answer sat in
  `RE_output/dumps/bungie_bullshit_guide.txt` - a file this project extracted,
  digested and lists in its own doc map. Grep the local corpus before naming anything
  an open RE question. The handbook has now supplied FOUR gates.
- **L13 corollary 2**: an explicit stage list is a filter, and a filter's absences are
  its own. "21.5 s of complete silence" was a grep that omitted `stage=packet`, which
  was arriving every 250 ms throughout - and a whole build was designed on it. Census
  first (`grep -o "ev=X stage=[a-z_]*" | sort | uniq -c`), then filter. Match the
  event prefix too: `stage=keepalive` collided with a pre-existing `ev=activity` line.

## 8. STATE OF THE TREE
Server `72177ecd4083e6b0`, client `3fa02bb785a1cacc` on BOTH machines, fork p2(81)
= d7ec16b, both repos clean. Settings: both machines `region_public_slice_set: 56`,
`region_public` false, `region_private` false; server `search_self_host: true`.
Boot logs archived under RE_output/boots/p2-78_*.
