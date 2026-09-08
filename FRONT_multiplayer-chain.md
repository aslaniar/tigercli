# FRONT - THE MULTIPLAYER CHAIN (mechanism-grounded; replaces hypothesis tracking)

STATUS: live (2026-09-08, built in 20.336). This chart tracks THE CHAIN THE GAME
ACTUALLY FOLLOWS - each row is a thing that must be true for a peer's guardian to
appear, in causal order. It is NOT a list of the project's hypotheses.

READING RULE: a row is DONE only when it is MEASURED WORKING in a named boot -
never when a hypothesis about it was eliminated. "Eliminated" belongs in FINDINGS,
not here. Every row names WHO OWNS IT, because that decides whether we can act.

## STAGE A - TRANSPORT, SESSION, ROSTER  (complete)

| # | What must be true | Owner | Status | Evidence |
|---|---|---|---|---|
| A1 | Both clients exchange packets with the server | server+client | DONE | acks climb through probe sequences (p2-197) |
| A2 | Both clients join the server's activity session | server | DONE | join_result completed, both machines |
| A3 | The roster the server sends is ACCEPTED (checksum passes) | server | DONE | p2-205/206: zero `membership checksum failed` lines |
| A4 | The peer appears as a MACHINE in the roster | server | DONE | p2-206 `peers valid: 0x7` (3 peers) |
| A5 | The peer appears as a PLAYER slot in the session | server | DONE | p2-206 `players valid: 0x3`; `player-properties accepted for player #0` and `#1` on group_target |
| A6 | Both clients load the same world instance | server | DONE | both `changed world to: city_tower_social_d2` |

## STAGE B - WHO IS THE PEER  (UNRESOLVED - do not build on it yet)

READ THE WARNING BEFORE THE TABLE. Stage B was mis-stated FOUR times on
2026-09-08, by me, in one session:
  (1) "the peer's identity fields are never sent"  - wrong, they are wired
      (foreign_member_identity fills the real row, activity_session_lookup.cpp).
  (2) "the character override corrupts them"       - wrong, that override lives
      inside the crafted-self-row branch, which is OFF.
  (3) "the peer row is refused 62 of 63 times"     - WRONG AND INVERTED. Only
      REFUSAL lines carry a `reason=` field, so a regex requiring `reason=`
      selected the failures and reported them as the population. The measured
      truth is 482 of 545 snapshots DID carry a peer.
  (4) "the mac is starved 22:1"                    - unsupported. `result=paced`
      (412 of 487) is the 30-SECOND DUTY CYCLE doing its job, not a failure, and
      `key=` names the PEER IN THE ROW, so a key tally is not a per-recipient
      delivery count.
The common cause: reading one stage of a THREE-STAGE pipeline and treating it as
the whole. Nothing in this stage should be acted on until the pipeline's three
line families are read together - which `chain_status.py` now prints separately
and explicitly refuses to summarise.

THE PIPELINE, and what each line family actually means:

| Line | Stage | Meaning |
|---|---|---|
| `wire_snapshot peer=0/1` | COMPOSITION | was a peer put into the body at all. Only peer=0 lines carry `reason=` |
| `membership_peer result=included\|paced\|gained` | PUBLICATION | `paced` = held by `membership_peer_duty_cycle_ms` (30000). Not a failure |
| `key=0x...` on those lines | SUBJECT | the peer NAMED IN the row - a row naming machine X goes to the OTHER machine |

MEASURED ON p2-206 (complete archive, both clients in the tower):

| # | What must be true | Owner | Status | Evidence |
|---|---|---|---|---|
| B1 | A peer is composed into the body | server | **MOSTLY YES** | 482 of 545 snapshots carried a peer. The 63 that did not: `same_account` x48, `none_joined` x9 (before the rig joined), `same_client` x5, `identity_missing` x1 |
| B2 | The row is actually published | server | **THROTTLED, cause unknown** | included=70, paced=412, gained=5. Whether 70 publications in a 5-minute boot is adequate is UNMEASURED - the duty cycle is 30s and nobody has checked what the client needs |
| B3 | Both clients receive rows at a workable rate | server | **UNRESOLVED** | rows naming the mac: 65; naming the rig: 3. This is NOT established as starvation - it must be checked against join times and the duty cycle first |
| B4 | The row carries the peer's account + character | server | WIRED | `stage=identity result=ok key=0xE4DD... acct=0x9EAA300100100100 character=0x9EAA300100100101`; field5 IS the character; both accounts held distinctly (key=0 and key=1) |
| B5 | The client can LOAD that character's data | server+client | UNREACHED | 20.295 R0/R1: the client READS the character field and a named NON-LOADED character BLOCKS instantiation |
| B6 | The row carries a reachable address ("citizen") | server | UNVERIFIED | `membership_peer_same_region_advert` is TRUE today, never re-measured on a REAL peer row |

