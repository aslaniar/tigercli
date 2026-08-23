# -*- coding: utf-8 -*-
"""live_console.py — the Layer-1 triage console (the reviewer's game plan).

Tails BOTH logs (the server + the client), parses the ev=/stage= streams, and renders
one merged, real-time-aligned, color-coded view with the fixed panels:
  - THE LADDER: the family-4 / family-0 version mirrors, tracked from the frame
    lines (each delivered increment = +1; the snapshot/companion replays = the v0),
    plus the pushed-frame count (the nonce's visible proxy).
  - THE BOOTFLOW STRIP: the client's world-controller states on a 40-cell bar.
  - THE TRAP TRANSLATIONS: the known failure signatures -> the plain English at the
    moment they fire (the FINDINGS corpus as a rule set).
  - THE CENSUS FEED: the resolve pairs / marker polls / stamp fires / 2100 verbs.

MAC PORT (2026-08-22, lane cockpit): the log paths now resolve relative to the repo
root (Game/bin/x64/Sunrise/logs/sunrise.log + RE_output/s1_accept/Sunrise/logs/
sunrise.log), so the same script runs on Windows via --server/--client overrides or
the old absolute constants. ev=item_gate is SUPPRESSED by default (65k+ lines a boot
on macOS — pass --item-gate to show it). The census panel is dormant while
ability_gate/gate_trace are default-off in client_hook_activation.cpp; the
install-trap fires for item_gate now.

Zero server changes, zero client changes, zero boots. The old recording tails are
preserved as live_server_tail.ps1.v1 + live_client_tail.ps1.v1 (the fallback pair).

Usage:  python -X utf8 RE_scripts/live_console.py [--server LOG] [--client LOG] [--height N] [--item-gate]
Quit:   Ctrl+C
"""
import argparse
import os
import re
import shutil
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SERVER_LOG = str(REPO_ROOT / "RE_output" / "s1_accept" / "Sunrise" / "logs" / "sunrise.log")
CLIENT_LOG = str(REPO_ROOT / "Game" / "bin" / "x64" / "Sunrise" / "logs" / "sunrise.log")

# --- ANSI ------------------------------------------------------------------
R, G, Y, B, M, C, W, D = "\x1b[31m", "\x1b[32m", "\x1b[33m", "\x1b[34m", \
    "\x1b[35m", "\x1b[36m", "\x1b[37m", "\x1b[90m"
X, BOLD = "\x1b[0m", "\x1b[1m"
HOME, CLREOL = "\x1b[H", "\x1b[K"

# --- the log-line grammar ---------------------------------------------------
LINE_RE = re.compile(r"^(?P<side>server|client) level=(?P<level>\w+) t=(?P<t>\d+) "
                     r"ev=(?P<ev>\S+)(?: (?P<rest>.*))?$")

# the family-4 stages that deliver a +1 increment (the replays deliver v0)
F4_BUMP_STAGES = {"subclass_select", "subclass_equip", "subclass_selection",
                  "select", "change", "acquire", "dismantle", "socket_plug",
                  "profile_acquire", "item_state"}
F0_BUMP_STAGES = {"banner_refresh", "banner_move"}

# --- the bootflow strip codes ------------------------------------------------
STATE_CODES = {
    "setup:activity_session_creation": "ASC",
    "setup:matchmaking": "MM",
    "setup:activity_host_setup": "AH",
    "setup:prologue_intro_loading": "PROL",
    "setup:orbit_outro": "ORBOUT",
    "setup:activity_world_transition": "XIT",
    "activity:initial_slice_set_loading": "SLICE",
    "activity:physics_join": "PHYS",
    "activity:in_world": "WRLD",
    "world_controller:state:cleanup:kick_to_bootflow_start": "KICK",
}
ENTER_STATE_RE = re.compile(r"Entering state '(?P<state>[^']+)'")
WORLD_RE = re.compile(r"successfully changed world to: (?P<world>\S+)")

