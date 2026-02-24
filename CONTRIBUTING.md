# Contributing to actant-hub

Thank you for contributing to the Actant official component hub!

## Adding a New Skill

### 1. Create SKILL.md (source of truth)

Create a directory: `skills/{skill-name}/SKILL.md`

Use YAML frontmatter with required fields:

```yaml
---
name: my-skill
description: One-line description of what this skill does.
version: "1.0.0"
license: MIT
compatibility: Requires Node.js 18+
allowed-tools: Bash(npm:*) Read
metadata:
  author: your-github-username
  actant-tags: "tag1,tag2"
---
```

| Field | Required | Notes |
|-------|----------|-------|
| `name` | Yes | Lowercase letters, numbers, hyphens only. Must match parent directory name. |
| `description` | Yes | Max 1024 characters. |
| `version` | Recommended | Semver format. |
| `license` | Recommended | SPDX identifier (e.g. `MIT`, `Apache-2.0`). |
| `compatibility` | Optional | Environment requirements, max 500 characters. |
| `allowed-tools` | Optional | Space-delimited pre-approved tool list. |

### 2. Create JSON equivalent

Create `skills/{skill-name}.json` with matching fields:

```json
{
  "name": "my-skill",
  "version": "1.0.0",
  "description": "One-line description of what this skill does.",
  "tags": ["tag1", "tag2"],
  "license": "MIT",
  "content": "# Skill content here..."
}
```

### 3. Register the component

- Add the JSON path to `actant.json` under `components.skills`
- Add metadata to `registry.json`

## Adding a New Template

1. Create `templates/{template-name}.json` with required fields:

```json
{
  "name": "my-template",
  "version": "1.0.0",
  "description": "What this agent does",
  "backend": { "type": "claude-code" },
  "domainContext": {
    "skills": ["skill-name"],
    "prompts": ["prompt-name"],
    "mcpServers": []
  }
}
```

> **Note**: The `provider` field is optional. When omitted, the agent will use the user's configured default provider. Only specify `provider` when the template requires a specific model provider.

2. Add the path to `actant.json` under `components.templates`
3. Add metadata to `registry.json`

## Adding a New Preset

1. Create `presets/{preset-name}.json`:

```json
{
  "name": "my-preset",
  "version": "1.0.0",
  "description": "What this bundle provides",
  "skills": ["skill1", "skill2"],
  "prompts": ["prompt1"],
  "mcpServers": ["mcp1"],
  "templates": ["template1"]
}
```

Use **unqualified** component names (e.g. `"code-review"`, not `"actant-hub@code-review"`). The source manager applies namespace prefixes automatically.

2. Add the path to `actant.json` under `presets`
3. Add metadata to `registry.json`

## Quality Checklist

- [ ] Component has a clear, concise `description`
- [ ] Version follows semver (`1.0.0` format)
- [ ] Tags are relevant and lowercase
- [ ] Skill `name` is lowercase with hyphens, matches its directory name
- [ ] Skill content is actionable (tells the agent what to do, not just what to know)
- [ ] Template references only components that exist in this repository
- [ ] `actant.json` and `registry.json` are both updated
- [ ] Passes validation: `actant source validate --path . --compat agent-skills`

## Versioning

- Each component has its own `version` field (semver)
- Bump the version when changing a component's content
- The repository-level version in `actant.json` tracks the overall collection
