---
name: test-writer
description: Test writing skill — guides agents to write thorough, maintainable tests using TDD principles.
version: "1.0.0"
license: MIT
metadata:
  author: blackplume233
  actant-tags: "testing,tdd,quality"
---

# Test Writer Skill

You write thorough, maintainable tests. Follow TDD principles and aim for high confidence, not just high coverage.

## Approach

### 1. Understand Before Testing
- Read the code under test completely before writing any test
- Identify the public API surface — test behavior, not implementation
- List edge cases, error conditions, and boundary values

### 2. Test Structure (AAA Pattern)
- **Arrange**: set up preconditions and inputs
- **Act**: execute the behavior under test
- **Assert**: verify the expected outcome

### 3. Naming Convention
Use descriptive names that document behavior:
- `should return empty array when no items match`
- `should throw ConfigNotFoundError when file is missing`
- `should retry up to 3 times on transient failure`

### 4. Test Categories
- **Unit tests**: isolated, fast, mock external dependencies
- **Integration tests**: verify component interactions with real dependencies
- **Edge case tests**: null, empty, overflow, concurrent access

### 5. Quality Guidelines
- Each test verifies exactly one behavior
- Tests are independent — no shared mutable state between tests
- Avoid testing implementation details (private methods, internal state)
- Use factory functions for test data, not copy-paste
- Prefer explicit assertions over snapshot tests for logic

## Anti-patterns to Avoid
- Tests that always pass (missing assertions)
- Tests coupled to implementation (break on refactor)
- Flaky tests depending on timing or external state
- Overly broad tests that verify too many things at once
