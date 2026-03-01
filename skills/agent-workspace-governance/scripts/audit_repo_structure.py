#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path


REQUIRED_DIRS = [
    "docs",
    "history",
    "init",
    "issues",
    "skills",
    "subagents",
    "topics",
]

REQUIRED_FILES = [
    "AGENTS.md",
    "SUBAGENTS.md",
    "history/HISTORY.md",
    "init/AGENT_INIT.md",
]

WORKFLOW_REQUIRED_FILES = [
    ".trellis/workflow.md",
    ".trellis/scripts/get-context.sh",
    ".trellis/scripts/task.sh",
    ".trellis/scripts/init-developer.sh",
    ".trellis/scripts/add-session.sh",
    "docs/guides/dev-workflow-guide.md",
]

LEGIBILITY_SIGNAL_PATHS = [
    "AGENTS.md",
    "docs",
    "docs/guides",
    "docs/reports",
]

CONSTRAINT_SIGNAL_PATHS = [
    ".github/workflows",
    "eslint.config.js",
    ".eslintrc.json",
    "biome.json",
    "tsconfig.json",
]

FEEDBACK_SIGNAL_PATHS = [
    "tests",
    "vitest.config.ts",
    "pytest.ini",
    ".trellis/scripts/task.sh",
]

CONTROL_LOOP_SIGNAL_PATHS = [
    "history/HISTORY.md",
    "skills/agent-workspace-governance/scripts/validate_skill.py",
    "skills/agent-workspace-governance/scripts/reinforcement_loop.py",
]

CORE_SLASH_COMMANDS = [
    "start",
    "plan-start",
    "finish-work",
    "create-pr",
    "ship",
    "stage-version",
    "qa",
    "check-backend",
    "check-frontend",
    "check-cross-layer",
    "update-spec",
    "break-loop",
    "record-session",
    "parallel",
]

RECOMMENDED_DIRS = [
    "docs/architecture",
    "docs/design",
    "docs/decisions",
    "docs/guides",
    "docs/planning",
    "docs/stage",
    "docs/reports",
    "docs/setup",
    "docs/.local",
    "docs/human",
    "docs/agent",
    "issues/active",
    "issues/backlog",
    "issues/completed",
    "issues/archived",
    "issues/.local/active",
    "issues/.local/completed",
    "issues/.local/archived",
    "skills/.local",
    "topics/.local",
]


@dataclass
class AuditResult:
    root: str
    missing_required_dirs: list[str]
    missing_required_files: list[str]
    missing_recommended_dirs: list[str]
    missing_workflow_files: list[str]
    harness_readiness: dict[str, object]
    action_plan: list[dict[str, object]]
    strict_failures: list[str]
    guided_next_steps: list[dict[str, str]]
    move_suggestions: list[dict[str, str]]
    created_paths: list[str]


def exists_all(root: Path, paths: list[str]) -> list[str]:
    return [p for p in paths if not (root / p).exists()]


def count_lines(path: Path) -> int:
    if not path.exists() or not path.is_file():
        return 0
    return len(path.read_text(encoding="utf-8", errors="ignore").splitlines())


def has_trellis_source_marker(path: Path) -> bool:
    if not path.exists() or not path.is_file():
        return False
    text = path.read_text(encoding="utf-8", errors="ignore")
    return "Source: Trellis" in text or "source: trellis" in text.lower()


def expected_command_paths() -> tuple[list[str], list[str]]:
    claude_paths = [f".claude/commands/act/{name}.md" for name in CORE_SLASH_COMMANDS]
    cursor_paths = [f".cursor/commands/act-{name}.md" for name in CORE_SLASH_COMMANDS]
    return claude_paths, cursor_paths


def build_command_stub(command_name: str, platform: str) -> str:
    trigger = f"/act:{command_name}" if platform == "claude" else f"act-{command_name}"
    return (
        f"# {command_name}\n\n"
        "> Source: Trellis workflow (renamed prefix to `act`)\n\n"
        f"Auto-generated placeholder for `{trigger}`.\n\n"
        "## Purpose\n\n"
        "Describe command intent and execution flow.\n\n"
        "## Checklist\n\n"
        "- Define prerequisites\n"
        "- Define command actions\n"
        "- Define success criteria\n"
    )


