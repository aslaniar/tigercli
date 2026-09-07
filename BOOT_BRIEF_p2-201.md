# BOOT BRIEF p2-201 - THE ACTIVITY-HOST DESIGNATION: the fork tells each client to START hosting

STATUS: prepared 2026-09-07 (post p2-200 clean null + 20.326). Front:
**activity-host-designation** (new; streak 0). Server-only: one new type-9 push
in the join burst behind `activity_start_host_push`.

## PURPOSE (what this boot learns, win or lose)

The receiver-object construction (row 8) is gated on VMP-managed client state
(20.326 R6b; the gate global is VM-resolved, NULL in dump_p2146 = the receiver
infra is genuinely not built in our state). The activity-plane participation
machinery is ALIVE (citizens adopted, bubble authority granted grant=6, roster
published) — what no one has ever sent is the **host designation**: activity
type 9 (start_activity_host), whose client apply (0x140E0EE40 -> 0x140C208D0 ->
0x140C11B60) runs the per-session host state-machine step. This boot sends it.
Win: ANY new client-side behavior past the p2-200 baseline (activity-host
lines, ent/receive movement, router-census changes). Lose (pre-named): silence
— the designation alone does not open the receiver, and the next levers are
the type-51 handshake (the 'V'-magic validator, apply-table row 11) or a
non-empty type-54 bubble-host table.

## GRAPHICS DELTA

Zero new rendered models expected. Server-only change; clients stay
be5807eca028ddea (the audited platform; tree client ee31a1b1-class builds stay
undeployed per D-049). No client hooks ship (HOOK COUNT 0).

## FALSIFIABLE CLAIM

With activity_start_host_push=true, every join burst carries one type-9
notification whose body is exactly 13 bytes: [01][activity-session-id u64
little-endian][04 u32 little-endian] (for session 0x9EAA300100200001:
01 01 00 20 00 01 30 aa 9e 04 00 00 00). The client's decode variant
(0x140E0DC20) requires byte0==1 and reads dword[+9] directly; the apply sets
its state-machine flag from dword==4. CONTENT NEGATIVE: no type-9 push exists
in any prior archive (the server's own push census lists types 1/5/12/2/52/17/
54/47/4/39/20/0 — never 9).

## EFFECT CLAIM (distinct from delivery)

DELIVERY: the type-9 frame rides the proven svc9 notification path (the same
frame the applied type-20 uses), byte-count 13+frame. EFFECT (pre-named, not
claimed): the client's host state-machine step runs for the named session; any
downstream receiver/participation movement is the win. A clean null closes the
"designation alone" arm and the next boot arms type-51.

## ABSENCE NEGATIVE (L13: what ZERO new lines means)

If the client shows no new line and ent_recv stays 0: either (a) the client's
session lookup missed (the id in the body does not match its session record —
check the unmix/lookup path 0x140E36C30), or (b) the state-machine step ran
and the receiver gate sits deeper (the VMP'd +0x25 global). The fork-side log
line `stage=start_host push` separates "we sent" from both.

## CHAIN MARKS (L16)

- the push frame path (svc9 notification, type + payload) ................... verified-by-execution (the applied type-20 rides it)
- the type-9 body layout: [1][u64 session][u32 4] ........................... verified-by-disasm (0x140E0EE40 byte[0]==1; 0x140C11B60 dword[+9]==4, qword[+1]; 0x140E0DC20 decode variant)
- the apply is a 15-table row (type 9 = FUN_140E0EE40) ....................... verified-by-reading (apply-table-entity.md row 2)
- fail-safe: unknown session id -> 0x140E36C30 returns null -> no-op ......... verified-by-disasm (0x140C208D0 null check)
- the activity-plane participation machinery is alive (citizens, grants) .... verified-by-log (p2-200: grant=6, peer_advert built, membership_peer included)

## ADVERSARIAL PASS: self (this session) - three ways this boot could mislead me

1. The type-9 push could arrive BEFORE the client's session record exists (the
   join burst is early) - the no-op degradation makes this invisible. If the
   readout is silence, the FIRST retry variant is sending type 9 again later
   (on the roster/keepalive cycle), before concluding the designation is wrong.
