# PLAN: P2 Tower blocker - svc-25 identity instrument + extended crypto fingerprints
Written: 2026-08-23 (plan mode, orientation session). Repo: sunrise-fork.
Build tree: RE_build/Sunrise-fork-inventory (branch `integration`, tip c517a66).

## 0. ORIENTATION RESULT - THE H1/H2 PICTURE CHANGED (all verified on disk this session)

Read STATE.md + FINDINGS 20.12 -> 20.11 -> 20.11a first, then verified against
disk and code. Three findings REFRAME the blocker before any boot:

**F1 - H2-as-written is refuted by code read.** plaintext.cpp has NO
first-connection gate: `plaintext::consume()` runs the identical svc-25 path
(including `match_session_token`, lines 205-226) for EVERY connection.
open_session (bap_route.cpp:88-99) just zeroes the Session. So conn=2 DOES
consult accountKey.

**F2 - "The identity stamp never took" is TRUE but BENIGN.** The rig did not
fail identity - it legitimately IS slot 0:
- server_http.cpp:31 serves `state::sign_on()` whose default arg is
  kLegacyAccount (runtime.h:42) -> the SignOn response ALWAYS carries slot 0's
  sessionToken. The rig answers SignOn IN-PROCESS from its own settings, so the
  rig received-and-echoed ITS OWN slot-0 token.
- Rig settings (dcv build\bin\x64\Sunrise\settings.json, verified over ssh):
  accounts[0].bootstrap_token = 84cc3be9...5b88 (=A), accounts[1] =
  c33faf80...1f86 (=B). Mac server settings: SAME order [A, B].
- Therefore echo == HMAC(A)-derived token == server slot 0 -> SILENT match
  (a match logs nothing; only mismatch logs). Explains: /ladder root=slot-0,
  rig log `ev=account stage=identity key=0`, family-4 served fine, orbit OK,
  and NO `unprovisioned_token_accepted` warn anywhere in the P2-B1 server log
  (grep verified: only persistence load_account_id + https handshake fails).
- M1 cross-check (20260823_m1_remote_rig events): pre-P2 server logged
  `token_mismatch_accepted` on svc=25 and STILL loaded the Tower - global crypto
  made identity irrelevant then.

**F3 - The real delta: M1 hosted locally, P2-B1 went guest.**
- m1_success capture: server log has ONE accept (conn=1 only); rig log t=45516
  "As HOST of [posse:471FF778:9E930AEC], all our peers are done setting up" -
  NO second BAP connection ever existed in M1.
- obs_validation capture (Mac solo, pre-P2 server): DID use conn=2 successfully
  - same flow byte-for-byte at the log level: hello 140/48 bytes, b35=02,
    svc=6 selection 7747 bytes, activity push type=1 soid=0x9EAA300100200001
    len=234, keepalive 234 - ALL VERIFIED FINE by the Mac client.
- p2b1: IDENTICAL flow, but the rig dies at "Received an encrypted message with
  an invalid signature" while waiting for the activity-host startup response -
  AFTER its own client->server frames verified fine server-side (the 7747-byte
  svc=6 opened cleanly). Asymmetric failure: client->server OK, server->client
  rejected => AEAD tag mismatch => the CLIENT verified conn=2 server frames
  against different key/nonce material than we sealed with. Frame sizes
  identical pre/post P2 => content likely unchanged => suspect the PAIRING,
  not the payload.
- Note: post-a000d41 seal/open code is behavior-identical for a slot-0 peer
  (`state::bap(session.accountKey)` == old `state::bap()` when key=0), so the
  defect is probably NOT the a000d41 accessor change itself. Conn=2 arming from
  the SAME slot-0 BapState as conn=1 (same key + same base nonce on both
  links) is structurally unchanged since pre-P2 too - but the CLIENT-side
  anti-replay/counter story under two links sharing one (key, nonce-base) is
  now the top suspect, alongside any P2-era change to what conn=1 already
  consumed before conn=2 opens.

REFRAMED BLOCKER QUESTION: why does the rig reject server->client conn=2
sealed frames that the Mac client accepted pre-P2? The identity layer must
first be PROVEN clean by the instrument (one boot), and the same boot's crypto
fingerprints should discriminate the pairing hypotheses.

## 1. PHASE 1 - THE INSTRUMENT (server-side only; no client rebuild)

### 1a. Identity line (the brief's ask) - plaintext.cpp, after line ~217

Right after `match_session_token` returns, before stamping, emit ONE info line:

    ev=bap svc=25 stage=identity conn=%u matched=%s served=%u
    echo=%08X%08X slot0=%08X%08X slot1=%08X%08X proto=%02X len=%zu

