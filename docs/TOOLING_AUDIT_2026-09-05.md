# TOOLING AUDIT - WHERE THE INSTRUMENTS FAILED (2026-09-04 -> 2026-09-05)

STATUS: live (2026-09-05). Written for REFINEMENT, not blame: every entry is a
concrete defect observed in this arc, with what it cost and what would fix it.
Companion to POSTMORTEM_2026-09-05_THE-REBUILD.md (which covers the human errors).
Ordered by SEVERITY = (how silent it was) x (what it cost).

## TIER 1 - INSTRUMENTS THAT RETURNED A CONFIDENT WRONG ANSWER

### T1.1 `grep` is shadowed and lies by omission  *** WORST ***
The shell's `grep` is a function routing to ugrep with `--ignore-files --hidden -I`.
  - `--ignore-files` honours .gitignore. This repo ignores `RE_build/` AND `RE_output/`:
    THE ENTIRE SERVER SOURCE TREE AND THE ENTIRE EVIDENCE CORPUS.
  - `-I` skips files it guesses are binary. `file` calls the capture logs
    "core file (Xenix)", so they are skipped whole.
Both return EXIT 0 with no message. `/usr/bin/grep -ic peer` returned 95 on a log the
wrapped grep reported as empty.
COST: two published false claims before it was caught ("the knob is not in the repo";
"the 20.53 capture has no variant= lines" - it has 53).
FIX (do all three):
  1. A repo-local `rg`/grep wrapper on PATH that forces `-u -a --no-ignore` for paths
     under RE_build/ or RE_output/, or simply alias the project's search to
     /usr/bin/grep in the session bootstrap.
  2. `bootstrap_check.sh` should PROVE the search tool works: grep a known literal in a
     known capture and fail loud if the count is 0.
  3. `loggrep.sh` calls bare `grep -an` and inherits this - pin it to /usr/bin/grep.

### T1.2 `needle_scan.py` is hardcoded to a machine that does not exist
    FileNotFoundError: 'C:\\Users\\rasla\\...\\dump_healthy_inproc.dmp'
It is registered in TOOLS.md under caps `needle-search, dump-sweep` as if general. It is
a DUMP scanner with a baked-in Windows path, unusable for the static PE scan I needed.
COST: dead end mid-analysis; I hand-rolled a PE section scan instead (which worked and
found the 0x2AC0 sites in one pass).
FIX: parameterise the target (`--dump PATH` / `--pe PATH`), default to the repo's
`RE_output/destiny2_unpacked_full.exe`, and PROMOTE the hand-rolled static scan into it -
"find every site referencing constant X in .text" is a recurring need with no tool.

### T1.3 `field_xref.py` misclassifies indirect CALLs as writes
`field_xref.py 0x38` reported 13 "write/RMW" of which most were `ff /2` =
`call qword [reg+0x38]` - vtable dispatch, not writes. Its own TOOLS.md entry says
"judge by context", but the OUTPUT COLUMN SAYS `RMW`, and a reader trusts the column.
Also: the default run covers disp32 only, while a small offset like 0x38 is normally
encoded disp8 - so the scan was both noisy AND incomplete.
COST: nearly concluded "nothing writes +0x38" from a scan that could not have seen a
writer. (The conclusion later held for a different, sound reason - the stride scan.)
FIX: split the `ff` group by ModRM.reg (2/3 = CALL, 0/1 = INC/DEC) and label them
CALL-INDIRECT, never RMW. Warn loudly when the requested displacement is < 0x80 that
disp8 coverage is required and say whether it ran.