WHY THE GUARDS EXIST - DO NOT SIMPLY DELETE THEM. `same_client` and
`same_account` were written against reproduced failures:
  same_client  - one client holds several BAP connections, so its own sibling
                 session came back as a "peer" and the client rendered a second
                 copy of the LOCAL guardian named "You". That is what 20.53's
                 retracted "milestone" actually was.
  same_account - two characters of ONE account are not peers even across two
                 machines with distinct Steam identities and member keys. The
                 client refuses that roster as `tried-to-join-self`; it cost TWO
                 HARD CLIENT FREEZES (20.64).

THE NEXT HONEST STEP FOR STAGE B (not yet taken): correlate the three line
families on ONE boot against each machine's join time, and establish what
publication rate the client actually requires, before changing anything.

## STAGE C - ENTITY SUPPLY  (partial)

| # | What must be true | Owner | Status | Evidence |
|---|---|---|---|---|
| C1 | The client holds free entity index slots | client | **PARTIAL - runs dry** | manager is low=100/high=200; fills once (~150), drains in 6, reads `mgr_free=0` for the rest of the boot. Rig failures run t=51594..237031 - 185s past its one fill |
| C2 | The server supplies indices for ALL members | **server** | **NOT DONE - unbuilt** | `index_allocation push members=1` x17 in p2-206 - the CADENCE is adequate, but EVERY push names ONE member. Call site: *"the cross-member map is deferred"*. Encoder already supports 64 rows |
| C3 | Entity creation succeeds | client | FAILS 17-80x/boot | `failed to create 'player_broadcast' entity` in EVERY archived boot, both machines. NOTE: the LOCAL player recovers - 7 of 24 mac attempts succeed once the pool fills |

## STAGE D - THE REPLICATION RECEIVE PATH  (the structural wall)

| # | What must be true | Owner | Status | Evidence |
|---|---|---|---|---|
| D1 | The four ent receive-block objects EXIST on the client | client | **NOT DONE - the wall** | zero heap instances in SIX dumps (p2-146, p2-180, p2-205, p2-206 + 2). Re-tested 2026-09-08 with the correct needle (vtable bases, 20.336 R4) - still zero |
| D2 | The chain that builds them is entered | client | **NEVER RUNS** | 9 hops, EVERY ONE single-caller: `0x140B5ECD0 -> 0x1416FCDF0 -> 0x1416F6640 -> 0x141709800 -> 0x141702580 -> 0x141703910 -> 0x1416FF3C0 -> 0x1416CA0B0 -> 0x1416BB1E0`. The root has NO direct callers - it sits in a VTABLE slot, .rdata RVA 0x1C166A0. So construction is a VIRTUAL METHOD that is never invoked |
| D3 | The server sends a peer entity | server | DONE | p2-197: `result=sent` x8, packets acked, no drops |
| D4 | The client CONSUMES it | client | NOT DONE | silent - blocked by D1, not by the wire |

## STAGE E - THE BODY

| # | What must be true | Owner | Status |
|---|---|---|---|
| E1 | A guardian body is instantiated from the entity | client | UNREACHED |
| E2 | It renders and moves | client | **THE GOAL** |

## HOW TO READ THIS CHART

TWO independent things are missing, and they may be the same thing:

  STAGE B  the client has a player slot for the peer but NO IDENTITY IN IT -
           no account, no character. Server-owned, never sent, cheap to test.
  STAGE D  the machinery that would receive a peer's body is never built.
           Client-owned, and the construction path is a virtual method that
           never fires.

THE LINK WORTH TESTING FIRST: D may be DOWNSTREAM OF B. A client with an
anonymous player slot has nothing to build a body FOR - so it may never
construct the receive machinery. That is a testable ordering, not a claim:
fill in B (server-side, allowed) and re-census D1 from a dump. If D1 stays at
zero with the peer fully identified, then D is genuinely independent and the
question becomes what owns the vtable at RVA 0x1C166A0.

WHAT IS *NOT* ON THIS CHART, AND WHY: the join gate, the state ladder, the
retarget arms, the (3,4) stall, the view message, the type-9/51 designations,
idx_alloc-as-blocker, the +0x818 and cond5 hunts. Each was a HYPOTHESIS about
where the chain ran, and each was eliminated. Eliminations live in FINDINGS.
A chart that lists them reads as progress; it is not.

STAGE C's honest weight: C1/C2 are real unfinished server work, but the local
player recovers from C3, so C is NOT established as a peer-render blocker. Do
not promote it to one without evidence.
