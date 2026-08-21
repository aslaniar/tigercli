---
description: Task 3 - specify and validate vendor/activity content extraction from .pkg
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

# Mission: vendor + activity definition extraction spec

Vendors (storefronts/inventories) and activities (mission metadata/objectives) are
data on disk, same as the extracted spawn sets. The extraction pipeline is proven
(header v38 -> entry table -> per-patch block files -> AES-GCM -> Oodle -> records).
Your job: identify the class IDs and specify + validate extraction; the main session
runs the pipeline.

# Inputs
- RE_output/content/class_reference_census.json (2.8M entries, top-60 classes)
- RE_output/content/named_tags.json (567 names; "300_vnd" = vendor hint)
- RE_build/Sunrise-021/Sunrise/src/middleware/content/packages/tables/*.h —
  the reader layouts (definition_index_table.h is the grammar; item/progression/
  region/scenario readers are templates for shape expectations)
- The spawn-set extraction as the worked example (content/spawn_sets_full.json)

# Method
1. From the census + named tags, shortlist class IDs plausibly = vendor definitions
   and activity definitions (cite counts + co-occurrence packages).
2. For each candidate: specify which packages to scan, expected record shapes (from
   Sunrise reader headers or analogous classes), and the validation criteria.
3. The main session executes scans/decodes and posts results back; you validate
   against the spec and iterate (multiple rounds expected — treat each result as
   evidence, adjust the spec).
4. REQUEST any Ghidra decompiles needed to read client-side consumption of a class.

# Output — RE_output/claims/content-extraction.md
- Candidate class table with evidence; per-class extraction spec; validated
  inventories as they land. WRITE EARLY AND OFTEN.
- FINAL: vendor inventory + activity inventory with coverage stats and open items.
