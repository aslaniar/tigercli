# BOOT_BRIEF_p2-173 — THE QUEUE-EVENT CARRIER: eventType 17 AS THE ROUTING KEY

STATUS: READY (2026-09-04 ~12:0x PDT) — change BUILT (server 3bc9a3b922b398bb; client
89e1a2180973938f), verify_hook_rvas PASS (95 RVAs, 0 bad), adversarial pass executed
(session ses_f9258977affe679b6AI6s1baew, verdict FAIL→5 amendments applied: provenance
paths, client artifact identity, falsifier false-positive branch (b), crash family +
0x140E74F80, status/rollback). IMPLEMENTATION boot (the server changes what it sends to
provoke a client behavior), not observational. Ancestor: BOOT_BRIEF_p2-172 (client
build reused; its reseed lever stays OFF).

## PURPOSE

20.292 showed the client's own participant-image apply ends by re-posting a sim-event of
type **17** (0x140B54130: `mov edx,0x11; call 0x140E74FF0` → 0x140DFE4C0, the per-type
apply that resolves decoder(17) via 0x14106F870 and commits via ring_commit's dominant
site 0x140DFE4C0+0x532). The fork's world-population carrier (p2-136/137 era, 20.208 R6)
sends the SAME wire message family (svc-9 activity type 17 → router case 0x11 →
0x1416F0F60) with sim-event **eventType 7** (sobject_message, 0x89-byte Zavala baseline).
20.210/20.211 measured that record taking queue_down's fixed-r8=1 branch (0x140E02740 →
ring_commit) and going ring-only — never consumed.

THE ONE UNKNOWN THIS BOOT ANSWERS: is the sim-event eventType (block+0x08, fully
server-controlled) the routing key that sends a decoded queue-event down the per-type
apply branch (0x140DFE4C0 → decoder(17) → the image/participant plane) instead of the
fixed-type-1 ring branch? If yes, the fork gains a server-side lever into the exact
plane 20.292 reopened — without ever emitting the pointer-carrying message 20.291 R3
forbids.

## THE CHANGE (one line + one knob, server only)

`RE_build/Sunrise-fork-inventory/Sunrise/src/server/bap/encrypted/push/activity/
activity_world_population_push.cpp` line 172 writes the `worldPopulationCarrier`
setting into the payload (change verified in the built exe 3bc9a3b922b398bb). NOTE:
the `RE_build/Sunrise-fork/` tree (without -inventory) is a dead clone at d660a93
still carrying the old constant — do not cite or build from it; the source of record
is -inventory (20.278 R4, ENVIRONMENTS.md). Deploy with `worldPopulationCarrier=17`.

Framing is pre-proven live (20.210: the fork's type-17 message decoded, sobj_decode
fired with the exact 0x89 bytes) — this boot changes ONLY the eventType field.

## VARIANTS (pre-named, one boot, settings flip between runs; reset_lobby_claims.sh
between runs; solo control first)

  V-A  eventType=17, payload = the existing 0x89-byte sobject record (unchanged).
  V-B  eventType=17, payload = 0x80-byte descriptor shape per the client's own re-post
       (0x140B54130 builds {byte 1, u32 selector, u32 size=0, u32, ...} in a 0x80-byte
       region), size field = 0x80. V-B runs only if V-A's decode is rejected (content
       negative 1) — the per-type decoder for 17 may demand the descriptor's size class.

## SETUP

  server   BUILT: sunrise-server.exe 3bc9a3b922b398bb (eventType now written from the
           setting). Settings worldPopulationCarrier=17; the existing
           world_population push gate ON; membership push ON (normal); reseed OFF.
  clients  BOTH steam_api64.p2-173-client.dll 89e1a2180973938f (fresh build, clean
           2e91f94 tree, same resv_claim/image_set observers; the p2-172
           4aa099b6105745e6 artifact is dead — not byte-reproducible; hash + observer
           literals asserted per deployed file). Run the 20.290 R3 no-live-client
           pre-deploy check before deploy; server exe reverts keep the PAIRED
           build_data.bin (20.289 R4). Observers riding: resv_claim 0x1417C3480,
           image_set 0x1403CB720, pool type-trace, ent census, resv_rec/pgate. ZERO new
           hooks. gate_poke=0 both.
  rollback restore client a96a6a70f578fc40 (p2-171) + the PAIRED build_data.bin per
           20.289 R4, using the deploy script's .bak convention.
  capture  capture_bap30975.sh for the wire; verify_hook_rvas.py before deploy (the p2-172
           client RVAs are already verified — re-run anyway, it is cheap).
  gates    gate_boot.py on this brief; LESSONS pre-boot checklist; solo control first.

## INSTRUMENTS: image_set, resv_claim (literals to assert in the DEPLOYED client dll
## 89e1a2180973938f via deploy_client_dll.sh; pool type-trace/ent census/resv_rec/pgate
## ride the same build and are asserted by their own tags)

