"""Generate the RVA atlas + hook (bridge) notes (kinds: rva, hook).

RVA sources (verified):
- community_forks/Wow.md (the activity/launch-pipeline atlas on the pinned exe)
- the 2026-08-19 opcode-hunt lanes + claims' dispatch anchors (bap-dispatch,
  decoder-registry-fill-order, opcode-decoder-map, flag-dictionary, consumer-trace)
Hooks: the fork's client/hooks tree + the gate_trace observer targets (kind: hook
= the BRIDGE where a fork source file hooks an RVA).
"""
from __future__ import annotations
import sys
sys.path.insert(0, __file__ and str(__import__('pathlib').Path(__file__).parent) or ".")
from common import write_note, safe_filename

# ---------------- RVA ATLAS (subsystem -> [(rva, name, note, evidence)]) ----------------
RVAS = {
 "activity-launch": [
  ("0x175E520","activity-script selection pump","branches on descriptor +0x12: 0=local mode 6, nonzero=authored mode 1","community_forks/Wow.md"),
  ("0x1772440","local manager initializer","produces mode 6","community_forks/Wow.md"),
  ("0x1773200","authored manager initializer","produces mode 1","community_forks/Wow.md"),
  ("0x17B8C50","authored receiver creator","","community_forks/Wow.md"),
  ("0x1766A30","component dispatch","","community_forks/Wow.md"),
  ("0x17ADA60","current-selection publisher","hooked by the community build","community_forks/Wow.md"),
  ("0x175B8F0","activity selection-ingest boundary","calls manager authored-input update via vtable +0xB8","community_forks/Wow.md"),
  ("0x1751F50","route-commit function","NEVER force (bad bad bad)","community_forks/Wow.md"),
  ("0x1757600","local route-lane constructor","never fired in the failing path","community_forks/Wow.md"),
  ("0x00BFA5A0","activity-selection launcher","approx beginning","community_forks/Wow.md"),
  ("0x00BFA610","282→266 rewrite boundary","route rewrite return","community_forks/Wow.md"),
 ],
 "dispatch": [
  ("0x14280E3E0","decoder registry (DAT)","308 qwords, 71 populated at static-init by FUN_140E75790","RE_output/claims/decoder-registry-fill-order.md"),
  ("0x140E75790","decoder-registry factory","the ONLY writer; 71-row static table DAT_141fbef60","RE_output/claims/decoder-registry-fill-order.md"),
  ("0x141fbef60","71-entry static decoder table","fills the registry at init","RE_output/claims/decoder-registry-fill-order.md"),
  ("0x140E74F80","type→decoder accessor thunk","*(qword*)(&DAT_14280e3e0 + type*8)","RE_output/claims/opcode-sweep.md"),
  ("0x141FCF6A0","BAP dispatch table base (A)","class handles A[0..7]; records A[8..44]","RE_output/claims/bap-dispatch.md"),
  ("0x141FCF6E0","response/type table (B)","B[t] = A[t+8]","RE_output/claims/bap-dispatch.md"),
  ("0x141C3C600","8 class descriptors","receive-path handler vtables, 18 qwords each","RE_output/claims/bap-dispatch.md"),
  ("0x141C3CB88","37 per-type response records","12 qwords each","RE_output/claims/bap-dispatch.md"),
  ("0x141FBCB60","family-4 push object table (15)","investment push sub-dispatcher","RE_output/claims/bap-dispatch.md"),
  ("0x140DFEC50","svc-11 decoded-body apply","vtable dispatch, NOT an opcode switch (lane B)","RE_output/claims/opcode-decoder-map.md"),
  ("0x140DFDBC0","content-table-patch gate","svc-11 special case","RE_output/claims/bap-dispatch.md"),
  ("0x1417417D0","signon dispatcher","shello rsp 0x1a / ssc rsp 0x131 branches","RE_output/claims/signon-schema.md"),
 ],
 "flags": [
  ("4bL","account flag bank (offset +0x742C)","12,300 bytes @+0x742C = the 12,300-index bank","RE_output/claims/anchor-consumer-trace-completion.md"),
  ("+0xA438","objectiveValues bank","6,200 i32, keyed by manifest objective index","RE_output/claims/lane_dict_record-bridge.md"),
  ("0x904E7433","veteran trio 0/1/2 (hash)","the recap veteran candidates (0x904E7433/30/31)","RE_output/claims/flags-r1-n1-canonical.md"),
 ],
 "store": [
  ("0x140E078F0","rollback decision point","desired-vs-store diff apply; memcmp 12,300-B flag bank","RE_output/claims/anchor-consumer-trace-completion.md"),
  ("0x140E01520","after-image memcmp walker","the store diff walker","RE_output/claims/anchor-consumer-trace-completion.md"),
  ("0x140E02280","commit (decode-only)","L3 verdict re-verified","RE_output/claims/anchor-consumer-trace-completion.md"),
  ("0x140FA8FD0","acquire/record-state writer","item-index + value + caller","RE_output/claims/lane_dict_record-bridge.md"),
 ],
 "census-hooks": [
  ("0x14050F4C0","item-service vtable+0x6F8 resolver","hash→index; 0xFFFF = miss sentinel (resolve stage)","RE_output/claims/lane_census_trace_schema.md"),
  ("0x140548E00","requirement-expression evaluator","type-3 node resolves via the resolver","RE_output/claims/flags-r1-n2-consumers.md"),
  ("0x140540320","expression VM generic driver","","RE_output/claims/lane_census_trace_schema.md"),
  ("0x140A42FD0","stamp-table consume (edge-triggered)","","RE_output/claims/lane_census_trace_schema.md"),
  ("0x140E82AB0","stamp-table gate","called by the consume","RE_output/claims/lane_census_trace_schema.md"),
  ("0x140E80FC0","UI refresh (end of consume chain)","","RE_output/claims/lane_census_trace_schema.md"),
  ("0x140C8F1C0","marker-bit poller primitive","shared by both per-item pollers; indexes marker space","RE_output/claims/lane_census_trace_schema.md"),
  ("0x140E06090","character-object bank test","char_test observer target","RE_output/claims/lane_census_hook_spec.md"),
  ("0x140E06070","account-bank gate test","flag_test observer target (deployed since 10.42)","RE_output/claims/lane_census_trace_schema.md"),
 ],
}
count = 0
for subsystem, entries in RVAS.items():
    for rva, name, note, ev in entries:
        front = {
            "kind": "rva",
            "id": name.lower().replace(" ","-"),
            "name": name,
            "status": "VERIFIED",
            "subsystem": f"rva-{subsystem}",
            "rva": rva,
            "evidence": ev,
            "notes": note,
        }
        body = f"RVA **{rva}** — {name} ({subsystem}).\n\n{note}\n\nBacklink: Canvas B node {subsystem}."
        write_note("02 Registry/rvas", f"rva-{safe_filename(subsystem)}-{safe_filename(name, 40)}", front, body)
        count += 1
