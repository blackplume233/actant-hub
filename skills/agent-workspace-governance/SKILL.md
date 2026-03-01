---
name: agent-workspace-governance
description: 引导一个工程目录优化到目标 Agent-first 结构（审计差异、输出迁移建议、可选创建缺失目录与占位文件）。当用户请求“优化目录结构/对齐目标结构/仓库结构治理”时使用。
---

# Agent Workspace Governance

## 执行目标

将现有工程目录与目标结构进行对比，输出可执行的优化路径，并在用户明确允许时做非破坏式补齐。
目标结构融合 AgentCraft 的生命周期流程：`Plan -> Code -> Review -> PR -> Ship -> QA -> Stage`。

## 执行步骤

1. 先执行结构审计（默认 dry-run，不改文件）：

```bash
python skills/agent-workspace-governance/scripts/audit_repo_structure.py \
  --root . \
  --output docs/reports/repo-structure-audit.md
```

2. 用 `references/target-structure.md` 对照审计结果，输出三段式迁移计划：
   - 必需项（required）
   - 推荐项（recommended）
   - 工作流能力缺口（workflow readiness）
   - 迁移建议（move suggestions）

3. 仅在用户确认后执行非破坏式补齐：

```bash
python skills/agent-workspace-governance/scripts/audit_repo_structure.py \
  --root . \
  --apply \
  --output docs/reports/repo-structure-audit-after-apply.md
```

4. 若需要新增工作话题目录，再使用创建脚本（可选）：

```bash
python skills/agent-workspace-governance/scripts/create_agent_workspace.py --name "<topic-name>"
```

5. 对结构治理启用循环补强（推荐）：

```bash
python skills/agent-workspace-governance/scripts/reinforcement_loop.py \
  --root . \
  --max-rounds 3 \
  --apply \
  --report docs/reports/reinforcement-loop-report.md \
  --json
```

6. 需要门禁时启用 strict（CI 推荐）：

```bash
python skills/agent-workspace-governance/scripts/audit_repo_structure.py \
  --root . \
  --strict \
  --fail-on-agents-too-long \
  --min-legibility-score 80 \
  --min-constraints-score 60 \
  --min-feedback-score 60 \
  --min-control-loop-score 90 \
  --min-command-coverage-score 90 \
  --json
```

7. 需要统一 slash command 前缀时执行迁移（`trellis` -> `act`，并写入来源标记）：

```bash
python skills/agent-workspace-governance/scripts/rename_trellis_to_act_commands.py --root . --overwrite --remove-old --json
```

## 目标结构来源

- 规范文件：`skills/agent-workspace-governance/references/target-structure.md`
- 核心指导：`skills/agent-workspace-governance/references/harness-core-guidance.md`
- 引导流程：`skills/agent-workspace-governance/references/guided-rollout.md`
- 审计脚本：`skills/agent-workspace-governance/scripts/audit_repo_structure.py`
- 循环补强脚本：`skills/agent-workspace-governance/scripts/reinforcement_loop.py`
- 前缀迁移脚本：`skills/agent-workspace-governance/scripts/rename_trellis_to_act_commands.py`
- 工作目录脚本（可选）：`skills/agent-workspace-governance/scripts/create_agent_workspace.py`

## 约束

- 默认 dry-run，只读审计。
- 未经用户确认，不执行 `--apply`。
- `--apply` 仅创建缺失目录和占位文件，不自动删除或覆盖现有文件。
- 不自动执行 git commit。

## 输出要求

- 明确列出缺失的 required 项
- 明确列出缺失的 recommended 项
- 明确列出缺失的 workflow 文件（`missing_workflow_files`）
- 输出 harness readiness 四维度（legibility/constraints/feedback/control_loop）
- 输出 slash-command coverage（Claude/Cursor 双树覆盖）
- slash command 默认前缀为 `act`，并附带 Trellis 来源标记
- 输出 `AGENTS.md` 行数与是否超过建议上限
- 输出 `guided_next_steps`，给出按阶段可执行命令
- 给出可执行迁移步骤（先创建，再迁移，再验证）
- 对潜在移动操作给出 `from -> to` 建议，但默认不自动移动

## 核心指导内化

- 以 `AGENTS.md` 为目录索引，避免巨型说明文档。
- 以仓库文档作为系统真相源（versioned, discoverable, checkable）。
- 将架构边界与质量要求编码到可执行检查，不仅依赖人工评审。
- 通过循环补强维持长期收敛，持续压制熵增。

## 循环补强规则

- 每轮执行：`评估(audit) -> 补齐(apply) -> 复评(audit)`。
- 收敛条件：总缺失项为 0，或连续一轮无下降（避免无效循环）。
- 每轮输出 before/after 差异，写入补强报告。
- 需要时可追加 `--run-validate`，在循环结束后执行技能全量回归。

## 近乎完美标准（Practical Perfection）

- `required/workflow` 缺失为 0。
- `harness_readiness` 四维均达到团队阈值。
- 核心 slash command 覆盖达到阈值（建议 >= 90）。
- `strict` 模式通过。
- 连续两轮补强无新增缺口（系统进入稳态）。

## AgentCraft 对齐点

- 文档分区：`docs/human/` 与 `docs/agent/` 分离
- 生命周期文档：`docs/guides/dev-workflow-guide.md`
- 规划与版本沉淀：`docs/planning/`、`docs/stage/`
- Trellis 脚本入口：`.trellis/workflow.md` 与 `.trellis/scripts/*.sh`

## 持续进化闭环

每次技能执行完成后，按以下闭环运行：

1. 运行回归校验：

```bash
python skills/agent-workspace-governance/scripts/validate_skill.py
```

2. 若发现偏差/失败，用结构化反馈记录：

```bash
python skills/agent-workspace-governance/scripts/record_feedback.py \
  --source "user|agent|ci" \
  --profile "all|generic|npm|npm-monorepo|unreal|unreal-cpp" \
  --issue "<具体问题>" \
  --action "<修复动作>" \
  --status "open|fixed|wontfix"
```

3. 每次修改脚本或模板后，再次执行 `validate_skill.py`，通过后再交付。

4. 将结论追加到 `skills/agent-workspace-governance/history/EVOLUTION.md`。

## 示例

```bash
# 先审计
python skills/agent-workspace-governance/scripts/audit_repo_structure.py --root . --output docs/reports/repo-structure-audit.md

# 用户确认后补齐
python skills/agent-workspace-governance/scripts/audit_repo_structure.py --root . --apply --output docs/reports/repo-structure-audit-after-apply.md

# 需要专题工作目录时（可选）
python skills/agent-workspace-governance/scripts/create_agent_workspace.py --name "repo-structure-migration"
```
