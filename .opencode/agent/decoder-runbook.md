---
description: Task 4 - produce the live-read runbook for the 237 unpopulated decoder entries
mode: subagent
model: opencode-go/deepseek-v4-flash
reasoningEffort: max
temperature: 0.1
permission:
  read: allow
  grep: allow
  glob: allow
  edit:
    "RE_output/claims/*": allow
  bash: allow
  webfetch: deny
  websearch: deny
  task: deny
  external_directory: deny
---

Read RE_scripts/domain_brief.md FIRST — distilled domain map, trap list, claims
discipline. Everything below assumes it.

# Mission: decoder-population runbook

The type->decoder registry (DAT_14280E3E0, 308 slots) instantiates lazily: only 71
were live at orbit AND at a normal destination. The other 237 populate when specific
content runs. Your job: produce the exact runbook for a human-in-the-loop capture
session that populates as many as possible.

# Inputs
- RE_output/content/live_destination_dump.json (the 71 populated: which types)
- claims/bap-dispatch.md (the complete message-type map: which types exist, names)
- claims/opcode-sweep.md (which ws-opcodes are suspected behind which types)
- The full message-ID key space: req/rsp 6..307 (domain brief + claims)

# Method
1. Diff: which of the 308 slots are populated vs empty, mapped against message-type
   names — i.e., WHICH content instantiates WHICH decoders (PvP? raids? social?
   character-edit? director? vendors?).
2. For each unpopulated cluster, name the game state that should instantiate it,
   ordered by expected yield per session-minute (Crucible private match, raid
   arrival overrides, vendor interaction, director usage, emblem/collections UI...).
3. Specify the read: the existing script re-run after each state; expected deltas;
   the acceptance criteria (new non-zero slots; decoder object uniqueness).
4. Flag which unpopulated types likely NEVER instantiate offline (server-only or
   live-build-only) — honest negative expectations prevent wasted session time.

# Output — RE_output/claims/decoder-runbook.md
- Ordered state->expected-types table; per-state capture instructions; acceptance
  criteria; the never-offline list. WRITE EARLY AND OFTEN.
- FINAL: the runbook itself, ready for a 30-60 min play session.
