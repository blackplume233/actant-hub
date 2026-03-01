#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class CreateResult:
    workspace_path: Path
    action: str
    created_files: list[str]
    created_dirs: list[str]
    task_path: Path | None


def slugify(name: str) -> str:
    text = name.strip()
    text = re.sub(r"[\\/\s]+", "-", text)
    text = re.sub(r"[^\w\-.]+", "-", text, flags=re.UNICODE)
    text = re.sub(r"-+", "-", text).strip("-._")
    if text:
        return text
    return f"workspace-{datetime.now().strftime('%Y%m%d-%H%M%S')}"


def read_developer_name(repo_root: Path) -> str:
    dev_file = repo_root / ".trellis" / ".developer"
    if not dev_file.exists():
        return "agent"

    for line in dev_file.read_text(encoding="utf-8").splitlines():
        if line.startswith("name="):
            value = line.split("=", 1)[1].strip()
            return value or "agent"
    return "agent"


def build_readme(title: str, slug: str, now: str, profile: str) -> str:
    profile_hint = {
        "generic": "Generic engineering workspace for mixed stacks.",
        "npm": "NPM/Node-oriented workspace for package/app tasks.",
        "npm-monorepo": "NPM monorepo workspace for multi-package and workspace-level changes.",
        "unreal": "Unreal Engine-oriented workspace for assets, gameplay, and build/debug tasks.",
        "unreal-cpp": "Unreal C++ workspace for module/build/runtime-focused changes.",
    }[profile]

    return f"""# {title} Agent Workspace

> Created at: {now}
> Workspace ID: `{slug}`
> Profile: `{profile}`

{profile_hint}

## Goal

- Define the target outcome for this topic.

## Scope

- In scope:
- Out of scope:

## Acceptance Criteria

- [ ]

## References

- Related issue/PR:
- Related docs:

## Execution Notes

- Keep changes small and verifiable.
- Record key decisions in `decisions.md`.
"""


def build_todo() -> str:
    return """# TODO

- [ ] Clarify requirements
- [ ] Implement first milestone
- [ ] Verify and summarize
"""


def build_notes() -> str:
    return """# Notes

Capture exploration results, command outputs, and useful snippets.
"""


def build_decisions() -> str:
    return """# Decisions

## YYYY-MM-DD

- Decision:
- Reason:
- Impact:
"""


def build_handoff() -> str:
    return """# Handoff

## Current Status

-

## Next Actions

1.

## Risks / Open Questions

-
"""


def profile_files(profile: str) -> dict[str, str]:
    if profile == "npm":
        return {
            "checklist-npm.md": """# NPM Checklist

- [ ] Confirm package manager (npm/pnpm/yarn)
- [ ] Confirm Node.js version and runtime constraints
- [ ] Define scripts to run (lint/test/build)
- [ ] Verify lockfile/update policy
- [ ] Document release impact and semver decision
""",
            "references/npm-context.md": """# NPM Context

- package(s) impacted:
- expected commands:
- env variables:
- release notes impact:
""",
        }

    if profile == "npm-monorepo":
        return {
            "checklist-npm-monorepo.md": """# NPM Monorepo Checklist

- [ ] Confirm workspace manager and root scripts
- [ ] Identify affected packages and dependency graph
- [ ] Define package-level and root-level test/build scope
- [ ] Validate lockfile and version bump strategy
- [ ] Document release order and rollback plan
""",
            "references/npm-monorepo-context.md": """# NPM Monorepo Context

- workspace manager:
- affected packages:
- dependency impact:
- commands by package:
- publish/release notes:
""",
            "references/package-impact-map.md": """# Package Impact Map

| Package | Change Type | Downstream Impact |
|---------|-------------|-------------------|
|         |             |                   |
""",
        }

    if profile == "unreal":
        return {
            "checklist-unreal.md": """# Unreal Checklist

- [ ] Confirm UE version and target platform
- [ ] Confirm module/asset scope
- [ ] Capture repro steps and expected in-editor behavior
- [ ] Record build logs and runtime diagnostics
- [ ] Note rollback plan for risky content changes
""",
            "references/unreal-context.md": """# Unreal Context

- project path:
- map/level:
- related blueprint/assets:
- build target/config:
- observed errors/logs:
""",
        }

    if profile == "unreal-cpp":
        return {
            "checklist-unreal-cpp.md": """# Unreal C++ Checklist

- [ ] Confirm UE version, target, and build configuration
- [ ] Identify affected module(s) and Build.cs dependencies
- [ ] Capture compile log and first failing symbol/file
- [ ] Verify runtime/thread assumptions and ownership boundaries
- [ ] Define validation map, reproduction steps, and rollback plan
""",
            "references/unreal-cpp-context.md": """# Unreal C++ Context

- engine version:
- project path:
- module(s):
- target/config:
- first failing compile log:
- expected runtime behavior:
""",
        }

    return {}


def profile_dirs(profile: str) -> tuple[str, ...]:
    if profile == "npm":
        return (
            "artifacts",
            "deliverables",
            "scratch",
            "artifacts/test-reports",
            "artifacts/build-logs",
            "references",
        )

    if profile == "unreal":
        return (
            "artifacts",
            "deliverables",
            "scratch",
            "artifacts/blueprints",
            "artifacts/datatables",
            "artifacts/build-logs",
            "references",
        )

    if profile == "npm-monorepo":
        return (
            "artifacts",
            "deliverables",
            "scratch",
            "artifacts/test-reports",
            "artifacts/build-logs",
            "artifacts/package-graphs",
            "references",
            "packages",
        )

    if profile == "unreal-cpp":
        return (
            "artifacts",
            "deliverables",
            "scratch",
            "artifacts/build-logs",
            "artifacts/crash-dumps",
            "artifacts/symbol-traces",
            "references",
        )

    return ("artifacts", "deliverables", "scratch")


