# BOOT BRIEF — p2(47): the four-field trailer, solo control

Deployed and ready. **This is the ONE-MACHINE CONTROL.** Boot a single client on
the Mac only. Do not start the rig.

---

## The question

Does the client accept a type-12 membership body carrying **all four** of the
top-level trailing 32-bit fields its own schema declares, instead of the two we
have shipped since the beginning?

| | before (p2(46)) | now (p2(47)) |
|---|---|---|
| trailing fields published | 2 of 4 | 4 of 4 |
| meaningful bits | 29,968 | **30,032** |
| solo body | 3,746 B | **3,754 B** |
| peer body | 3,831 B | 3,839 B |

Why we think there are four: the client's schema for type 12 (packed key
`0x808086A8`, read out of its own registry — FINDINGS 20.61/20.62) declares four
presence-flagged 32-bit fields at presence indices 996–999, and Lane M's
parsed-struct field registry names exactly four in that order —
`peer_and_player_counts, peer_updates, player_updates, player_seq_number`.
Lesson 17: a declared field we never send is a missing requirement.

**This boot commits to no semantics.** All four fields carry the historical value,
which is `1` in a solo body — and with one member a slot mask, a member count and
packed counts are all the number 1. So the only thing under test is whether the
client accepts the four-field *shape*. Values are the next boot's variable.

## 1. Provenance ✔

```
server exe   c8f6bde2a8f16303      built hash == deployed hash (checked twice)
gates        SIX, all rc=0         incl. the new --membership-wire-test
fork         upstream-gameplay-scoped @ baf5b07, clean
settings     membership_sweep_pin: 5   (solo — NO peer row is published)
             membership_peer_retry_cap: 6, membership_sweep: false
client DLLs  eb893d2b1b6d8534 — UNCHANGED, no client redeploy needed
```

Instrument literals confirmed **in the deployed file**:
`stage=membership_ack`, `stage=wire_snapshot`, `ev=wire_test stage=case`,
`release_peer_reservation`.

The new gate is not decorative: it encodes real solo and peer bodies, seeks to
`region_block_end_bit`, and checks each of the four fields returns the distinct
value it went in with. It was verified to **fail (rc=1)** against a deliberately
reverted two-field encoder before being trusted.

## 2. Liveness (must appear whatever the outcome)

```
grep -a "stage=wire_snapshot" RE_output/s1_accept/Sunrise/logs/sunrise.log
```

Every type-12 body built anywhere converges on this line. If it is **absent**, no
membership body was due and the boot tested nothing — re-run, do not interpret.

## 3. The verdict lines

```
grep -aE "stage=membership_ack|stage=membership result=encode_fail" \
     RE_output/s1_accept/Sunrise/logs/sunrise.log
```

`ev=activity stage=membership_ack` is **new in p2(47b)**. The acknowledgement is
the client's only positive verdict on a body and it previously wrote nothing at
all, so every earlier boot inferred acceptance from the absence of symptoms.

## 4. Both negatives, pre-named

| observation | reading |
|---|---|
| `membership_ack result=ok revision=N`, N advancing | **PASS.** The client applied a four-field body. The schema reading is confirmed on the wire and the peer boot is next. |
| `membership_ack result=parse_failed` | The client sent a type-38 we could not parse — our own bug, not a verdict. |
| `membership_ack result=not_staged` | Parsed, refused by our state machine. Ours, not the client's. |
| **zero `membership_ack` lines while `wire_snapshot` lines exist** | **DECISIVE NEGATIVE.** The client received bodies and acknowledged none. The four-field trailer is refused → revert to p2(46)'s two fields and the "four fields" reading of the schema is wrong. |
| `membership result=encode_fail` | Our encoder refused its own snapshot. Ours; the wire gate should have caught it, so that gate is then also wrong. |
| client hangs at load | Unexpected here — solo has never hung. Treat as the four-field shape being actively rejected, and revert. |

## 5. Chain marks (lesson 16)

| link | mark |
|---|---|
| the schema declares 4 flagged 32-bit fields at 996–999 | **verified by reading** — self-verifying node, key at `node+0x08` |
| our encoder published only 2 | **verified by reading** — source |
| the emitted body now carries 4, at the right offset, byte-aligned | **verified by execution** — `--membership-wire-test`, both cases |
| the 4 map to `peer_and_player_counts / peer_updates / player_updates / player_seq_number` | **inference** — count and order match Lane M's registry; NOT tested by this boot |
| the client accepts the four-field shape | **unknown — this is what the boot resolves** |
| four fields fix the peer freeze | **unknown** — a later boot, and only if this one passes |

## 6. Graphics delta (lesson 12)

**Zero.** No definition, inventory or equipment change. Nothing new renders.

## 7. What to do

1. Launch **one** client on the Mac. Let it reach a destination.
2. Confirm zero peers — this is the control; no peer row is published at pin 5.
3. Run the greps in §2 and §3.

Rollback if it fails: the previous exe is beside the live one as
`sunrise-server.exe.bak_p2d6_<stamp>`; restore it with its matching
`build_data.bin.bak_p2d6_<stamp>` (they are a pair), then relaunch with
`bash mac-port/launch-server-macos.sh`.