- matched: `slot0` / `slot1` / `none` (names WHICH branch produced served).
- echo prefix: first 8 bytes of the echoed token (frame.body.data()+kTokenOffset).
- slotN prefixes: `state::sign_on(i).sessionToken` first 8 bytes,
  i < `state::account_count()` (both exported in runtime.h; loop dynamically,
  print up to 2 slots - extend format if ever >2).
- proto/len: from frame.body (ties the identity line to the shape line).
On match==none ONLY: append the full 36-byte body hex (bounded dump, once per
hello) so we can locate where the FAH variant actually puts the token.
SECRETS NOTE (owner call, flagged): the file's authored discipline says tokens
never reach the log; the brief explicitly overrides for this private research
rig. Prefixes (8 bytes) + one bounded mismatch dump is the proposed compromise;
full values only if the prefixes prove ambiguous.

### 1b. Crypto fingerprints (extension, small, same boot) - encrypted_runtime.cpp

At open_frame success AND at each sealed send in the encrypted path, add a
debug-level line:

    ev=bap stage=crypt dir=open|seal conn=%u keyfp=%08X nonce=%02X%02X%02X
    ctr=%u bytes=%zu route=%u

- keyfp: first 4 bytes of bap(session.accountKey).sessionKey.
- nonce: first 3 bytes of the CURRENT direction nonce at this frame.
- ctr: how many frames this direction has advanced (add a tiny counter to
  Session, or derive from nonce tail).
Purpose: one boot shows whether conn=2 reuses conn=1's exact (key, base-nonce)
and exactly how many frames flowed before the client rejected. Keep at debug
level so normal boots stay quiet-ish; enable via existing client=info server
log level (server lines already log debug into the capture).

NO-NEW-STATE RULE: everything above uses existing exports except the optional
per-direction counter; if adding counters to Session feels invasive, log the
raw nonce bytes instead (the counter IS the nonce tail).

### 1c. Discipline (binding)

- ASCII-only comments (no em-dashes).
- `python -m py_compile` N/A (C++); instead: build MUST pass clean before
  deploy; treat warnings in touched files as failures.
- Smoke rule: the rebuilt exe must boot headless and serve /ladder before any
  game launch (existing launch-server-macos.sh flow).

## 2. PHASE 2 - DEPLOY + ONE BOOT

1. Kill server pid (current pid 91442 - re-check, do not trust stale pid).
2. Rebuild sunrise-server.exe (llvm-mingw via mac-port/launch-server-macos.sh,
   -j 8). Record new exe hash.
3. Restamp build_data identity offsets 12/16 (scripts/restamp_build_data.py);
   recompute eqHash only if equipped items changed - they did NOT, so expect
   eqHash to stay 0xAC65559674A52DD8 (verify, do not assume).
4. Restart server; verify listeners 30975/8443/8099 TCP + 3074/3075 UDP ACCEPT;
   run check_invariants.py BEFORE the boot (expect 17/18, DETAIL_COVERAGE red
   = expected/inert).
5. RIG BOOT BRIEF (binding):
   - PURPOSE: prove the svc-25 identity outcome per connection and capture
     per-direction crypto parameters on conn=1 vs conn=2.
   - FALSIFIABLE CLAIM: both connections will show matched=slot0 served=0 with
     echo==slot0 prefix (F2 prediction). If conn=1 shows matched=none or
     served!=0, F2 is WRONG and the token-derivation lane reopens.
   - WHAT IT DOES NOT TEST: gameplay/DTLS plane wiring (still absent,
     20.11a), WARP fix (no Mac boot), entity front, Mac client DLL 83345d39.
   - GRAPHICS DELTA: ZERO. Server-only rebuild; rig client binary untouched;
     equipped loadout unchanged -> zero new shader compilations at pick.
6. Boot the rig via ssh master socket (write .ps1 to disk, scp, -File, verify
   on disk - NEVER inline multi-line PowerShell). Drive to orbit -> attempt
   Tower once. Capture server_log + rig_client_log into
   RE_output/boots/<ts>_p2c1_identity_crypt/.
7. Run check_invariants.py AFTER the boot.

## 3. DECISION TABLE (pre-named next move per outcome)

- D1 (PREDICTED): conn=1 AND conn=2 both matched=slot0 served=0, and the rig
  still dies on conn=2 signature:
  -> Identity fully exonerated (record the exoneration WITH its direction:
     tested as "echo vs derived slots", valid in that direction only).
  -> Read crypt lines: if conn=2 seal/open used the SAME keyfp+base nonce as
     conn=1 (expected - same slot-0 BapState), prime suspect = cross-link
     (key, nonce) reuse tripping the retail client's replay/counter state.
     Next surgical candidate (ONE variable): give each BAP connection its own
     nonce base at arm time while keeping the account key material - BUT only
     after checking what the M1/obs_validation boots' envelopes delivered
     (pre-P2 ALSO reused one global BapState across conns and obs_validation's
     Mac client accepted it; so if D1 lands here, compare what DIFFERS: remote
     transport, P2 commits, two-account settings). Do NOT guess-fix; take the
     fingerprint diff to the next instrument step.