def ensure_files(
    target: Path,
    title: str,
    slug: str,
    now: str,
    profile: str,
    append_only: bool,
) -> tuple[list[str], list[str]]:
    created_files: list[str] = []
    created_dirs: list[str] = []

    for folder in profile_dirs(profile):
        d = target / folder
        if not d.exists():
            d.mkdir(parents=True, exist_ok=True)
            created_dirs.append(str(d))

    files = {
        "README.md": build_readme(title=title, slug=slug, now=now, profile=profile),
        "todo.md": build_todo(),
        "notes.md": build_notes(),
        "decisions.md": build_decisions(),
        "handoff.md": build_handoff(),
        ".workspace-meta.json": json.dumps(
            {
                "id": slug,
                "title": title,
                "profile": profile,
                "created_at": now,
                "layout": [
                    "README.md",
                    "todo.md",
                    "notes.md",
                    "decisions.md",
                    "handoff.md",
                    "artifacts/",
                    "deliverables/",
                    "scratch/",
                ],
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
    }

    files.update(profile_files(profile))

    for rel, content in files.items():
        p = target / rel
        if append_only and p.exists():
            continue
        if not p.exists() or not append_only:
            p.write_text(content, encoding="utf-8")
            created_files.append(str(p))

    return created_files, created_dirs


def create_trellis_task(repo_root: Path, slug: str, title: str) -> Path:
    today = datetime.now().strftime("%m-%d")
    today_full = datetime.now().strftime("%Y-%m-%d")
    task_dir = repo_root / ".trellis" / "tasks" / f"{today}-{slug}"
    task_dir.mkdir(parents=True, exist_ok=True)

    developer = read_developer_name(repo_root)
    payload = {
        "id": slug,
        "name": slug,
        "title": title,
        "description": "",
        "status": "planning",
        "dev_type": None,
        "scope": None,
        "priority": "P2",
        "creator": developer,
        "assignee": developer,
        "createdAt": today_full,
        "completedAt": None,
        "branch": None,
        "base_branch": "master",
        "worktree_path": None,
        "current_phase": 0,
        "next_action": [
            {"phase": 1, "action": "implement"},
            {"phase": 2, "action": "check"},
            {"phase": 3, "action": "finish"},
            {"phase": 4, "action": "create-pr"},
        ],
        "commit": None,
        "pr_url": None,
        "subtasks": [],
        "relatedFiles": [],
        "notes": "Created by agent-workspace-governance skill",
    }

    task_file = task_dir / "task.json"
    task_file.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return task_file


def run(args: argparse.Namespace) -> CreateResult:
    repo_root = Path(args.root).resolve()
    base = repo_root / "topics" if args.tracked else repo_root / "topics" / ".local"
    base.mkdir(parents=True, exist_ok=True)

    slug = slugify(args.name)
    title = args.title or args.name
    profile = args.profile
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    target = base / slug

    if target.exists():
        if args.on_exist == "fail":
            raise FileExistsError(f"Workspace already exists: {target}")
        if args.on_exist == "reuse":
            created_files, created_dirs = [], []
            task_path = (
                create_trellis_task(repo_root, slug, title)
                if args.with_trellis_task
                else None
            )
            return CreateResult(
                target, "reused", created_files, created_dirs, task_path
            )
        if args.on_exist == "append":
            created_files, created_dirs = ensure_files(
                target, title, slug, now, profile, append_only=True
            )
            task_path = (
                create_trellis_task(repo_root, slug, title)
                if args.with_trellis_task
                else None
            )
            return CreateResult(
                target, "appended", created_files, created_dirs, task_path
            )
        if args.on_exist == "archive":
            archived = target.with_name(
                f"{target.name}__archived_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
            target.rename(archived)
        elif args.on_exist == "overwrite":
            shutil.rmtree(target)

    target.mkdir(parents=True, exist_ok=True)
    created_files, created_dirs = ensure_files(
        target, title, slug, now, profile, append_only=False
    )
    task_path = (
        create_trellis_task(repo_root, slug, title) if args.with_trellis_task else None
    )
    return CreateResult(target, "created", created_files, created_dirs, task_path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create agent workspace directory with governance-ready scaffolding."
    )
    parser.add_argument("--name", required=True, help="Workspace name or topic.")
    parser.add_argument("--title", default=None, help="Display title in templates.")
    parser.add_argument(
        "--profile",
        choices=["generic", "npm", "npm-monorepo", "unreal", "unreal-cpp"],
        default="generic",
        help="Template profile for workspace structure and checklists.",
    )
    parser.add_argument(
        "--tracked",
        action="store_true",
        help="Create under topics/ instead of topics/.local/.",
    )
    parser.add_argument(
        "--on-exist",
        choices=["fail", "reuse", "append", "archive", "overwrite"],
        default="fail",
        help="Behavior when workspace already exists.",
    )
    parser.add_argument(
        "--with-trellis-task",
        action="store_true",
        help="Also create .trellis/tasks/MM-DD-<slug>/task.json",
    )
    parser.add_argument("--root", default=".", help="Repository root path.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = run(args)
    output = {
        "workspace": str(result.workspace_path),
        "action": result.action,
        "created_files": result.created_files,
        "created_dirs": result.created_dirs,
        "task": str(result.task_path) if result.task_path else None,
    }
    print(json.dumps(output, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