### T1.4 `verify_hook_rvas.py` verifies DECLARATIONS, not INSTALLATIONS
After I disabled a hook by commenting out its targets-table entry, the tool still
reported 95 RVAs - because it scans declared RVA constants in source, not the table
that actually gets installed. It PASSED a build whose hook table had a
value-initialised `{nullptr, 0}` entry that detoured RVA 0 and crashed login.
COST: the gate that exists precisely to catch bad hook addresses did not catch the
worst hook-address bug of the session.
FIX: parse the TARGETS TABLE (name, rva, and count) and verify THAT, then cross-check
declared-but-unused constants as a separate advisory. Fail on any target with rva == 0
or name == nullptr. (A compile-time guard now exists in the source; the tool should
agree with it independently.)

### T1.5 `field_xref.py` skips the REX prefix - WRONG VA, WRONG REGISTERS
Found 2026-09-08 during the +0x1AEF8 writer census (FINDINGS 20.349 R9). The disp32
scan anchors on the OPCODE byte and does not walk back over a REX prefix. Two
consequences, both observed on the same run:
  (a) the reported VA is one byte past the instruction start, so `slice_back.py`
      correctly REFUSED it as a mid-instruction anchor (that refusal is the tool
      working - do not read it as "no such site");
  (b) THE REPORTED REGISTERS ARE WRONG whenever REX is present. It rendered
      0x14178CD98 as `mov [rdi+0x1aef8], esi` when the instruction at 0x14178CD97 is
      `mov [rdi+0x1aef8], r14d`, and 0x1417B37DF as `mov [rsi+0x1aef8], edi` when
      0x1417B37DE is `mov [r14+0x1aef8], r15d` - WRONG BASE and WRONG SOURCE on the
      single most important writer in the census.
COST: none this time, because every writer was re-read by linear disassembly before it
entered a conclusion (the 09-03 rule). Had the columns been trusted, the session-state
setter would have been attributed to the wrong base register and sliced from the wrong
provenance - a wrong answer that would have looked entirely plausible.
NOTE: the same run also carried a plain base-register false positive -
`mov [rsp+0x1aef8], eax` reported as a write to the field. The displacement is not the
field; base+displacement is. Neither the tool nor its output says so.
FIX: decode the full prefix chain (REX/66/67/F2/F3) before classifying, report the
INSTRUCTION START as the VA, and render register names through the REX-extended
tables. Until then: every field_xref hit is a CANDIDATE SITE ONLY - re-read it with
`lane_svc43_disasm_range.py` before using its base, its source register, or its VA.

## TIER 2 - GATES THAT PASSED WHEN THEY SHOULD HAVE FAILED

