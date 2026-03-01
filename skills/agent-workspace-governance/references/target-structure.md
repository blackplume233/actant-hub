# Target Structure (Agent-First Repository)

This structure is used by the skill to guide repository optimization.

## Required Top-Level Directories

- `docs/`
- `history/`
- `init/`
- `issues/`
- `skills/`
- `subagents/`
- `topics/`

## Required Core Files

- `AGENTS.md`
- `SUBAGENTS.md`
- `history/HISTORY.md`
- `init/AGENT_INIT.md`

## Workflow-Critical Files (AgentCraft-inspired)

- `.trellis/workflow.md`
- `.trellis/scripts/get-context.sh`
- `.trellis/scripts/task.sh`
- `.trellis/scripts/init-developer.sh`
- `.trellis/scripts/add-session.sh`
- `docs/guides/dev-workflow-guide.md`

## Core Slash Command Coverage

Both command trees should include at least these workflow commands:

- `start`
- `plan-start`
- `finish-work`
- `create-pr`
- `ship`
- `stage-version`
- `qa`
- `check-backend`
- `check-frontend`
- `check-cross-layer`
- `update-spec`
- `break-loop`
- `record-session`
- `parallel`

Expected paths:

- Claude: `.claude/commands/act/<command>.md`
- Cursor: `.cursor/commands/act-<command>.md`

Each command file should include a source marker indicating provenance from Trellis workflow conventions.

## Recommended Directories

- `docs/architecture/`
- `docs/design/`
- `docs/decisions/`
- `docs/guides/`
- `docs/planning/`
- `docs/stage/`
- `docs/reports/`
- `docs/setup/`
- `docs/.local/`
- `docs/human/`
- `docs/agent/`
- `issues/active/`
- `issues/backlog/`
- `issues/completed/`
- `issues/archived/`
- `issues/.local/active/`
- `issues/.local/completed/`
- `issues/.local/archived/`
- `skills/.local/`
- `topics/.local/`

## Non-Destructive Migration Policy

- Never delete files automatically.
- Prefer creating missing directories and placeholders.
- Move/rename suggestions are reported only unless `--apply` is explicitly requested.

## Workflow Alignment Goals

- Repository should support lifecycle: `Plan -> Code -> Review -> PR -> Ship -> QA -> Stage`.
- Keep human and agent outputs separated (`docs/human/` vs `docs/agent/`).
- Keep stage snapshots in `docs/stage/` and planning artifacts in `docs/planning/`.

## Harness Readiness Planes

- **Legibility**: concise `AGENTS.md` + discoverable docs map.
- **Constraints**: lint/schema/CI boundary signals present.
- **Feedback**: test/check/review loop signals present.
- **Control Loop**: reinforcement + validation + history logging present.

## Reinforcement Loop

For structure hardening, run iterative loop:

1. Audit current gaps
2. Apply non-destructive scaffold
3. Re-audit and compare delta
4. Repeat until convergence or no further reduction

## Strict Gate Recommendation

Use strict mode in CI to prevent regression:

- Fail on missing required/workflow artifacts
- Fail on readiness scores below team thresholds
- Optionally fail when `AGENTS.md` grows beyond map-style length
