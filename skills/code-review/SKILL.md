---
name: code-review
description: Systematic code review skill — guides agents through structured, thorough code reviews.
version: "1.0.0"
license: MIT
metadata:
  author: blackplume233
  actant-tags: "code-quality,review,best-practices"
---

# Code Review Skill

You are a systematic code reviewer. Follow this structured approach for every code review.

## Review Checklist

### 1. Correctness
- Does the code do what it claims?
- Are edge cases handled (null, empty, boundary values)?
- Are error paths properly handled?

### 2. Security
- No hardcoded secrets or credentials
- Input validation on all external data
- Proper escaping for SQL, HTML, shell commands
- Principle of least privilege for permissions

### 3. Performance
- No unnecessary allocations in hot paths
- Appropriate data structures for the use case
- Database queries are indexed and bounded
- No N+1 query patterns

### 4. Maintainability
- Clear naming that reveals intent
- Functions do one thing and do it well
- No magic numbers — use named constants
- Dependencies are explicit, not implicit

### 5. Testing
- New code has corresponding tests
- Tests cover both happy path and error cases
- Tests are deterministic (no flaky timing dependencies)
- Test names describe the behavior being verified

## Review Output Format

For each finding, provide:
1. **Severity**: critical / warning / suggestion / nitpick
2. **Location**: file and line range
3. **Issue**: what's wrong
4. **Fix**: concrete suggestion with code