# --- the trap rules (the FINDINGS corpus as a rule set) -----------------------
# (regex, the plain-English translation, the color, the panel-visible flag)
TRAPS = [
    (re.compile(r"queuez version is out of order"),
     "FAMILY-4 VERSION REJECTED - the out-of-order crash class", R, True),
    (re.compile(r"kick_to_bootflow_start"),
     "CLIENT KICK - the bootflow restart (the rejection follow-up)", R, True),
    (re.compile(r"_connection_failure_suicide"),
     "the fatal teardown (after a kick = the crash; alone = the quit path)", Y, True),
    (re.compile(r"stage=swap \S+ cache=0 result=mismatch"),
     "IDENTITY GATE FAILED - run the eqHash dry-run", R, True),
    (re.compile(r"not_ready region="),
     "the gameplay advertise skip (the session-seed work item)", Y, False),
    (re.compile(r"ability_change result=fail step=mutate"),
     "the 2100 scenario-hash correctly refused (expected)", D, False),
    (re.compile(r"stage=install result=ok count="),
     "the item_gate observers installed (the validation-chain census armed; gate_trace is "
     "default-off)", G, False),
    (re.compile(r"result=fail"),
     "a stage failed", R, True),
    (re.compile(r"result=skip"),
     "a stage skipped", D, False),
]

CENSUS_STAGES = {"resolve", "marker_poll", "stamp_consume", "stamp_gate",
                 "emit_2100", "expr_eval", "rollback_apply"}


class Tail:
    """One seek-based log follower with the rotation handling."""

    def __init__(self, path, side):
        self.path = path
        self.side = side
        self.pos = self._size()

    def _size(self):
        try:
            return os.path.getsize(self.path)
        except OSError:
            return 0

    def poll(self):
        size = self._size()
        if size < self.pos:          # the rotation / the truncation
            self.pos = 0
        if size == self.pos:
            return []
        lines = []
        try:
            with open(self.path, "r", encoding="utf-8", errors="replace") as f:
                f.seek(self.pos)
                lines = f.readlines()
                self.pos = f.tell()
        except OSError:
            pass
        return [line.rstrip("\n") for line in lines]


