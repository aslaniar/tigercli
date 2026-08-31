STATUS: live (newest handoff as of 2026-08-26; verify against STATE.md header, which outranks handoffs when both are current).

# Handoff — Sunrise fork, peer front (2026-08-25 ~22:10)

The previous session ended at its limit mid-way through opening the client's
schema registry. Everything is committed and the deployed server is in a SAFE
state. Read this, then `STATE.md`'s header, then the findings it points at.

---

## 1. Read in this order

1. `AGENTS.md` — binding. Lessons 13–17 and THE PRE-BOOT CHECKLIST especially.
   **Lesson 17 is new and was earned today**, at the cost of a hard client freeze.
2. `INCIDENT_2026-08-25_false-loops.md` — the three traps; all three recurred today.
3. `STATE.md` header.
4. `FINDINGS_2026-08-25.md` **20.49 → 20.58** (newest first — today's whole arc).
5. `RE_output/claims/protocol-census-2026-08-25.md` — the message-type census.

## 2. Deployed state — do not disturb casually

```
server exe  7fb79777e265843d   (p2(45)), five gates rc=0
settings    membership_sweep_pin: 5      <- solo; NO peer row is published
            membership_peer_retry_cap: 6
            membership_sweep: false
client DLL  eb893d2b1b6d8534   on BOTH machines
fork        upstream-gameplay-scoped @ 3006f9b, clean
```

**Leave the pin at 5.** A peer row the client refuses freezes it — six bodies
hard-froze the Mac tonight. The retry cap (p2(44)) stops the server hammering,
but the freeze happens well inside six.

## 3. What today actually established

**The "two guardians" milestone was false and is retracted.** The peer we
published was the client's own sibling session: one client holds several BAP
connections, `foreign_member_identity` excluded only the caller's session id,
and the client rendered a second copy of the local guardian named "You". Fixed
in p2(45) by excluding candidates that share the caller's member key. This is
the same bug 20.37 fixed for matchmaking.

**Every trailing-field result is void.** `mask_mask`, `packed_mask`,
`count_mask` were all measured against a self-peer. Do not treat them as
refuted; re-run only after a genuine foreign peer is proven.

**A genuine cross-peer HAS since been served** (distinct keys, correctly
crossed) — and the receiving client froze. A self-peer renders fine; a foreign
peer hangs. The client evidently needs to already know who that person is.

**The census names why:** we accept requests and never answer them.
`request_activity_host` → 9/10, `request_peer_reservation` → grant/45,
`keepalive_request` → 17 are all accepted-and-dropped. And the client sent
`release_peer_reservation` 56 ms after our first peer body, twice — its verdict,
in its own vocabulary, which we discard.

## 4. Your task

### 4a. The one cheap thing that needs no new knowledge

Stop discarding message type 14. Log its 16-byte payload. It is the client
telling us why it rejects our roster and it needs no wire format we lack.

### 4b. The blocker: one packed schema key

The registry is OPEN and verified offline against
`...\destiny-preservation\RE_output\content\dump_healthy_inproc.dmp` (5.7 GB,
already on the rig, from 08-15). Tooling is written and works:

- `RE_scripts/minidump_reader.py` — VA resolution in a full dump
- `RE_scripts/schema_walk.py` — `--table`, `--node`, `--key`, `--find`

Both run ON THE RIG (Python 3.13 is installed) so 5.7 GB never moves.

Verified and safe to build on:
```
TABLE = *(*(0x142439C70))            TWO dereferences; one level looks empty
registry stride 0x40                 shl rcx,6 in FUN_1404c1930
field-entry stride 0x28              lea rax,[rbx+rbx*4] / [r14+rax*8] / inc rbx
field offsets are relative to node + idx*0x28, body starts one stride in
24/24 buckets live, sane bases and strides
```

**What does not work: no packed key resolves.** `0x80806AC0` (our own
world-population schema hash) and `0x80808635` both return `node absent`.
Probing buckets directly is meaningless — the bucket derives from the key. No
walk call site loads a key as an immediate (scanned both .text spans).

Three routes, cheapest first, detail in 20.58:
1. A schema HASH may not BE a packed key. Find where a hash is translated into
   one — that lookup is the missing step.
2. Re-verify the bucket arithmetic against signed 32-bit semantics; the Python
   mirrors the disassembly but has never been checked against a known-good key.
3. Lane M's original route: capture the key live at `0x1404c72e0`'s entry, one
   boot, small hook. **Everything downstream of the key is already built.**

## 5. Ground rules

- **ONE WRITER on the tree.** Two agents collided mid-boot-test today; nothing
  was lost but a boot was confounded and `p2(39)` was used twice. Check
  `git log` before numbering. Next free is **p2(46)**.
- **The one-machine control comes first.** Boot a single client, confirm zero
  peers, before any two-machine peer test. Sixty seconds, and it is what caught
  the self-peer bug after three boots had been spent on results it invalidated.
- **Deploy scripts assert provenance.** `deploy_p2d6_gameplay.sh` stages from
  the build and checks the deployed hash; five gates including
  `--membership-sweep-test`. Do not weaken either.
- **A null from a mechanism whose syntax already failed is not evidence.** Three
  separate censuses were wrong today — two greps and a PowerShell-over-ssh —
  each caught only by re-asking through a mechanism that could not fail the same
  way. Verify empirically (what did the client actually receive?) over
  grep-and-assume.

## 6. Honest position on the three goals

1. **Separate accounts** — working, identity-complete.
2. **Two guardians in one instance** — further than this morning looked, and on
   firmer ground. The roster CAN create a body (proven, even if that body was a
   clone). A real foreign peer freezes the client. The next real step is the
   unanswered request/response pairs, which needs the schema, which needs one key.
3. **Fireteam** — downstream of 2, untouched.
