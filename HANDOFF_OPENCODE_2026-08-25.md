# Handoff — Sunrise fork, peer/multiplayer front (2026-08-25 evening)

You are taking over a standalone dedicated server for Destiny 2 (Season of
Arrivals), forked from stanuwu/Sunrise. The previous session hit its limit right
after a finding that **moved the whole front**. Read before doing anything.

---

## 1. Read these first, in this order

1. `AGENTS.md` — the whole file is binding. Pay special attention to **lessons
   13–16** and **THE PRE-BOOT CHECKLIST**, which were written today in response
   to real waste. Also honour the **model budget ladder**: start on tier 1
   (`opencode-go/deepseek-v4-flash`) and escalate only when you can name the
   specific reasoning step that failed.
2. `INCIDENT_2026-08-25_false-loops.md` — why lessons 13–16 exist. Three false
   loops cost the user roughly a day. You will be tempted by all three.
3. `STATE.md` — current state. The top section is authoritative; everything
   below the "predates the descriptor decode" marker is history.
4. `FINDINGS_2026-08-24.md` entries **20.38** and **20.40**.

---

## 2. Where we are, in one paragraph

Two clients (a Mac and a Windows "rig") each load into their own Tower. We spent
days assuming that was a server-side placement problem and built out the BAP
matchmaking search-result path to hand one client a pointer to the other's
session. Today we finally decoded the 128-byte descriptor the client actually
publishes: **it contains no IP address and no port.** It names a Steam identity
and a Steam lobby — and both are hardcoded/fabricated constants in our own Steam
shim, identical on every machine. The peer join is Steam-brokered, and our
`ISteamNetworkingSocketsSerialized` shim drops every rendezvous message by
design. That is why nothing has ever connected.

---

## 3. Your task

Two changes, one build, one boot. **Neither makes multiplayer work — say so
plainly to the user rather than letting it become a fourth "one boot away."**

