# Guided Rollout (Internalized Harness Flow)

Use this sequence to guide users from raw repository to stable harness-ready structure.

## Phase A: Assess

Goal: produce a full structural and harness-readiness snapshot.

Command:

```bash
python skills/agent-workspace-governance/scripts/audit_repo_structure.py --root . --json
```

## Phase B: Stabilize

Trigger: required/workflow gaps exist.

Goal: establish minimum operable baseline without destructive changes.

Command:

```bash
python skills/agent-workspace-governance/scripts/audit_repo_structure.py --root . --apply --output docs/reports/repo-structure-audit-after-apply.md
```

## Phase C: Reinforce

Trigger: recommended gaps remain or readiness score is below target.

Goal: iterative hardening with convergence check.

Command:

```bash
python skills/agent-workspace-governance/scripts/reinforcement_loop.py --root . --max-rounds 3 --apply --run-validate --json
```

## Phase D: Gate

Trigger: before merge/release.

Goal: enforce strict quality threshold in CI.

Command:

```bash
python skills/agent-workspace-governance/scripts/audit_repo_structure.py --root . --strict --fail-on-agents-too-long --min-legibility-score 80 --min-constraints-score 60 --min-feedback-score 60 --min-control-loop-score 90 --min-command-coverage-score 90 --json
```

## Phase E: Prefix Migration

Trigger: repository still uses `trellis` command prefix.

Goal: migrate to `act` prefix while preserving Trellis provenance markers.

Command:

```bash
python skills/agent-workspace-governance/scripts/rename_trellis_to_act_commands.py --root . --overwrite --remove-old --json
```
