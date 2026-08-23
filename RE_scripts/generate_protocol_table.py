#!/usr/bin/env python3
"""Generate the protocol tape's service/kind tables from the handbook dump.

Source of truth: the page-marked raw text of "Internet's guide to bungie's
bullshit.pdf" (RE_output/dumps/bungie_bullshit_guide.txt), sections:

  10.2 Current BAP request services   (pp15-16)
  10.3 Current BAP response services  (pp16-17)
  10.4 Current server notifications   (p17)
  21.2 Server-to-client message types (p46)
  21.3 Client-to-server message types (pp46-47)

Output: src/client/hooks/handle_message/protocol_table.h in the integration
worktree - C++ constexpr DATA with per-entry page cites. The observer only
looks names up here; the registry text never lives inside the observer.

Cross-check: the parsed request/response/notification NUMBER SETS must equal
the fork's own enums in src/middleware/bap/frame.h (RequestService /
ResponseService / NotificationService). Any mismatch fails the run - the
handbook and our code must not drift apart silently.

Usage:
  python3 -X utf8 RE_scripts/generate_protocol_table.py            # real emit
  python3 -X utf8 RE_scripts/generate_protocol_table.py --output X # smoke emit
  python3 -X utf8 RE_scripts/generate_protocol_table.py --no-cross-check  # dev

ASCII-only output (AGENTS no-syntax-tax rule 6); the dump carries ff/fi/fl
ligature characters (U+FB00 family) that are folded to ASCII here.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DUMP_PATH = REPO_ROOT / "RE_output" / "dumps" / "bungie_bullshit_guide.txt"
DEFAULT_OUTPUT = (
    REPO_ROOT
    / "RE_build"
    / "Sunrise-fork-inventory"
    / "Sunrise"
    / "src"
    / "client"
    / "hooks"
    / "handle_message"
    / "protocol_table.h"
)
FRAME_H_PATH = (
    REPO_ROOT
    / "RE_build"
    / "Sunrise-fork-inventory"
    / "Sunrise"
    / "src"
    / "middleware"
    / "bap"
    / "frame.h"
)

PAGE_MARK = re.compile(r"^===== PAGE (\d+) =====")
HEADING = re.compile(r"^(10\.2 Current BAP request services|10\.3 Current BAP response "
                     r"services|10\.4 Current server notifications|21\.2 Server-to-client "
                     r"message types|21\.3 Client-to-server message types)")
BULLET = re.compile(r"^\s*\u2022\s+(\d{1,3}):\s+(.+?)\s*$")

# ff fi fl ffi ffl ligatures -> ASCII (the dump's text extractor kept them).
LIGATURES = str.maketrans(
    {"\ufb00": "ff", "\ufb01": "fi", "\ufb02": "fl", "\ufb03": "ffi", "\ufb04": "ffl"}
)

# Compact tape names for the activity-message kinds. The handbook names are
# sentences ("join result or pending-join notification"); the tape prints the
# compact form and carries the handbook text in `desc`. Key = exact handbook
# phrase (after ligature folding), value = compact identifier.
KIND_ALIASES = {
    "entity-slot notification": "entity_slot_notification",
    "global activity state": "global_activity_state",
    "join result or pending-join notification": "join_result",
    "auth and sense update": "auth_sense",
    "membership replication": "membership_replication",
    "bubble-host table": "bubble_host_table",
    "join request": "join_request",
    "sense update": "sense_update",
    "request activity host": "request_activity_host",
    "start new activity": "start_new_activity",
    "request peer reservation": "request_peer_reservation",
    "release peer reservation": "release_peer_reservation",
    "peer leave request": "peer_leave",
    "client keepalive": "keepalive",
    "state refresh": "state_refresh",
    "incident report": "incident_report",
    "entity-slot grant request": "slot_grant_request",
    "entity-slot return": "slot_return",
    "client authoritative data": "client_authoritative_data",
    "client identity": "client_identity",
    "abandon authority": "abandon_authority",
    "purge request": "purge",
    "reset acknowledgement": "reset_ack",
    "per-bubble query answer": "query_answer",
    "whole-activity query answer": "query_answer",
    "abdicate authority": "abdicate",
    "debug command": "debug",
    "connectivity failure report": "connectivity_failure",
    "membership acknowledgement": "membership_ack",
    "client heartbeat": "heartbeat",
    "bug-claw report": "bug_claw",
    "lag-switch report": "lag_switch",
    "connection-quality report": "connection_quality",
    "speculative migration report": "speculative_migration",
    "high-water report": "high_water",
    "inspirations refresh": "inspirations_refresh",
    "patch epoch": "patch_epoch",
}


def fold(text: str) -> str:
    """Folds ligatures and strips line noise from handbook text."""
    return text.translate(LIGATURES).strip()


def identifier(name: str) -> str:
    """Turns a handbook name into an ASCII snake_case identifier."""
    name = fold(name).lower()
    name = re.sub(r"[^a-z0-9]+", "_", name)
    return name.strip("_")


def parse_sections(text: str) -> dict[str, list[tuple[int, str, str]]]:
    """Returns {section heading: [(number, name, page), ...]} in dump order."""
    sections: dict[str, list[tuple[int, str, str]]] = {}
    current: str | None = None
    page = 0
    for line in text.splitlines():
        page_match = PAGE_MARK.match(line)
        if page_match:
            page = int(page_match.group(1))
            continue
        heading_match = HEADING.match(line)
        if heading_match:
            current = heading_match.group(1)
            sections[current] = []
            continue
        if current is None:
            continue
        bullet = BULLET.match(line)
        # Sections carry a caption line ("CURRENT SOURCE: ...") between the
        # heading and the bullet list; only a non-bullet line AFTER bullets
        # were collected ends the list. Without this the collector keeps
        # eating later bullet lists in the document.
        if bullet:
            sections[current].append((int(bullet.group(1)), fold(bullet.group(2)), page))
            continue
        if line.strip() and sections[current]:
            current = None
    return sections


def parse_frame_h(text: str) -> dict[str, set[int]]:
    """Extracts {enum name: number set} from the fork's frame.h enums."""
    enums: dict[str, set[int]] = {}
    current: str | None = None
    for line in text.splitlines():
        if line.startswith("enum class "):
            current = line.split("enum class ")[1].split(" :")[0]
            enums[current] = set()
            continue
        if current is None:
            continue
        if line.startswith("};"):
            current = None
            continue
        value = re.search(r"=\s*(\d+)", line)
        if value is not None:
            enums[current].add(int(value.group(1)))
    return enums


