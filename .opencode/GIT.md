# GIT.md — Git safety rules for ProbeIQ

Prioritize protection of user work over convenience. When in doubt, do nothing
destructive and ask the user.

## Safe / read-only commands (may run without approval)
- `git status`
- `git diff`
- `git diff --cached`
- `git log`
- `git show`
- `git branch`
- `git branch -vv`
- `git remote -v`
- `git fetch`

## Commands requiring explicit user approval
- `git add`
- `git commit`
- `git push`
- `git pull`
- `git merge`
- `git stash`
- `git cherry-pick`
- `git revert`

## High-risk commands that must NEVER be run autonomously
- `git reset --hard`
- `git clean -fd`
- `git clean -fdx`
- `git rebase`
- `git push --force`
- `git push --force-with-lease`
- `git branch -D`
- `git checkout` that discards changes
- `git restore` that discards changes
- `git commit --amend`
- any history-rewriting command

## Rules
- Never delete user work to resolve Git conflicts.
- Never rewrite history to solve a normal development problem.
- Never force-push.
- Never automatically resolve conflicts by choosing one side.
- Before destructive Git operations, stop and ask the user.
- Before committing, inspect `git diff --cached`.
- Never stage `node_modules/`, `.venv/`, `__pycache__/`, `*.pyc`, secrets,
  `.env` files, build artifacts, or caches.
- Never commit credentials, API keys, tokens, or passwords.
- Never assume `.gitignore` is correct; inspect it.
- Never use `git add .` blindly when there is a possibility of unrelated
  changes; prefer targeted `git add <path>`.
- After a commit, verify with `git status`.
- After a push, verify the push result.

## Notes specific to this repository
- `frontend/node_modules/` is untracked (removed from tracking; kept local via
  `.gitignore`).
- Keep `main` tracking `origin/main`. Do not modify existing commits or rewrite
  history.
