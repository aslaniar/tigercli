# POSTMORTEM - THE REBUILD SESSION: FOUR LAUNCHES LOST, THREE TO ME

STATUS: closed (2026-09-05, updated after 20.301). Covers 2026-09-04 evening
through 2026-09-05 midday:
the p2-176/177/178 arc, the 4-change rebuild, and every failure in between.
Read BEFORE writing or changing a client hook, and before shipping any build.

## THE TALLY, STATED PLAINLY

Launches consumed: ~9. Launches that produced a measurement: 3.
Boots briefed against a front the corpus had already closed: 2 (see FAILURE 5).
Of the 6 lost: 2 to environment (network move), 1 pre-existing (rig hang), and
3 TO DEFECTS I INTRODUCED OR SHIPPED. That ratio is the subject of this document.

## FAILURE 1 - THE BOM (self-inflicted, cost 1 launch)

Wrote the rig's settings.json with PowerShell `Set-Content -Encoding UTF8`, which
prepends EF BB BF. The shim's parser rejected it and the game refused to launch with
"problem verifying game files' integrity" - which reads like a corrupted install, not a
config edit, so it cost diagnosis time on top of the launch.
RULE (now in ENVIRONMENTS.md TRAP 18b): write rig configs with
`[System.IO.File]::WriteAllText($p,$t,(New-Object System.Text.UTF8Encoding($false)))`
and VERIFY byte 0 == 123.
DEEPER MISS: ENVIRONMENTS.md already carried TRAP 18 ("never round-trip settings.json
through a serialiser") and I did not read it before editing a settings file. The trap
that existed named the file I was about to break.

## FAILURE 2 - THE ARRAY SIZE (self-inflicted, cost 1 launch, the worst one)

To stop a hang I commented out one entry in the client's hook table:
    constexpr std::size_t kTargetsSize = 48;
    constexpr std::array<Target, kTargetsSize> kTargets{{ ...47 entries now... }};
std::array VALUE-INITIALISES the missing element, so kTargets[47] became
{name=nullptr, rva=0}. The installer then detoured RVA 0 - writing into the PE header -
and the client CRASHED DURING LOGIN, earlier than the bug it was meant to fix.
It compiled clean. Worse: I had ADDED static_asserts in that same edit to prove the
table binding was correct, and they stepped straight over the null entry, because
kIndexOf returns early on a match and never reads the tail.
WHY IT HAPPENED: I removed an element from a container whose size was declared
separately, and did not check whether the size was derived or hardcoded. One grep.
THE FIX SHIPPED: kTargetsSize corrected, plus a compile-time guard that makes the
compiler catch the whole class:
    constexpr bool all_targets_populated();   // name != nullptr && rva != 0, all entries
    static_assert(all_targets_populated(), "...would be installed at RVA 0...");
GENERAL RULE: when a guard is added in the same edit as the change it guards, the guard
must be shown to FAIL on the pre-fix state. An assertion never observed failing is an
assumption with syntax.

## FAILURE 3 - THE RE-ARM THAT COULD NOT FIRE (self-inflicted, cost the boot's contract)

The rebuild's HEADLINE change was a rate-limited re-arm of the withdrawn peer row,
gated on N acknowledged bodies. I chose N=8 from an assumption that acknowledgements
keep arriving at keepalive rate. They do not: EXACTLY ONE ack follows a withdrawal
(27-80 ms later) and then none, because the client never acknowledges a peer-bearing
body at all (20.48). The threshold was unreachable BY CONSTRUCTION. 0 re-arms fired.
The boot did not test what it was built to test.
WHAT WOULD HAVE CAUGHT IT: the same fixture discipline I applied to the OTHER new probe
in the same build. I replayed R3's trigger over a recorded log and it caught two real
defects. I did not replay R1's trigger over the SAME logs - and p2-175's log already
contained the withdrawal-then-single-ack pattern that falsifies N=8. The fixture existed;
I only pointed it at one of the two changes.
RULE: replay EVERY new trigger in a build over recorded data, not the one that feels
riskiest. The one that feels safe is the one that ships unexamined.

## FAILURE 4 - THE HANG I WORKED AROUND WITHOUT UNDERSTANDING (open debt)

image_set had fired ZERO times in p2-175/176/177, then fired once on the new build and
never returned - `stage=enter fn=image_set call=1` last line, no leave, no further
census, main thread dead. That is the signature this file's own Target comment records
for p2-145 attempt 1 (a bad dereference inside a detour).
I DISABLED THE HOOK RATHER THAN DIAGNOSING IT. Defensible - its front is parked (20.291)
and it was blocking a paired boot - but it is a WORKAROUND, and the underlying condition
is unknown. If the hang was in the game function rather than our detour, disabling our
hook removes the observation, not the hang. Recorded in the source with re-enable
conditions. THIS IS OPEN DEBT, not a fixed bug.

## FAILURE 5 - THE BIGGEST ONE: I RE-MEASURED A FRONT THAT WAS ALREADY CLOSED
## (cost: 3 findings, 2 paired boots, one whole analysis document)

20.260 (2026-09-02, NO BOOT SPENT) had already read the creation loop, measured its
gate 2 on BOTH machines across THREE boots, and concluded verbatim:
    "The loop is not the peer path and never could be."
20.221 R2 had said it first: "0x1413086E0 is the LOCAL-PLAYER build path... the whole
'why doesn't the loop create the peer' framing is answered: IT IS NOT SUPPOSED TO."

I then spent 20.298, 20.299 and 20.300 measuring that same loop in increasing detail,
briefed two paired boots around it (p2-176, p2-178), and wrote
FRONT_chain-to-a-moving-guardian.md on top of it - a 237-line analysis whose central
premise ("the wall is the claim state, gated by participant+0x38") was refuted by the
corpus before I opened the file. 20.301 retracts it.

WHY IT HAPPENED, precisely:
  - I entered the front through STATE's headline and the most recent findings (20.292+)
    and reasoned FORWARD from there. The refutation lived ~2,000 lines earlier in the
    same file, under a finding number I never looked at.
  - `bash RE_scripts/q.sh <term>` exists for exactly this - one-name recall over the
    indexes - and I did not run it once. Not for "0x818", not for "creation loop", not
    for "0x1413086E0". The tool that would have surfaced 20.260 in one command was in
    the router I had read that morning.
  - The user's own instinct ("you're likely looking at the wrong thing") was the trigger
    that finally sent me to the source. That should not be the mechanism.
  - NOTHING IN THE WORKFLOW FORCED A PRIOR-ART CHECK. gate_boot.py enforces brief
    SECTIONS; nothing enforces "has this question already been answered".

WHAT IT COST vs WHAT IT BOUGHT: the boots were not worthless - they produced the first
ATTRIBUTED foreign-peer measurement, eliminated delivery volume, and closed the
attribution gap. But every one of those was framed against a wall that does not exist,
and the framing is what a reader inherits.

THE RULE: BEFORE OPENING OR RE-OPENING A FRONT, RUN q.sh ON ITS CENTRAL ADDRESS AND ITS
CENTRAL NOUN, AND READ EVERY HIT. A front is not "open" because the newest findings talk
about it; it is open because nothing in the corpus closes it.

## THE PATTERN ACROSS ALL FIVE

Failures 1-4 are one shape: A CHANGE SHIPPED WITHOUT ITS OWN NEGATIVE TEST.
  - the BOM: no byte-0 check after writing
  - the array: no check that the guard would have failed before the fix
  - the re-arm: no replay of its trigger over recorded data
  - image_set: no confirmation the disable addressed the actual mechanism
The project already had the rule that covers all four (POSTMORTEM_2026-09-01: replay a
new trigger over a recorded run before deploying). It was applied to one change out of
four in a single build.

## WHAT ALSO WENT WRONG THAT WAS NOT A DEFECT

INSTRUMENT BLINDNESS (see ENVIRONMENTS TRAP 19): `grep` in this shell is a ugrep wrapper
honouring .gitignore and skipping "binary" files - it cannot see RE_build/ or RE_output/
and returns exit 0 on a log it silently skipped. Two false claims were published from it
before it was caught. Use /usr/bin/grep for anything under those trees.

FIVE RETRACTIONS were issued across the arc (20.298/20.299/20.300), four of them mine:
20.297 R2's verdict (starved measurement), the "empty-manager spin" (rotation, not a
hang), "the black screen is unexplained" (publish_player_profile is the suspect),
render-and-motion over-separated, and 20.298's "engaged and failed to create" (the create
is never ATTEMPTED - 20.300 R1). The corpus is healthier for them, but each was a
conclusion published before the producing code was read.

