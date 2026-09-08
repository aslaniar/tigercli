# BOOT BRIEF p2-206 - THE PER-PEER SETUP-COMPLETE SIGNAL: THE ONE NAMED,
# WIRED, NEVER-ARMED WIRE ITEM (activity_member_setup_flags=true)

STATUS: prepared 2026-09-07 (post 20.330-20.332; the milestone question
re-examined). Server-only SETTINGS change - NO rebuild: the encoder has been
in every deployed binary (group_host.cpp flags the peer rows, the middleware
writes varint fields to the membership body); the config had it FALSE for the
entire modern boot era (the p2(91) all-rows experiment broke the citizen
join; the self-row-exclusion fix was written and NEVER BOOTED). Clients
unchanged (be5807eca028ddea both). HOOK COUNT 0.

front: member-setup-flags

## WHY THIS IS THE NEXT MOVE (the milestone question, answered from the corpus)

The 2020 live game worked with this exact build. The fork measured everything
the client's render chain requires and found ONE named wire item never
published: the per-peer activity-setup-complete signal - member flag bytes
+0xED/+0xEF on the client (ms-start-gate claims 6/7, FINDINGS 20.151/20.152),
carried by member protobuf FIELDS 11/12 (proven the only 1-byte member
fields by the client's own descriptor table 0x141ca68e0). That signal is the
state the per-peer managed-session setup completes on - the same setup the
per-connection sweep armed bytes wait on (lane #4: [entry+0x109] never armed
in ANY artifact; the only readable gate inputs, all downstream of this
setup). In 2020 the host side of a session sent peer rows WITH those flags;
every boot the fork has run, it sent them WITHOUT (member_setup_flags=0 in
every launch line). FINDINGS 20.328 R1 said it flatly: "gated on the
per-peer 'activity-setup-complete' signal the fork does not publish" - the
publication exists in code, behind a switch the config has held OFF since the
p2(91) accident.

## PURPOSE (what this boot learns, win or lose)

SEND the membership rows with flagA/flagB=1 on every PEER row (never the
recipient's own - the p2(91) regression signature is pre-named), and measure
whether the client's per-peer setup completes: the armed-pair census, the
sweep/connection state, and THE receive-block construction (the ent slot-10
instance census) - the row-8 door, for the first time with its upstream
signal present. Win: any NEW client line; the armed-pair delta; ent
instances > 0 (a boot-end dump). Lose (pre-named): flags sent, census
identical - the setup-complete signal is necessary-but-not-sufficient and
the remaining gate state is the VMP-reader residue (the +0xED/+0xEF base
fixups) - the milestone's next question stays client-internal but this boot
retires the strongest unarmed lead either way.

## GRAPHICS DELTA

Zero new rendered models expected. Server-only settings flip. No hooks.

## FALSIFIABLE CLAIM

1. The server's membership bodies carry flagA=flagB=1 on every peer row and
   NOT on the recipient's own row: verifiable in the server log / a captured
   membership frame (the session_messages.cpp kMemberFlagA/kMemberFlagB
   writes; selfRow = recipient+1 excluded per group_host.cpp).
2. The client's per-peer setup proceeds past the +0xED/+0xEF gate: the
   boot's armed-pair census (transition_readout.py, identity-armed hunt) and
   any NEW client line are the readouts.
3. CONTENT NEGATIVE: flags on peer rows + census byte-identical to p2-205
   => the signal is necessary-but-not-sufficient; the residue is the VMP
   reader side, and no further boot is spent on this arm without a new
   static discovery.

## EFFECT CLAIM (distinct from delivery)

DELIVERY: the membership body with the flag bytes rides the proven
membership keepalive path (row-1 plane). EFFECT (pre-named, not claimed):
the setup completes, the per-connection armed bytes set, the transport job
sweep RUNS armed, and the receive blocks construct. The effect is what this
boot measures - it is NOT assumed.

## ABSENCE NEGATIVE (L13)

Flags sent + zero census delta + zero new client lines: the setup-complete
signal alone does not open the door. The next (and by elimination final)
candidates are the +0xED/+0xEF reader base-fixups (VMP) and the armed-byte
top driver 0x140BFE620 (VMP) - client-internal residues; a milestone
verdict then depends on a NEW static discovery or a different plane, not
another settings flip.

## CHAIN MARKS (L16)

- the flag bytes = the setup-complete signal .... verified-by-reading (20.151/20.152: +0xED/+0xEF, fields 11/12, descriptor-table proof)
- the encoder (peer rows, not self) ........... in-tree (group_host.cpp; selfRow exclusion; the p2(91) lesson)
- the wire writes ............................. in-tree (session_messages.cpp kMemberFlagA/B varints)
- the setting ................................. measured OFF in every boot's launch line (member_setup_flags=0) - this boot flips it
- the readouts ................................. all pre-built and proven (transition_readout on 3 artifacts; identity_dumpcheck; the census diff)

## ADVERSARIAL PASS: self - four ways this boot could mislead me

1. THE P2(91) REGRESSION: flags on the RECIPIENT'S OWN row break the
   citizen join. The encoder excludes selfRow; the CENSUS must check the
   joins still complete (join_result accepted, both clients land). If the
   citizen join breaks, that is the pre-named signature: roll back the
   setting (backup .bak_p2-206_pre_setup) - no rebuild needed.
2. THE FLAGS MAY ALREADY BE ON THE WIRE BY ANOTHER ROW-IDENTITY ERROR: the
   selfRow arithmetic is recipient+1 (host row 0, peers 1..n) - if the
   recipient's row index differs, its own row gets flags (the p2(91) shape).
   The server log's membership body readout discriminates.
3. THE SETUP-COMPLETE GATE READS +0xED/+0xEF WITH A DIFFERENT BASE (the
   ms-start-gate note: "the gate's +0xED/+0xEF readers use a different
   base") - the flags may land on the RECORD while the reader looks at a
   sub-object. That is exactly the necessary-but-not-sufficient branch; the
   census still reads the armed-pair delta.
4. THE ARMED-PAIR HUNT IS HEURISTIC: delta or no delta, the ent instance
   census is the verdict; the heuristic is corroboration.

## PRIOR ART (09-05 FAILURE 5 - q.sh each central term)

- q.sh "setup flags | member_setup": 20.151/20.152 (the flag bytes + fields
  11/12 proof), ms-start-gate claims 6/7 (the same signal named as
  unpublished), 20.328 R1 (the synthesis: "the fork does not publish" - the
  publication exists, the switch was off), p2(91) (the all-rows accident).
- q.sh "sweep armed": lane #4 claims 6d/6f (the per-connection armed bytes,
  never set in any artifact; the top driver VMP) + 20.330-20.332 (the
  constant-state verdict across three artifacts).
- q.sh "receive blocks": 20.302-20.304 + lane #4 (the construct chain).

## DEAD-END AUDIT

- The keying axes (account-slot/digits/session): closed by measurement -
  the svc25-echo keying (v3) is deployed and proven.
- The type-51 apply: verified inert (p2-205 + lane #4) - it is DOWNSTREAM of
  the setup signal this boot arms; it stays on as a witness, not a lever.
- The gate cluster/VMP byte: constant across every artifact WITH the signal
  absent. THIS BOOT is the first with the signal present - the cluster is
  re-read in the dump.

## STATE READERS (a direct reader per asserted state)

- "the flags reached the wire" -> the membership body decode (varint fields
  11/12 = 1 on peer rows, 0 on self) - server log / frame capture.
- "the join still completes" -> ev=activity stage=join_result status=accepted
  (the p2(91) regression signature absent).
- "the client moved" -> ANY new client line past the p2-205 census.
- "the receiver opened" -> ent slot-10 instance census > 0 in the boot-end
  dump (transition_readout.py) - THE verdict.
- "the setup state moved" -> the armed-pair census delta vs p2-205/p2-180.

## WIDE NET (probes at every decision point)

All existing instruments (HOOK COUNT 0): the membership push lines, the
client census diff vs p2-205, the ent/mgr/pool instruments, boot_verdict,
the boot-end dump readouts (transition_readout + identity_dumpcheck).

## FIX SURFACE: server (settings only)

activity_member_setup_flags=false -> true (backup .bak_p2-206_pre_setup).
The encoder was already in the deployed binary 8d881a0b580afe85. NO
SERVER-SIDE GAP: this boot sends the ONE wire item the corpus names as
unpublished; THE CLIENT IS NEVER MODIFIED.

## ABANDON OUTCOME (pre-named)

activity_member_setup_flags=false: the membership bodies return to the
p2-205 byte shape. Also the p2(91)-regression rollback path (identical
flip) if the citizen join breaks. No rebuild either way.

## NEGATIVE TEST (the arm that fails on the bad state, and where it RAN)

1. THE ENCODER (selfRow exclusion): ran in the recorded p2(91) accident
   (all-rows = citizen join breaks; the shipped form excludes selfRow -
   in-tree, group_host.cpp). The boot's joins-not-completing is the live
   negative arm replayed over no archive (first run of the fixed form).
2. THE READOUTS: transition_readout.py ran over THREE artifacts (p2-146 /
   p2-180-transition / p2-205) - the armed-pair baseline (4 sites/dump) and
   the gate cluster are recorded constants this boot must match or deviate
   from; identity_dumpcheck's positive control ran over dump_p2146 (MATCH).
3. THE BOOT'S OWN NEGATIVE: flags on the wire + zero delta = the signal is
   necessary-but-not-sufficient - pre-named, decisive, not a surprise.

## MODEL REVIEW (required: the milestone framing)

This boot is the answer to "what is missing vs the live 2020 game": the
corpus had the name (per-peer activity-setup-complete) for three days, the
code had the encoder, and the config had the switch off - a settings
oversight carried through every modern boot (member_setup_flags=0 in every
launch line; the p2(91) fix never re-armed). THE DEAD ASSUMPTION NAMED:
"the fork does not publish the setup-complete signal" (20.328 R1) - WRONG
as a capability statement; it publishes it whenever the switch is on, and
no boot has ever had it on. If this boot nulls, the milestone's remaining
candidates are the VMP reader residue, and the verdict becomes "the wire
side is exhausted" - to be stated as such, with the evidence. If it moves,
row 8 opens and row 10 (render) becomes the next boot's question with the
proven send (row 9) as the delivery.