def build_harness_readiness(root: Path) -> dict[str, object]:
    agents_path = root / "AGENTS.md"
    agents_lines = count_lines(agents_path)
    agents_too_long = agents_lines > 150

    legibility_missing = exists_all(root, LEGIBILITY_SIGNAL_PATHS)
    constraint_missing = exists_all(root, CONSTRAINT_SIGNAL_PATHS)
    feedback_missing = exists_all(root, FEEDBACK_SIGNAL_PATHS)
    control_loop_missing = exists_all(root, CONTROL_LOOP_SIGNAL_PATHS)
    claude_expected, cursor_expected = expected_command_paths()
    claude_missing = exists_all(root, claude_expected)
    cursor_missing = exists_all(root, cursor_expected)
    claude_provenance_missing = [
        p
        for p in claude_expected
        if (root / p).exists() and not has_trellis_source_marker(root / p)
    ]
    cursor_provenance_missing = [
        p
        for p in cursor_expected
        if (root / p).exists() and not has_trellis_source_marker(root / p)
    ]

    def score(missing: list[str], total: int) -> int:
        if total <= 0:
            return 0
        present = total - len(missing)
        return int((present / total) * 100)

    return {
        "legibility": {
            "score": score(legibility_missing, len(LEGIBILITY_SIGNAL_PATHS)),
            "missing": legibility_missing,
            "agents_md_lines": agents_lines,
            "agents_md_too_long": agents_too_long,
            "agents_md_recommended_max": 150,
        },
        "constraints": {
            "score": score(constraint_missing, len(CONSTRAINT_SIGNAL_PATHS)),
            "missing": constraint_missing,
        },
        "feedback": {
            "score": score(feedback_missing, len(FEEDBACK_SIGNAL_PATHS)),
            "missing": feedback_missing,
        },
        "control_loop": {
            "score": score(control_loop_missing, len(CONTROL_LOOP_SIGNAL_PATHS)),
            "missing": control_loop_missing,
        },
        "command_coverage": {
            "score": score(
                claude_missing + cursor_missing,
                len(claude_expected) + len(cursor_expected),
            ),
            "claude_missing": claude_missing,
            "cursor_missing": cursor_missing,
            "claude_provenance_missing": claude_provenance_missing,
            "cursor_provenance_missing": cursor_provenance_missing,
            "core_commands": CORE_SLASH_COMMANDS,
        },
    }


def build_action_plan(
    missing_required_dirs: list[str],
    missing_required_files: list[str],
    missing_workflow_files: list[str],
    missing_recommended_dirs: list[str],
    harness_readiness: dict[str, object],
) -> list[dict[str, object]]:
    plan: list[dict[str, object]] = []

    if missing_required_dirs or missing_required_files:
        plan.append(
            {
                "priority": "P0",
                "title": "Fill required structure baseline",
                "items": {
                    "missing_required_dirs": missing_required_dirs,
                    "missing_required_files": missing_required_files,
                },
            }
        )

    if missing_workflow_files:
        plan.append(
            {
                "priority": "P0",
                "title": "Restore workflow-critical files",
                "items": {"missing_workflow_files": missing_workflow_files},
            }
        )

    if missing_recommended_dirs:
        plan.append(
            {
                "priority": "P1",
                "title": "Complete recommended structure",
                "items": {"missing_recommended_dirs": missing_recommended_dirs},
            }
        )

    legibility = harness_readiness["legibility"]
    constraints = harness_readiness["constraints"]
    feedback = harness_readiness["feedback"]
    control_loop = harness_readiness["control_loop"]
    command_coverage = harness_readiness["command_coverage"]

    if legibility["agents_md_too_long"]:
        plan.append(
            {
                "priority": "P1",
                "title": "Reduce AGENTS.md size and keep TOC-style map",
                "items": {
                    "agents_md_lines": legibility["agents_md_lines"],
                    "recommended_max": legibility["agents_md_recommended_max"],
                },
            }
        )

    if constraints["missing"]:
        plan.append(
            {
                "priority": "P1",
                "title": "Add mechanical constraints (lint/schema/CI)",
                "items": {"missing_constraint_signals": constraints["missing"]},
            }
        )

    if feedback["missing"]:
        plan.append(
            {
                "priority": "P2",
                "title": "Strengthen feedback loops (tests/check scripts)",
                "items": {"missing_feedback_signals": feedback["missing"]},
            }
        )

    if control_loop["missing"]:
        plan.append(
            {
                "priority": "P2",
                "title": "Reinforce control loop tooling",
                "items": {"missing_control_loop_signals": control_loop["missing"]},
            }
        )

    if command_coverage["claude_missing"] or command_coverage["cursor_missing"]:
        plan.append(
            {
                "priority": "P0",
                "title": "Complete core slash-command coverage",
                "items": {
                    "claude_missing": command_coverage["claude_missing"],
                    "cursor_missing": command_coverage["cursor_missing"],
                },
            }
        )

    if (
        command_coverage["claude_provenance_missing"]
        or command_coverage["cursor_provenance_missing"]
    ):
        plan.append(
            {
                "priority": "P1",
                "title": "Add Trellis source markers to act commands",
                "items": {
                    "claude_provenance_missing": command_coverage[
                        "claude_provenance_missing"
                    ],
                    "cursor_provenance_missing": command_coverage[
                        "cursor_provenance_missing"
                    ],
                },
            }
        )

    return plan