## GRAPHICS DELTA

POSSIBLE NEW RENDER, pre-declared: the payload names Commander Zavala (vendor baseline,
definitionHash 0x04243655) at Tower courtyard spawn point 18 ([53.69, 65.90, 18.03]). If
the injected event is consumed as an entity/placement record, a vendor-shaped model may
appear near that point — a SUCCESS signal, not an anomaly. A rendered PEER would still be
a surprise to explain (the payload names the vendor, not the peer).

## FALSIFIABLE CLAIM

After the server line `ev=world_population stage=push result=ok type=17` (V-A), at least
ONE of: (a) an `image_set` line fires on either client (the image cache writer was
reached); (b) the pool type-trace names SIM-EVENT eventType **17** reaching the traced
dispatcher — pre-change control: it named **7** (the wire activity-type was already 17
before this change and the always-sent type-52 epoch bump exist; both are EXCLUDED from
(b) — 20.248 saw wire-type 17 and 20.211 R2 saw type-52 unrouted at the activity
router); (c) the client log shows a decode warning naming the type-17 body (which
sizes it); (d) a client crash whose minidump names a frame inside {0x140DFE4C0,
0x1416F0F60, 0x14106F870, **0x140E74F80**} — the decoder this boot's change provokes
(resolved via 0x14106F870(17) at 0x140DFE4C0+0x532) and the most likely first deref
site for a wrong-size body. ZERO of the four after a clean server push = the claim
fails.

## CONTENT NEGATIVE (each pre-named with its next action)

  (1) client decode warning on the V-A body → decoder(17) rejects the 0x89 size class;
      run V-B (pre-authorized). A V-B warning naming ITS size closes the shape question.
  (2) clean decode, no image_set, no new trace name, no crash → queue_down does not route
      by eventType (or 17 is unrouted); the wire→image road CLOSES at the obfuscated
      router wall (the wall 20.291 R5 stands, now with a measured negative); fall back to
      the C3 crafted-row boot (character-data-lookup-brief.md).
  (3) image_set fires with a null/zero image → routing PROVEN (the plane was reached);
      the payload shape is wrong, not the pipe — format work proceeds with a live pipe.
  (4) client crash → consumed and dereferenced; minidump_parse names the site = routing
      proven the hard way; a crash inside 0x140E74F80 is a SIZE-CLASS rejection → run
      V-B; any other site in the family → relaunch, record, treat as (3).

## CHAIN MARKS  (L16)

1. svc-9 framing + envelope encode (fork) — verified-by-execution (20.210: the client
   decoded the fork's type-17 body; sobj_decode fired on the exact 0x89 bytes)
2. activity router dispatch: case 0x11 -> 0x1416F0F60 — verified-by-reading (20.211 R2;
   re-confirmed 20.293 by independent jump-table dump, 1:1 types 1..93)
3. 0x1416F0F60 decode layout {4 x u32, payload[size], tail[136]} — verified-by-reading
   (20.291 R4; re-read 20.293, verbatim match)
4. queue_down 0x140E04E30 -> per-type branch selection — **unknown: THE LINK THIS BOOT
   RESOLVES** (is eventType/block+0x08 the key that picks 0x140DFE4C0 over the
   fixed-r8=1 branch 0x140E02740?)
5. per-type apply 0x140DFE4C0 -> decoder(17) -> image/participant plane —
   verified-by-reading (20.293 R0: the client's own image apply re-post takes exactly
   this path with type 17)
6. image cache write 0x1403CB720 observable (image_set observer) — assumed (install
   verified: RVAs pass verify_hook_rvas, observers in tree; live fire unproven — the
   p2-172 client never ran; the boot's install census covers this)
7. eventType field is server-controlled — verified-by-reading (fork line 169 now writes
   the worldPopulationCarrier setting; server build 3bc9a3b922b398bb)

## ADVERSARIAL PASS: ses_f9258977affe679b6AI6s1baew — verdict FAIL, 5 findings, ALL
## AMENDED (provenance path -inventory; client artifact 89e1a218 named; falsifier (b)
## false-positive branch excluded w/ pre-change control 7; crash family + 0x140E74F80
## size-class branch; STATUS/rollback naming). Re-run of the gate below.

## ABSENCE NEGATIVE

  - ZERO client-side trace of any kind after `result=ok` → check the install census
    (attached=1 for both observers) before calling the routing dead; a silence that
    cannot be told apart from "never installed" is not an answer (20.210 R1's lesson).
  - NO `ev=world_population stage=push` line at all → the server gate/settings regressed;
    fix server-side, no client conclusion possible.

## DO NOT

  - Do not touch the client beyond deploying the already-built p2-172 DLL (no new hooks,
    no pokes; gate_poke=0). Do not enable the p2-172 reseed setting. Do not run paired
    before the solo control shows a clean push. Do not change the payload shape mid-run
    outside the two pre-named variants (boot-test scope is fixed at brief approval).