def cross_check(handbook: dict[str, list[tuple[int, str, str]]],
                frame_h: dict[str, set[int]],
                out: list[str]) -> bool:
    """Verifies the handbook number sets against the fork's own enums."""
    pairs = [
        ("10.2 Current BAP request services", "RequestService"),
        ("10.3 Current BAP response services", "ResponseService"),
        ("10.4 Current server notifications", "NotificationService"),
    ]
    ok = True
    for section, enum_name in pairs:
        handbook_numbers = {entry[0] for entry in handbook[section]}
        fork_numbers = frame_h.get(enum_name, set())
        missing = handbook_numbers - fork_numbers
        extra = fork_numbers - handbook_numbers
        status = "MATCH"
        if missing or extra:
            ok = False
            status = "MISMATCH"
        out.append(f"  {enum_name:24s} {status} handbook={len(handbook_numbers)} "
                   f"frame_h={len(fork_numbers)}")
        if missing:
            out.append(f"    in handbook, absent from frame.h: {sorted(missing)}")
        if extra:
            out.append(f"    in frame.h, absent from handbook:  {sorted(extra)}")
    return ok


def emit_header(sections: dict[str, list[tuple[int, str, str]]]) -> str:
    """Renders protocol_table.h from the parsed handbook sections."""
    requests = sections["10.2 Current BAP request services"]
    responses = sections["10.3 Current BAP response services"]
    notifications = sections["10.4 Current server notifications"]
    kinds = (sections["21.2 Server-to-client message types"]
             + sections["21.3 Client-to-server message types"])
    kinds.sort(key=lambda entry: entry[0])

    lines: list[str] = []
    add = lines.append
    add("#pragma once")
    add("/**")
    add(" * BAP service registry and activity-message kinds, as DATA with handbook")
    add(" * page cites. GENERATED FILE - do not edit by hand.")
    add(" *")
    add(" * Source: RE_scripts/generate_protocol_table.py parses the page-marked")
    add(" * handbook dump (RE_output/dumps/bungie_bullshit_guide.txt) and cross-")
    add(" * checks the number sets against src/middleware/bap/frame.h enums.")
    add(" * Rerun the generator after any handbook or frame.h revision.")
    add(" *")
    add(" * Registry: Internet's guide to bungie's bullshit.pdf, sections 10.2")
    add(" * (request services, pp15-16), 10.3 (response services, pp16-17), 10.4")
    add(" * (server notifications, p17). Kinds: sections 21.2/21.3 (pp46-47).")
    add(" *")
    add(" * The tape looks names up here; no registry text lives in the observer.")
    add(" */")
    add("")
    add("#include <array>")
    add("#include <cstdint>")
    add("#include <string_view>")
    add("")
    add("namespace sunrise::client::hooks::handle_message::protocol {")
    add("")
    add("/** One BAP service registry entry (handbook sections 10.2-10.4). */")
    add("struct ServiceEntry {")
    add("    std::uint16_t number;")
    add("    std::string_view name;")
    add("    std::string_view role;   // request | response | notification")
    add("    std::string_view page;   // handbook page cite")
    add("};")
    add("")
    add("/** One activity-message kind inside the svc-9 envelope (21.2/21.3). */")
    add("struct KindEntry {")
    add("    std::uint8_t number;")
    add("    std::string_view name;   // compact tape name")
    add("    std::string_view desc;   // handbook phrasing")
    add("    std::string_view page;   // handbook page cite")
    add("};")
    add("")

    def emit_service(entries: list[tuple[int, str, str]], role: str, var: str) -> None:
        add(f"/** {role} services; handbook p{min(e[2] for e in entries)}-p{max(e[2] for e in entries)}. */")
        # Double braces: the inner list initializes std::array's single member.
        add(f"inline constexpr std::array<ServiceEntry, {len(entries)}> {var}{{{{")
        for number, name, page in entries:
            ident = identifier(name)
            add(f"    {{{number}, \"{ident}\", \"{role}\", \"p{page}\"}}, "
                f"// {number}: {name}")
        add("}};")
        add("")

    emit_service(requests, "request", "kRequestServices")
    emit_service(responses, "response", "kResponseServices")
    emit_service(notifications, "notification", "kNotificationServices")

    add("/** activity-message kinds; handbook p46-p47. */")
    add(f"inline constexpr std::array<KindEntry, {len(kinds)}> kMessageKinds{{{{")
    for number, name, page in kinds:
        compact = KIND_ALIASES.get(name)
        if compact is None:
            compact = identifier(name)
            add(f"    // NOTE: no tape alias for \"{name}\"; using normalized text.")
        add(f"    {{{number}, \"{compact}\", \"{name}\", \"p{page}\"}},")
    add("}};")
    add("")
    add("/** @return Handbook name for one BAP service number, or \"\" when unknown. */")
    add("[[nodiscard]] inline const char* service_name(std::uint16_t number) noexcept {")
    add("    for (const ServiceEntry& entry : kRequestServices) {")
    add("        if (entry.number == number) return entry.name.data();")
    add("    }")
    add("    for (const ServiceEntry& entry : kResponseServices) {")
    add("        if (entry.number == number) return entry.name.data();")
    add("    }")
    add("    for (const ServiceEntry& entry : kNotificationServices) {")
    add("        if (entry.number == number) return entry.name.data();")
    add("    }")
    add("    return \"\";")
    add("}")
    add("")
    add("/** @return Tape name for one activity-message kind, or \"\" when unknown. */")
    add("[[nodiscard]] inline const char* kind_name(std::uint8_t number) noexcept {")
    add("    for (const KindEntry& entry : kMessageKinds) {")
    add("        if (entry.number == number) return entry.name.data();")
    add("    }")
    add("    return \"\";")
    add("}")
    add("")
    add("} // namespace sunrise::client::hooks::handle_message::protocol")
    add("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT,
                        help="header path to write (default: the worktree header)")
    parser.add_argument("--no-cross-check", action="store_true",
                        help="skip the frame.h number-set comparison")
    args = parser.parse_args()

    if not DUMP_PATH.is_file():
        print(f"FATAL: handbook dump not found: {DUMP_PATH}", file=sys.stderr)
        return 2
    sections = parse_sections(DUMP_PATH.read_text(encoding="utf-8"))
    expected = ["10.2 Current BAP request services",
                "10.3 Current BAP response services",
                "10.4 Current server notifications",
                "21.2 Server-to-client message types",
                "21.3 Client-to-server message types"]
    missing_sections = [name for name in expected if name not in sections]
    if missing_sections:
        print(f"FATAL: handbook sections not found: {missing_sections}", file=sys.stderr)
        return 2

    for name in expected:
        entry = sections[name]
        print(f"  parsed {name}: {len(entry)} entries "
              f"(pages p{min(e[2] for e in entry)}-p{max(e[2] for e in entry)})")

    if not args.no_cross_check:
        if not FRAME_H_PATH.is_file():
            print(f"FATAL: frame.h not found: {FRAME_H_PATH}", file=sys.stderr)
            return 2
        report: list[str] = []
        if not cross_check(sections, parse_frame_h(FRAME_H_PATH.read_text(encoding="utf-8")),
                           report):
            print("CROSS-CHECK FAILED - handbook and frame.h drifted apart:", file=sys.stderr)
            for line in report:
                print(f"  {line}", file=sys.stderr)
            return 1
        for line in report:
            print(f"  {line}")

    header = emit_header(sections)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(header, encoding="ascii")
    print(f"  wrote {args.output} ({len(header.splitlines())} lines)")
    return 0


if __name__ == "__main__":
    sys.exit(main())