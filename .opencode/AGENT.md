# AGENT.md — How OpenCode should behave on ProbeIQ

These rules apply to every OpenCode session working on ProbeIQ.

## Repository inspection before modification
1. Inspect the repository structure and read relevant existing files before
   creating or changing anything.
2. Use the actual repository contents as the source of truth — never memory of
   "how it usually looks".

## Never hallucinate project functionality
3. Never invent functionality that is not present in the code.
4. Never assume an API exists; verify it in the code.
5. Never assume a dependency is installed; check `pyproject.toml`,
   `uv.lock`, `package.json`, or `package-lock.json` first.

## Reuse and avoid duplication
6. Read relevant existing files before creating new ones.
7. Reuse existing code when appropriate.
8. Avoid duplicate components, services, utilities, schemas, or helpers.

## Clarity and verification
9. Ask for clarification when requirements are ambiguous instead of guessing.
10. Clearly distinguish facts (verified in the repository) from assumptions.
11. Verify changes after implementation.
12. Run the appropriate tests, lint, and type checks when available
    (backend: `pytest`, `ruff`, `mypy` from `backend/`).
13. Report exactly what was changed, including file paths.
14. Never claim tests passed unless they were actually executed.
15. Never claim an API works unless it was actually verified.
16. Never silently change architecture.
17. Never add dependencies without justification.
18. Never delete files without explicit approval.

## Truthfulness / Anti-Hallucination Policy
- Repository contents are the source of truth.
- User-provided requirements are requirements, not proof that implementation
  exists.
- Documentation is not proof that a feature is implemented.
- Comments are not proof that functionality exists.
- Planned features must not be represented as implemented.
- When uncertain, inspect the repository.
- If still uncertain, report the uncertainty instead of guessing.
- When a document says "Not currently verified in the repository", leave it as
  unverified rather than resolving it with assumptions.

## Git safety
- Follow `GIT.md` exactly. Never run destructive or history-modifying Git
  commands autonomously.
- Prefer read-only inspection commands (`git status`, `git diff`,
  `git diff --cached`, `git log`, `git show`).
