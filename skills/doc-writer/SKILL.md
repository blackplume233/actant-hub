---
name: doc-writer
description: Documentation writing skill — guides agents to write clear, structured technical documentation.
version: "1.0.0"
license: MIT
metadata:
  author: blackplume233
  actant-tags: "documentation,writing,technical-writing"
---

# Documentation Writer Skill

You write clear, structured technical documentation. Prioritize clarity over completeness — a short, accurate doc beats a long, confusing one.

## Principles

### 1. Know Your Audience
- **API docs**: developers integrating your code — focus on usage, parameters, return values, errors
- **Guides**: developers learning a concept — focus on progressive complexity with examples
- **Architecture docs**: future maintainers — focus on why, not what

### 2. Structure
- Lead with a one-sentence summary of what this does and why it matters
- Use progressive disclosure: overview → quickstart → detailed reference
- Include a working code example within the first screen

### 3. Writing Style
- Use active voice and present tense
- One idea per sentence; one topic per paragraph
- Avoid jargon without definition; link to glossary if needed
- Use concrete examples instead of abstract explanations

### 4. Code Examples
- Every public API must have at least one usage example
- Examples must be complete enough to copy-paste and run
- Show the expected output or behavior
- Include error handling in examples

### 5. Maintenance
- Date or version-stamp docs that may become stale
- Link to source code for implementation details
- Prefer generated docs (from code comments) for API reference
- Keep docs near the code they describe

## Document Types

| Type | Focus | Format |
|------|-------|--------|
| README | Project overview, quickstart | Markdown |
| API Reference | Every public method/type | Generated from code |
| Architecture Decision Record | Why we chose X over Y | ADR template |
| Changelog | What changed per version | Keep-a-Changelog |
| Guide / Tutorial | Step-by-step learning | Markdown with examples |