## WHAT WENT RIGHT, AND SHOULD BE COPIED

1. THE FIXTURE REPLAY (where it was applied). Replaying R3's trigger over the p2-177 log
   caught a change-gate bug that would have burned the budget in seconds, and a measured
   3.3 s blind spot now documented in the brief's absence-negative. Both fixed pre-boot.
2. INPUT-GATE-FIRST READING. Checking `result=withdrawn` before reading any result is
   what exposed that the rebuild's own headline fix had not fired - instead of reading a
   null result as a finding, which is exactly how 20.297 R2 died.
3. PRE-NAMED ABSENCE NEGATIVES. "Zero gatebyte lines means pgate never ran, NOT that the
   byte stayed zero" was written into the brief BEFORE the boot, so the distinction
   survived contact with the data.
4. TESTING THE USER'S HYPOTHESIS INSTEAD OF AGREEING WITH IT (20.300 R7): asked to
   confirm "the local player takes a different path", the check supported half of it
   (the receive path is remote-only) and refuted the other half (it is ONE create loop),
   which is more useful than agreement.

Failure 5 is a different and more expensive shape: WORK STARTED WITHOUT A PRIOR-ART
CHECK. It cost more than the other four combined, and no gate in this project would
have caught it.

## THE TWO ONE-LINE LESSONS

1. Ship no change without the test that would have caught it failing - and when a build
   carries four changes, that means four tests, not one.
2. Open no front without running q.sh on its central address and its central noun. The
   corpus answering a question is worth more than any boot measuring it again.
