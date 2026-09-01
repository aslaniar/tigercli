# Plan: scan-negative hygiene (2026-08-31) - SHIPPED

The 20.209 R2 class: a scan's coverage limit promoted to a structural claim
("statically unreachable", "no writers") - three incidents (xref_scan form
filter, field_xref disp32-only, image-encoding-only pointer scans against
RUNTIME_BASE-relocated .data). The class cost the entity-table dead end and
nearly the pool-protocol front.

## THE FOUR MECHANISMS (all shipped 2026-08-31)
1. DUAL-ENCODING SCANS: xref_scan.py --ptrs tests BOTH pointer encodings in
   .data/.rdata (image-based AND RUNTIME_BASE-relocated), counts reported
   per encoding. Verified against the real case: finds 0x141C9AE28 ->
   ent_recv 0x141718510 from the static image in milliseconds - the
   reference that "required" the 6.5GB dump hunt.
2. SCAN-NEGATIVE LEDGER FIELDS: lane-brief-template requires an ENCODEDS:
   line on every zero/none finding (what forms were searched). Negative
   results without encodeds are flagged by negative_audit.py.
3. INVALIDATION SCANNING: negative_audit.py greps the corpus for
   scan-negative claims and flags (a) claims missing ENCODEDS, (b) claims
   predating an invalidating encoding fact (RUNTIME_BASE, 08-30). First
   run: 9 corpus claims flagged - including the exact entity-receive-chain
   dead-end premise and two 08-15 scan-negatives that predate the
   relocation fact. Wired into bootstrap_check (liveness: prints even
   when clean).
4. DEAD-END AUDIT FIELD: lane-brief-template requires one line before
   building instruments to escape a recorded dead end: "the cheap check
   that would falsify the dead end's premise". Precedent recorded:
   20.209 R2 died to a 5-minute relocated-pointer scan after a 6.5GB
   dump tool was built.

## KEEP-LIST (what the dump hunt did right)
The dump-search tool shipped with a self-oracle stronger than designed
(found player_broadcast at base+0x1CA1518, independently confirmed against
20.209 R3's static VA), caught and corrected its own base-conflation in
one step, and recorded structure before pushing on. The dump work was not
the mistake - launching it without the cheap premise-audit was.

## BOOT-GATE CROSS-REF
Mechanisms #1 (STATE READERS), #6 (third-branch counter), #2 (per-arm
discriminator), #8 (unbuilt-instrument grep) live in
~/.opencode/plan/boot-gate-v3.md - pinned, separate build.
