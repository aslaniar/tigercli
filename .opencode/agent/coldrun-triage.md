---
description: Task 1 - classify and name the 12,699 recovered cold-run functions
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

Read RE_scripts/domain_brief.md FIRST — it is the distilled domain map, trap list,
and claims discipline for this territory. Everything below assumes it.

# Mission: classify and name the cold-run functions

The 12,699 functions in 0x145D0D000-0x148A5E000 (zone-active code, phase10 corpus)
have auto-names only. Classify them by subsystem and name what you can.

# Method
1. Digest RE_output/export/phase10/decompiles.txt (the 40-function sample) to learn
   the region's call shapes: tiny 1-9B stubs = vtable thunks; 60-160B bodies = methods.
2. Cross-reference every function against the known-region map (domain brief):
   which call into the entity apply chain, the 19-command registry handlers, the
   schema readers, the queuez arms? A call into a known function = classification
   evidence.
3. Correlate with functions.csv density clusters and strings_dump addresses inside
   the two ranges.
4. Classify into subsystem buckets (entity/combat/encounter/audio/UI/unknown) and
   name high-confidence functions in the vocabulary of the existing maps.
5. REQUEST specific decompile batches (address ranges, <=60 functions each) for the
   clusters you most want; the main session executes them and the corpus grows.

# Output — RE_output/claims/coldrun-naming.md
- Per function: addr, proposed name, bucket, evidence (callee/strings/shape),
  confidence.
- A coverage table: how many of 12,699 classified/named/bucket-only/unknown.
- WRITE EARLY AND OFTEN. FINAL section: subsystem map of the cold runs + ranked
  REQUEST list for the next decompile batch.
