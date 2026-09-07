# BOOT BRIEF p2-203 - THE BUBBLE-STARTUP ECHO: a validator-passing type-51

STATUS: prepared 2026-09-07 (post 20.326-20.328 + the wire-map closure W8).
Front: **bubble-startup** (new; streak 0). Server-only: one new type-51 push
per join burst behind `activity_bubble_startup`, echoing the recipient's own
captured SteamNetworkingIdentity. The type-9 duty-cycle is RETIRED
(activity_start_host_push=false - structurally dead, 20.327).

## PURPOSE (what this boot learns, win or lose)

The type-51 (bubble_host_startup_info) body is now 100% specified and
femu-validated end to end: the decode lands byte-exact in every validator
window (the blob-length magics 0x56, the identity echo, the presence bytes),
and the identity compare passes for the authored form (the compare oracle:
the authored form matches, a wrong token rejects). This boot sends it and
measures WHAT THE CLIENT DOES with a validator-passing startup — the apply
half (FUN_140B928D0, obfuscated) is the last candidate to drive the
receiver-object construction gate (row 8: the ent receive blocks have ZERO
instances in all four dumps) or the managed-session setup state.
Win: ANY new client line past the p2-202 baseline; the ent_recv instance
census going 0 -> >0 (a boot-end dump check). Lose (pre-named): silence —
the apply half is inert for our state, and row 8 concentrates fully on the
transport job-gate (20.326 R6b) with no message lever left.

## GRAPHICS DELTA

Zero new rendered models expected. Server-only; clients stay
be5807eca028ddea. No client hooks (HOOK COUNT 0).

## FALSIFIABLE CLAIM

With activity_bubble_startup=true, every join burst carries one type-51
notification (443 bytes) whose body is the femu-validated form: field 1 =
`0A 58 0A 56 <0x56 zeros>`, field 2 = `12 58 0A 56 <the recipient's own
"steamid:<id>#<token>" + zero pad + 0x06 at [0x55]>`, fields 3/4 = `18 41`
and `21 42`, field 5 = `2A 80 02 <256 bytes>` — ALL ASCENDING. The identity
is captured from the recipient's own matchmaking advertisement (the capture
logs `ev=identity stage=capture result=stored account=N`). CONTENT NEGATIVE:
no type-51 push exists in any archive (the all-archive census, 20.324 R4).

## EFFECT CLAIM (distinct from delivery)

