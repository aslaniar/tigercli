# Incident: the false loops of 2026-08-25

Written at the user's instruction after a full "upstream-to-downstream analysis"
was followed, one conversation turn later, by a retraction. The complaint was
exact: *"either you didn't do a full analysis or your methodology for
verification was wrong or something else."* The answer is "something else," and
naming it precisely matters more than apologising for it.

The binding rules in `AGENTS.md` (2026-08-20) are good rules. They did not
prevent today. This document explains why, and what closes the gap.

---

## The deepest cause, stated once

**When an observation came back null, every hypothesis I generated was about the
system under test. None was about the measuring apparatus.**

That single omission produced the day's largest waste, and it is a repeat: the
deploy-script ordering bug days earlier (harness gate ran before the cache
restamp, so a good build failed a gate for a reason unrelated to the build) is
the same shape. A failure in the rig gets attributed to the subject.

Everything below is either that error or a variant of it.

---

## Loop 1 — the stale artifact (cost: 2 boots, 1 wrong strategic call)

**Sequence**

1. Wrote `read()` + a descriptor instrument (`p2(30)`). Round-trip verified it
   against `build()` on the host. That part was sound.
2. Ran the deploy script. It printed `exe 7be6064f86f2206a`, passed all four
   harness gates, relaunched, and verified listeners. Every signal said success.
3. User booted. **Zero `stage=descriptor` lines** against a stream of
   `advertisement_update` calls.
4. I concluded: *the client publishes no descriptor at all*. I told the user not
   to boot the rig, and reframed several days of work as built on an empty
   premise.
5. Built `p2(31)` to disambiguate the null. Deployed. Same reported success.
6. User booted. Zero lines again — including the branch that fires
   unconditionally.
7. Only then did I check the binary. **Neither instrument had ever been
   deployed.**

**Mechanical root.** `deploy_p2d6_gameplay.sh` consumed a hand-staged
`sunrise-server.exe.NEW_candidate` and never produced one. With no staging step,
it re-deployed a stale binary and reported success through every gate. Nothing
in the pipeline asserted that the file under test was the file just built.

**Why the existing rules missed it.** Rule 8 ("THE DISK IS THE TRUTH") is aimed
at *claims and documents* — spot-verify what a report asserts. It was never
pointed at *build artifacts*. Rule 9 ("DOCUMENT EVERY GATE'S EXPECTED VALUE")
covers a gate that reads a line; it says nothing about a gate that reads
*silence*.

**The tell I walked past.** Step 4's conclusion required the instrument to have
run. I had no evidence it ran. A one-command check
(`grep -ac "stage=descriptor" <deployed exe>`) was available at every point from
step 3 onward and would have ended the loop immediately.

**Aggravating factor.** The conclusion in step 4 was not idle — it changed what
the user did (told them to keep the rig off) and rewrote the project's status.
A claim that steers action deserves a verification step proportional to that.

---

## Loop 2 — a source used outside its authority (cost: a retraction)

I read upstream's tree, found `sessionSearch` answered with
`encode_empty_message`, and called it **"decisive"** evidence that fireteam join
does not run through session search.

The reading was correct. I re-checked upstream's tip today
(`0188841`, identical to our ref) — the tree really does return an empty search
result. **The error was not staleness.** It was that a committed tree cannot
answer "how did their demo work." Those are different questions, and the source
is authoritative for only one.

Worse: the user had already given me this exact fact two days earlier —
*"upstream is not the most up to date source of truth, the mods' video demos
are."* I had the correction in hand and failed to apply it.

**What this is not.** It is tempting to file this under Rule 1 ("THE REFERENCE
IS THE ORACLE — fetch fresh"). That would be the wrong lesson, and acting on the
wrong lesson is its own cost. The fetch was fine. The scope was not.

---

## Loop 3 — the first plausible gap becomes "the blocker" (cost: 3 boots)

Three times across this front I named a single missing piece, called us "one
boot away," and was wrong. The pattern each time: find the first plausible gap →
declare it *the* blocker → boot → fail → find the next gap.

It only broke when the user refused the fourth instance and demanded a full
chain walk. That walk (FINDINGS 20.38) immediately produced better information
than any of the three guesses: four unverified links, not one, and a subsystem
(peer visibility) that does not exist in either tree.

**The structural fault.** I was marking one link and leaving the rest
unexamined but implicitly "fine." An unexamined link is not a passing link.

---

## What actually worked today, and why

Worth recording, because the successful moves share one property.

- **Round-trip verifying `read()` against `build()` before wiring it.** Caught
  nothing — but it is the reason I never had to wonder whether the decoder was
  the problem.
- **Deleting the defaulted `AccountKey` parameters** (20.22) and **deleting the
  fail-closed advertisement stubs** (20.31): both converted a silent runtime
  misuse into a compile error.
- **Grepping the merged result against upstream's version of a function** after
  the 3-way merge mangled `arm_repushes` while still compiling.

The common property: **each one moves a failure from "discoverable at runtime by
a careful observer" to "impossible to express, or loudly asserted."** That is
the durable technique on this project. Prefer it to vigilance every time —
today is a demonstration of what vigilance is worth under fatigue.

---

## The checks that would have prevented each loop

| Loop | One check | Cost |
|------|-----------|------|
| 1 | `grep -ac "<instrument literal>" <deployed binary>` before asking for a boot | seconds |
| 2 | "Can this source answer this question, or only a neighbouring one?" | one sentence |
| 3 | Enumerate every link with an evidence mark before proposing a fix | one table |

None of these are expensive. All three were skipped while moving fast on a front
that had already cost the user several days.
