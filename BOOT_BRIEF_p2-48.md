# BOOT BRIEF — p2(48): the peer boot, packed counts

Deployed and ready. **Two machines.** This one has hard-frozen the Mac before —
read §6 before you start.

---

## The question

With two members in the roster, does the client accept a peer-bearing body when
`peer_and_player_counts` carries **packed counts** instead of the slot mask we
have always sent?

This is the first test in which the trailing fields' MEANING is observable at
all. With one member a mask, a count and packed counts are all the number 1 —
which is why p2(47)'s solo boot could confirm the four-field shape while testing
no semantics (20.63). With two members they finally diverge:

| field (presence idx) | name | we always sent | pinned reading now sends |
|---|---|---|---|
| [4] 996 | `peer_and_player_counts` | `3` (slot mask) | **`0x00020002`** (2 peers, 2 players) |
| [5] 997 | `peer_updates` | `3` | `3` |
| [6] 998 | `player_updates` | never sent | `3` |
| [7] 999 | `player_seq_number` | never sent | `1` |

**The freeze hypothesis, in one line:** if the client reads [4] as a count, every
peer body we ever sent told it *three* members while the roster held two — and it
walked into an absent slot.

Which 16-bit half of `0x00020002` is peers and which is players is unknown, and
this value deliberately does not depend on the answer: with two of each it reads
the same either way.

## 1. Provenance ✔

```
server exe   c6e65a3dbc71f671    built hash == deployed hash (checked)
gates        SIX, all rc=0
fork         upstream-gameplay-scoped @ 845c278, clean
settings     membership_sweep_pin: 0        <- packed_masks, PINNED (never advances)
             membership_peer_retry_cap: 2   <- was 6; see §6
client DLLs  eb893d2b1b6d8534 on BOTH machines — verified on the rig, no redeploy
identities   Mac ...861   rig ...862   (distinct: a genuine foreign peer)
```

Literals confirmed in the deployed file: `packed_masks`, `stage=membership_ack`,
`request_peer_reservation`, `release_peer_reservation`, `result=withdrawn`.

## 2. Run it in this order

1. **One-machine control first.** Launch the Mac client alone, let it reach a
   destination. Confirm:
   ```
   grep -a "stage=wire_snapshot" RE_output/s1_accept/Sunrise/logs/sunrise.log | tail -3
   ```
   Every line must read `peer=0`. `reason=same_client` or `none_joined` is correct
   — it is the p2(45) self-peer exclusion working. **If any line reads `peer=1`
   with only one machine up, stop: that is the self-peer bug back, and every
   result after it is void.** Sixty seconds, and it is what caught it last time.
2. **Then launch the rig client** and bring it to the same destination.
3. Watch the log.

## 3. Liveness (must appear, whatever the outcome)

```
grep -aE "stage=wire_snapshot|stage=membership_peer" RE_output/s1_accept/Sunrise/logs/sunrise.log
```

Once both clients are in, `wire_snapshot ... peer=1` and
`membership_peer result=included key=0x...` must appear. **If they never do, the
boot tested nothing** — the server never found a foreign peer, so no reading was
ever published. That is a matchmaking/join problem, not a verdict on the counts.

## 4. The verdict

```
grep -aE "stage=membership_ack|result=withdrawn|name=re(quest|lease)_peer_reservation" \
     RE_output/s1_accept/Sunrise/logs/sunrise.log
```

## 5. Both negatives, pre-named

| observation | reading |
|---|---|
| `membership_ack result=ok` on a body sent while `peer=1`, revision advancing, **and both guardians visible** | **PASS.** The counts reading is right and the peer front is open. |
| `membership_ack result=ok` but no second guardian renders | Body accepted, roster applied, something downstream (spawn/replication) is the next gap. A real result, not a failure. |
| `membership_peer result=withdrawn variant=packed_masks unacked=2` | **CLEAN NEGATIVE.** Two peer bodies, no acknowledgement, peer withdrawn, client keeps running on a solo body. Packed counts are not the answer — re-pin to `1` (count_masks) and re-run. |
| client freezes anyway | The counts reading is not the cause, or not the only one. Do NOT re-pin and retry blindly — go to the reservation lead (§7). |
| `name=request_peer_reservation ... payload=<hex>` | **The prize regardless of the verdict.** The client asking for a slot, captured for the first time. |
| `name=release_peer_reservation ... payload=<hex>` | Its refusal, in its own vocabulary. Also never yet captured. |
| zero `membership_ack` AND zero `withdrawn` while `peer=1` lines exist | Fewer than 2 peer bodies shipped. Let it run longer before reading anything. |

## 6. The freeze, and what changed about it

A peer row has hard-frozen the Mac — six bodies did it, and the freeze happens
well inside six. **`membership_peer_retry_cap` is now 2, down from 6.** After two
unacknowledged peer bodies the peer row is withdrawn for that session (sticky),
a solo body goes out, and the client should carry on. A refusal is meant to cost
a clean negative, never a hung client.

That budget is a guess against an unknown threshold. If the Mac freezes anyway,
that is itself information — record how many `peer=1` bodies preceded it.

Rollback: `sunrise-server.exe.bak_p2d6_<stamp>` **with** its matching
`build_data.bin.bak_p2d6_<stamp>` — they are a pair. Settings back to
`membership_sweep_pin: 5` (solo) to make the peer row impossible again.

## 7. Chain marks (lesson 16)

| link | mark |
|---|---|
| four flagged 32-bit fields exist at presence indices 996–999 | **verified by reading** — self-verifying schema node |
| the client accepts a four-field body | **verified by execution** — 20.63, `body=3882`, acked ×3 |
| the encoder emits all four with the pinned values | **verified by execution** — `--membership-wire-test`, both cases |
| the four map to `peer_and_player_counts / peer_updates / player_updates / player_seq_number` | **inference** — Lane M's registry; count and order match. **This boot tests it.** |
| the client READS [6]/[7] at all | **unknown** — they sit at the end; a parser that stops early ignores them |
| a count/mask confusion causes the freeze | **hypothesis** — this boot's actual subject |
| the missing reservation grant (13 → 45) causes the freeze | **untested, still open** — the competing explanation, and §5 sends you here if this one fails |

## 8. Graphics delta (lesson 12)

**Zero.** No definition, inventory or equipment change on either machine.
