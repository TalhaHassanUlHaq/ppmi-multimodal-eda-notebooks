#!/usr/bin/env python3
"""agent_bridge.py: Bidirectional automated bridge between Gemini and Codex CLI.

Provides programmatic interaction:
1. send_to_codex: Pushes instructions/handoffs to the active Codex terminal session via `codex queue`.
2. get_latest_review: Reads and parses the latest review section from docs/review_log.md.
3. wait_for_review_update: Blocks until docs/review_log.md is updated by Codex, then returns the verdict.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
from pathlib import Path
import subprocess
import sys
import time

REPO_ROOT = Path(__file__).resolve().parents[2]
REVIEW_LOG_PATH = REPO_ROOT / "docs" / "review_log.md"
DECISIONS_PATH = REPO_ROOT / "docs" / "dataset_selection_decisions.md"
CODEX_HOME = Path(os.environ.get("USERPROFILE", "")) / ".codex"
LOCKS_DIR = CODEX_HOME / "thread-writer-locks"
SESSIONS_DIR = CODEX_HOME / "sessions"


def get_active_codex_thread() -> str | None:
    """Finds the active Codex session UUID, prioritizing root user sessions over internal guardian subagents."""
    if not LOCKS_DIR.exists():
        return None
    candidates = []
    for f in LOCKS_DIR.glob("*.lock"):
        if f.name.startswith("."):
            continue
        stem = f.stem
        rollouts = list(SESSIONS_DIR.glob(f"**/rollout-*-{stem}.jsonl"))
        is_user_root = False
        size = 0
        if rollouts:
            size = rollouts[0].stat().st_size
            try:
                with open(rollouts[0], "r", encoding="utf-8") as rf:
                    meta = json.loads(rf.readline())
                    pl = meta.get("payload", {})
                    if pl.get("parent_thread_id") is None and pl.get("thread_source") == "user":
                        is_user_root = True
            except Exception:
                pass
        candidates.append((is_user_root, size, f.stat().st_mtime, stem))

    if not candidates:
        return None
    # Sort: root user session first, largest rollout size next, then newest lock file
    candidates.sort(key=lambda c: (c[0], c[1], c[2]), reverse=True)
    return candidates[0][3]


def send_to_codex(message: str, resume: bool = True) -> dict:
    """Sends a message into the active Codex terminal session via `codex queue`."""
    thread_id = get_active_codex_thread()
    if not thread_id:
        raise RuntimeError("No active Codex session lock found in ~/.codex/thread-writer-locks.")

    cmd = ["codex", "queue", "--thread", thread_id, "--message", message]
    if resume:
        cmd.append("--resume")

    print(f"[*] Dispatching message to Codex thread {thread_id}...")
    res = subprocess.run(cmd, capture_output=True, text=True, shell=(sys.platform == "win32"))
    if res.returncode != 0:
        print(f"[!] Warning: codex queue exited with code {res.returncode}:\n{res.stderr}", file=sys.stderr)
    else:
        print(f"[+] Message successfully queued to Codex thread {thread_id}!")
    return {
        "thread_id": thread_id,
        "returncode": res.returncode,
        "stdout": res.stdout,
        "stderr": res.stderr
    }


def parse_latest_review() -> dict:
    """Parses the most recent review block in docs/review_log.md."""
    if not REVIEW_LOG_PATH.exists():
        raise FileNotFoundError(f"Missing review log at {REVIEW_LOG_PATH}")

    content = REVIEW_LOG_PATH.read_text(encoding="utf-8")
    sections = content.split("\n## ")
    if len(sections) < 2:
        return {"raw": content, "verdict": "UNKNOWN", "findings": []}

    latest_section = "## " + sections[-1].strip()
    lines = latest_section.splitlines()
    header = lines[0] if lines else ""

    verdict = "UNKNOWN"
    for line in lines[:15]:
        upper = line.upper()
        if "VERDICT:" in upper or "RECOMMENDATION:" in upper:
            # Extract just the verdict phrase after the label
            verdict_phrase = upper.split("VERDICT:")[-1].split("RECOMMENDATION:")[-1].split(".")[0].strip()
            if "BLOCKED" in verdict_phrase:
                verdict = "BLOCKED"
            elif "CHANGES REQUIRED" in verdict_phrase or "REVISE" in verdict_phrase:
                verdict = "CHANGES_REQUIRED"
            elif ("APPROVED" in verdict_phrase or "PASS" in verdict_phrase) and "NOT" not in verdict_phrase and "UNAPPROVED" not in verdict_phrase:
                verdict = "PASS"
            break

    # Extract open findings
    findings = []
    for line in lines:
        if line.strip().startswith("|") and ("P1-" in line):
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 4 and not parts[1].startswith("---") and not parts[1].startswith("Finding"):
                finding_id = parts[1]
                status = parts[2]
                correction = parts[3]
                findings.append({
                    "id": finding_id,
                    "status": status,
                    "correction": correction
                })

    return {
        "header": header,
        "verdict": verdict,
        "findings": findings,
        "section_text": latest_section
    }


def wait_for_review_update(timeout_seconds: int = 1800, poll_interval: float = 2.0) -> dict:
    """Polls docs/review_log.md and docs/dataset_selection_decisions.md until updated by Codex."""
    if not REVIEW_LOG_PATH.exists():
        raise FileNotFoundError(f"Missing review log at {REVIEW_LOG_PATH}")

    initial_mtime = REVIEW_LOG_PATH.stat().st_mtime
    initial_size = REVIEW_LOG_PATH.stat().st_size
    initial_dec_mtime = DECISIONS_PATH.stat().st_mtime if DECISIONS_PATH.exists() else 0.0
    initial_dec_size = DECISIONS_PATH.stat().st_size if DECISIONS_PATH.exists() else 0

    print(f"[*] Watching {REVIEW_LOG_PATH.name} and {DECISIONS_PATH.name} for updates from Codex (timeout: {timeout_seconds}s)...")

    start_time = time.time()
    while time.time() - start_time < timeout_seconds:
        time.sleep(poll_interval)
        try:
            curr_stat = REVIEW_LOG_PATH.stat()
            curr_dec_stat = DECISIONS_PATH.stat() if DECISIONS_PATH.exists() else None

            changed = False
            if curr_stat.st_mtime != initial_mtime or curr_stat.st_size != initial_size:
                changed = True
            elif curr_dec_stat and (curr_dec_stat.st_mtime != initial_dec_mtime or curr_dec_stat.st_size != initial_dec_size):
                changed = True

            if changed:
                # Wait briefly for file write to complete
                time.sleep(1.0)
                print(f"[+] Change detected from Codex!")
                review = parse_latest_review()
                print(f"[+] Latest Review: {review.get('header')}")
                print(f"[+] Verdict: {review.get('verdict')}")
                return review
        except Exception:
            pass

    raise TimeoutError(f"Timed out waiting for Codex update after {timeout_seconds} seconds.")


def main():
    parser = argparse.ArgumentParser(description="Bidirectional agent bridge for Codex and Gemini.")
    subparsers = parser.add_subparsers(dest="action", required=True)

    # push command
    push_p = subparsers.add_parser("push", help="Push a message to Codex via codex queue")
    push_p.add_argument("message", help="Message to queue for Codex")
    push_p.add_argument("--no-resume", action="store_true", help="Do not pass --resume")

    # parse command
    subparsers.add_parser("latest", help="Parse and display the latest Codex review from docs/review_log.md")

    # wait command
    wait_p = subparsers.add_parser("wait", help="Wait for Codex to update docs/review_log.md")
    wait_p.add_argument("--timeout", type=int, default=1800, help="Timeout in seconds")

    args = parser.parse_args()

    if args.action == "push":
        res = send_to_codex(args.message, resume=not args.no_resume)
        print(json.dumps(res, indent=2))
    elif args.action == "latest":
        review = parse_latest_review()
        print(json.dumps(review, indent=2))
    elif args.action == "wait":
        review = wait_for_review_update(timeout_seconds=args.timeout)
        print(json.dumps(review, indent=2))


if __name__ == "__main__":
    main()

