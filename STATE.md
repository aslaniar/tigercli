# STATE - living snapshot

STATUS: live (dieted 2026-08-26 ~21:0x under DOC GOVERNANCE; prior full text =
git history of this file. Superseded headline stacks live ONLY in FINDINGS now;
this file holds the current verdict, standing facts, and next steps - nothing
else fits.)

Updated: 2026-08-26 ~20:40 (BOOT #12 / p2(58): the reason-decision instrument.
The hook ATTACHED, the refusal HAPPENED on both machines, and `reason_name` was
NEVER CALLED - the ABSENCE negative, exactly as pre-named. Mechanism: the
release path logs NO reason ("Sending peer-reservation release for machine"),
the byte goes straight to the wire; only OUR server decodes type-14. THE NAMING
ROUTE TO THE DECISION IS CLOSED (20.85 -> 20.86). New candidate, marked not
claimed: the reason may be a CONSTANT at the fixup call site. Reason 1 is now
reproducible across boots #11/#12, all four releases. FINDINGS 20.86.)

## WHERE WE ARE (one paragraph)
Two clients boot clean against our fork with separated accounts and identities
holding on the wire (20.68-20.74). The peer row DELIVERS and the client ACCEPTS
it (`result=ok accepted=1`, boot #10) - the type-12 wire shape is SETTLED; do
not re-open it. The single open blocker = FINDINGS 20.82 link 4: the client
resolves a peer through a TRACKING TABLE that the type-12 roster does not
populate; posse/fireteam hold `player #0` only on both machines every boot,
`send_rendezvous`=0 always. Every proposed reason-surface has been closed by
execution (see DEAD ENDS); four consecutive entries point at 20.82 link 4.

## DEAD ENDS - DO NOT RESUME (authoritative, rewritten 20:45; condensed to
## one line each; full mechanism quotes in the FINDINGS entries cited)

CLOSED BY EXECUTION (boots #10-#12):
  - TYPE-12 WIRE SHAPE - parses, accepted with two descriptors + peer row. (20.81)
  - DELIVERY-GAP THEORY - both endpoints shipped, release fired anyway naming
    a LOOKUP failure, not an address. (20.74.4 -> refuted by boot #10)
  - GATE-TABLE <-> REASON-ENUM correspondence - unique fireteam ids SPREAD
    reason 1 to both machines instead of clearing it. (20.83 retracted 20.84)
  - NAMING ROUTE (`reason_name`) - never called on release path; hook attached,
    refusal occurred, zero calls. (20.85 -> 20.86)
  - `client.region_private` as cause of privacy-mode - decision path never ran.
    HYGIENE REMAINS OPEN: Mac sets it true, rig lacks the key entirely. (20.82)
  - WS opcodes 701/702 as fireteam lead - already tagged subclass-swap. (20.82)
STANDING:
  - MEMBER ROW SHAPE BY BLIND SWEEP - six shapes swept, none informative; row
    read comes from schema (20.61), which is NOT resuming the sweep. (20.49-51)
  - TRAILING-FIELD VALUES (counts vs masks) - untestable until a peer is actually
    admitted; all prior verdicts measured on self-peers pre-p2(45).

## READ FIRST (any session taking over)
  1. AGENTS.md (router) + the conditional triggers there; boot work ALSO loads
     LESSONS.md PRE-BOOT CHECKLIST and runs gate_boot.py on the brief.
  2. INCIDENT_2026-08-25_false-loops.md - why lessons 13/14/11 exist.
  3. FINDINGS_2026-08-25.md 20.78 -> 20.86 newest-first (today's whole arc);
     walk supersession links via RE_output/INDEX_findings.md or q.sh.
  4. Contract refs: RE_output/claims/s1-accept-contract.md (BAP),
     msg12-schema-decoded.md (type-12), transport-relay-design.md,
     client-steam-vtable-names.md, msg12-parser-read.md.
  5. Captures contain NUL bytes - grep them with `grep -a`.

## OPERATIONAL FACTS
  - Fork repo: RE_build/Sunrise-fork-inventory, branch upstream-gameplay-scoped.
    HISTORY NOTE: TWO COMMITS CLAIM p2(39) (f2d0995 Claude, 9639aa4 opencode).
    Next number continues upward; do not renumber.
  - Build: cd RE_build/Sunrise-fork-inventory/build && make -j8 (src/steam/**
    compiles ONLY into steam_api64.dll).
  - Deploy server: bash RE_scripts/deploy_p2d6_gameplay.sh (gates inside;
    asserts deployed==built).
  - Deploy client DLL: bash RE_scripts/deploy_client_dll.sh <mac|rig> "<literals...>"
    - hash assert + literal grep IN the deployed file; never skip.
  - Logs: server RE_output/s1_accept/Sunrise/logs/sunrise.log; each client
    <game>/Sunrise/logs/sunrise.log. Grep ev=steamnet / ev=activity /
    peers valid / ev=relay stage=register.
  - Rig: ssh master ~/.ssh/cm-rig to rasla@192.168.1.136 (reopen per
    FINDINGS_2026-08-24.md:1476; needs the USER's password). Rig game dir:
    C:\Users\rasla\Downloads\destiny-preservation\dcv build\bin\x64\.
  - Identities: Mac default steamId ...861; rig ...862. Member keys are
    BOOT-SCOPED (measured on keepalives) - reread per boot, do not hardcode.
  - Mac note: use /usr/bin/python3 for DB/sqlite work (miniconda's sqlite3 is
    broken here); rg for corpus greps.

## DEPLOYED RIGHT NOW (asserted by incident.py hashes, 2026-08-26 20:50)
  client DLLs  `9bba721d961c0869` BOTH machines (p2(58): reason_name instrument,
               behavior-neutral)
  server exe   `1991b3da6f518165` (s1_accept)
  build_data   `8d787442018dc4fc` (restamped 20:33)
  settings     rig state.local_account_key:1; membership_sweep_pin:0 (ARMED,
               packed_masks) cap 2
  instruments  stage=peerlink reason reporting (p2(58)); keepalive slot= names;
               svc-24 answered soid; ws503 proposed vs answered; type-13/14 raw;
               stage=body_capture peer-bearing type-12 heads

## NEXT (naming route CLOSED per 20.86 - pick ONE)
  1. HOOK THE TYPE-14 SEND PATH (tests the CONSTANT candidate). Anchors:
     activity_client_send_message referenced 0x1404FB7D4; wrapper 0x1404FB790
     reads [rsi+0x65BC0]/[rcx+0x6C18] then calls [r10+0x28]; 0x6C18 sits in the
     self-key cluster msg12-parser-read.md named. Pattern:
     client/hooks/bootflow/peer_reason.cpp (signature verified UNIQUE offline
     before shipping; report (value, site) deduped as RVA AND static VA ->
     feeds disasm_fn.py directly).
  2. OR go straight at 20.82 link 4 (what populates the peer tracking table) -
     if the reason IS a constant this is the only remaining question anyway.
