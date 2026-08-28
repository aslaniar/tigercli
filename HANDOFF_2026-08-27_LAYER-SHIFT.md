STATUS: superseded-by HANDOFF_2026-08-27_ROAD-C.md (2026-08-27 ~21:0x). Its scope
shift still holds; everything after section 2 is overtaken by 20.113-20.122.
Originally: live (2026-08-27 ~12:5x, Claude -> next session). STATE.md outranks this file
when both are current. Read STATE "SCOPE" first; it is the whole point of this handoff.

# HANDOFF: the scope moved up a layer, and we now have an instrument

## 1. THE ONE THING TO UNDERSTAND

**The Steam layer is cosmetic to this goal.** The managed-session player pipeline was
read end to end today and makes NO Steam call (20.106/20.107). Everything shipped on
2026-08-27 - shared lobby id, LobbyChatUpdate, persona name, presence relay - works,
is deployed, and feeds nothing that decides the roster. Do not add friends or
matchmaking bindings for this goal. That is not a preference; it is a read of the code.

**The roster is a reconcile loop, not an injection point.** Per tick, per session slot
(there are TEN, not one):
    adds     = candidates(session+0xC8) MINUS added(session+0x608)
    removals = added(+0x608) MINUS candidates(+0xC8)
A value forced into +0xC8 once is computed as a REMOVAL on the next tick. Only a
sustained source works. That source is the network session message plane -
`player-add` / `player-refuse` / `player-remove`, sitting beside `membership-update`
in the client's own message table (20.104) - which we have never spoken.

## 2. WHAT TO DO NEXT (static, costs no boot)

Locate the `player-add` message handler and read what it requires before it accepts
one. Method that got us here, repeat it: .pdata for function bounds + an E8-displacement
scan for xrefs (both scripted inline in 20.106's session; ~40 lines of python).

**Reservations are the prime suspect upstream.** `no-reservation` and
`no-ambassador-reservation` are join-refuse reasons; LESSONS records a client FREEZE
from naming a foreign peer in the roster without reserving a slot (lead recorded in
20.53); and that lead was deprioritised for three boots once already because trailing-
field guesses were cheaper to run. Do not deprioritise it a second time.

Other layers never touched, in rough priority: the party join state machine
(`party_start_join -> party_join_host -> party_join_clients -> party_join_complete`);
the membership PROTOBUF path, which is a different encoding from the bit-packed
type-12 schema every boot has aimed at; the ten session slots (logs show msi 0 AND
msi 1 per client); `network_session_check_properties` with its "IN SESSION WITH DUDES"
/ "ALONE" predicate.

## 3. THE INSTRUMENT (LESSONS 18) - reusable on ANY unknown code

Three parts, all read-only, all cheap:
  (a) Size a shim table PAST the interface and fill every slot with a per-slot logging
      stub. The client's own calls then name the real ABI.
  (b) Log the ARGUMENT REGISTERS in that stub, not just the slot number. Declaring
      four parameters is safe for a callee taking fewer. Read an argument by whether
      it is stable across machines (constant/flag), an identity (xuid), or a
      module-offset pointer (string).
  (c) `_ReturnAddress()` in any funnel you already hook gives the CALLER's address.
      Report it as a module-relative RVA - image bases differ per machine. With .pdata
      and an xref scan, one address opens a call graph with NO further boots.
Live in: steam/interfaces/tables/logged_empty.h and
client/hooks/retail_log/retail_log_enqueue_observer.cpp. Registered in TOOLS.md.

Corollary: bundle OBSERVATION freely (logging cannot break anything, so it costs no
attribution). Bundle BEHAVIOUR only behind switches flippable without a rebuild -
p2(62) changed six bindings at once, froze, and its cause is now unknowable.

## 4. RETRACTIONS MADE TODAY - do not re-derive from older entries
- "Could not find tracking data for peer" is a SELF-HEALING WARNING inside a per-peer
  loop, not the release. Held as the failure since 20.82; boots #10-#13 were read
  against it (20.105).
- The friends lane was not "closed", it was MIS-MAPPED. Slot 43 takes two pointers to
  identical static strings on both machines - it IS the key/value setter 20.101 said
  was never called (20.103).
- U2 (counts vs bitmasks) is not the lever: five of six sweep variants send
  player_updates=0b11 and the client still reports players valid: 0x1 (20.104).

## 5. STATE OF THE TREE
Both machines on client `a2b9b93646e14827` (p2(70)), server `896b37eec11fe30d`, both
repos clean, fork at ceed017, next number p2(71). Server routes and claim table are
IN-MEMORY: `RE_scripts/reset_lobby_claims.sh` BETWEEN runs. `boot_verdict.sh` reads
both machines and rules mechanically.

DEBT, stated rather than hidden: STATE.md is 134 lines against a 120 budget. The SCOPE
section is the overrun and it should retire once L3 work starts and the framing is no
longer novel.

## 6. SHELL GOTCHAS THAT COST TIME TODAY
Launching the server and deploying to the rig both HANG AFTER SUCCEEDING (a held pipe
and the ssh ControlMaster). One long-running or ssh-touching action per call, never
chained - an interrupt otherwise leaves the server dead or the two machines on
DIFFERENT builds. See ENVIRONMENTS.md "SHELL".