- D2: conn=1 matched=none (or served!=0): F2 wrong; token derivation/staging
  lane reopens. Compare echo prefix vs slot prefixes: echo==neither ->
  rig DLL/settings drift (verify rig clone freshness at
  destiny-preservation\RE_build\Sunrise-fork); echo==slot1 -> staging/order
  issue somewhere else entirely - stop and re-orient.
- D3: conn=1 matched=slot0, conn=2 matched=none: proto-02 FAH framing reads
  non-token bytes at the fixed offset; the body dump locates the real offset;
  fix = FAH-aware token extraction (separate surgical edit, separate boot).
- D4: anything showing served=1 anywhere: contradicts all captured evidence;
  full stop, re-orient before touching anything.
- IF THE TOWER LOADS THIS BOOT (possible - e.g. if the failure was
  timing-dependent): still harvest the crypt lines, then decide whether the
  SignOn-always-slot-0 design gap (below) becomes the new P2 headline.

## 4. FOLLOW-UP ITEMS SURFACED BY ORIENTATION (record in FINDINGS at landing)

- **P2 design gap (real, independent of the blocker)**: with SignOn answering
  `state::sign_on()` (default slot 0), NO machine can ever sign on as any slot
  other than 0 of its own settings. Two machines with identical [A,B]
  settings both run as legacy/slot-0. Guest accounts (the actual P2 goal) need
  an account-selection mechanism (SignOn request names the account, or
  per-machine settings order, or per-machine single-slot settings). OWNER CALL
  required; do not implement silently.
- 20.12's "roster result=no_epoch soid=0x...00200001" oddity: the SAME soid +
  warn appears in obs_validation (working, pre-P2) - it is NOT a P2 regression;
  classify as benign/pre-existing.
- M1-vs-P2-B1 host/guest flip (F3): worth one paragraph in FINDINGS; if D1
  confirms crypto pairing as the killer, the flip is explained as downstream
  (dead host startup response => guest retry path), else it reopens.

## 4b. PHASE 0 - RECORD HYGIENE (do FIRST, before any rebuild; ~15 min)

Catch-up reading added these specifics (all verified on disk 2026-08-23 ~21:1x):

- STATE headline stack block is stale (08-22 era: exe 04a3a1ca, client
  67f3d053, cache ts 0x6A8A90A5). Refresh to current: server exe
  434d4be2ee1f9c08 (from p2b1_boot_brief_claude.md), mac client 83345d39,
  cache ver24 ts 0x6A8BB0D8 size 0x02CFA000 eqHash 0xAC65559674A52DD8.
- Four artifacts carry FUTURE stamps vs their own mtimes: p2b1_boot_brief
  ("~21:0x", mtime 20:49), STATE ("~21:0x", mtime 20:52), FINDINGS 20.11a
  ("~21:1x", mtime <= 20:51). Annotate or correct; the newest-timestamp-wins
  rule depends on honest clocks.
- Landing-review status is resolved but scattered: D1 corrected (FINDINGS
  182-192 tree map), D2 fixed (interpreter pin + exit-2), A1 fixed
  (c517a66 launcher shim resolution). STILL OPEN: D3 (ensure_token
  external.configGuid branch - own boot), A2 (bottle wipe cause unknown;
  adopt the loud launcher-side check recommendation).
- FINDINGS 20.13 (the reconciliation entry from section 4) should also note:
  the P2-B1 brief's Lose branch pre-classification ("pre-P2 DLL falls back")
  was wrong - the rig DLL IS post-P2; the stamp matched slot 0 legitimately.
  Record so the next brief calibrates its negatives against the SignOn-serves-
  slot-0 fact.
- Entity front record fix (cheap, separate lane): vendor-first-s2.md section
  1.2 still says 443 bits; deployed encoder emits 464 (+21 refinement, see
  peer-visibility-codec-findings.md F1). One-table correction.
- PROVISIONING FEEDING PROOF (for the eventual SignOn account-selection fix):
  with state.accounts[] present, slots derive ONLY from
  accounts[i].bootstrap_token (initialize_provisioned, state_runtime.cpp:347);
  legacy server.bootstrap_token feeds only the single-account initialize()
  path (state_runtime.cpp:330). The rig carries token B in BOTH places plus
  as its SignOn identity intent - all inert while SignOn serves slot 0.

## 5. NOT DOING (guardrails)

- No client rebuild, no rig DLL copy (Mac mingw DLL must NOT go to the rig).
- No fix rides the instrument boot (rule: instrument BEFORE intervention).
- Do not chase DETAIL_COVERAGE red (proven inert, FINDINGS 20.11).
- Do not touch: gameplay plane wiring, WARP, entity front, upstream reconcile.
- Live stack left alone except the deliberate server restart in Phase 2.
