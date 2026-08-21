"""Build the two Canvas files (A: the conversation, B: the target) inside the
sunrise-vault, as Obsidian Canvas JSON. File nodes link to generated registry
notes by their real on-disk names (looked up, not guessed).

Canvas JSON shape (Obsidian core plugin):
  nodes: [{id,type:x|file|text, x,y,width,height, file|text, label}]
  edges: [{id, fromNode, fromSide, toNode, toSide, label}]
"""
from __future__ import annotations
import json, sys
from pathlib import Path

VAULT = Path(r"C:\Users\rasla\Documents\sunrise-vault")

def find_note(folder, stem_fragment: str) -> str | None:
    """Return the vault-relative .md path whose filename starts with the fragment."""
    d = VAULT / folder
    if not d.exists():
        return None
    for p in sorted(d.glob("*.md")):
        if p.name.startswith(stem_fragment):
            return f"{folder}/{p.name}"
    return None

def build_canvas(name: str, nodes, edges) -> None:
    canvas = {"nodes": nodes, "edges": edges}
    (VAULT / "01 Canvases").mkdir(parents=True, exist_ok=True)
    (VAULT / "01 Canvases" / name).write_text(
        json.dumps(canvas, indent=1), encoding="utf-8")
    print(f"wrote 01 Canvases/{name}: {len(nodes)} nodes, {len(edges)} edges")

nodes = []
edges = []
_node_id = [0]
def N(node_type, text_or_file, x, y, w=260, h=90, label=None):
    _node_id[0] += 1
    n = {"id": f"n{_node_id[0]}", "type": node_type, "x": x, "y": y, "width": w, "height": h}
    if node_type == "file":
        n["file"] = text_or_file
    elif node_type == "text":
        n["text"] = text_or_file
    if label:
        n["label"] = label
    nodes.append(n)
    return n["id"]

def E(frm, to, label="", side_from="right", side_to="left"):
    _node_id[0] += 1
    edges.append({"id": f"e{_node_id[0]}", "fromNode": frm, "fromSide": side_from,
                  "toNode": to, "toSide": side_to, "label": label})

# ------------------- CANVAS A: THE CONVERSATION -------------------
# left-to-right: client -> hooks -> wire -> server -> persistence
cA_client = N("text", "destiny2.exe\n(the CLIENENT — Arrivals build, VMProtect)", 0, 120, 250, 90, "client")
cA_hooks = N("file", find_note("02 Registry/hooks", "hook-egress") or "02 Registry/hooks/hook-egress.md", 300, 100, 260, 90, "steam_api64.dll hooks")
cA_wire = N("file", find_note("02 Registry/bap-types", "bap-type-10") or "02 Registry/bap-types/bap-type-10.md", 620, 120, 260, 90, "the wire: BAP")
cA_ws = N("file", find_note("02 Registry/opcodes", "opcode-403") or "02 Registry/opcodes/opcode-403.md", 940, 40, 260, 80, "web-service svc 10/11")
cA_q = N("file", find_note("02 Registry/bap-types", "bap-type-123") or "02 Registry/bap-types/bap-type-123.md", 940, 160, 260, 80, "queuez pushes")
cA_server = N("text", "sunrise-server.exe\n(standalone server: bap/http/transport/runtime)", 1250, 100, 260, 90, "server")
cA_persist = N("text", "persistence\nstate.db · cache · settings\n(stamp-on-persist)", 1250, 240, 260, 90, "persistence")

E(cA_client, cA_hooks, "egress forced → loopback")     # right->left
E(cA_hooks, cA_wire, "SignOn POST + BAP frames")        # right->left
E(cA_wire, cA_ws, "svc 10/11 opcode frames")
E(cA_wire, cA_q, "svc 123 queuezUpdate")
E(cA_ws, cA_server, "svc-11 responses / pushes")
E(cA_q, cA_server, "family 0/3/4/5 pushes")
E(cA_server, cA_persist, "read/write · cache re-stamp", "right", "left")

build_canvas("A Conversation.canvas", nodes, edges)

# ------------------- CANVAS B: THE TARGET (binary internals by RVA) -------------------
nodes = []
edges = []
_node_id[0] = 0

