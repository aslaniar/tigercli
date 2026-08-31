# Plan: closing the log-tooling adoption gap (2026-08-29)

## DIAGNOSIS (evidence-based, not assumed)

**Adoption is real where the tool fits.** The ms-start-gate lane built and
cited indexes properly (`logindex index_20260828_180921.db` appears in claims
with addresses); three index dbs exist spanning 08-27..08-28. The teaching
survived the 08-28 governance diet: AGENTS.md router trigger (line 51) +
ENVIRONMENTS.md log-digging block (line 152).

**But grep persists in three specific frictions** (from today's FINDINGS):
1. **No zero-decision path.** Every new boot's logs need a manual "build an
   index? name it? which db covers which boot?" decision. Deep lanes do it;
   every quick/medium check defaults to grep because that's zero decisions.
2. **Live/boot-moment watching has no indexed path.** logindex is post-hoc
   (snapshot semantics). During/after a boot the habit is tail+grep.
   boot_verdict.sh mechanizes exactly ONE verdict (lobby lane) - every other
   front re-rolls grep bundles.
3. **Unregistered surfaces.** The peer-channel DTLS pcap (20.144: "read by
   SIZE and CADENCE") is analyzed by hand - no tool; the next peer-channel
   lane will fork its own (the exact pattern TOOLS.md exists to prevent).

So: NOT "tooling broken" and NOT merely "needs enforcement words" - it is
one missing convenience layer + one missing small tool + light template
reinforcement.

## DELIVERABLES

### A. `RE_scripts/logq.sh` - the zero-decision wrapper (main gap)
`bash RE_scripts/logq.sh <pattern...> [--capture DIR] [--ev E] [--stage S]
[--tail N] [--source S] [--rebuild]`
- Resolves logs: default = the live three (server s1_accept + mac client +
  rig client via the boot_verdict.sh transport pattern: ssh ControlPath +
  scp, honest UNREACHABLE fallback); `--capture DIR` = frozen capture dir.
- Ensures a fresh index: per-index manifest json (source paths + mtime +
  size, written by the wrapper) - reuse if all match, rebuild otherwise,
  print which happened (liveness on the boring path).
- Then runs logq.py. ONE command from question to cited answer.
- logindex.py needs a tiny additive flag: `--manifest PATH` writing the
  manifest (or the wrapper computes it; prefer wrapper-side to keep
  logindex.py untouched).

### B. `logq.py --list` (small)
Lists available indexes under RE_output/logindex/: name, per-source coverage
+ event counts, manifest freshness vs current log mtimes. Makes "which db do
I query" answerable in one line instead of ls archaeology.

### C. `RE_scripts/pcapcadence.py` - peer-channel size/cadence reader
pcap -> per-flow (5-tuple) packet-size histogram + inter-arrival cadence
(min/median/max, packets/sec buckets). DTLS payloads are opaque by design;
this mechanizes exactly what 20.144 did by hand. `--selftest` with a
synthetic pcap (stdlib struct - classic pcap format is simple; no tshark
dependency needed for UDP stats). Register in TOOLS.md.

### D. Enforcement touch-ups (one small commit)
- lane-brief-template.md: evidence lines for log digs cite logq format.
- TOOLS.md: note boot_verdict.sh as the CANONICAL shape for per-front
  mechanical verdicts (script, not a bundle of greps) so the next front
  generalizes instead of re-rolling.

## SAFETY ENVELOPE (another session holds the pen)
- Branch `meta/logq2-v1`, additive new files (logq.sh, pcapcadence.py,
  fixtures); logq.py --list is an additive mode change to my own tool.
- Doc edits (D) staged but left uncommitted or committed-only-if-clean,
  same discipline as the 08-27/28 fold-ins: never mix hunks with the pen
  session's dirty files.
- Read-only on all logs/captures/pcaps. No boots, no deploys, no fork code.

## ACCEPTANCE
1. `logq.sh <term>` on the live three logs answers with cited hits and
   prints "index reused" or "index rebuilt (reason)" - zero pre-steps.
2. Stale detection proven: append to a log (or touch) -> next wrapper call
   rebuilds; unchanged -> reuses.
3. `--list` shows all indexes + staleness at a glance.
4. pcapcadence --selftest passes; tool reproduces a stated 20.144 cadence
   observation from an existing peer pcap if one is available on disk.
5. All selftests run green twice (stability), parse-checked first.
