# Resume brief — Lane M continuation (2026-08-25 late)

Your lane was paused so a server-side sweep could run without two writers on one
checkout. It has run. **Your revision finding was correct and it was the whole
fix** — and the boot it enabled produced evidence your lane did not have, which
changes what to look for next.

Read `FINDINGS_2026-08-25.md` **20.49 → 20.51** first, then `STATE.md`'s header.

---

## 1. What your finding did

`p2(39)` (advance the revision on peer gain/loss) plus `p2(41)` (advance it as
each swept shape retires) made the client **apply a peer-bearing membership body
for the first time**. Both sessions acknowledged one:

- session A `0xB34F7851304A19CF` — acked revision 6, carrying `key_account`
- session B `0x846C8338F7D022E6` — acked revision 5, carrying `key_only`

Both clients stayed connected ~100 s past the last body with `membership=1` on
all 48 following keepalives, so nothing else ended the republish loop.

## 2. What the sweep closed

**The row SHAPE is not the constraint. Do not sweep it again.**

Six shapes were swept, each on its own revision, from `memberKey` alone up to
the full mirrored row. `key_only` and `full_mirror` produce identical client
behaviour. **memberKey alone is sufficient to be accepted.** No field addition
changes anything, because the row is evidently not being read.

This also retires 20.49's apparent "key_only refused, key_account acked" — that
was the same repeat-revision artifact one level down, before p2(41) existed.

## 3. The new evidence — this is what your lane did not have

Mac client, entire run: **13 `ev=steamnet` lines**, all sign-in scaffolding
(`interface_acquired`, `identity`, `get_certificate`, `relay_ticket_count`, two
`lobby_create`, seven `stub`). **Zero `send_rendezvous`, ever.** After the peer
bodies landed at t=230910: **zero `ev=steamnet` lines of any kind.**

And both players stood at the shared Tower spawn for the whole window. Neither
saw the other.

So: the client accepts the row, and then touches no Steam surface at all.
Applying membership triggers nothing. That substantially weakens 20.44's
"server-declared membership is the join driver" reframe — we declared it, the
client took it, nothing followed.

Corroboration the bits do arrive: Mac type-12 receipts grow 3891 → 3976 bytes
with the peer row, +85 B against `kPeerRowExtraBits = 673` (84.125 B,
byte-padded). The row ships and parses. It is simply not acted on.

## 4. Your two questions, re-aimed

### Q1 (highest value) — `peer_and_player_counts`

Your own section 1b names the parsed structure:

```
session_id, update_number, incremental_setup, peer_and_player_counts,
peer_updates, player_updates, player_seq_number, leader_peer_index,
host_peer_index, slot_counts, party nonce, checksum
```

and notes: *"a SEPARATE peer_and_player_counts field exists upstream of them —
our body does not currently distinguish counts from valid-masks."*

Our encoder writes `masks = 0b11` twice and nothing plainly a count:
`Sunrise/src/middleware/bap/activity_message/activity_replicate_membership_encoder.cpp:12,28,35-36`.

**Hypothesis to test from statics:** the count still says one member, so the
client parses our slot-1 row into a slot it then ignores. This fits every
observation simultaneously — body parses, revision acks, peer never appears,
shape irrelevant, no connection attempted.

What is needed: where `peer_and_player_counts` sits in the bit layout, its
width, and what our fixed `kMeaningfulBitCount = 29'968` prefix currently puts
there. Calibrate against our own accepted solo body before trusting any read of
the two-member case — the discipline that has held all lane.

### Q2 — make the client name its own reason

The ~44-entry peer-link failure-reason enum at `.rdata 0x141c9e2f8`
(`not-joinable`, `no-reservation`, `address-invalid`, `player-count-zero`,
`session-full`, …) is the client's own vocabulary for a failed peer add. You
flagged it as a follow-up: three parallel registries at `.data 0x142035910+`,
`0x143549cc8+`, `0x149217540+`, no direct code xrefs, double indirection.

If we can surface which reason fires, the client tells us the cause outright
instead of us inferring it from silence. Given how much of this front has been
spent inferring from silence, that is worth real effort.

`player-count-zero` in that enum is worth noting beside Q1.

## 5. Ground rules

- **You hold the pen on the fork tree.** The Claude session is not editing it
  while you work. Last collision cost a confounded boot: opencode deployed over
  a live boot test, and both sessions independently wrote a commit numbered
  `p2(39)`. One writer at a time, or take a worktree.
- Current HEAD carries `p2(41)`; check `git log` before numbering anything.
- Deploy scripts now stage from the build output and assert the deployed hash
  equals it. `deploy_p2d6_gameplay.sh` runs five gates including
  `--membership-sweep-test`. Do not weaken either.
- `AGENTS.md` lessons 13–16 and THE PRE-BOOT CHECKLIST are binding. Lesson 13
  in particular has now caught the same trap three times: *peers valid 0x1* on
  both machines is **absence of measurement**, not measurement of absence —
  neither client has dumped membership since minutes before the peer bodies
  arrived (Mac t=91529, rig t=54172; bodies t=220907+).

## 6. What a good outcome looks like

Either a named bit-layout gap we can encode (Q1), or a client-side diagnostic
that speaks the failure enum (Q2). Not another shape theory. If the statics say
the count is fine and the row IS read, say so plainly — that refutes the leading
hypothesis and is worth as much as confirming it.
