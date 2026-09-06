# BOOT_BRIEF_p2-192 — THE CHANNEL FIX: THE RELAYED JOIN ON THE ENGINE ASSOCIATION
STATUS: live (2026-09-06).
FRONT: session-lookup-identity

ONE CONTRACT: the relayed join is delivered on the ENGINE association
(relay_join_engine_channel=true) so the join gate's container-scoped lookup
walks the client's RICH container instead of the dtls association's empty
one. p2-190f's complete walk readout proved the mechanism: the join gate
walks [ctx+0x28] of the packet's OWN connection (disasm-verified); the
dtls-delivered join walked a 1-slot container (blob=0) and refused every
value arm. The rich container demonstrably matches the verbatim key
(key=blob match=1 measured on the gate chain at t=109527, p2-190f boot).

## MODEL REVIEW (p2-194b update - the front carries 2 third-branches: p2-194a, p2-194b)
BANKED (p2-187 + carried all night): the idB-via-membership assumption.
ADDED THIS BOOT (the two third-branches' indictment): the first channel-boot
attempt shipped the walk_leave leave-probe as a SECOND ROW ON THE SAME RVA
(dual detours = an unsupported install; the rig froze in the loading loop) and
its readout was swallowed by boot-cumulative budgets; the redeploy moved the
state reads INTO the walker's hot path (the mac's landing transition stalled).
BOTH were instrument defects, not hypothesis failures - the channel fix's wire
proof (channel=engine sent) stands, and no boot has yet delivered a COMPLETE
readout of the relayed join's walk (d5ed2ae3f12e42fb is the first build whose
hot-path cost equals the proven-landing build's while carrying the
walk-return + state readouts). THE DEAD ASSUMPTION THIS BOOT RETIRES: that
"the walk emitted everything" after the reset - it did not; the budget and
the hot-path cost each hid parts of it. The next boot is the first with a
complete readout by construction.

Carried: the idB assumption (p2-187), the caller-union reading (fixed),
the alignment guard + the hash collision (fixed, THE BLIND-GUARD postmortem
+ ADDENDUM), the stamp-timing hypothesis (RETRACTED - p2-190e: spawned mac,
unchanged blob set). THIS BOOT's new assumption being tested: that the
dtls-vs-engine association split IS the container boundary. If the fix
fails, the container-id log (new instrument) attributes the split directly
and the front moves to the association-ownership decode, not another guess.