**3a. Per-instance Steam identity.**
`Sunrise/src/steam/interfaces/methods/common.cpp:18` has
`constexpr std::uint64_t kLocalSteamId = 0x0110000130AA9EC5ULL;` returned by
`get_steam_id` to every caller. Both machines therefore claim to be the same
Steam user, and a client will not rendezvous with itself. Make it configurable
per instance through the existing settings system (see
`core/settings/client/...` for the established pattern; follow the surrounding
code's style and the no-defaulted-key discipline in FINDINGS 20.22).

**3b. Call-trace the serialized-networking table.**
`Sunrise/src/steam/interfaces/methods/serialized_networking.cpp` — all eight
methods are no-ops. Log every call with its arguments; for
`serialized_send_rendezvous` also dump `remoteId`, `sourceConnectionId`,
`messageSize` and a hex of `message`. **The call order matters as much as the
contents** — it shows how far the client gets before giving up.

Then: one boot, **both machines** (the rig finally earns its keep). The question
that boot answers: does `send_rendezvous` fire, and naming whom?

**The load-bearing unknown** is what is inside the rendezvous `message` blob. If
it carries candidate addresses, we can relay it between clients through our
server and they connect. If it is Steam-signed, we can still move the bytes but
the peers may refuse without valid certificates. That decides whether this front
is days of work or a wall. **Do not guess it. The instrument answers it.**

---

## 4. Dead ends — do not resume these

- **The svc-43 search-result contents** (p2(26), p2(27), the IdPair, the field-3
  Ghidra lane). The shape is correct and the client parses it. The pointer aims
  at a stubbed Steam layer. Perfecting it changes nothing.
- **The peer-subnet egress relaxation** (p2(28)). There is no IP in the
  advertisement, so there was never a connection attempt to permit.
- **The physics/visibility gates** (`physicsHostSession`, `serverDefaultEntity`,
  `gameplayExternalBody`). Not on the critical path — 20.38. `playerBroadcast`
  is defined and never constructed; peer visibility is peer-authored and happens
  only after a peer link exists.

---

## 5. Operational facts

- **Fork repo**: `RE_build/Sunrise-fork-inventory`, branch
  `upstream-gameplay-scoped`, HEAD `7cad785`. Commits are conventionally
  `p2(NN): summary` with a body explaining *why*, and end with
  `Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>`.
- **Outer repo**: `/Users/rubenaslanian/Documents/opencode/sunrise-fork`, `main`.
  `RE_output/` is **gitignored** — anything that must survive belongs at root
  beside the FINDINGS files.
- **Build**: `cd RE_build/Sunrise-fork-inventory/build && make -j8`. Builds two
  targets: `sunrise-server.exe` (standalone server) and `steam_api64.dll`
  (client hook). The Steam shim compiles into **both**, so a change there
  changes the client DLL too — the rig needs the new DLL, not just the Mac.
- **Deploy**: `bash RE_scripts/deploy_p2d6_gameplay.sh`. It now stages the
  candidate from the build output itself and asserts the deployed hash equals
  the build hash. **It did not always do this** — that bug burned two boots
  today. Do not "fix" it back.
- **Currently deployed**: exe `8605161b5c3c4db6`.
- **The rig**: reachable over ssh, ControlMaster socket at `~/.ssh/cm-rig`.
- **Boot loop**: you cannot launch the game. The user does. You prepare, deploy,
  verify provenance, then ask. A boot costs them real minutes and they have
  spent many today — earn each one.
- **Deploying restarts the server and drops any connected client.** Stage your
  work *before* asking the user to boot, not after.

---

## 6. The three traps, concretely

**Trap 1 — reading a null result as data.** Zero instrument lines got read as
"the client publishes no descriptor," which was told to the user as fact and
changed what they did. The actual cause: the instrument was never in the
deployed binary. *Before any boot, confirm the instrument literal is present in
the deployed file (`grep -ac "<literal>" <exe>`) and make sure something logs on
the boring path so silence stays readable.*

**Trap 2 — claims outrunning evidence.** Upstream's tree was read correctly and
then called "decisive" about a question a committed tree cannot answer (how
their video demo worked). *Name what a source can actually answer before citing
it. Mark every claim as verified-by-execution / verified-by-reading / inferred
as you write it — not retroactively.*

**Trap 3 — the first plausible gap becomes "the blocker."** Three consecutive
"one boot away" claims, three failed boots. *Enumerate the whole chain and mark
every link. An unexamined link is not a passing link.*

---

## 7. How to think about this work

Distilled from what actually paid off here versus what wasted days.

- **Prefer making a failure impossible to express over remembering to check
  for it.** Every durable win on this project did that: deleting the defaulted
  `AccountKey` parameters so unkeyed calls became compile errors; deleting the
  fail-closed advertisement stubs so binding to them became a compile error;
  asserting the deployed hash equals the build hash. Vigilance does not survive
  a long day. Structure does.

- **Read the bytes. Do not reason about what should be there.** Days were spent
  refining a descriptor nobody had ever decoded. One 20-line instrument settled
  in a single boot what a week of inference got wrong. When you catch yourself
  reasoning about the contents of something you have never printed, print it.

- **When an observation is null, suspect your instrument first.** This is the
  single highest-value habit on this project, and its absence caused the worst
  waste. A failure in the rig gets attributed to the subject unless you actively
  resist it.

- **Distinguish what you observed from what you concluded, every time.** State
  the confidence in the same sentence as the claim. "The descriptor contains no
  IPv4" is verified. "Therefore joins are Steam-brokered" is inference. Both are
  useful; conflating them is how a day gets lost.

- **State the limit of good news.** When you find something real, say what it
  does *not* fix in the same breath. The user has been burned by optimism
  repeatedly and has explicitly asked for this.

- **Own errors in one sentence and move on.** Correct the record plainly, do not
  ruminate, do not apologise repeatedly, do not re-audit statements that were
  accurate. Then keep working.

- **Finish the whole task and report faithfully.** If part is blocked, do
  everything else in full and say exactly what you left out and why. Scaling
  the work down is the user's call.

- **On tone:** this user is technically sharp, has been at this for weeks, and
  is discouraged — the upstream project's maintainers made clear this fork will
  never be part of Sunrise, which hit hard. They do not want pep talks, they do
  not want the architecture re-explained unprompted, and they have said so
  directly. What they want is honest, competent forward motion. Give them the
  result and the real distance to the goal. Do not oversell a finding.

- **The three goals** they track, and will ask about in this format:
  (1) fully separate accounts, (2) two guardians in the same destination
  instance, (3) two guardians in the same fireteam. Answer all three with honest
  distances, and if a distance is unknown, say unknown rather than inventing a
  boot count.

---

## 8. First moves

1. Read §1's documents.
2. Confirm the deployed exe is `8605161b5c3c4db6` and the tree is clean.
3. Implement 3a and 3b in one build. Gate it. Deploy it. Run the pre-boot
   checklist from `AGENTS.md`.
4. Ask the user for one boot on **both** machines, telling them exactly what the
   boot will and will not settle.
