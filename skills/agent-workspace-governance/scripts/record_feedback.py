#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Record evolution feedback for agent-workspace-governance skill."
    )
    parser.add_argument("--source", choices=["user", "agent", "ci"], required=True)
    parser.add_argument(
        "--profile",
        choices=["generic", "npm", "npm-monorepo", "unreal", "unreal-cpp", "all"],
        required=True,
    )
    parser.add_argument("--issue", required=True, help="Observed issue or gap.")
    parser.add_argument("--action", required=True, help="Action taken or planned.")
    parser.add_argument("--status", choices=["open", "fixed", "wontfix"], required=True)
    parser.add_argument("--root", default=".", help="Repository root path.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repo_root = Path(args.root).resolve()
    history_dir = repo_root / "skills" / "agent-workspace-governance" / "history"
    history_dir.mkdir(parents=True, exist_ok=True)
    history_file = history_dir / "EVOLUTION.md"

    if not history_file.exists():
        history_file.write_text(
            "# Evolution History\n\n"
            "Tracks iterative improvements for `agent-workspace-governance`.\n\n",
            encoding="utf-8",
        )

    now = datetime.now()
    stamp = now.strftime("%Y-%m-%d %H:%M:%S")
    payload = {
        "source": args.source,
        "profile": args.profile,
        "issue": args.issue,
        "action": args.action,
        "status": args.status,
        "timestamp": stamp,
    }

    entry = (
        f"## {stamp}\n\n"
        f"- source: `{args.source}`\n"
        f"- profile: `{args.profile}`\n"
        f"- status: `{args.status}`\n"
        f"- issue: {args.issue}\n"
        f"- action: {args.action}\n"
        f"- json: `{json.dumps(payload, ensure_ascii=False)}`\n\n"
    )
    with history_file.open("a", encoding="utf-8") as f:
        f.write(entry)

    print(
        json.dumps(
            {"status": "recorded", "history": str(history_file), "entry": payload},
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
