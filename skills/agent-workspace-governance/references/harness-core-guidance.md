# Harness Core Guidance (In-Skill Mapping)

This skill internalizes the core guidance from OpenAI's harness engineering article.

## Principle 1: Humans steer, agents execute

- Engineers define intent, constraints, and feedback loops.
- Agents execute implementation and verification work.

## Principle 2: Agent legibility first

- Keep `AGENTS.md` concise and map-like.
- Keep deep knowledge in repository-local, versioned docs.
- Prefer progressive disclosure over monolithic manuals.

## Principle 3: Enforce invariants mechanically

- Encode architecture and quality rules in linters/tests/CI.
- Do not rely on ad-hoc review comments as the primary guardrail.

## Principle 4: Build feedback loops, not one-shot prompts

- Require repeatable validation pathways (tests, checks, staged verification).
- Run iterative hardening loops: audit -> apply -> re-audit.

## Principle 5: Fight entropy continuously

- Record drift and fixes as versioned artifacts.
- Use recurring cleanup and quality scans.

## Audit Mapping Used By This Skill

- **Legibility readiness**: AGENTS map quality + docs discoverability.
- **Constraint readiness**: lints/schemas/CI checks existence.
- **Feedback readiness**: tests/check scripts/review loops presence.
- **Control-loop readiness**: reinforcement and validation scripts, history logs.
- **Command readiness**: core slash commands available on both Claude and Cursor trees.