def evaluate_strict_failures(
    result: AuditResult,
    min_legibility_score: int,
    min_constraints_score: int,
    min_feedback_score: int,
    min_control_loop_score: int,
    min_command_coverage_score: int,
    fail_on_agents_too_long: bool,
) -> list[str]:
    failures: list[str] = []

    if result.missing_required_dirs:
        failures.append("Missing required directories")
    if result.missing_required_files:
        failures.append("Missing required files")
    if result.missing_workflow_files:
        failures.append("Missing workflow-critical files")

    legibility = result.harness_readiness["legibility"]
    constraints = result.harness_readiness["constraints"]
    feedback = result.harness_readiness["feedback"]
    control_loop = result.harness_readiness["control_loop"]
    command_coverage = result.harness_readiness["command_coverage"]

    if legibility["score"] < min_legibility_score:
        failures.append(
            f"Legibility score below threshold ({legibility['score']} < {min_legibility_score})"
        )
    if constraints["score"] < min_constraints_score:
        failures.append(
            f"Constraints score below threshold ({constraints['score']} < {min_constraints_score})"
        )
    if feedback["score"] < min_feedback_score:
        failures.append(
            f"Feedback score below threshold ({feedback['score']} < {min_feedback_score})"
        )
    if control_loop["score"] < min_control_loop_score:
        failures.append(
            f"Control-loop score below threshold ({control_loop['score']} < {min_control_loop_score})"
        )
    if command_coverage["score"] < min_command_coverage_score:
        failures.append(
            "Slash command coverage below threshold "
            f"({command_coverage['score']} < {min_command_coverage_score})"
        )
    if (
        command_coverage["claude_provenance_missing"]
        or command_coverage["cursor_provenance_missing"]
    ):
        failures.append("Some act commands are missing Trellis source markers")

    if fail_on_agents_too_long and legibility["agents_md_too_long"]:
        failures.append(
            "AGENTS.md exceeds recommended line count "
            f"({legibility['agents_md_lines']} > {legibility['agents_md_recommended_max']})"
        )

    return failures


def build_guided_next_steps(root: Path, result: AuditResult) -> list[dict[str, str]]:
    root_str = str(root)
    steps: list[dict[str, str]] = []

    steps.append(
        {
            "phase": "assess",
            "condition": "always",
            "goal": "Collect full gap snapshot with readiness dimensions",
            "command": f'python skills/agent-workspace-governance/scripts/audit_repo_structure.py --root "{root_str}" --json',
        }
    )

    if (
        result.missing_required_dirs
        or result.missing_required_files
        or result.missing_workflow_files
    ):
        steps.append(
            {
                "phase": "stabilize",
                "condition": "required/workflow gaps exist",
                "goal": "Apply non-destructive baseline scaffolding",
                "command": f'python skills/agent-workspace-governance/scripts/audit_repo_structure.py --root "{root_str}" --apply --output docs/reports/repo-structure-audit-after-apply.md',
            }
        )

    steps.append(
        {
            "phase": "reinforce",
            "condition": "recommended gaps or low readiness remain",
            "goal": "Run iterative hardening loop until convergence",
            "command": f'python skills/agent-workspace-governance/scripts/reinforcement_loop.py --root "{root_str}" --max-rounds 3 --apply --run-validate --json',
        }
    )

    steps.append(
        {
            "phase": "gate",
            "condition": "before merge/ship",
            "goal": "Enforce strict quality gate",
            "command": f'python skills/agent-workspace-governance/scripts/audit_repo_structure.py --root "{root_str}" --strict --fail-on-agents-too-long --min-legibility-score 80 --min-constraints-score 60 --min-feedback-score 60 --min-control-loop-score 90 --min-command-coverage-score 90 --json',
        }
    )

    old_claude = [
        root / ".claude" / "commands" / "trellis" / f"{name}.md"
        for name in CORE_SLASH_COMMANDS
    ]
    old_cursor = [
        root / ".cursor" / "commands" / f"trellis-{name}.md"
        for name in CORE_SLASH_COMMANDS
    ]
    if any(p.exists() for p in old_claude + old_cursor):
        steps.append(
            {
                "phase": "migrate-prefix",
                "condition": "legacy trellis-prefixed commands exist",
                "goal": "Rename slash command prefix to act and preserve Trellis provenance",
                "command": f'python skills/agent-workspace-governance/scripts/rename_trellis_to_act_commands.py --root "{root_str}" --overwrite --remove-old --scaffold-missing --json',
            }
        )

    return steps


