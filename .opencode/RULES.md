# RULES.md — Universal engineering rules for ProbeIQ

These rules apply to every part of the project (backend, frontend, docs, tooling).

## Code quality
- Prefer simple solutions.
- Avoid unnecessary abstraction.
- Avoid premature optimization.
- Follow existing project conventions.
- Keep functions focused.
- Use meaningful names.
- Remove dead code only when its removal is verified safe.

## Dependencies
- Do not add dependencies unnecessarily.
- Check existing dependencies before adding a new package.
- Prefer existing project tooling.
- Never silently replace a framework/library.

## Files
- Inspect before creating.
- Do not create duplicate files.
- Do not delete files without verifying references.
- Do not rename files without checking imports/references.
- Keep generated files out of Git (`node_modules/`, `.venv/`, `__pycache__/`,
  `*.pyc`, build artifacts, caches).

## Security
- Never expose secrets.
- Never hardcode credentials.
- Never commit API keys.
- Never log sensitive credentials.
- Treat user input as untrusted.

## Testing
- Run the smallest relevant test suite.
- Never claim tests passed unless actually run.
- Report failures honestly.
- Do not modify tests simply to make them pass, unless the test itself is
  demonstrably incorrect and the user requested that work.

## Documentation
- Documentation must reflect actual implementation.
- Do not document planned functionality as implemented.
- When implementation changes, update relevant documentation when appropriate.

## Scope control
- Work only on the requested area.
- Do not perform unrelated refactoring.
- Do not perform dependency upgrades unless requested.
- Do not change architecture without approval.