### T2.1 `gate_boot.py` cannot tell whether a brief's decisive read is POSSIBLE
BOOT_BRIEF_p2-177 passed the gate with a decisive read ("watch f38 across the husk
event") that was STRUCTURALLY IMPOSSIBLE: the probe it relied on fires on
participant-table events, not on creation, so it could never have sampled the event.
The gate checks that SECTIONS EXIST. It cannot check that the instrument can observe
the thing.
COST: one solo boot whose headline question could not be answered by construction.
FIX (cheap, high value): require a new brief field `READOUT TRIGGER:` naming, for each
instrument, THE EVENT THAT MAKES IT EMIT - and require a line citing a PRIOR LOG in
which that instrument emitted under that trigger, or the explicit words
`NEVER-OBSERVED (first-fire risk)`. That one field would have caught p2-177 on paper.

### T2.2 Nothing enforces a PRIOR-ART CHECK before opening a front
The single most expensive failure of the arc (POSTMORTEM FAILURE 5): three findings and
two paired boots spent re-measuring a loop that 20.260 closed on 2026-09-02.
`RE_scripts/q.sh` exists for exactly this and was never run.
FIX: add to gate_boot.py a required brief field `PRIOR ART:` listing the q.sh queries
run (central address, central noun) and their verdicts. A brief whose front is already
closed then fails ON PAPER, before a machine is booted.

### T2.3 `negative_audit.py` cannot see tool-blindness
It verifies that a scan-negative declared its encodings. It cannot catch a claim whose
SEARCH TOOL was silently blind (T1.1). New class, uncovered.
FIX: have it flag any scan-negative whose evidence line cites a bare `grep` over
RE_build/ or RE_output/ and does not name /usr/bin/grep or a logindex query.

## TIER 3 - INSTRUMENTS THAT WERE RIGHT BUT EASY TO MISREAD

### T3.1 Budget-capped detail lines vs uncapped census counters
`pb_create` logs 32 enter/leave pairs, then goes counter-only - while the census reports
thousands. "No pb_create line at time T" reads as "no create happened" and is wrong.
This trap is documented and I still nearly hit it; it is now pre-named in briefs.
FIX: make the LAST budgeted line say so - e.g. `budget_exhausted=1 census_continues=1` -
so the log itself tells the reader the detail stream ended.

### T3.2 `logq.py` output buries the payload behind a ~200-char path prefix
Every hit prints snapshot path + archive path + file:line before the message, so any
`cut` truncates the payload and any regex must anchor past it. I lost several queries to
this and had to pipe through `grep -oE` to recover the message.
FIX: `--bare` / `--msg-only` flag printing `t=... <message>`; make it the default for
`--grep` and keep full citation for `--source`.

### T3.3 Field ORDER in mtrace lines is not what a reader assumes
Lines are `ev=mtrace stage=enter fn=pb_create ...` - stage BEFORE fn. I wrote
`--grep "fn=X stage="` and got a clean, believable, WRONG null result.
FIX: document the canonical field order at the top of the observer source and in
TOOLS.md's logq row; better, give logq `--fn` and `--stage` flags so nobody has to know.

### T3.4 `pdata_bounds` correctly says "in a gap" but nothing routes around it
Two of the getters I needed (0x1404DD470, 0x1404DF470) are leaf functions with no
.pdata entry. The right move is the LINEAR disassembler; `disasm_fn` would have invented
a plausible false stream (the documented 20.291 trap).
FIX: `disasm_fn.py` should REFUSE (not warn) when pdata_bounds says "gap", and print the
exact linear-disassembler command to run instead.

## TIER 4 - MISSING INSTRUMENTS (the gaps that cost the most time)

  M1 A TRIGGER-REPLAY HARNESS. The project's own rule (POSTMORTEM_2026-09-01) is
     "replay a new trigger over a recorded run before deploying". There is NO TOOL for
     it - I hand-rolled the replay for one probe and skipped it for the other, and the
     one I skipped shipped an unreachable threshold. A `replay_trigger.py <logindex>
     <predicate>` that answers "how many times would this have fired, and when" would
     have caught BOTH defects in minutes.
  M2 A STATIC CONSTANT SCANNER over the PE (see T1.2). The 0x2AC0 stride scan that broke
     this analysis open was 20 lines of throwaway python.
  M3 MAC-SIDE DUMP TOOLING. Still absent, still on the debt list since 20.297. Every
     dump question is rig-only, and the mac is where half the interesting hangs happen.
  M4 A SESSION<->MACHINE MAP AT THE TOP OF EVERY SERVER LOG. Added this session as a
     keepalive field (R2 of the rebuild) - it should have existed for months; every
     attribution claim before it was inference.
  M5 A "WHAT CHANGED SINCE THE LAST GOOD BOOT" DIFF. Three failures were diagnosed by
     manually comparing state sequences between an archived good run and a bad one.
     `boot_diff.py` exists but was never reached for; it should be the FIRST step of any
     regression triage and named as such in the router.

## THE SHORTEST PATH TO REFINEMENT (if only three things get done)
  1. Fix the search tool (T1.1) and make bootstrap_check PROVE it works. Everything
     downstream inherits its blindness.
  2. Add `PRIOR ART:` and `READOUT TRIGGER:` as required brief fields (T2.2, T2.1).
     Both are paper-cheap and each would have prevented a boot.
  3. Build the trigger-replay harness (M1). It is the only tool that catches an
     instrument defect BEFORE the launch that exposes it.