def find_move_suggestions(root: Path, missing_files: list[str]) -> list[dict[str, str]]:
    suggestions: list[dict[str, str]] = []
    for target in missing_files:
        target_name = Path(target).name
        candidate = root / target_name
        if candidate.exists() and candidate.is_file() and target != target_name:
            suggestions.append({"from": str(candidate.relative_to(root)), "to": target})
    return suggestions


def apply_scaffold(
    root: Path,
    missing_required_dirs: list[str],
    missing_required_files: list[str],
    missing_recommended_dirs: list[str],
    missing_workflow_files: list[str],
) -> list[str]:
    created: list[str] = []

    for rel in missing_required_dirs + missing_recommended_dirs:
        path = root / rel
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            created.append(rel + "/")

    for rel in missing_required_files:
        path = root / rel
        if not path.parent.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            created.append(str(path.parent.relative_to(root)) + "/")
        if not path.exists():
            path.write_text(
                f"# Placeholder\n\nGenerated by audit_repo_structure.py for `{rel}`.\n",
                encoding="utf-8",
            )
            created.append(rel)

    for rel in missing_workflow_files:
        path = root / rel
        if not path.parent.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            created.append(str(path.parent.relative_to(root)) + "/")
        if not path.exists():
            path.write_text(
                f"# Placeholder\n\nGenerated by audit_repo_structure.py for workflow file `{rel}`.\n",
                encoding="utf-8",
            )
            created.append(rel)

    # Scaffold core slash commands for Claude and Cursor.
    claude_expected, cursor_expected = expected_command_paths()
    for rel in claude_expected:
        path = root / rel
        if not path.parent.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            created.append(str(path.parent.relative_to(root)) + "/")
        if not path.exists():
            command_name = Path(rel).stem
            path.write_text(
                build_command_stub(command_name, "claude"), encoding="utf-8"
            )
            created.append(rel)

    for rel in cursor_expected:
        path = root / rel
        if not path.parent.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            created.append(str(path.parent.relative_to(root)) + "/")
        if not path.exists():
            command_name = Path(rel).stem.replace("act-", "")
            path.write_text(
                build_command_stub(command_name, "cursor"), encoding="utf-8"
            )
            created.append(rel)

    return created


