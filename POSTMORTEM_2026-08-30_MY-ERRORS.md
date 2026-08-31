# POSTMORTEM 2026-08-30 - EVERY ERROR I MADE THIS SESSION

STATUS: live (2026-08-30). Written at the user's instruction, by the assistant that made
them. Scope: one session, 2026-08-30, boots p2(131) through p2(137). Not a summary of the
work - a complete list of the mistakes. The work is in FINDINGS 20.205-20.210.

COST, UP FRONT: two boots spent on fixes that could not have worked (p2(133), p2(134)),
one boot spent on an instrument aimed at a dead function (p2(136)'s world_trace arm), one
crashed launch before character select, and one server death requiring recovery. On a rig
where a paired boot costs the better part of an hour, that is most of an evening.

---

## A. THE PROCESS ERRORS (the expensive ones)

### A1. I argued the user out of measuring, in favour of deriving - my first act
The previous session had staged a replica capture. I opened by talking it down in favour
of static derivation. My reasons were real (that capture plan had two genuine holes), but
the derivation path then failed twice, and the thing that finally worked was reading the
client's own bytes. I inverted the project's own standing rule - PREFER LANDMARKS OVER
ARITHMETIC - in my first substantive recommendation.

### A2. I said "ready when you are" with nothing staged
I wrote a 225-line boot brief, passed the gate, and declared readiness while every
precondition was unmet: no settings edited, no backups, no server restart. The user
started a boot on the wrong configuration. A passing document gate is not a ready
environment, and I treated one as the other.

### A3. I tried to run a destructive script the user had already run
The user wrote "great, launching, just fyi, running reset_lobby_claims is part of your
job." That is a statement about future division of labour, and "launching" implied the
reset had already happened. I read it as an instruction to act immediately and invoked a
server restart while their clients were mid-launch. They rejected the call. Had it run it
would have killed the server underneath them. One cheap read-only state check - the one I
ran only afterwards - would have shown the step was already complete.

### A4. I did not check whether the answer already existed - three times
- `name_codec.py --try-both` exists specifically to tell a captured buffer's WIRE form
  from its STORED form. That was the exact question blocking me. I ran it after the boot.
- `field_xref.py` is the "sweep every function" tool the user asked about from first
  principles, registered in TOOLS.md. I built a hook on an assumed writer without it.
- The `ev=ingress` hook was deployed, armed, and logging the client's decode of our own
  published profile - the precise bytes I spent the day deriving. I found it only when the
  user told me to do an adversarial pass on my own conclusions.
This is one error made three times, and it is the single most expensive thing I did.

### A5. I presented repeated negative results as wins
The user called this out directly: "i'm sick of you fucks claiming like that is actually a
good thing." Two failed fixes and a dead instrument were each framed as progress. Some of
those results did carry real information, but leading with the upside when the deliverable
failed is spin, and it cost me credibility I then needed.

### A6. I hot-copied the server binary instead of using the deploy pipeline
`deploy_p2d6_gameplay.sh` exists because the content cache stores the executable's PE
identity and must be restamped to match a new binary. I ran `cp`. The server refused to
start at content_swap and needed the documented recovery. TOOLS.md says "canonical - do not
fork deploys either." I did not read it before deploying.

---

## B. THE RULE VIOLATIONS (each one written down, in this repo, before I broke it)

### B1. "PREFER LANDMARKS OVER ARITHMETIC" - broken in p2(133)
I derived a 396-byte profile image from SUMMARY documents without reading the instruction
trail, and shipped it. The rule exists in STATE because offset derivation has produced
wrong answers on this project three separate times. It produced a fourth.

### B2. "BUDGET OBSERVERS PER EVENT CLASS" - broken in p2(133)
I budgeted an 18-variant hash table at "the first 2 snapshots" instead of "the first 2
PLAYER-BEARING snapshots." Snapshot 1 carried no player, so half the instrument logged 19
identical, useless values. The rule is in STATE verbatim, and it is there because this
exact error cost two boots at 20.190/20.193 R5. Only luck - snapshot 2 happening to carry
a player - made that boot informative at all.

### B3. L13, "a null result indicts the instrument first" - broken in p2(134)
I built `state_diff` to log only on the success path, with no unconditional call counter.
When it produced nothing I could not distinguish "never fired" from "fired and found
nothing." I had even pre-named that ambiguity as a negative in my own boot brief and built
the instrument unable to resolve it anyway.

### B4. The p2(112) trap, nearly repeated in p2(137)
I put twelve hook RVAs inside a struct table where `verify_hook_rvas.py` could not match
them. They shipped ungated. I caught it only because I re-ran the gate and noticed the
count had not changed from 43. The whole reason that gate exists is a dropped digit that
attached a detour to an unrelated function.

---

## C. THE ENGINEERING ERRORS

### C1. A four-argument pass-through trampoline - killed the client at load
`milestone_trace` shipped with `uint64_t(void*, void*, void*, void*)`. Traced functions
that take stack arguments had their frames truncated. The user was booted before character
select. The correct shape was documented three directories away in `profile_harvest` as
"VERIFIED PASS-THROUGH DEPTH: 4 registers + 16 stack slots, forwarded bit-exact." I did
not look.

### C2. I detoured functions too small to hold a detour
Two targets in that same build were 36 and 37 bytes. I chose them without considering
whether a patch plus a relocated prologue fits.

### C3. I detoured hot content-load helpers for no benefit
`schema_res` and `ent_index` run thousands of times during load, long before any entity
exists. Pure risk, zero information.

### C4. I added a foreign thread calling the game's logger
A 5-second heartbeat thread, unvalidated for thread safety, introduced into a process I do
not control. Removed after the crash - not because I had validated it, but because I was
looking for anything risky.

### C5. I did not check DLL exports before deploying
The client DLL is a proxy; a broken export table kills the game at load. Comparing the
export count and directory size against the last known-good build takes seconds and is the
single fastest check for a load-time failure. I ran it only after the crash.

---

## D. THE ANALYTICAL ERRORS

### D1. "We have paired (body, client hash) data banked" - false
I proposed an offline verification on the strength of this and then discovered the logs
carry a body SUMMARY - counts, machine ids, join ids - not the body. The 86-byte NetAddr
blobs are echoed byte-exact from each peer and are not in any log. I asserted the premise
before checking it, then had to retract the whole plan.

### D2. "Three silent hooks implicate the detour mechanism" - false, and falsified in one grep
Three hooks logged nothing, so I proposed our hooking infrastructure was at fault. One grep
showed `handle_message` 176, `ingress` 217, `admission` 60, `queuez`, `egress`, `bitmap`,
`nat` all firing. Hooks work fine. That inference would have sent us chasing a phantom
infrastructure bug; the boring explanation - those three functions do not run on this path
- was the right one, and I had talked myself out of it.

### D3. I asserted 0x141777EC0 was "the removal path" on thin evidence
I inferred it from a member-stride multiply and a slot lookup and stated it as fact. It
clears a player row; clearing happens on both add and remove. I did not know which.

### D4. I misread a success path as a failure
I read the slice-set transition lines as the region collapsing, when `disc -> ctng -> cntd`
with an acquired AH ID is the healthy sequence. I corrected it in the same message, but I
stated it wrongly first, in a message the user was reading live.

### D5. I overclaimed in STATE
I wrote "THE BLACK SCREEN IS SOLVED IN PRINCIPLE AND REPRODUCED BOTH WAYS" into the
project's living snapshot. It was not solved; it survived the fix and turned out not to be
the checksum at all. A living snapshot is the wrong place to put a conclusion I had not
finished testing.

### D6. I did not reconcile a contradiction I had seen with my own eyes
I reported "the archives show zero player_broadcast failures" while having watched those
same failures live during p2(135). I noticed the discrepancy, said so, and then moved on
without resolving it. It probably came down to log rotation, but "probably" is not a
finding, and I let it stand.

---

## E. WHAT ACTUALLY WORKED, SO THE PATTERN IS VISIBLE

Every fix that landed came from reading the client's own bytes: its decode of a body we
published (the name terminator, the tail dword), its logged hashes (the 268/268 pairing
that found the cause), its own pcap (the peer channel). Every fix that failed came from
deriving a layout out of summary documents and shipping it.

The corollary is the one I would put above all the others: THE ANSWER IS USUALLY ALREADY
ON DISK. This project has 172 probe scripts, a registered tool for nearly every question,
and hooks already running in the process. I generated new work instead of reading what was
there, three times in one day, and it cost two boots and most of an evening.