class Console:
    def __init__(self, server_log, client_log, height, item_gate=False):
        self.tails = [Tail(server_log, "server"), Tail(client_log, "client")]
        self.height = max(height, 18)
        self.item_gate = item_gate      # False = suppress the 65k-line-a-boot flood
        self.stream = []           # the rendered stream lines (the ring)
        self.f4 = 0
        self.f0 = 0
        self.frames = 0
        self.last_frame = "none"
        self.states = []
        self.last_trap = None
        self.last_trap_ts = 0
        self.saw_kick = False
        self.census = {name: 0 for name in CENSUS_STAGES}
        self.resolve_pairs = {}
        self.start = time.time()

    # --- the state updates ---------------------------------------------------
    def _update(self, side, t, ev, rest):
        rest = rest or ""
        if ev == "queuez":
            stage = re.search(r"stage=(\w+)", rest)
            stage = stage.group(1) if stage else ""
            if "family=4" in rest and stage in F4_BUMP_STAGES:
                self.f4 += 1
                self.frames += 1
                self.last_frame = "%s ok" % stage
            if stage in F0_BUMP_STAGES:
                self.f0 += 1
                self.frames += 1
                self.last_frame = "%s ok" % stage
        if side == "client" and ev == "gate_trace":
            stage = re.search(r"stage=(\w+)", rest)
            stage = stage.group(1) if stage else ""
            if stage in self.census:
                self.census[stage] += 1
            if stage == "resolve":
                m = re.search(r"hash=0x([0-9A-Fa-f]{8})\s+idx=0x([0-9A-Fa-f]+)", rest)
                if m:
                    pair = (m.group(1), m.group(2))
                    self.resolve_pairs.setdefault(pair, 0)
                    self.resolve_pairs[pair] += 1
        if side == "client" and ev == "ability_gate" and "emit_2100" in rest:
            self.census["emit_2100"] += 1
        if side == "client":
            m = ENTER_STATE_RE.search(rest)
            if m:
                self.states.append(STATE_CODES.get(m.group("state"),
                                                    self._code(m.group("state"))))
            m = WORLD_RE.search(rest)
            if m:
                self.states.append(self._world_code(m.group("world")))
            if "kick_to_bootflow_start" in rest:
                self.saw_kick = True
        for rx, text, color, panel in TRAPS:
            if rx.search(rest):
                self.last_trap = (text, color, time.time(), rest[:120])
                if text.startswith("the fatal teardown") and not self.saw_kick:
                    self.last_trap = (text, D, time.time(), rest[:120])
                break
        self.states = self.states[-40:]

    @staticmethod
    def _code(state):
        parts = [p[:3].upper() for p in state.split(":")]
        return ".".join(parts)[:10]

    @staticmethod
    def _world_code(world):
        if "tower" in world:
            return "TOWER"
        if "orbit" in world:
            return "ORBIT"
        return world[:8].upper()

    # --- the stream rendering -------------------------------------------------
    def _line_color(self, side, ev, rest):
        if "ws_capture" in rest:
            return M, ">>> CLIENT REQUEST ARRIVED: "
        if ev == "queuez" and re.search(r"stage=(subclass_select|subclass_equip)\b", rest):
            return G, ">>> SERVER DELIVERED the family-4 answer: "
        if ev == "queuez" and "banner_refresh" in rest:
            return G, ""
        if side == "client" and "stage=resolve" in rest:
            return M, ""
        if side == "client" and "emit_2100" in rest:
            return Y, "the client emitted a swap verb: "
        if side == "client" and re.search(r"stage=(marker_poll|stamp_)", rest):
            return G, ""
        if "result=fail" in rest or "level=warn" in rest or "level=error" in rest:
            return Y, ""
        return D, ""

    def render(self):
        out = []
        now = time.strftime("%H:%M:%S")
        elapsed = time.time() - self.start
        out.append("%s%s  SUNRISE LIVE CONSOLE (Layer 1)  -  the server + the client merged"
                   "  [%s  +%ds]%s" % (BOLD, C, now, int(elapsed), X))
        trap = self.last_trap
        trap_text = "%s%s%s (t=%.1fs)%s" % (trap[1], trap[0], X,
                                            trap[2] - self.start, X) if trap else \
            "%snone yet%s" % (D, X)
        out.append("ladder:  family4=%d  family0=%d  frames=%d  last=%s" %
                   (self.f4, self.f0, self.frames, self.last_frame))
        strip = " ".join("[%s]" % s for s in self.states) or "%s(bootflow quiet)%s" % (D, X)
        out.append("bootflow: " + strip)
        out.append("trap:     " + trap_text)
        census = " ".join("%s=%d" % (k, self.census[k]) for k in sorted(self.census)
                          if self.census[k])
        out.append("census:   " + (census or "%snone yet%s" % (D, X)))
        out.append(D + "-" * min(shutil.get_terminal_size((120, 24)).columns, 178) + X)
        for line in self.stream:
            out.append(line)
        # the leftovers cleared + the cursor homed
        sys.stdout.write(HOME + "\n".join(out) + CLREOL + "\n" + CLREOL)
        sys.stdout.flush()

    # --- the main loop ----------------------------------------------------------
    def run(self):
        if os.name == "nt":
            os.system("")   # the Windows VT enable
        try:
            while True:
                new = 0
                for tail in self.tails:
                    for line in tail.poll():
                        m = LINE_RE.match(line)
                        if not m:
                            continue
                        side, t = m.group("side"), int(m.group("t"))
                        ev, rest = m.group("ev"), m.group("rest") or ""
                        if ev == "item_gate" and not self.item_gate:
                            continue
                        self._update(side, t, ev, rest)
                        color, banner = self._line_color(side, ev, rest)
                        rendered = "%s[%s t=%d] %s%s%s%s" % (
                            color, side[0].upper(), t, banner, ev, " " + rest if rest else "", X)
                        self.stream.append(rendered)
                        new += 1
                        trap = self.last_trap
                        if trap and trap[2] > self.last_trap_ts:
                            self.last_trap_ts = trap[2]
                            self.stream.append("%s>>> TRAP: %s%s" % (trap[1], trap[0], X))
                            new += 1
                self.stream = self.stream[-(self.height - 7):]
                if new:
                    self.render()
                time.sleep(0.1)
        except KeyboardInterrupt:
            sys.stdout.write(HOME + CLREOL + "console stopped.\n")


def main():
    ap = argparse.ArgumentParser(description="the Layer-1 live triage console")
    ap.add_argument("--server", default=SERVER_LOG)
    ap.add_argument("--client", default=CLIENT_LOG)
    ap.add_argument("--height", type=int, default=32)
    ap.add_argument("--item-gate", action="store_true",
                    help="show the ev=item_gate flood lines (suppressed by default)")
    args = ap.parse_args()
    Console(args.server, args.client, args.height, args.item_gate).run()


if __name__ == "__main__":
    main()
