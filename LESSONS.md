# LESSONS - the deep layer (process, method, failure history)

STATUS: live (2026-08-26)
Loaded conditionally by AGENTS.md (the router). Read the section you need:

- About to run / deploy ANY game boot -> read THE PRE-BOOT CHECKLIST below,
  then run `python3 RE_scripts/gate_boot.py <brief.md>` before the boot.
- Investigating a failure, a silence, or a null result -> Lessons 13, 14, 11,
  then INCIDENT_2026-08-25_false-loops.md (all three traps recur).
- Spawning or briefing a lane -> THE ANTI-RABBIT-HOLE RULES + the lane-brief
  template (RE_output/claims/lane-brief-template.md).
- Writing or editing any project documentation -> DOC GOVERNANCE section of
  AGENTS.md first; this file's size budget is uncapped but its ADDITIONS obey
  one-in-one-out (see below).
- Escalating a stuck question -> THE UNIVERSAL LESSON 7 (escalate after N), and
  the escalation contract wording in the session protocol.

Everything here was paid for. Do not soften the examples when consolidating.

---

# THE UNIVERSAL LESSONS (2026-08-20, binding - what the equip front paid for)

The subclass-equip panel took five failed delivery-shape boots (16/C/M/N/P) and
closed in ONE boot once the discipline below applied. Every rule = a named
failure mode from this front. DO NOT re-learn them.

1. **THE REFERENCE IS THE ORACLE.** Fetch the upstream/community tree FRESH and
   check the history since the last fetch before ANY mechanism claim about it.
   A stale partial clone produces false lessons (the "upstream has no
   subclass-equip flow" lesson was refuted - the nine commits postdated the
   partial fetch). Read the reference's COMMENTS like documentation and quote
   them in claims - the fix's key ("or the Client completes against the old
   store") was sitting in an upstream comment the whole time.
   **COROLLARY (20.114, and it cost three days).** The oracle you ALREADY HOLD
   counts, and it is the one you will forget to open. "The only remaining unknown
   is one protobuf shape" was carried as the honest next front for three days
   while the answer sat in `RE_output/dumps/bungie_bullshit_guide.txt` - a
   document THIS project extracted, digested, and listed in its own doc map.
   Before naming anything an open RE question, grep the local corpus (dumps/,
   claims/, community/) for it. U1 said fetch the reference; it now also says
   read the references you have. Strengthens U1, replaces nothing.
   **COROLLARY 2 (20.120, and it cost a wasted build).** AN EXPLICIT STAGE LIST IS A
   FILTER, AND A FILTER'S ABSENCES ARE ITS OWN. A grep naming
   `stage=(join|membership|publish|player|link|connect|parameters|view)` was read as
   "21.5 s of complete silence" and a keepalive was designed on it; the omitted
   `stage=packet` was arriving every 250 ms throughout. CENSUS FIRST
   (`grep -o "ev=X stage=[a-z_]*" | sort | uniq -c`), THEN filter - the census had
   already been run that same session and would have shown it. Also: match the event
   prefix, not just the stage (`stage=keepalive` collided with a pre-existing
   `ev=activity` line and briefly read as 20 hits of a thing that never fired).
   Strengthens L13, replaces nothing.
