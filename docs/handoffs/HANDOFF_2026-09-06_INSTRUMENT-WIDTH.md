# HANDOFF 2026-09-06 — THE INSTRUMENT WAS NOT WIDE ENOUGH (the identity-census surprise)

STATUS: live (2026-09-06, after p2-188b). Written for a workflow session
taking over the session-lookup-identity front's instrumentation. Read
STATE.md + FRONT_peer-render-chain.md row 5 first.

## THE ONE-PARAGRAPH STATE OF THE WORLD

p2-188b proved the retarget mechanism live: the server rewrote the relayed
join's sessionId, the client received it, and the client's refusal line
NAMES the rewritten value. Arm 1's value (the recipient's join machine id)
is refuted — the gate's 6-slot lookup refused it and the join processor
never ran (0 events). The unexpected finding is the blob census: the
mac's client holds ALL THREE identity values in its session records
somewhere — the fork's sessionId (match=1), the machine id (match=1), the
real account key (0xD3DABDA3AF16F99E) — plus two more identities
(0xF1355488131A3F56, 0x8E4B5C1BE4FBBA92). The gate STILL refused. The
question "which of these containers does the failing gate actually walk?"
is UNANSWERABLE from the current instrument's output, and that limitation —
not the mechanism — is what the next instrument must fix.

## WHY THE CURRENT INSTRUMENT CANNOT ANSWER IT (three specific gaps)

1. THE HELPER IS SHARED. sess_cmp hooks the equality helper 0x141A83C00,
   which the project's own decode proves is called from MULTIPLE consumers:
   the join gate's walker (0x14177A0B0), the by-id lookup (0x14179AF00),
   the candidate table, the mac's own join flow. The instrument logs
   (key, blob, match) — but NOT WHO CALLED. Every logged pair is
   attributable to any caller. The p2-188b "blob census" is a census of ALL
   consumers mixed together; the gate's own slot contents are invisible
   inside it.

2. THE NOVELTY GATE HIDES REPEATS. The hook is novelty-gated on the
   (key, blob) pair: each distinct pair emits ONCE. The refusal's walk at
   the moment of failure compared only previously-seen pairs — so the ONE
   comparison that decides the outcome produced ZERO log lines. Two boots
   in a row read pre-refusal comparisons as if they described the refusal's
   walk (the 09-03 postmortem class: a conclusion drawn from a probe field
   without reading what produces it).

3. NO CONTAINER IDENTITY. The walker's slots are pointers inside a
   per-connection context; the blobs live at record+0x57C/+0x94E selected
   by bit 4 of [rec+4]. Without the caller (and ideally the container base
   and slot index), a blob value cannot be attributed to "the gate's slot
   for connection X" vs "the landing's session" vs "the candidate table".

## THE COST ALREADY PAID (what the narrowness hid)

- p2-187: "the blobs hold the machine's own identity" — derived from pairs
  whose caller was unknown; the STATE then carried "the gate's slots hold
  the receiver's own identity" as if observed at the gate.
- p2-188b: the retarget value appeared with match=1 in SOME container while
  the gate refused — two readings conflict unless callers are known.
- The three identity forms (fork sessionId / machine id / real account key)
  were each "present" in logs without ever being locatable in the walked
  container. Two boots spent on value arms that the instrument could not
  have confirmed in advance.

## THE NEXT INSTRUMENT (spec, for the workflow session)

- NAME: sess_cmp_caller (or widen sess_cmp in place — one hook either way).
- CHANGE: at the equality helper's entry, log the RETURN ADDRESS
  (module-relative RVA via the _ReturnAddress pattern — retail_log_enqueue_
  observer.cpp is the proven precedent, LESSONS 18c), plus the existing
  (key, blob). Optionally also the caller's container pointer if cheap.
- GATE: novelty-gated per (caller RVA, key, blob) TRIPLE, not (key, blob) —
  a repeat comparison by a DIFFERENT caller must still emit.
- BUDGET: 64 triples (the shared helper fires from several consumers; the
  p2-187 budget of 24 pairs undercounted by construction).
- ACCEPTANCE (the replay gate, 09-01 rule): replay p2-188b's mac capture
  through replay_trigger.py with a triple-emitting fixture BEFORE deploy;
  it must produce firings whose caller RVAs include 0x14177A0B0's call
  site of the helper, or the hook placement is wrong — do not boot.
- DEPLOY: client DLL only (both machines), 59 targets, verify_hook_rvas
  before boot; the helper sits in a .pdata gap (review-not-fail, as banked).

## THE QUESTION THE WIDENED INSTRUMENT ANSWERS

With (caller, key, blob) triples from one landing: which caller RVAs fire
during the relayed join's gate, and what blobs THOSE calls see. That names
the gate's walked container directly — the answer that decides between
"the binding decode (connect-family handlers)" and "arm 2 (the real
account key)" WITHOUT another value-arming boot.

## RULES THIS ARC EARNED (do not re-derive)

- A shared helper is NOT a chokepoint for one consumer — a hook on it
  measures the UNION of its callers; widen to caller identity before
  reading any container claim off it.
- Novelty gates hide the exact moment they were built to catch; gate per
  the discriminating triple, never per the observed values alone.
- The client's join identity table caches the PRE-NETWORK-MOVE address in
  its first NetAddr pair (mac: .164 stale / .7 current); any decoder that
  requires the two pairs to agree will fail one machine and look like a
  decode failure. Accept either pair matching the datagram source (SHIPPED).
- The refusal line's session field renders as two reversed dword groups
  ("CB8F2E17:019EF916" = 0x16F99E01172E8FCB) — decode before comparing.

## ARTIFACTS

- Boot outcomes: RE_output/map/boot_outcomes.jsonl (p2-188 third-branch,
  p2-188b hypothesis-wrong, p2-189 hypothesis-survived; D-018/D-020 closed).
- Captures: RE_output/captures/<stamp>_p2-188b and _p2-189 (server + both
  clients).
- p2-189's outcome (this spec's validation): ALL six new instruments fired on
  both machines; the caller-discriminated sesscmp works (two consumers named
  by caller_rva) but the flat 64-triple budget was spent by the landing's
  noise before the relayed join — the spec's gate design was right, the
  budget allocation needs PER-CALLER sub-budgets (16/caller, first-seen-key
  per caller). The walk_map probe worked first boot (its map is in the
  capture; cosmetic stage-tag mismatch: the line says `walkmap`).
- The retarget mechanism (proven live): peer_transport.cpp
  relay_join_body + rewrite_join_session_id; setting
  relay_join_target_identity, currently FALSE (byte-verbatim).
- The decoder fix: join_messages.h/.cpp JoinMachineIdentity address2/port2.
- The blob census source: RE_output/captures/*_p2-188b/mac_client_sunrise.log
  (grep "stage=sesscmp" | blob= | sort | uniq -c).
