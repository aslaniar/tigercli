---
description: Task 5 - close out family 7 and the family-4 discrepancy (completeness)
mode: subagent
model: opencode-go/glm-5.3
reasoningEffort: max
temperature: 0.1
steps: 80
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

# Mission: family 7 close-out + the family-4 discrepancy (the last completeness items)

Families 0/3/4/5 are mapped to FINAL standard. Family 7 has its register site
(FUN_140be49d0, in the investment region alongside family 5) but no map. One
discrepancy also remains: client character-progressions sit 0x10 earlier than
Sunrise's reconstruction (family4-decoders.md FINAL flag).

# Method — family 7
1. Template: family3-roster.md and family4-decoders.md are the shape to imitate.
2. Corpus: the investment region functions (0x140BExxxx decompiles across
   phase3b/6/8), the family-5 helpers already mapped (FUN_140be9430/BE54A0/BDE860/
   BDB930), the dispatch entries for types 100-112, and Sunrise's
   datagen/investment + family5 sources for the server-side shapes.
3. Determine: why 7 co-registers with 5 (hypothesis: talent/unlock/investment-
   adjacent data), wire format (expect the 21B/20B headers), object kinds, apply
   arms, store slots. REQUEST decompiles for any specific function the corpus lacks
   (the 0x140BE9xxx region is only partially exported).

# Method — the 0x10 discrepancy
4. Re-read Sunrise character/layout.h against the client's progression banks
   (FUN_140E07BA0 offsets, the 127-row bank at acquiredFlags-0x742C context).
   Decide: which side is wrong, what the 0x10 shift means, and what a server
   implementer must do (follow the client, not Sunrise, if they disagree).

# Output — RE_output/claims/family7-closeout.md
- Family-7 map to FINAL standard + the discrepancy verdict. WRITE EARLY AND OFTEN.
- FINAL: family 7 end-to-end + corrected progression offsets + open items (if any).
