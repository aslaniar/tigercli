---
description: Task 2 - join schema field names to the captured 170-field layout
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

# Mission: name the schema fields

The live-captured schema tree (content/schema_tree_live.json: 3 nodes, 170-field main
schema) is STRUCTURALLY complete — ordinal, bits, back-offset, codec per field — but
semantically unnamed. The property-name vocabulary is known (38+ names,
entity-archetypes.md, extended by the phase9 gap-dump: update_at_rest, ammo,
rigid_body_transforms, power, health_station_charges, auto_turret_aiming...).
The join between them has not been made.

# Method
1. From claims/entity-archetypes.md FINAL + phase9 tables: re-derive the exact
   property-name list and the schema-node layout relationships.
2. Hypothesize the join mechanism: the schema nodes' sibling pointers (the q0 row
   chain's c2/c3 columns, the array objects at 0x30EAxxxx vtables) likely carry
   name-table links. Specify EXACTLY what live read would expose them (address,
   expected shape, acceptance criterion).
3. Cross-validate offline first: field ORDER vs property-name address ORDER in
   .rdata (0x141CA0E20-0x141CA1348) — if both tables were emitted by the same
   codegen, ordinal order may equal name-table order. Test the hypothesis against
   bits/codec sanity (position = vector3d codec, vitality = quantized f32...).
4. If the offline join succeeds: emit the named schema. If not: the live-read spec
   becomes a REQUEST.

# Output — RE_output/claims/schema-named.md
- The join hypothesis + validation; the named 170-field schema if it lands;
  REQUESTs for the live reads otherwise. WRITE EARLY AND OFTEN.
- FINAL: schema with field names, codecs, bits — or the exact blocker.