2. The body's byte order could be wrong (native LE assumed from the client's
   direct struct reads; if the schema decode transforms the wire, the id
   mismatches -> no-op, indistinguishable from (1)). The femu arm below pins
   the struct read, not the wire transform - named honestly.
3. The client might BECOME a host without any visible log line - the receiver
   gate opening would show as ent/receive movement only. The readout therefore
   watches the FULL client census, not just activity-host strings.

## PRIOR ART (09-05 FAILURE 5)

- sgrep "start_activity_host" in the corpus: apply-table-entity.md row 2 (the
  client's own apply, decoded), the name table (type 9), the fork's route
  (type 8 accepted as client->host; type 9 never sent by anyone).
- q.sh "bubble host": 20.326 (the view road), the registry decode. Verdict: no
  boot has ever carried a type-9 push; this is the first.
- The community fork never implemented types 8/9/51/54 encoders (upstream tree
  grepped) - their own status list ends at "citizen join waits forever".

## DEAD-END AUDIT (required: PRIOR ART cites retracted work)

- The view road (20.326: structurally dropped): NOT re-armed; this lane is the
  activity-plane replacement, motivated by the same row-8 question.
- The type-21 grant (no applier... inapplicable): stays off.
- The 62-row 0xa8 table / the 15-table applies: not claimed as the receiver.

## STATE READERS (a direct reader per asserted state)

- "we sent it" -> server `ev=activity stage=start_host push session=... bytes=13`.
- "the client ran the step" -> ANY new client line past the p2-200 baseline
  (activity-host state-machine logs, error-log variant `enum-name bound < 2`
  would itself prove the apply RAN with body[0]!=1 - a framing bug signature).
- "participation moved" -> ent_recv calls > 0, stage=tail > 0, new router
  census types, the mgr/pool instruments' deltas.

## EFFECT CLAIM (see above) / WIDE NET (probes at every decision point)

All existing instruments (HOOK COUNT 0): server push lines (stage=start_host),
the upstream svc8 dump lane (any client-host-state echo), the client census
lines (ent/mgr/pool/retail site lines), boot_verdict both-machine comparison
vs the p2-200 archive.

## FIX SURFACE: server

Server only: the new encoder + push-site + settings switch (default OFF; this
boot turns it ON). Client untouched. No SERVER-SIDE GAP section - the missing
wire item (the host designation) is what this boot sends.

## ABANDON OUTCOME (pre-named)

activity_start_host_push=false: the burst returns byte-identical to p2-200
(the type-9 frame disappears; no other body changes).

## NEGATIVE TEST (the arm that fails on the bad state, and where it RAN)

1. THE BODY LAYOUT: ran in disasm this session - 0x140E0EE40 requires byte0==1
   (jne error-log path), 0x140C11B60 reads qword[+1]/dword[+9] (sete from ==4),
   0x140E0DC20 (the decode variant) re-checks byte0 and reads dword[+9] before
   the tail validator. The failing arm = any body with byte0!=1 (client-side
   error log fires - visible).
2. THE ENCODER: ran in the standalone round-trip this session
   (01 01 00 20 00 01 30 aa 9e 04 00 00 00 for 0x9EAA300100200001; asserts the
   mode/id/value round-trip).
3. THE FRAME PATH: ran in boot p2-198 (the type-20 push applied end to end on
   the identical notification frame).
4. Byte-order caveat (honest): the WIRE transform between payload and decoded
   struct is not femu-pinned; the no-op degradation is the pre-named cost, and
   ADVERSARIAL 2 names the follow-up.

## MODEL REVIEW (required: front history)

Front activity-host-designation is NEW (streak 0; p2-200's allocation-content
closed hypothesis-wrong = a clean null, pre-named). THE DEAD ASSUMPTION NAMED:
"participation = membership + allocation" - both are proven working
(citizens, grants, mask filled) and the receiver still never builds; the
missing half must be a designation, and type 9 is the only host-designation
message whose client apply is fully decoded.