## PRIOR ART (required field)
q.sh terms: 0x1416E0460 / ctx 0x28 / 14177A0B0 / relay_join_engine_channel /
association::send_payload / walk_map container. Verdicts cited as closed
premises: all four value arms refused (forkSession x4 boots, machine id
p2-188b, joinId p2-190b/c) - against the EMPTY dtls container; the "stamp
timing" hypothesis retracted; the receive pump is VMP (static ends at
0x140B5xxxx); the walker has ~35 callers (every connection-layer type
handler walks its own ctx's container).

## DEAD-END AUDIT (cited as premises, not roads)
- the value arms: CLOSED against the empty container (the refusals stand;
  the value re-test becomes meaningful only on the primed container).
- the "stamp timing" theory: retracted this session (spawned mac, unchanged
  blob set, refused) - the container identity, not a timing, explains the
  boot-to-boot variance.
- the session-apply / copier-walk blob-writer hunt: parked - the container
  question supersedes it (the blob stamping was observed INSIDE the rich
  container which we now target directly).
- the connect-family re-decode: closed (pure transport, 20.320); its
  handlers DO consult these containers (0x1417C3920 calls the helper) -
  that is banked, not re-opened.

## PURPOSE (ONE CONTRACT)
Deliver the relayed join on the association whose client-side container is
primed, and observe the walk COMPLETELY (the p2-190f instruments): pass =
join_processor enters (row 5 falls); refuse = the walk names the container
and slot state (the association split attributed).

## THE CHANGE (amended after the first channel-boot attempt)
- server acbb62af4a3ca133: relayJoinEngineChannel (default false =
  byte-identical; TRUE this boot) - the relay's sends go
  association-first/dtls-fallback; the join_relay line now carries
  channel=engine. Settings backup .bak_p2-192_dtls.
- client BOTH 572ca7c2fc02ada3 (redeployed after the first channel-boot
  attempt exposed the gap): emit_walkmap container-id log + first-reject
  markers (as planned), PLUS the p2-192 fix: the walk-coupled reset now
  ALSO clears the per-caller budget counters - the first attempt proved
  the landing's walks burn the gate-chain callers' 32 triples minutes
  before the relay arrives (0x17944FA budget_exhausted at t=151794, the
  relayed join at t=284109: the p2-154 class again - a budget measures
  the beginning of a boot; per-event budgets measure the event).
- Hook count UNCHANGED 64/64 (verify_hook_rvas PASS 112 RVAs 0 bad).
## READOUT TRIGGER (required field)
- stage=join_relay ... channel=engine: PRIOR-LOG CITE (join_relay lines emit
  every boot; the channel= field is new this build).
- result=container / result=reject lines: NEVER-COMPLETE-BEFORE (the reject
  paths existed silently; their first emission names the swallow).
- the refusal line / its absence: prior-log cite (p2-190d/e/f).
- join_processor enter: NEVER-OBSERVED for a relayed join - the event.
- the complete sesscmp set between pktdump and the verdict: prior-log cite
  p2-190f (the reset + hash fix proved the walk emits completely).

## PRE-NAMED OUTCOMES
  (a) refusal ABSENT + join_processor -> row 5 FALLS; rows 6-8 fire or name
      the next blocker (the chart moves).
  (b) refusal PRESENT + the walk_map container= line DIFFERS from the
      landing walk's container -> the engine association's container is ALSO
      not the rich one -> the container ownership question moves to which
      association the landing machinery runs on (the helper-entry hook is
      the next instrument - ONE target).
  (c) refusal PRESENT + the container MATCHES the landing walk's container
      + a complete miss-set -> the association fix delivered to the right
      connection but the container's blobs at relay time don't hold the key:
      the blob-state question is now scoped to ONE container (the fork must
      publish the missing form).
  (d) result=reject reason=slots/container lines on the relayed join's walk
      -> the container is UNREADABLE (the p2-190f silent swallow, now loud):
      the ctx object differs structurally - the association split is proven
      and the decode moves to the ctx+0x28 assignment.

## ABANDON OUTCOME (empty-mask #7)
If (b) AND (d) both fire (both containers wrong or unreadable), the
association-split fix is insufficient: the road narrows to decoding WHERE
[ctx+0x28] is assigned per connection (the ctx constructor) and which
connection object the client binds its landing sessions to. No further
channel flips without that decode.

## EFFECT CLAIM (empty-mask #5)
The relayed join walks a PRIMED container for the first time - the
difference between "the gate evaluates the peer's join against the client's
actual session state" and "against an empty stub". Row 5 falls on a pass.

## STATE READERS (empty-mask #1)
- the container identity: walk_map result=container lines (DIRECT, new).
- the walked slot state: the complete sesscmp set between pktdump and the
  verdict (DIRECT - the reset guarantees completeness).
- the game's verdict: the refusal line or its absence.
- the channel: join_relay ... channel=engine (DIRECT).

## FIX SURFACE: server
The channel selection IS the server-side fix (no wire content change - the
join container bytes are identical; only the carrier association changes).
SERVER-SIDE GAP: none - the client needs nothing.

## WIDE NET
joincapture / join_relay (+ channel=) / join_type0a + pktdump / walk_map
(+ result=container / result=reject) / sesscmp (complete set) /
join_processor / join_reserve / admit / resv / sess_state /
add_candidates / bootflow / the refusal line / stage=identity.

## INPUT GATE (hard rule)
Do not read walk lines before the server's join_relay result=sent
channel=engine.

## OBSERVER BUDGET / CALL FREQUENCY
- walk_map: the change-gate stays; NEW: one container= line per new
  container, one result=reject line per reject class per container. The
  relayed join's walk emits its map (the reset is NOT coupled to walk_map -
  the sesscmp reset stays on the join packet's hook).
- sesscmp: unchanged (32/caller; reset per join packet).
- every other target: unchanged.

## HOOK COUNT: 64 (unchanged; hook_targets declares=64 initializers=64)
## INSTRUMENT SOURCES: RE_build/Sunrise-fork-inventory/Sunrise/src/client/hooks/milestone_trace/milestone_trace_observer.cpp
## INSTRUMENT LIVENESS
- the literals budget_exhausted / stage=walk_map verified IN the deployed
  binaries (88f5482af8228e89, BOTH machines; preflight PASS 13/0/0).
- NEW liveness mark: "result=container" appearing = the container-id log is
  live; the landing walk's container= value vs the relayed join's = the
  attribution readout.
- "result=reject" ABSENT = no reject path fired (expected when the
  container is readable).

## FALSIFIABLE CLAIM
With the relay on the engine channel and both links up: the relayed join's
walk EITHER emits a walk_map map line (a readable container, complete
sesscmp set) or a result=reject line naming why it cannot. REFUTED if the
pktdump fires and NEITHER a walk_map map/reject/container line NOR a
sesscmp line appears in the window (the walker did not run for the relayed
join -> the gate's own path gets re-derived).

## ABSENCE NEGATIVES (both kinds)
- zero walk_map container= lines across the whole boot: the container-id
  log is not firing (the container never changes or the hook misses) -
  the attribution readout is void until fixed.
- zero refusal AND zero join_processor with the relay sent: the join
  arrived and neither branch logged - framing/transport, p2-183(b) class.

## GRAPHICS DELTA (U12)
None. Both clients spawned via the subclass swap last boot (p2-190f) -
repeat the swap; a black-screen mac does not void the readout (the
instruments log regardless).

## SETUP
- server acbb62af4a3ca133 RUNNING (relaunched post-deploy WITH the setting;
  initialize ok, ports bound, claims=0). Note: reset_lobby_claims.sh's
  pre-registered defect fired again (executed as python) - the manual
  kill+relaunch path was used (ENVIRONMENTS canonical).
- clients BOTH 88f5482af8228e89 (mac bak_p2d7_20260906_1406xx; rig
  bak_p2d7_20260906_140703); preflight PASS 13/0/0.
- rollback: settings .bak_p2-192_dtls; client .bak_p2d7_20260906_*; server
  .bak_p2d6_<stamp from the 14:0x deploy>.
- ARming order: mac alone first -> link bound -> rig second -> the relay
  fires (channel=engine).

## CHAIN MARKS (L16)
- the gate walks [ctx+0x28] of the packet's own connection:
  VERIFIED-BY-READING (the join gate's disasm, p2-190f).
- the dtls-delivered relayed join walks a 1-slot container:
  VERIFIED-BY-EXECUTION (p2-190f's complete readout).
- the rich container matches the verbatim key: VERIFIED-BY-EXECUTION
  (key=blob match=1 on the gate chain, p2-190f boot).
- the rich container's owning association: INFERRED (the fork's
  association split + the compare-count difference) - THIS BOOT TESTS IT.
- this boot proves: the relayed join walks the primed container. NOT YET.

## ADVERSARIAL PASS: ses_f882ff186ffeIGc0ofsy65C5k1
The server change is a channel-order swap on the relay's send only (the
payload bytes identical - fixture-proven rewrite machinery untouched); the
setting is default-off (byte-identical off path). The client change adds
LOG-ONLY paths (first-reject + container-id) that cannot alter game state;
its negative test: the reject classes correspond one-to-one to the
early-returns the old code silently took (the p2-190f silent swallow) - the
new build MUST emit result=container at the first walker entry (pre-named;
its absence = the instrument is broken, outcome (d)-adjacent). The
replay-honest limit: previously-silent paths cannot be replayed - stated,
not hidden.

## DO NOT
- iterate the retarget VALUE this boot (the verbatim key is the measured
  match; the container was the problem).
- spend a boot on a second channel variant (engine-vs-dtls is binary; the
  readout decides).
- read walk lines before join_relay result=sent channel=engine.
- sleep in shell chains (background + notify).