def build_markdown_report(result: AuditResult) -> str:
    lines: list[str] = []
    lines.append("# Repository Structure Audit")
    lines.append("")
    lines.append(f"- Root: `{result.root}`")
    lines.append(f"- Missing required dirs: {len(result.missing_required_dirs)}")
    lines.append(f"- Missing required files: {len(result.missing_required_files)}")
    lines.append(f"- Missing recommended dirs: {len(result.missing_recommended_dirs)}")
    lines.append(f"- Missing workflow files: {len(result.missing_workflow_files)}")
    lines.append("")
    lines.append("## Harness Readiness")
    lines.append("")
    lines.append(
        f"- Legibility score: {result.harness_readiness['legibility']['score']}"
    )
    lines.append(
        f"- Constraints score: {result.harness_readiness['constraints']['score']}"
    )
    lines.append(f"- Feedback score: {result.harness_readiness['feedback']['score']}")
    lines.append(
        f"- Control-loop score: {result.harness_readiness['control_loop']['score']}"
    )
    lines.append(
        f"- Slash-command coverage score: {result.harness_readiness['command_coverage']['score']}"
    )
    lines.append("")
    lines.append(
        f"- AGENTS.md lines: {result.harness_readiness['legibility']['agents_md_lines']}"
    )
    lines.append(
        "- AGENTS.md too long: "
        + (
            "yes"
            if result.harness_readiness["legibility"]["agents_md_too_long"]
            else "no"
        )
    )
    lines.append("")

    lines.append("## Missing Required Directories")
    lines.append("")
    if result.missing_required_dirs:
        lines.extend([f"- `{x}/`" for x in result.missing_required_dirs])
    else:
        lines.append("- (none)")
    lines.append("")

    lines.append("## Missing Required Files")
    lines.append("")
    if result.missing_required_files:
        lines.extend([f"- `{x}`" for x in result.missing_required_files])
    else:
        lines.append("- (none)")
    lines.append("")

    lines.append("## Missing Recommended Directories")
    lines.append("")

    lines.append("## Missing Workflow Files")
    lines.append("")

    lines.append("## Harness Readiness Gaps")
    lines.append("")
    lines.append("- Legibility missing:")
    if result.harness_readiness["legibility"]["missing"]:
        lines.extend(
            [f"  - `{x}`" for x in result.harness_readiness["legibility"]["missing"]]
        )
    else:
        lines.append("  - (none)")
    lines.append("- Constraints missing:")
    if result.harness_readiness["constraints"]["missing"]:
        lines.extend(
            [f"  - `{x}`" for x in result.harness_readiness["constraints"]["missing"]]
        )
    else:
        lines.append("  - (none)")
    lines.append("- Feedback missing:")
    if result.harness_readiness["feedback"]["missing"]:
        lines.extend(
            [f"  - `{x}`" for x in result.harness_readiness["feedback"]["missing"]]
        )
    else:
        lines.append("  - (none)")
    lines.append("- Control-loop missing:")
    if result.harness_readiness["control_loop"]["missing"]:
        lines.extend(
            [f"  - `{x}`" for x in result.harness_readiness["control_loop"]["missing"]]
        )
    else:
        lines.append("  - (none)")
    lines.append("- Slash-command coverage missing (Claude):")
    if result.harness_readiness["command_coverage"]["claude_missing"]:
        lines.extend(
            [
                f"  - `{x}`"
                for x in result.harness_readiness["command_coverage"]["claude_missing"]
            ]
        )
    else:
        lines.append("  - (none)")
    lines.append("- Slash-command coverage missing (Cursor):")
    if result.harness_readiness["command_coverage"]["cursor_missing"]:
        lines.extend(
            [
                f"  - `{x}`"
                for x in result.harness_readiness["command_coverage"]["cursor_missing"]
            ]
        )
    else:
        lines.append("  - (none)")
    lines.append("- Slash-command provenance missing (Claude):")
    if result.harness_readiness["command_coverage"]["claude_provenance_missing"]:
        lines.extend(
            [
                f"  - `{x}`"
                for x in result.harness_readiness["command_coverage"][
                    "claude_provenance_missing"
                ]
            ]
        )
    else:
        lines.append("  - (none)")
    lines.append("- Slash-command provenance missing (Cursor):")
    if result.harness_readiness["command_coverage"]["cursor_provenance_missing"]:
        lines.extend(
            [
                f"  - `{x}`"
                for x in result.harness_readiness["command_coverage"][
                    "cursor_provenance_missing"
                ]
            ]
        )
    else:
        lines.append("  - (none)")
    lines.append("")
    if result.missing_workflow_files:
        lines.extend([f"- `{x}`" for x in result.missing_workflow_files])
    else:
        lines.append("- (none)")
    lines.append("")
    if result.missing_recommended_dirs:
        lines.extend([f"- `{x}/`" for x in result.missing_recommended_dirs])
    else:
        lines.append("- (none)")
    lines.append("")

    lines.append("## Move Suggestions")
    lines.append("")
    if result.move_suggestions:
        for item in result.move_suggestions:
            lines.append(f"- Move `{item['from']}` -> `{item['to']}`")
    else:
        lines.append("- (none)")
    lines.append("")

    lines.append("## Created Paths")
    lines.append("")
    if result.created_paths:
        lines.extend([f"- `{x}`" for x in result.created_paths])
    else:
        lines.append("- (none, dry-run)")

    lines.append("")
    lines.append("## Action Plan")
    lines.append("")
    if result.action_plan:
        for item in result.action_plan:
            lines.append(f"- [{item['priority']}] {item['title']}")
    else:
        lines.append("- (none)")

    lines.append("")
    lines.append("## Strict Failures")
    lines.append("")
    if result.strict_failures:
        lines.extend([f"- {x}" for x in result.strict_failures])
    else:
        lines.append("- (none)")

    lines.append("")
    lines.append("## Guided Next Steps")
    lines.append("")
    for step in result.guided_next_steps:
        lines.append(
            f"- [{step['phase']}] {step['goal']} (condition: {step['condition']})"
        )
        lines.append(f"  - command: `{step['command']}`")

    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit and scaffold repository structure to target layout."
    )
    parser.add_argument("--root", default=".", help="Repository root path")
    parser.add_argument(
        "--apply", action="store_true", help="Create missing dirs/files placeholders"
    )
    parser.add_argument(
        "--output", default=None, help="Write markdown report to file path"
    )
    parser.add_argument("--json", action="store_true", help="Print JSON output")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero when strict quality gates are not met",
    )
    parser.add_argument("--min-legibility-score", type=int, default=70)
    parser.add_argument("--min-constraints-score", type=int, default=40)
    parser.add_argument("--min-feedback-score", type=int, default=40)
    parser.add_argument("--min-control-loop-score", type=int, default=80)
    parser.add_argument("--min-command-coverage-score", type=int, default=80)
    parser.add_argument(
        "--fail-on-agents-too-long",
        action="store_true",
        help="Fail strict mode when AGENTS.md exceeds recommended length",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = Path(args.root).resolve()

    missing_required_dirs = exists_all(root, REQUIRED_DIRS)
    missing_required_files = exists_all(root, REQUIRED_FILES)
    missing_recommended_dirs = exists_all(root, RECOMMENDED_DIRS)
    missing_workflow_files = exists_all(root, WORKFLOW_REQUIRED_FILES)
    move_suggestions = find_move_suggestions(root, missing_required_files)
    harness_readiness = build_harness_readiness(root)

    created_paths: list[str] = []
    if args.apply:
        created_paths = apply_scaffold(
            root,
            missing_required_dirs=missing_required_dirs,
            missing_required_files=missing_required_files,
            missing_recommended_dirs=missing_recommended_dirs,
            missing_workflow_files=missing_workflow_files,
        )
        # Refresh after apply
        missing_required_dirs = exists_all(root, REQUIRED_DIRS)
        missing_required_files = exists_all(root, REQUIRED_FILES)
        missing_recommended_dirs = exists_all(root, RECOMMENDED_DIRS)
        missing_workflow_files = exists_all(root, WORKFLOW_REQUIRED_FILES)
        move_suggestions = find_move_suggestions(root, missing_required_files)
        harness_readiness = build_harness_readiness(root)

    action_plan = build_action_plan(
        missing_required_dirs=missing_required_dirs,
        missing_required_files=missing_required_files,
        missing_workflow_files=missing_workflow_files,
        missing_recommended_dirs=missing_recommended_dirs,
        harness_readiness=harness_readiness,
    )

    result = AuditResult(
        root=str(root),
        missing_required_dirs=missing_required_dirs,
        missing_required_files=missing_required_files,
        missing_recommended_dirs=missing_recommended_dirs,
        missing_workflow_files=missing_workflow_files,
        harness_readiness=harness_readiness,
        action_plan=action_plan,
        strict_failures=[],
        guided_next_steps=[],
        move_suggestions=move_suggestions,
        created_paths=created_paths,
    )

    strict_failures = evaluate_strict_failures(
        result,
        min_legibility_score=args.min_legibility_score,
        min_constraints_score=args.min_constraints_score,
        min_feedback_score=args.min_feedback_score,
        min_control_loop_score=args.min_control_loop_score,
        min_command_coverage_score=args.min_command_coverage_score,
        fail_on_agents_too_long=args.fail_on_agents_too_long,
    )
    result.strict_failures = strict_failures
    result.guided_next_steps = build_guided_next_steps(root, result)

    markdown = build_markdown_report(result)
    if args.output:
        output = Path(args.output)
        if not output.is_absolute():
            output = root / output
        if not output.parent.exists():
            output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(markdown, encoding="utf-8")

    payload = {
        "root": result.root,
        "missing_required_dirs": result.missing_required_dirs,
        "missing_required_files": result.missing_required_files,
        "missing_recommended_dirs": result.missing_recommended_dirs,
        "missing_workflow_files": result.missing_workflow_files,
        "harness_readiness": result.harness_readiness,
        "action_plan": result.action_plan,
        "strict_failures": result.strict_failures,
        "guided_next_steps": result.guided_next_steps,
        "move_suggestions": result.move_suggestions,
        "created_paths": result.created_paths,
    }

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(markdown)

    if args.strict and strict_failures:
        sys.exit(2)


if __name__ == "__main__":
    main()
