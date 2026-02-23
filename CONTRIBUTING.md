# Contributing to actant-hub

Thank you for contributing to the Actant official component hub!

## Adding a New Skill

1. Create a directory: `skills/{skill-name}/SKILL.md`
2. Use YAML frontmatter with required fields:

```yaml
---
name: my-skill
description: One-line description of what this skill does.
version: "1.0.0"
license: MIT
metadata:
  author: your-github-username
  actant-tags: "tag1,tag2"
---
```

3. Create the JSON equivalent: `skills/{skill-name}.json`
4. Add the JSON path to `actant.json` under `components.skills`
5. Add metadata to `registry.json`

## Adding a New Template

1. Create `templates/{template-name}.json` with required fields:

```json
{
  "name": "my-template",
  "version": "1.0.0",
  "description": "What this agent does",
  "backend": { "type": "claude-code" },
  "provider": { "type": "anthropic" },
  "domainContext": {
    "skills": ["skill-name"],
    "prompts": ["prompt-name"],
    "mcpServers": []
  }
}
```

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

2. Add the path to `actant.json` under `presets`
3. Add metadata to `registry.json`

## Quality Checklist

- [ ] Component has a clear, concise `description`
- [ ] Version follows semver (`1.0.0` format)
- [ ] Tags are relevant and lowercase
- [ ] Skill content is actionable (tells the agent what to do, not just what to know)
- [ ] Template references only components that exist in this repository
- [ ] `actant.json` and `registry.json` are both updated
- [ ] JSON files are valid (run `npx jsonlint <file>` to check)

## Versioning

- Each component has its own `version` field (semver)
- Bump the version when changing a component's content
- The repository-level version in `actant.json` tracks the overall collection