DELIVERY: the type-51 frame rides the proven svc9 notification path.
EFFECT (pre-named, not claimed): the client's decode succeeds (femu-proven),
the validator's compare passes (the authored echo), and the obfuscated apply
half runs — whatever it does to the bubble-host state. Downstream movement
(entity lines, the receive blocks' construction) is the win.

## ABSENCE NEGATIVE (L13)

If the client shows no new line: the apply half is inert for our state (the
bubble-host startup may require a co-state — e.g. the validator passing is
necessary but the epilogue's obfuscated gate wants more). The readout
distinguishes: the identity capture lines (stored?) vs the push lines (sent?)
vs the client census (moved?). Each stage names the next lane.

## CHAIN MARKS (L16)

- the wire form (all 7 validator windows) ................................. verified-by-emu (W8: reason=returned, every window set; both scalar encodings)
- the identity compare (the authored form passes, wrong token rejects) ..... verified-by-emu (the compare oracle)
- the identity capture (the advertisement's ASCII steamid region) .......... verified-by-log (p2-202: both clients' live identities in the server log, per-session tokens)
- the push frame path ...................................................... verified-by-execution (the applied type-20 / the delivered type-9 rides it)
- the forward-only field order ............................................. verified-by-emu (W2: out-of-order tags are skipped)

## ADVERSARIAL PASS: self - four ways this boot could mislead me

1. The captured advertisement identity might differ from the client's
   DAT_1426BDCC8 row 2 (different token form/padding). The capture logs the
   version byte when forced; a mismatch shows as the validator REJECTING —
   indistinguishable from an inert apply half ONLY by the client's error
   line (if any). The readout must check for a validator-reject signature.
2. The obfuscated epilogue may crash or no-op silently — a clean null on the
   client is the pre-named lose arm; no boot is spent re-trying encodings.
3. The type-9 retirement (activity_start_host_push=false) changes the burst
   byte-count — any client-side delta attribution must account for the
   REMOVED type-9 frames (they were inert by measurement, 20.327).
4. The identity capture is keyed by account slot; if a client's advertisement
   arrives on the OTHER account's connection (the p2-89 cross-link lesson),
   the echo would carry the WRONG client's identity — the validator would
   reject (a token mismatch). The capture lines name the account; the readout
   cross-checks account ↔ steamid64 pairing.

## PRIOR ART (09-05 FAILURE 5)

- q.sh "bubble_host_startup_info": zero FINDINGS/CLAIMS hits beyond the name
  table (checked this session — the gate's own q.sh run). Verdict: no prior
  boot or lane ever carried the message; the wire form is newly closed (W8).
- q.sh "start_activity_host": the apply-table row + the p2-201/202 records
  (the structurally dead predecessor arm).
- sgrep "type-51|bubble_startup" across RE_output/claims + the upstream tree:
  the community fork never implemented it; the fork's only prior sender =
  none (this is the first).
- The three lane claims (session-identity-decode / type54-and-receiver-gate /
  type51-bubble-startup-spec W1-W8) + 20.326/20.327/20.328.
- The community fork never implemented type-51 (the upstream tree grepped).

## DEAD-END AUDIT

- The view road (20.326): structurally dead, not re-armed.
- The type-9 designation (20.327): structurally dead (the body's session id
  is never read); RETIRED this boot, not iterated.
- The 15-table "validator returns 1" framing: re-read as "the validator's
  return value semantics differ per type" — the compare's pass/fail is the
  decodable contract, femu-verified.

## STATE READERS (a direct reader per asserted state)

- "the identity was captured" -> `ev=identity stage=capture result=stored`.
- "the push went out" -> `ev=activity stage=bubble_startup push bytes=443`.
- "the client moved" -> ANY new client line past the p2-202 baseline (the
  mechanical census diff).
- "the receiver opened" -> ent_recv instance census > 0 (a boot-end dump) or
  the in-boot ent instruments.

## WIDE NET (probes at every decision point)

All existing instruments (HOOK COUNT 0): the capture lines, the push lines,
the client census diff vs the p2-202 archive, the ent/mgr/pool instruments,
boot_verdict's both-machine comparison.

## FIX SURFACE: server

Server only: the bubble-startup encoder + the identity capture/store + the
push site + the settings switch. Client untouched. No SERVER-SIDE GAP
section - the wire item (the startup handshake) is what this boot sends.

## ABANDON OUTCOME (pre-named)

activity_bubble_startup=false: no type-51 anywhere; the burst returns to the
p2-202-minus-type-9 shape (the type-9 gate also flips off this boot).

## NEGATIVE TEST (the arm that fails on the bad state, and where it RAN)

1. THE BODY: ran in femu (W8) - the decode returns cleanly with every
   validator window set; the failing arm = any body without the identity/field-5
   (the windows unset - measured).
2. THE COMPARE: ran in femu (the compare oracle) - the authored form matches,
   a wrong token rejects.
3. THE CAPTURE: the advertisement descriptor's steamid ASCII is proven present
   server-side (p2-202's logs carry both clients' live identities).

## MODEL REVIEW (required: front history)

Front bubble-startup is NEW (streak 0). THE DEAD ASSUMPTION NAMED: "the
validator's return-1 = reject" (the apply-table's framing) — re-read this
session: the compare's pass/fail is the real contract and the femu oracle
proves the authored form passes. The second dead assumption: "the identity
token must be derived" — it is the client's own published per-session token
(20.42's capture), echoed, never derived.
