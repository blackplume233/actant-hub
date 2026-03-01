#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass
class AuditCounts:
    required_dirs: int
    required_files: int
    recommended_dirs: int
    workflow_files: int

    @property
    def total(self) -> int:
        return (
            self.required_dirs
            + self.required_files
            + self.recommended_dirs
            + self.workflow_files
        )


def run_json(command: list[str], cwd: Path) -> dict:
    result = subprocess.run(
        command, text=True, capture_output=True, cwd=str(cwd), check=False
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"Command failed: {' '.join(command)}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )
    return json.loads(result.stdout)


def to_counts(payload: dict) -> AuditCounts:
    return AuditCounts(
        required_dirs=len(payload.get("missing_required_dirs", [])),
        required_files=len(payload.get("missing_required_files", [])),
        recommended_dirs=len(payload.get("missing_recommended_dirs", [])),
        workflow_files=len(payload.get("missing_workflow_files", [])),
    )


def render_report(rounds: list[dict], converged: bool) -> str:
    lines: list[str] = []
    lines.append("# Reinforcement Loop Report")
    lines.append("")
    lines.append(f"- Rounds executed: {len(rounds)}")
    lines.append(f"- Converged: {'yes' if converged else 'no'}")
    lines.append("")
    lines.append("| Round | Before Missing | After Missing | Delta | Action |")
    lines.append("|------:|---------------:|--------------:|------:|--------|")

    for item in rounds:
        delta = item["before_total"] - item["after_total"]
        lines.append(
            f"| {item['round']} | {item['before_total']} | {item['after_total']} | {delta} | {item['action']} |"
        )

    lines.append("")
    if rounds:
        last = rounds[-1]
        lines.append("## Final Breakdown")
        lines.append("")
        lines.append(f"- missing_required_dirs: {last['after_required_dirs']}")
        lines.append(f"- missing_required_files: {last['after_required_files']}")
        lines.append(f"- missing_recommended_dirs: {last['after_recommended_dirs']}")
        lines.append(f"- missing_workflow_files: {last['after_workflow_files']}")

    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run iterative reinforcement loop for repository structure hardening."
    )
    parser.add_argument("--root", default=".", help="Repository root path")
    parser.add_argument(
        "--max-rounds", type=int, default=3, help="Maximum reinforcement rounds"
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply non-destructive scaffolding in each round",
    )
    parser.add_argument(
        "--run-validate", action="store_true", help="Run validate_skill.py after loop"
    )
    parser.add_argument(
        "--report",
        default="docs/reports/reinforcement-loop-report.md",
        help="Markdown report output path",
    )
    parser.add_argument("--json", action="store_true", help="Print JSON summary")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = Path(args.root).resolve()

    script_dir = Path(__file__).resolve().parent
    audit_script = script_dir / "audit_repo_structure.py"
    validate_script = script_dir / "validate_skill.py"

    rounds: list[dict] = []
    prev_total: int | None = None
    converged = False

    for idx in range(1, args.max_rounds + 1):
        before_payload = run_json(
            ["python", str(audit_script), "--root", str(root), "--json"],
            cwd=root,
        )
        before = to_counts(before_payload)

        if before.total == 0:
            converged = True
            rounds.append(
                {
                    "round": idx,
                    "before_total": before.total,
                    "after_total": before.total,
                    "before_required_dirs": before.required_dirs,
                    "before_required_files": before.required_files,
                    "before_recommended_dirs": before.recommended_dirs,
                    "before_workflow_files": before.workflow_files,
                    "after_required_dirs": before.required_dirs,
                    "after_required_files": before.required_files,
                    "after_recommended_dirs": before.recommended_dirs,
                    "after_workflow_files": before.workflow_files,
                    "action": "none-needed",
                }
            )
            break

        if args.apply:
            after_payload = run_json(
                ["python", str(audit_script), "--root", str(root), "--apply", "--json"],
                cwd=root,
            )
            action = "apply"
        else:
            after_payload = before_payload
            action = "dry-run"

        after = to_counts(after_payload)
        rounds.append(
            {
                "round": idx,
                "before_total": before.total,
                "after_total": after.total,
                "before_required_dirs": before.required_dirs,
                "before_required_files": before.required_files,
                "before_recommended_dirs": before.recommended_dirs,
                "before_workflow_files": before.workflow_files,
                "after_required_dirs": after.required_dirs,
                "after_required_files": after.required_files,
                "after_recommended_dirs": after.recommended_dirs,
                "after_workflow_files": after.workflow_files,
                "action": action,
            }
        )

        if after.total == 0:
            converged = True
            break

        if prev_total is not None and after.total >= prev_total:
            # Stop if no meaningful reduction.
            break
        prev_total = after.total

    if args.run_validate:
        subprocess.run(["python", str(validate_script)], cwd=str(root), check=True)

    report_path = Path(args.report)
    if not report_path.is_absolute():
        report_path = root / report_path
    if not report_path.parent.exists():
        report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_report(rounds, converged), encoding="utf-8")

    summary = {
        "status": "converged" if converged else "partial",
        "rounds": rounds,
        "report": str(report_path),
    }
    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
