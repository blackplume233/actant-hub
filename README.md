# actant-hub

Official component hub for [Actant](https://github.com/blackplume233/Actant) — the platform for building, managing, and composing AI agents.

## What's Inside

| Component Type | Count | Description |
|---------------|-------|-------------|
| **Skills** | 3 | Agent capabilities (code review, testing, documentation) |
| **Prompts** | 2 | System prompts (code assistant, QA assistant) |
| **MCP Servers** | 2 | Tool integrations (filesystem, memory) |
| **Templates** | 3 | Ready-to-use agent configurations |
| **Presets** | 2 | Domain-specific component bundles |

## Quick Start

### Use with Actant CLI

```bash
# Add as a source
actant source add https://github.com/blackplume233/actant-hub.git --name actant-hub

# Sync components
actant source sync actant-hub

# List available templates
actant template list

# Create an agent from a template
actant agent create my-reviewer --template actant-hub@code-reviewer
```

> **Note**: `actant-hub` is registered as the default source when you install Actant. You may already have it available.

### Use with Agent Skills (skill.sh)

Skills in this repository are compatible with the [Agent Skills](https://agentskills.io) ecosystem:

```bash
npx skills add blackplume233/actant-hub
```

This works with Claude Code, Cursor, Gemini CLI, and other supported platforms.

## Repository Structure

```
actant-hub/
├── actant.json          # Package manifest (Actant source system entry point)
├── registry.json        # Enhanced index for search and discovery
├── skills/              # Skill components (dual format: SKILL.md + .json)
├── prompts/             # Prompt components
├── mcp/                 # MCP server configurations
├── templates/           # Full AgentTemplate definitions
└── presets/             # Domain-specific component bundles
```

## Components

### Skills

| Name | Description |
|------|-------------|
| `code-review` | Systematic code review — security, performance, maintainability |
| `test-writer` | Test writing with TDD principles — unit, integration, edge cases |
| `doc-writer` | Technical documentation — READMEs, API docs, guides |

### Templates

| Name | Description | Skills | Prompt |
|------|-------------|--------|--------|
| `code-reviewer` | Code review agent | code-review | code-assistant |
| `qa-engineer` | QA testing agent | test-writer | qa-assistant |
| `doc-writer` | Documentation agent | doc-writer | code-assistant |

### Presets

| Name | Description | Includes |
|------|-------------|----------|
| `web-dev` | Web development suite | 3 skills, 1 prompt, filesystem MCP, 3 templates |
| `devops` | DevOps suite | 2 skills, 1 prompt, filesystem + memory MCP, 1 template |

## Skill Dual Format

Each skill is provided in two formats:

- **`skills/{name}/SKILL.md`** — [Agent Skills](https://agentskills.io/specification) compatible (YAML frontmatter + markdown)
- **`skills/{name}.json`** — Actant native SkillDefinition format

`SKILL.md` is the source of truth. JSON files can be generated from SKILL.md.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on adding new components.

## License

MIT
