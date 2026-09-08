# HANDOFF 2026-09-08 — THE GATE MACHINE IS MAPPED; THE WALL IS THE SESSION'S LIVE STATE

STATUS: live (2026-09-08, end of the two-day opencode arc). Written for the
next session taking over. Read STATE.md's header first (20.345-20.348
headlines), then this. Companions: FINDINGS 20.339-20.348 (full text, dual
format); the five lane reports RE_output/content/lane_[abcde]_report.md;
the live chart FRONT_multiplayer-chain.md.

## THE ONE-PARAGRAPH STATE OF THE WORLD

The client's gate machine — the activity/replication manager that the
peer-render front hinges on — is now FULLY MAPPED and readable. The
"VMP wall" retired (everything around the protection is plain code; the
protection is pointer-scrambling, not unreadable logic). The manager
singleton = 0x21DDC09C900 (found by the unique 32-slot init signature,
confirmed by a plaintext pointer cache at 0x6F9DEF5550 near the TEB). It
RUNS: state 4 (running), armed lamp on, +0x8=2 (running-UNESTABLISHED),
its pending-message queue EMPTY (no producer in the readable image — the
queue is a named schema field "i107", producer-silent BY DESIGN until
attached). The activation job (f7da0) is vmethod +0x88 of class vftable
0x141C14F70, whose lazy instance is built by a phase-init sequencer that
NEVER STARTED this boot (tail flag 0x141D4CD34=0xC2; also: 20.340's
target address was a transcription error — the true global is the
record's 0x14280E210, POPULATED). The attachment (mgr+0x8=1) driver is
the WORLD-CHANGE EXECUTOR gated on [r14+0x1AEF8] in 6..9 — the
managed-session LIVE window. In every archived boot the world change
happens but the session evaluated sits at 4 — so the executor skips.

## THE CORRECTED SYNTHESIS (the user's catch — do not regress)

"Runs in missions" is RETIRED (20.348). The tower works for everyone in
retail; the gate is the SESSION STATE, not the destination. The trigger
is: world-change × managed-session-LIVE (6..9). In retail Bungie's
server always holds that session live — including the tower. In our
fork, the session sits at 4. THE FORK-SIDE LEVER CANDIDATE: the
session-state climb 4→6 — the project's OLD front (20.320, the client
cycles stages 0..5), parked, now reopened from the client's other side.

## WHAT THE TWO SUBAGENT LANES LEFT NAMED (their reports are banked)

- Lane A (RE_output/content/lane_a_report.md): the +0x206b8 structure is
  a PENDING-MESSAGE QUEUE (participant-shaped, decoded by the type-20
  apply's initializer), NOT a free list; no producer in the image; +0x8
  semantics 0=down/1=established/2=running-unestablished; the
  entity-index pool (System A, +0xC118) is a DIFFERENT pool — the C2
  patch stands independently. idx_alloc/ent_make are OUR detours in these
  dumps: static reads start at +5.
- Lane B (lane_b_report.md): f7da0 = vft+0x88 of 0x141C14F70; the lazy
  construction; the job body HAS five static call sites (correction);
  the registry out-handles are ZERO (registration incomplete); mgr+0xC
  carries the machine identity.
- Lane C (lane_c_report.md): 0x14280E210 (NOT 0x142B0E210 — transcription
  error) populated; the phase-init sequencer never started; client-boot
  infra verdict; cheap boot instruments (hook 0xB37BF0, flag byte
  0x141D4CD34, watch array).
- Lane D (lane_d_report.md): no producer in any encoding/section; the
  queue is a named schema field ("i107") in runtime reflection tables;
  the manager family named (g_network_activity_status_line / "msgq %s:
  in…out…"). NOTE: the parent's string spot-check FAILED in .data —
  finish the verification (.rdata scan) before citing the strings.
- Lane E (lane_e_report.md): the attachment writers (mode-1 0x140B540C1;
  mode-2/3 FUN_0x140B534A0), the mode-1 driver = the world-change
  executor gated on 6..9, the cascade via the consumer's fall-through
  0x1416FCF95, its pump's gates OPEN; +8 has exactly four writers.

## WHAT'S LEFT (the three client-internal conditions + the fork items)

1. WHOSE SESSION does the world-change executor evaluate (r14 binding)?
   Static read of 0x140C090B0's call path — the next action.
2. The activation object's construction: does the phase-init sequencer
   ever start, and is it even required (vmethod +0x88 needs only an
   instance of the vft to be dispatched on — construct-and-dispatch may
   bypass the phase system entirely)?
3. The pending queue's producer: not in any encoding — produced only
   when established, or schema-applied, or virtualized. Feeding it
   attaches to finding #1's answer.
4. FORK-SIDE (independent): the session-state climb 4→6 (the parked
   front — now the lever candidate); Stage B churn (instrument the
   teardown: apply_p2211.py's server arm, written unrun in the staging
   worktree .claude/worktrees/fork-p2211); C2 deployment (patch at repo
   root, built, default-OFF settings).

## THE NEXT BOOT (p2-211, staged — the brief BOOT_BRIEF_p2-211.md needs its
readout refreshed to SIX values before gate_boot):
recv_root counter / af0 / f7da0 markers (obj+0x59820, b05/b07/b09) /
fragment-list built / vft 0x141C14F70 instance check / phase flag
0x141D4CD34. PLUS: executor-invoked during the tower landing (which
session evaluated). FAILURE-POINT CLIPS are pre-named in the session
transcript (FP1-FP9: archive-completeness gate; every negative routes to
its next action; the manager re-census via the 32-slot signature is the
identity clip).

## DO NOT
- Do not scan Game/destiny2.exe for code work (encrypted; use the carved
  image RE_output/destiny2_runtime_p2-206.exe).
- Do not cite 20.339's "af0 has no writer" / "the consumer has no
  references" or 20.342's "free list" — all corrected in 20.340/20.343/
  20.344.
- Do not trust ptr_decrypt_emu.py's prior results (Tier-1: file-layout
  image mapped at the base — results void; fix = map sections at VAs).
- Do not spend a boot without the archive-completeness check (20.336).
- The client is never modified — all fork-side.

## READING ORDER
STATE.md header → this handoff → FINDINGS 20.342-20.348 → the lane
reports → the staging note RE_output/content/SETUP_P2-211_FRONT.md.
