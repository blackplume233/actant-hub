#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path


def run_cmd(
    script: Path, args: list[str], expect_ok: bool = True
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["python", str(script), *args],
        text=True,
        capture_output=True,
        check=False,
    )
    if expect_ok and result.returncode != 0:
        raise RuntimeError(
            f"Command failed: {args}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )
    return result


def assert_base_files(workspace: Path) -> None:
    required = [
        "README.md",
        "todo.md",
        "notes.md",
        "decisions.md",
        "handoff.md",
        ".workspace-meta.json",
    ]
    for file_name in required:
        file_path = workspace / file_name
        if not file_path.exists():
            raise AssertionError(f"Missing base file: {file_path}")


def main() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    create_script = (
        repo_root
        / "skills"
        / "agent-workspace-governance"
        / "scripts"
        / "create_agent_workspace.py"
    )
    audit_script = (
        repo_root
        / "skills"
        / "agent-workspace-governance"
        / "scripts"
        / "audit_repo_structure.py"
    )
    loop_script = (
        repo_root
        / "skills"
        / "agent-workspace-governance"
        / "scripts"
        / "reinforcement_loop.py"
    )
    rename_script = (
        repo_root
        / "skills"
        / "agent-workspace-governance"
        / "scripts"
        / "rename_trellis_to_act_commands.py"
    )
    target_spec = (
        repo_root
        / "skills"
        / "agent-workspace-governance"
        / "references"
        / "target-structure.md"
    )

    summary: dict[str, str] = {}

    # Syntax check
    subprocess.run(
        [
            "python",
            "-m",
            "py_compile",
            str(create_script),
            str(audit_script),
            str(loop_script),
            str(rename_script),
        ],
        check=True,
    )
    if not target_spec.exists():
        raise AssertionError("target-structure.md is missing")
    summary["py_compile"] = "pass"
    summary["target_structure_spec"] = "pass"

    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)

        # Mode matrix on generic profile
        created = run_cmd(
            create_script,
            [
                "--name",
                "demo workspace",
                "--root",
                str(root),
                "--profile",
                "generic",
                "--on-exist",
                "fail",
            ],
        )
        payload = json.loads(created.stdout)
        workspace = Path(payload["workspace"])
        assert payload["action"] == "created"
        assert_base_files(workspace)

        failed = run_cmd(
            create_script,
            [
                "--name",
                "demo workspace",
                "--root",
                str(root),
                "--profile",
                "generic",
                "--on-exist",
                "fail",
            ],
            expect_ok=False,
        )
        if failed.returncode == 0 or "Workspace already exists" not in failed.stderr:
            raise AssertionError("fail mode did not reject existing workspace")

        reused = run_cmd(
            create_script,
            [
                "--name",
                "demo workspace",
                "--root",
                str(root),
                "--profile",
                "generic",
                "--on-exist",
                "reuse",
            ],
        )
        if json.loads(reused.stdout)["action"] != "reused":
            raise AssertionError("reuse mode not working")

        profile_expectations = {
            "npm": {
                "files": ["checklist-npm.md", "references/npm-context.md"],
                "dirs": ["artifacts/test-reports", "artifacts/build-logs"],
            },
            "npm-monorepo": {
                "files": [
                    "checklist-npm-monorepo.md",
                    "references/npm-monorepo-context.md",
                    "references/package-impact-map.md",
                ],
                "dirs": ["artifacts/package-graphs", "packages"],
            },
            "unreal": {
                "files": ["checklist-unreal.md", "references/unreal-context.md"],
                "dirs": [
                    "artifacts/blueprints",
                    "artifacts/datatables",
                    "artifacts/build-logs",
                ],
            },
            "unreal-cpp": {
                "files": [
                    "checklist-unreal-cpp.md",
                    "references/unreal-cpp-context.md",
                ],
                "dirs": [
                    "artifacts/crash-dumps",
                    "artifacts/symbol-traces",
                    "artifacts/build-logs",
                ],
            },
        }

        for profile, expected in profile_expectations.items():
            result = run_cmd(
                create_script,
                [
                    "--name",
                    f"{profile} demo",
                    "--root",
                    str(root),
                    "--profile",
                    profile,
                    "--on-exist",
                    "fail",
                ],
            )
            data = json.loads(result.stdout)
            ws = Path(data["workspace"])
            assert_base_files(ws)
            meta = json.loads((ws / ".workspace-meta.json").read_text(encoding="utf-8"))
            if meta.get("profile") != profile:
                raise AssertionError(f"metadata profile mismatch: {profile}")

            for rel in expected["files"]:
                if not (ws / rel).exists():
                    raise AssertionError(f"missing profile file for {profile}: {rel}")

            for rel in expected["dirs"]:
                if not (ws / rel).is_dir():
                    raise AssertionError(f"missing profile dir for {profile}: {rel}")

        tracked = run_cmd(
            create_script,
            [
                "--name",
                "tracked demo",
                "--root",
                str(root),
                "--tracked",
                "--profile",
                "npm-monorepo",
                "--with-trellis-task",
                "--on-exist",
                "fail",
            ],
        )
        tracked_payload = json.loads(tracked.stdout)
        task_file = Path(tracked_payload["task"])
        if not task_file.exists():
            raise AssertionError("task.json not generated")

        task_json = json.loads(task_file.read_text(encoding="utf-8"))
        required_keys = [
            "id",
            "name",
            "title",
            "status",
            "priority",
            "creator",
            "assignee",
            "createdAt",
            "next_action",
        ]
        for key in required_keys:
            if key not in task_json:
                raise AssertionError(f"missing task field: {key}")

        summary["mode_matrix"] = "pass"
        summary["profile_matrix"] = "pass"
        summary["trellis_task_schema"] = "pass"

        # Audit dry-run and apply behavior
        dry = run_cmd(
            audit_script,
            ["--root", str(root), "--json"],
        )
        dry_payload = json.loads(dry.stdout)
        if "missing_required_dirs" not in dry_payload:
            raise AssertionError("audit dry-run payload missing required keys")
        if "missing_workflow_files" not in dry_payload:
            raise AssertionError("audit dry-run payload missing workflow keys")
        if "harness_readiness" not in dry_payload:
            raise AssertionError("audit dry-run payload missing harness readiness")
        if "command_coverage" not in dry_payload["harness_readiness"]:
            raise AssertionError("harness readiness missing command coverage")
        if "guided_next_steps" not in dry_payload:
            raise AssertionError("audit dry-run payload missing guided steps")
        if (
            not isinstance(dry_payload["guided_next_steps"], list)
            or not dry_payload["guided_next_steps"]
        ):
            raise AssertionError("guided_next_steps should be a non-empty list")
        legibility = dry_payload["harness_readiness"].get("legibility", {})
        if "agents_md_lines" not in legibility:
            raise AssertionError("harness readiness missing AGENTS metadata")

        applied = run_cmd(
            audit_script,
            [
                "--root",
                str(root),
                "--apply",
                "--json",
            ],
        )
        applied_payload = json.loads(applied.stdout)
        if applied_payload["missing_required_dirs"]:
            raise AssertionError("audit apply did not scaffold required directories")
        if applied_payload["missing_required_files"]:
            raise AssertionError("audit apply did not scaffold required files")
        if applied_payload["missing_workflow_files"]:
            raise AssertionError("audit apply did not scaffold workflow files")
        summary["audit_dry_run"] = "pass"
        summary["audit_apply"] = "pass"
        summary["harness_readiness"] = "pass"

        # Strict mode should fail before apply and pass with relaxed thresholds after apply
        strict_fail = run_cmd(
            audit_script,
            ["--root", str(root), "--strict", "--json"],
            expect_ok=False,
        )
        if strict_fail.returncode == 0:
            raise AssertionError("strict mode should fail on uninitialized structure")

        strict_pass = run_cmd(
            audit_script,
            [
                "--root",
                str(root),
                "--apply",
                "--strict",
                "--min-legibility-score",
                "0",
                "--min-constraints-score",
                "0",
                "--min-feedback-score",
                "0",
                "--min-control-loop-score",
                "0",
                "--min-command-coverage-score",
                "0",
                "--json",
            ],
        )
        strict_payload = json.loads(strict_pass.stdout)
        if "strict_failures" not in strict_payload:
            raise AssertionError("strict payload missing strict_failures")
        if "guided_next_steps" not in strict_payload:
            raise AssertionError("strict payload missing guided_next_steps")
        summary["strict_mode"] = "pass"

        # Prefix migration should run and produce JSON summary
        migrated = run_cmd(
            rename_script,
            ["--root", str(root), "--scaffold-missing", "--json"],
        )
        migrated_payload = json.loads(migrated.stdout)
        if "core_commands" not in migrated_payload:
            raise AssertionError("prefix migration summary missing core_commands")
        summary["prefix_migration"] = "pass"

        # Reinforcement loop dry-run should execute and emit report
        loop = run_cmd(
            loop_script,
            [
                "--root",
                str(root),
                "--max-rounds",
                "2",
                "--apply",
                "--json",
            ],
        )
        loop_payload = json.loads(loop.stdout)
        report = Path(loop_payload.get("report", ""))
        if not report.exists():
            raise AssertionError("reinforcement loop report missing")
        summary["reinforcement_loop"] = "pass"

    print(
        json.dumps({"status": "pass", "checks": summary}, ensure_ascii=False, indent=2)
    )


if __name__ == "__main__":
    main()