print(f"rvas: {count}")

# ---------------- HOOKS (the BRIDGE: fork source file ↔ RVA it detours) ----------------
HOOKS = [
 ("egress","client/hooks/egress/**","force all egress to loopback (DNS/resolver/winsock)","0x140405F80","transport_kind forcing socket over SDR","RE_output/claims/s0-server-inventory.md"),
 ("bootflow","client/hooks/bootflow/**","the game's own boot state machine hooks","—","region/spawn/orbit/join/fade hooks","RE_output/claims/upstream-diff-review.md"),
 ("signon","client/hooks/network/signon/**","signon readiness force-pass","0x141073380 + readiness","SignOn readiness anchor cluster","RE_output/claims/signon-schema.md"),
 ("investment-family5","client/hooks/network/investment/**","family-4/5 rearm chain","0x140E06070","family5_commit/family4 resolved","RE_output/claims/lane_census_hook_spec.md"),
 ("teleport","client/hooks/teleport/**","teleport gates + move","—","ev=teleport","RE_output/claims/upstream-diff-review.md"),
 ("banner","client/hooks/banner/**","banner bind","—","ev=banner","RE_output/claims/upstream-diff-review.md"),
 ("retail-log","client/hooks/retail_log/**","capture the game's own log text","—","ev=retail site text","RE_output/claims/upstream-diff-review.md"),
 ("queuez-family0","client/hooks/queuez/**","family-0 seeding","—","ev=queuez stage=family0","RE_output/claims/upstream-diff-review.md"),
 ("package-trust","client/hooks/package_trust/**","custom-package signature bypass","—","package_validator_iv","RE_output/claims/upstream-diff-review.md"),
 ("external-server","client/hooks/external_server/**","URL rewrite to the standalone listener","—","route_descriptor hook","RE_output/claims/s0-server-inventory.md"),
]
for name, tree, note, rva, sem, ev in HOOKS:
    front = {
        "kind": "hook",
        "id": name,
        "name": f"hook: {name}",
        "status": "VERIFIED",
        "subsystem": "hooks",
        "rva": rva,
        "source_tree": tree,
        "evidence": ev,
        "notes": sem,
    }
    body = f"The **bridge**: fork source tree `{tree}` ↔ client RVA `{rva or '—'}`.\n\n{note} ({sem})\n\nThis is where Canvas A (source) meets Canvas B (binary)."
    write_note("02 Registry/hooks", f"hook-{name}", front, body)
print(f"hooks: {len(HOOKS)}")
