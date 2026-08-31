# BOOT BRIEF - p2(56), the first boot that can deliver a peer row (2026-08-26 ~19:10)

## THE POINT OF THIS BOOT

The client has **never once been asked** whether it accepts a foreign player in
its roster. Every previous verdict was measured against a peer that was actually
the player themselves (pre-p2(45)), or against a message that failed to encode
and never left the server (boot #9, FINDINGS 20.78). This boot asks the question
for the first time.

**Win or lose, we learn the single fact the whole front rests on:** does the
client accept a foreign member row, and if not, what does it say about it.

## WHAT THIS BOOT DOES *NOT* TEST

- It does **not** test whether two guardians can see each other. Even a fully
  accepted peer row leaves both clients self-hosting; nothing here assigns the
  guest role (types 8 -> 9/10 are still unanswered, gap 5).
- It does **not** test the Steam transport. `send_rendezvous` remains a log-only
  sink and the inbound callback still cannot be delivered (gap 2).
- It does **not** test the trailing-field semantics. The reading is PINNED to
  `packed_masks`; no sweep runs.
- It does **not** test lobby convergence (gap 1) or the empty bubble-host table
  (gap 4).

## PRE-BOOT CHECKLIST (AGENTS.md, binding)

### 1. Provenance - ASSERTED
```
built    1991b3da6f518165
deployed 1991b3da6f518165        HASH ASSERT: match
```
All seven deploy gates rc=0. Instrument literals confirmed present IN the
deployed file: `stage=peer_advert`, `stage=body_capture`, `stage=membership_peer`,
`result=encode_fail`, `stage=membership_ack`.
Fork `upstream-gameplay-scoped` @ `f0059b5`, clean.
**Client DLLs are NOT redeployed and do not need to be.** The machines keep
`e957951643ed987a`; the encoder that changed compiles into the DLL as dead code
for a standalone-server boot. Every client-side line this boot reads
(`peers valid`, `ev=retail`, `ev=steamnet`) already exists in that DLL.

### 2. Liveness - a line that MUST appear whatever the outcome
`ev=activity stage=peer_advert result=... own_region=N peer_region=N
own_citizen=0|1 peer_citizen=0|1` at **info** level, emitted on **every**
peer-bearing body including the boring path. New this build precisely because
two of the three "no peer endpoint" causes previously logged nothing.

Second, independent liveness signal - the body size alone names the shape:
```
  body=3882   solo + own citizen           (no peer row)
  body=3967   peer row + own citizen only  (peer named, endpoint NOT delivered)
  body=4095   peer row + BOTH endpoints    (the full delivery)
```
Those three numbers are exact, come from the gate, and 3882 is corroborated by
every solo body in boot #9.

### 3. Both negatives pre-named

**CONTENT negative** - the body ships and the client refuses it:
`stage=push type=12 body=3967|4095` followed by no `membership_ack` advance, then
`membership_peer result=withdrawn unacked=2`. Read the client's own verdict in
the type-14 `release_peer_reservation` payload (reason index into the peer-link
failure enum: 1 = tried-to-join-self, 5 = privacy-mode). **This is a RESULT, not
a failure** - it is the first genuine refusal we would ever have collected.

**ABSENCE negative** - zero `stage=peer_advert` lines means the peer condition
never held: the two sessions never coexisted in the same destination, so
`foreign_member_identity` never returned a peer. That indicts the SETUP, not the
client. Check both sessions reached `city_tower_social_d2` state=3 and overlapped
in time before concluding anything.

**Third outcome, pre-named because it has happened before:** the client
hard-freezes on a peer body. Retry cap is 2, and the observed freeze took six
bodies, so we should stay well under. **If it freezes anyway, the finding is HOW
MANY `peer=1` bodies preceded it** - record that number.

### 4. Chain marks (lesson 16)

| link | mark |
|---|---|
| two sessions coexist in one destination | verified-by-execution (boot #9) |
| accounts and identities are separated on the wire | verified-by-execution (20.68-20.74) |
| the peer is genuinely foreign (distinct member key AND account) | verified-by-execution (boot #9: 0x6F52AA…/0x846C83…, acct …100100/…110100) |
| a peer-bearing body ENCODES | verified-by-execution (gate, six cases, seen to fail without the fix) |
| a peer-bearing body is TRANSMITTED | **THIS BOOT resolves it** |
| the client ACCEPTS a foreign member row | **THIS BOOT resolves it** |
| one client takes the GUEST role | assumed-false; not addressed here (gap 5) |
| the two machines can carry peer traffic | unknown; not addressed here (gap 2) |

### 5. Graphics delta (lesson 12)
**ZERO.** No item definition, loadout or equipped-item change. No
never-before-rendered models are introduced, so character pick compiles exactly
the shaders it compiled last boot. This boot carries no renderer risk.

## THE RUN

1. Boot the Mac, take it into the Tower, let it settle.
2. Boot the rig, take it into the Tower.
3. Leave both standing for ~60 s. **Then have one player walk a short distance**
   - region is client-reported and the two must occupy DIFFERENT bubbles for the
   peer endpoint to be deliverable at all (`same_region` skips it by design).
4. Quit both.

## WHAT I READ AFTERWARDS

Server: `stage=peer_advert` (reason + both regions), `stage=push type=12 body=`
(3882/3967/4095), `stage=membership_ack` revisions, `stage=membership_peer`
included/withdrawn, `result=encode_fail` (must be ZERO), `stage=body_capture`
(must be non-zero if any 3967/4095 body shipped), any type-13/14 payload.
Clients: `peers valid:` - **success is `0x3` with a `peer # 1` row.**

**Grep every capture with `grep -a`.** These logs contain NUL bytes and plain
grep silently returns nothing.
