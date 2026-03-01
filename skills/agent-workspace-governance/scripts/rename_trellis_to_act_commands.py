#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


CORE_COMMANDS = [
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


def ensure_marker(content: str) -> str:
    marker = "> Source: Trellis workflow (renamed prefix to `act`)"
    if "Source: Trellis" in content:
        return content
    lines = content.splitlines()
    if lines and lines[0].startswith("# "):
        title = lines[0]
        rest = "\n".join(lines[1:]).lstrip("\n")
        return f"{title}\n\n{marker}\n\n{rest}".rstrip() + "\n"
    return f"{marker}\n\n{content}".rstrip() + "\n"


def build_stub(command_name: str, platform: str) -> str:
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


def rewrite_prefixes(content: str) -> str:
    updated = content.replace("/trellis:", "/act:")
    updated = updated.replace("trellis-", "act-")
    updated = updated.replace(".claude/commands/trellis/", ".claude/commands/act/")
    updated = updated.replace(".cursor/commands/trellis-", ".cursor/commands/act-")
    return updated


def migrate_file(src: Path, dst: Path, overwrite: bool) -> tuple[bool, str]:
    if not src.exists():
        return False, "source_missing"
    if dst.exists() and not overwrite:
        return False, "target_exists"

    content = src.read_text(encoding="utf-8", errors="ignore")
    content = rewrite_prefixes(content)
    content = ensure_marker(content)

    if not dst.parent.exists():
        dst.parent.mkdir(parents=True, exist_ok=True)

    dst.write_text(content, encoding="utf-8")
    return True, "migrated"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Rename slash-command prefix from trellis to act with Trellis provenance markers."
    )
    parser.add_argument("--root", default=".", help="Repository root path")
    parser.add_argument(
        "--overwrite", action="store_true", help="Overwrite existing act command files"
    )
    parser.add_argument(
        "--remove-old",
        action="store_true",
        help="Remove old trellis command files after migration",
    )
    parser.add_argument(
        "--scaffold-missing",
        action="store_true",
        help="Create act command stubs when trellis source command is missing",
    )
    parser.add_argument("--json", action="store_true", help="Print JSON summary")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = Path(args.root).resolve()

    migrated: list[str] = []
    skipped: list[dict[str, str]] = []
    removed: list[str] = []

    for name in CORE_COMMANDS:
        src = root / ".claude" / "commands" / "trellis" / f"{name}.md"
        dst = root / ".claude" / "commands" / "act" / f"{name}.md"
        ok, reason = migrate_file(src, dst, args.overwrite)
        if ok:
            migrated.append(str(dst.relative_to(root)))
            if args.remove_old and src.exists():
                src.unlink()
                removed.append(str(src.relative_to(root)))
        else:
            if (
                reason == "source_missing"
                and args.scaffold_missing
                and not dst.exists()
            ):
                if not dst.parent.exists():
                    dst.parent.mkdir(parents=True, exist_ok=True)
                dst.write_text(build_stub(name, "claude"), encoding="utf-8")
                migrated.append(str(dst.relative_to(root)))
            else:
                skipped.append({"file": str(dst.relative_to(root)), "reason": reason})

    for name in CORE_COMMANDS:
        src = root / ".cursor" / "commands" / f"trellis-{name}.md"
        dst = root / ".cursor" / "commands" / f"act-{name}.md"
        ok, reason = migrate_file(src, dst, args.overwrite)
        if ok:
            migrated.append(str(dst.relative_to(root)))
            if args.remove_old and src.exists():
                src.unlink()
                removed.append(str(src.relative_to(root)))
        else:
            if (
                reason == "source_missing"
                and args.scaffold_missing
                and not dst.exists()
            ):
                if not dst.parent.exists():
                    dst.parent.mkdir(parents=True, exist_ok=True)
                dst.write_text(build_stub(name, "cursor"), encoding="utf-8")
                migrated.append(str(dst.relative_to(root)))
            else:
                skipped.append({"file": str(dst.relative_to(root)), "reason": reason})

    # Remove empty old directory if requested.
    old_dir = root / ".claude" / "commands" / "trellis"
    if (
        args.remove_old
        and old_dir.exists()
        and old_dir.is_dir()
        and not any(old_dir.iterdir())
    ):
        old_dir.rmdir()
        removed.append(str(old_dir.relative_to(root)) + "/")

    summary = {
        "migrated": migrated,
        "removed": removed,
        "skipped": skipped,
        "core_commands": CORE_COMMANDS,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