2. **INSTRUMENT BEFORE INTERVENTION.** When a behavior is unexplained, the next
   move = the discriminator instrument (the kind hook), never another fix
   guess. Design the instrument the moment the question is named; NO fix rides
   a boot until the instrument deploys (the reviewer's DO-NOT #1).
3. **COMPLETE THE MAP BEFORE MOVING.** Every claim about a function = its full
   body read end to end + its xref census. Dumped-but-unanalyzed functions (the
   sink FUN_1412f3660 - dumped 08-17, analyzed 08-19) and un-priced gates (the
   inspected-def compare that killed boot P) are where the wrong fixes are born.
4. **THE COMPLETION VIEW.** In a client-server protocol, the reply envelope IS
   part of the contract: hunt the transaction-completion semantics (the
   promised revision, the ack token), not just the payload content. "The apply
   ran" != "the transaction completed" - all five shapes delivered content; the
   missing piece was the completion token (D1).
5. **LOG ROUTING, NOT ACTIVITY.** Instrument the decision points (which
   kind/class each object resolves to), not just "machinery fired." Activity
   hooks read "alive" on every dead delivery - the polls/evals/dispatch fired
   on all five failed boots.
6. **PRE-NAME THE NEGATIVE.** Every boot = a falsifiable claim + a pre-mapped
   next step for the negative. A composed variable is acceptable ONLY if the
   negative stays decisive; record the attribution gap honestly (the winning
   boot's five components = one contract; which was load-bearing = unproven,
   recorded).
7. **ESCALATE AFTER N FAILURES.** Two consecutive failures on the same question
   = write the honest failure list + the outside review (STATE + incident).
   Never let the same session keep guessing - the reviewer's DO-NOT list is
   what broke the loop.
8. **THE DISK IS THE TRUTH.** The report-back = a pointer; the deliverable =
   read end to end; the load-bearing claims = spot-verified on disk. This
   caught the INT32_MIN correction, the drifted line cites, and the t=0 false
   alarm before any of them shipped a wrong fix.
9. **DOCUMENT EVERY GATE'S EXPECTED VALUE.** A verification that reads a log
   line without a documented expected value becomes its own hazard (the t=0
   empty-account identity warn nearly triggered a false fix - the expected
   value is now recorded in FINDINGS 13.4).
10. **THE CONTRACT IS THE VARIABLE.** One boot = one delivery contract with the
    census as the arbiter. The win came from the upstream-exact 403 as a single
    falsifiable unit - not from another shape theory.

11. **AN EXONERATION IS ONLY VALID IN THE DIRECTION IT WAS TESTED.**
    Record the DIRECTION of every negative test, and never generalise a
    one-directional negative into "X is exonerated." Cost of the violation
    (2026-08-22, FINDINGS 15.8/15.9): 14.17 declared the flags "fully
    exonerated" from two probes that BOTH turned flags ON. The true cause was
    a flag being ON, under which "still broken" was the PREDICTED result, not
    a refutation. That false exoneration removed flags from the candidate set
    for six days, nine findings entries, an outside escalation and two full
    sessions of server-side search that kept correctly concluding the data was
    healthy - because it always was.
12. **EVERY BOOT BRIEF STATES ITS GRAPHICS DELTA.** On this Mac the renderer
    compiles cold every launch (no persistent MoltenVK/DXMT shader cache), and
    character pick is the first heavy renderer work. Changing an EQUIPPED
    item's definition changes what must compile there. Cost of the violation
    (2026-08-22, FINDINGS 15.7): a data-correct loadout experiment introduced
    two never-before-rendered weapon models and crashed the game at pick - the
    brief had named an art-index hazard and missed the real one. State how
    many new models an experiment introduces, and minimise it.

13. **A NULL RESULT INDICTS THE INSTRUMENT BEFORE THE SYSTEM.**
    When an expected line does not appear, the FIRST hypothesis to eliminate is
    that the measurement never ran - not that the system lacks the behaviour.
    Prove liveness from the artifact itself, e.g.
    `grep -ac "<instrument literal>" <deployed binary>`, and design every
    instrument so it emits a line on the BORING path too. An instrument that
    can only fire on the interesting case turns silence into an unreadable result.
    Cost of the violation (2026-08-25, INCIDENT_2026-08-25_false-loops.md): two
    boots and a wrong strategic call - "the client publishes no descriptor,
    don't boot the rig" - from an instrument that was never deployed. Note this
    is a REPEAT: the deploy-script gate/restamp ordering bug was the same shape,
    a rig failure attributed to the subject.

14. **THE ARTIFACT UNDER TEST MUST BE PROVEN TO BE THE ARTIFACT YOU BUILT.**
    Never infer provenance from a script's success output. Assert it: the
    deployed hash equals the build hash, checked by the script, which fails loud
    on mismatch. A pipeline step that can silently consume a stale input will
    eventually consume one, and it will report success while doing it. Rule 8
    ("THE DISK IS THE TRUTH") governs claims and documents; this is its build-
    artifact half, and its absence is what made lesson 13 possible.

15. **EVERY SOURCE HAS A SCOPE OF AUTHORITY. NAME IT BEFORE CITING IT.**
    A committed tree is authoritative for "what does their committed code do"
    and for NOTHING ELSE - not for what they have demoed, not for what they know.
    Before any claim built on a source, state the question the source can
    actually answer, and never label a cross-scope inference "decisive."
    Cost of the violation (2026-08-25): called upstream's empty search result
    decisive proof about their fireteam demo and retracted it one turn later.
    The reading was CORRECT and the ref was CURRENT - the failure was scope, so
    do not mis-file this under lesson 1 (fetch freshness). Corollary: a fact the
    user has already supplied ("their demos lead their tree") is binding
    context, and re-deriving a conclusion that contradicts it is a bug.

16. **MARK EVERY LINK IN THE CHAIN, NOT THE INTERESTING ONE.**
    Before proposing any fix, enumerate the full chain and give every link an
    evidence mark: verified-by-execution / verified-by-reading / assumed /
    unknown. An unexamined link is NOT a passing link, and "assumed" must never
    be silently promoted to "verified" by repetition. Never say "one boot away"
    unless every other link carries a verified mark.
    Cost of the violation (2026-08-23..25): three consecutive "one boot away"
    claims, three failed boots. The chain walk that the user finally forced
    (FINDINGS 20.38) produced better information in one pass than all three
    guesses - four unverified links and a subsystem absent from both trees.

17. **NOTHING IN A SHIPPED PROTOCOL IS OPTIONAL.**
    A retail game does not carry decorative message types. Every entry in the
    client's own schema exists because something in the game requires it, so an
    UNIMPLEMENTED type is a missing REQUIREMENT we have not tripped over yet -
    never a deferred nicety. The same holds for a failure enum: if the client can
    name a rejection cause, some path produces it.
    Before building on any protocol, census the client's type table against our
    handlers and write the gaps down. Treat each gap as load-bearing until a
    positive test says otherwise; do not rank candidates by how cheap they are to
    test, which is what ranking on the wrong axis looks like.
    Cost of the violation (2026-08-25, FINDINGS 20.55): types 13/14
    `request_peer_reservation` / `release_peer_reservation` exist in our tree ONLY
    as strings in two log name-tables - no handler at all - while the client's
    failure vocabulary carries `no-reservation` and `no-ambassador-reservation`.
    We named a foreign peer in the roster without ever reserving a slot for them
    and the client froze hard. The lead was recorded in 20.53 and deprioritised
    for three boots of trailing-field guesses because those were cheaper to run.
    This is Universal Lesson 4 ("the reply envelope IS part of the contract")
    generalised, and it was re-learned the expensive way after already being
    written down once.

18. **INSTRUMENT THE SPACE, NOT THE HYPOTHESIS.**
    A boot that tests a guess returns one bit. A boot that observes a whole
    surface returns a map, and maps make the next three boots unnecessary.
    THE UNIVERSAL UNKNOWN-CODE INSTRUMENT, in three parts, all cheap and all
    read-only:
      (a) SIZE THE TABLE PAST THE INTERFACE. Fill every slot of a shim vtable
          with a per-slot logging stub and make the table WIDER than the
          interface is believed to be. Then the client's own calls name the
          real ABI. (This absorbs the 20.97 candidate "a shim vtable must span
          the interface, not the features" - spanning it is what makes the
          census possible, not merely what avoids the crash.)
      (b) CAPTURE ARGUMENTS, NOT JUST NAMES. A slot number says a call happened;
          the argument registers say what it wanted. Read rcx/rdx/r8/r9 in the
          stub: declaring four parameters is safe for a callee that takes fewer,
          because a short call logs stale register contents rather than faulting.
          Judge an argument by whether it is STABLE ACROSS MACHINES (a constant
          or flag), an identity (an xuid), or a module-offset pointer (a string).
      (c) CAPTURE CALLERS FROM ANY FUNNEL YOU ALREADY HOOK. `_ReturnAddress()`
          in a noinline detour body is the caller's code address. Report it as a
          module-RELATIVE RVA, because image bases differ per machine and only
          the RVA is comparable across logs or against a disassembly. With
          .pdata for function bounds and an E8-displacement scan for xrefs, that
          one address opens a whole call graph WITH NO FURTHER BOOTS.
    Cost of not having it (2026-08-27): p2(62)..p2(66), five builds and three
    boots spent guessing friends ordinals from a published header. The census
    boot then answered the whole question at once AND killed the lane. Argument
    capture, added one boot later, immediately refuted 20.101's own conclusion.
    Caller capture, one boot after that, retracted a premise held since 20.82.
    REPLACES: nothing is removed - this SUBSUMES the three lesson candidates
    left pending by 20.98 (guessed ordinals as a crash class; tables spanning
    the interface; census-before-binding), which are now one rule with one
    mechanism instead of three prose fragments.
    COROLLARY (earned the same day): bundle pure OBSERVATION freely, because
    logging cannot break anything and therefore costs no attribution. Bundle
    BEHAVIOUR changes only behind switches that can be flipped without a
    rebuild - p2(62) changed six bindings at once, froze, and its cause is
    still unknown and now unknowable.
    COROLLARY 2 - PASS-THROUGH DETOUR ABI (2026-08-27, the p2(71)/p2(72) rig
    freezes): a pass-through detour body must forward the ENTIRE stack tail,
    not just the args it knows (4 registers + 12 stack slots, bit-exact; a
    callee ignores slots beyond its ABI, but a body that under-declares feeds
    the original frame garbage - reserve took >=7 args, admit ~10, and a
    5-arg body hung session creation). AND: before attaching, statically
    verify the target never reads its CALLER's frame beyond the arg area
    (rbp-relative offsets far above the arg slots) - no forwarding depth can
    fix a caller-frame read, and such a function must be hooked at its
    wrapper (or not at all). Both verified-by-execution on the rig.

## RULE LIFECYCLE (2026-08-26)
Every lesson above follows one flow: written here in full after its incident ->
converted where possible into an executable gate / brief field / rubric line ->
its PROSE redundancy resolved via the one-in-one-out rule. Lessons that stay
prose-only forever are labelled JUDGMENT RULES (e.g. 15) - automation cannot
carry them; review-time attention goes there instead. ADDING lesson N requires
naming which existing lesson it strengthens, sharpens, or REPLACES.

## THE PRE-BOOT CHECKLIST (binding - a boot costs the user real time)

Before asking for ANY boot test, all four must hold:

1. **Provenance** - the deployed artifact's hash equals the build's, asserted by
   the tooling, and any new instrument literal is confirmed present IN the
   deployed file.
2. **Liveness** - a named line that MUST appear if the instrument ran at all,
   independent of the outcome under test.
3. **Both negatives pre-named** - the CONTENT negative ("routable=0 means X")
   AND the ABSENCE negative ("zero lines means the instrument did not run, which
   means Y"). Lesson 6 requires the first; 08-26 proved the second is where the
   damage lives.
4. **Chain marks current** - the link this boot resolves is identified, and
   every other link's mark is written down (lesson 16).

Prefer, over all of the above, a change that makes the failure impossible to
express: a deleted overload, a deleted default argument, a compile error. The
moves that have actually paid on this project all convert runtime vigilance into
a compile-time or assert-time failure. Vigilance does not survive a long day.

NOTE 2026-08-26: items 1-4 are enforced mechanically by
`python3 RE_scripts/gate_boot.py <boot-brief.md>` (exit 1 = do not boot). The
checklist remains prose so the reasoning survives; the gate stops the slip.

---

# THE ANTI-RABBIT-HOLE RULES (2026-08-20, binding - the execution contract for lanes AND the main session)

The observed killer failure = the RABBIT HOLE: reacting to a symptom
turn-over-turn, fixing one thing, causing another, looping until someone has to
say "stop, breathe, get the facts straight, execute surgically." Every rule
below = that failure + its countermeasure. Every lane brief carries: THE
EVIDENCE ANCHORS, THE FALSIFIABLE QUESTION + THE EXPECTED VALUE, THE
DEATH SAFETY, THE DO-NOT.

1. **STOP -> SEE IT END TO END -> VERIFY -> ONE SURGICAL ACTION.** When a symptom
   or a failure appears mid-work: (a) STOP - no immediate fix; (b) SEE the
   whole picture FIRST - the full chain, the expected values, the newest
   evidence - before touching anything. The canonical near-miss: the deploy's
   t=0 identity warn, where a deep hash-hunt nearly shipped a false fix
   because the end-to-end read (which pass logged the line) never happened
   first. (c) VERIFY the facts from disk - the newest timestamp wins; (d) ONE
   surgical action with a pre-named expected outcome. If the outcome !=
   expected: STOP again - never a second guess in the same motion, never a
   cascading edit while the first one is unproven.
2. **A FIX MUST NOT MAKE NEW BUGS.** One variable per fix; the
   contract-preserving shape (the reference is the oracle); the harness gate
   before deploy; and the regression check of the previously-working behavior
   in the validation boot (e.g., the equip panel still switching).
3. **THE REFUTATION IS A DELIVERABLE.** Every brief names what would refute
   the expected answer, and the lane is instructed to write the refutation if
   it lands there. The lane's incentive = the truth, not the brief's
   confirmation. "A NEGATIVE is decisive" = uniform, not per-brief.
4. **THE 3-LINE REPORT-BACK.** The report-back = a fixed template (what
   landed / where / one-line verdict per question) - <=3 lines, <=10% of the
   budget. The budget belongs to the files. (The observed death mode: the
   report-back ate the budget - lanes C and T died at exactly this step.)
5. **PHASE-CONSISTENCY.** Each phase re-reads the PREVIOUS phase's claims
   before writing its own - the lane checks its own record, and the drift
   stops at the file. The per-phase claims = the required minimum deliverable;
   the consolidated file = OPTIONAL (the main session = the collector - the
   resume pattern that recovered lane T).
6. **THE LOAD-BEARING MARK.** The brief marks which claims are load-bearing;
   the lane writes those with full quotes + exact offsets (the main session's
   spot-verification reads them first - the verification arm exists for a
   reason).
7. **TWO DEAD-ENDS = A REWRITTEN BRIEF.** The same sub-question dead-ending
   twice -> the brief gets rewritten with a corrected premise, never re-run
   verbatim (the escalation contract, applied to lanes).
8. **THE COLLECTOR IS ALWAYS ARMED.** The main session completes a dead lane's
   deliverable from the raw, or spawns a resume with a synthesis-only brief.
   Check disk + the session DB BEFORE any respawn (the 12.6 correction -
   never respawn blind).

---

# THE NO-SYNTAX-TAX RULES (2026-08-20)

Converted 2026-08-26 to mechanical enforcement: RE_scripts/hooks/pre-commit
parses staged .py/.sh/.bash before any commit. The original six rules remain
documented here because the reasons matter when extending the hook:

1. **PARSE-CHECK BEFORE RUN** - now the hook's job.
2. **SMOKE-RUN FIRST** - run each new script once against trivial input, exit 0,
   before the real run. Still judgment; the hook cannot smoke-test FOR you.
3. **ONE GHIDRA RUN = ONE SCRIPT** - a syntax error at the end of a ~77 s Ghidra
   project run wastes the run; parse+smoke happens before submission.
4. **VERIFY THE BYTES BEFORE CONCLUDING** - mangled console output (missing
   fields, stray NULs) = re-read RAW bytes of the source/log before concluding;
   the captures contain NUL bytes (grep needs `-a`); a mangled line near-read
   as truth once already.
5. **NEVER GUESS THE TARGET TEXT** - edit-tool oldString comes from a fresh
   read; a failed match = re-read, never re-guess.
6. **ASCII-ONLY COMMENTS** - non-ASCII (U+2014 em-dash) mojibake corrupted three
   source comments once; the fix cost more than the dash was worth.

---

# METHOD (2026-08-15, the contract-first principle)

The in-process Sunrise DLL is the only proven-working server implementation for
this client. Its behavior IS the spec - divergence from it is a bug until proven
otherwise. Every new server capability starts with a DIVERGENCE CENSUS (grep
every mode-gated branch + diff the in-process behavior end-to-end) BEFORE any
implementation. The working contract lives in RE_output/claims/s1-accept-contract.md
(the living spec, one section per milestone). Elimination-by-diff, never
by-theory: a boot only happens when the diff names a candidate or says
"nothing left." Full operational shape: RE_output/claims/lane-brief-template.md.

# SESSION PROTOCOL (surviving core)

- **STATE.md (root) = the living snapshot. Read it FIRST** - or better, run
  `bash RE_scripts/bootstrap_check.sh`, which prints the STATE header, the
  newest finding headlines, the doc-budget report, and index liveness counts.
  After any restart/compaction: rewrite STATE.md from disk (distill, don't
  re-derive) within its structural limits (see DOC GOVERNANCE).
- **FINDINGS stays the append-only archive.** STATE holds no incident
  narratives; incidents live in FINDINGS entries (+ INCIDENT_* digests when
  generated).
- **Escalation contract**: invoke the outside review with "STATE + incident <ts>"
  only. Reviewer returns facts w/ evidence pointers, a ruling, bounded actions,
  and a DO-NOT list. The reviewer audits STATE against disk; the main session
  owns the pen. Load the dedicated reviewer agent when available
  (.opencode/agent/verify.md) for pre-boot adversarial passes (see AGENTS.md
  ADVERSARIAL PASS requirement).
- **Incidents**: `incident.py` digests logs/hashes/session events into
  RE_output/incidents/INCIDENT_<ts>.md when anything breaks live. NOTE
  2026-08-26: incident.py is Windows-era and schema-stale (reads legacy tables);
  treat its output as partial until the port lands. Re-verify hashes before
  every game boot regardless.

# CONVENTIONS (abbreviated; details retained where they live)

- VERIFIED facts get citations; INFERRED mechanisms are labeled.
- Timestamps on EVERY new recording (2026-08-16, hard): FINDINGS entries open
  `## N.N TITLE (YYYY-MM-DD ~HH:MM)`; exact time, never bare date; newest
  timestamp wins conflicts. The index lint reports violations.
- Deliverable rule (2026-08-16, hard): every subagent report-back is a POINTER,
  never the source of truth; deliverables are read END TO END at landing;
  load-bearing claims spot-verified on disk.
- Community links get recorded so sessions can pick up where the last left off.