r = {
    "reg": find_note("02 Registry/rvas", "rva-dispatch-decoder-registry"),   # DAT_14280E3E0
    "factory": find_note("02 Registry/rvas", "rva-dispatch-decoder-registry-factory"),
    "dispatch": find_note("02 Registry/rvas", "rva-dispatch-bap-dispatch-table"),
    "classes": find_note("02 Registry/rvas", "rva-dispatch-8-class-descriptors"),
    "records": find_note("02 Registry/rvas", "rva-dispatch-37-per-type-response"),
    "push15": find_note("02 Registry/rvas", "rva-dispatch-family-4-push-object"),
    "svc11": find_note("02 Registry/rvas", "rva-dispatch-svc-11-decoded-body"),
    "store": find_note("02 Registry/rvas", "rva-store-rollback-decision"),
    "flagbank": find_note("02 Registry/rvas", "rva-flags-account-flag-bank"),
    "launch": find_note("02 Registry/rvas", "rva-activity-launch-activity-script"),
    "mode1": find_note("02 Registry/rvas", "rva-activity-launch-authored-manager"),
    "resolver": find_note("02 Registry/rvas", "rva-census-hooks-item-service"),
    "stamp": find_note("02 Registry/rvas", "rva-census-hooks-stamp-table-consume"),
    "factory71": find_note("02 Registry/rvas", "rva-dispatch-71-entry-static"),
}
for k, v in r.items():
    if v is None:
        print(f"[warn] no note found for {k}")

n_reg = N("file", r["reg"] or "02 Registry/rvas", 0, 40, 260, 80, "BAP dispatch: 71-decoder registry")
n_fac = N("file", r["factory"] or "02 Registry/rvas", 0, 170, 260, 80, "factory FUN_140E75790 (static-init)")
n_disp = N("file", r["dispatch"] or "02 Registry/rvas", 320, 40, 260, 80, "BAP dispatch tables (two thunks)")
n_cls = N("file", r["classes"] or "02 Registry/rvas", 320, 170, 260, 80, "8 class descriptors")
n_rec = N("file", r["records"] or "02 Registry/rvas", 320, 300, 260, 80, "37 response records")
n_p15 = N("file", r["push15"] or "02 Registry/rvas", 640, 40, 260, 80, "family-4 push objects (15)")
n_s11 = N("file", r["svc11"] or "02 Registry/rvas", 640, 170, 260, 80, "svc-11 apply (R19, txnId)")
n_sto = N("file", r["store"] or "02 Registry/rvas", 960, 40, 260, 80, "store diff / rollback")
n_fb = N("file", r["flagbank"] or "02 Registry/rvas", 960, 170, 260, 80, "flag bank (@ +0x742C, 12,300)")
n_lau = N("file", r["launch"] or "02 Registry/rvas", 1280, 40, 300, 80, "activity launch pump (mode 6/1)")
n_m1 = N("file", r["mode1"] or "02 Registry/rvas", 1280, 170, 300, 80, "authored manager (mode 1)")
n_res = N("file", r["resolver"] or "02 Registry/rvas", 640, 300, 260, 80, "resolver vtable+0x6F8 (hash→index)")
n_st = N("file", r["stamp"] or "02 Registry/rvas", 960, 300, 260, 80, "stamp table consume")

E(n_fac, n_reg, "fills 71 (static table)")
E(n_reg, n_disp, "accessor FUN_140E74F80")
E(n_disp, n_cls, "class lookup")
E(n_disp, n_rec, "response records")
E(n_reg, n_p15, "family-4 sub-dispatch")
E(n_p15, n_s11, "decode apply")
E(n_s11, n_sto, "store after-image")
E(n_sto, n_fb, "memcmp flag bank on every push")
E(n_lau, n_m1, "route byte +0x12 → authored")
E(n_res, n_fb, "hash→index → evaluated byte == 2")
E(n_st, n_sto, "edge-triggered refresh")

build_canvas("B Target.canvas", nodes, edges)
print("\nlooking for any None links above — those would need manual re-pointing")
