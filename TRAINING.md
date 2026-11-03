# Training: the vibe-coding + GitHub workflow

This repo exists to demonstrate, end to end, the process used across this account's
projects for AI-assisted ("vibe-coded") development on GitHub — repo setup, the shared
`.claude` template, branch/PR discipline, automated review, and release tagging. The
Tetris game itself is incidental; what matters is the sequence of steps below, each one
grounded in what actually happened in this repo's history.

## 1. Create the repo, don't skip the bootstrap commit

```bash
gh repo create <owner>/<repo> --public --description "..." --source=. --remote=origin
```

A brand-new GitHub repo has no branches at all — you can't open a PR against `main`
until `main` exists. So the very first commit is a minimal bootstrap (here: just
`.gitignore` and a one-line `README.md`), committed and pushed **directly** to `main`:

```bash
git init -b main
git add .gitignore README.md
git commit -m "chore: initialize repository"
git push -u origin main
```

This is the one and only time this repo's history has a commit directly on `main`.
Every commit after this point goes through a feature branch and a PR — see Rule 1 in
`.claude/CLAUDE.md`.

## 2. Clone and adapt the shared `.claude` template

The account keeps a template repo (`i-machine-things/.claude`) with the rules every
project should start from: `CLAUDE.md` (the AI-assistant rulebook), `CODING_NOTES.md`
(accumulated best-practice notes, doubling as the findings log — see below), and a
generic `.github/workflows/ci.yml`.

Cloning it isn't a blind copy — each file gets adapted to the actual project:

- **`CLAUDE.md`**: filled in the `{{PROJECT_NAME}}`/`{{PROJECT_DESCRIPTION}}` placeholders,
  listed this project's actual key files, and replaced the generic "replace this TODO
  with project-specific test instructions" with the real `pytest tests/ -v` command.
  Also swapped every `master` reference for `main`, since that's this repo's default
  branch (the template was originally written assuming `master`).
- **`CODING_NOTES.md`**: kept as-is at first — its PyQt6 resource-cleanup notes applied
  directly to this project. (It later needed corrections; see step 5.)
- **`.github/workflows/ci.yml`**: adapted the lint/test/build skeleton to this stack —
  added `libegl1`/`libgl1` system packages and `QT_QPA_PLATFORM=offscreen` for PyQt6,
  and replaced the build job's placeholder with a real headless smoke test (construct
  the game window, run one drop cycle, close it) since this demo has no packaging step.

**The template repo itself was stale, and only direct correction caught it.** The
clone initially included a separate `S&P.md` — an empty "Standards & Practices" findings
log, which is what the template's own `CLAUDE.md` pointed to for logging review
findings. But current, actively-used repos on this account (JobDocs, shop-schedule) had
already folded that role into `CODING_NOTES.md` itself — topic-grouped notes with inline
citations like `(CodeRabbit, PR #341)`, no separate dated log file. `S&P.md` was removed,
its content migrated into the relevant `CODING_NOTES.md` topics, and every `CLAUDE.md`
reference to it rewritten to point at `CODING_NOTES.md` instead (see
[PR #1](https://github.com/i-machine-things/tetris-demo/pull/1)'s follow-up commit).
Lesson: a shared template is a starting point someone wrote at some point, not a live
source of truth — cross-check it against how current projects actually work, and expect
to correct it when they've drifted apart.

## 3. Build on a feature branch, verify locally before pushing

```bash
git checkout -b feat/pyqt6-tetris-scaffold
```

The actual feature work — `tetris/board.py` (pure game logic), `tetris/widget.py`
(PyQt6 UI), `main.py`, tests, `requirements*.txt` — was built on this branch, never on
`main`.

Before pushing, everything CI would check was run locally first, matching the exact
flags from `ci.yml`:

```bash
pytest tests/ -v
flake8 --max-line-length=120 --select=E,F --exclude=.git,__pycache__ .
bandit -r . --exclude ./.git --severity-level medium -q
QT_QPA_PLATFORM=offscreen python -c "<construct GameWindow, drop a piece, close it>"
```

Catching failures locally is faster than catching them in CI, and it means a pushed
branch should pass on the first try.

## 4. Open the PR, let CI gate it

```bash
git push -u origin feat/pyqt6-tetris-scaffold
gh pr create --base main --head feat/pyqt6-tetris-scaffold --title "..." --body "..."
```

[PR #1](https://github.com/i-machine-things/tetris-demo/pull/1) carries four required
checks, all defined in `.github/workflows/ci.yml`: **Lint & Security** (flake8 +
bandit), **Tests** (pytest), **Build** (the headless smoke test), plus **CodeRabbit**
as an automated reviewer. Per `.claude/CLAUDE.md` Rule 5, none of these is optional —
merging only happens once all of them are green.

## 5. The review loop: fix findings, log them, re-verify

CodeRabbit's first pass on PR #1 came back with 7 findings — 1 major, 6 minor:

| Finding | Fix |
|---|---|
| `GameWindow` never requested keyboard focus (**major** — controls could silently do nothing until the window was clicked) | `setFocusPolicy(StrongFocus)` + a `showEvent` override calling `setFocus()` |
| Held P/Space keys re-triggered pause/hard-drop via key-repeat | ignore `event.isAutoRepeat()` for those two keys |
| `main.py` scheduled `deleteLater()`/`processEvents()` **after** `app.exec()` had already returned | trimmed — `closeEvent` already handles cleanup while the loop is live |
| `CODING_NOTES.md`'s own example had the same deferred-deletion timing bug | moved `deleteLater()` into the `closeEvent` example |
| `CODING_NOTES.md` presented `bootloader_ignore_signals=True` as generic advice | scoped the note to when a supervisor process actually needs it |
| CI workflow had no `permissions:` block | added `permissions: contents: read` |
| `CLAUDE.md` claimed tagging triggers a release workflow that doesn't exist | corrected the claim and fixed the version-bump-count command to match only `v*` tags |

Two of those findings (`CODING_NOTES.md`, `CLAUDE.md`) were bugs in the *template
content itself*, inherited verbatim at clone time — proof that cloning a template
isn't a one-time, trust-it-and-move-on step. Review catches issues in your rules files
exactly like it catches issues in your code — and so can direct human correction, as
with the separate `S&P.md` mistake described above, caught by the user rather than a
review tool.

The fix-and-log loop, per Rule 5:

1. Read every finding before touching anything else.
2. Fix what's actionable, in the same PR, on the same branch.
3. Add or amend a note under the relevant topic in `.claude/CODING_NOTES.md` for each
   finding, with a short citation (`(CodeRabbit, PR #1)`), so the next review (human or
   AI) has the context instead of rediscovering the same issue.
4. Push, and because CodeRabbit's free tier caps included reviews at one per hour, wait
   out the rate-limit window before re-triggering with `gh pr comment <n> --body
   "@coderabbitai review"` rather than merging on an unreviewed diff. `.claude/CLAUDE.md`
   has the exact rule for this (check the comment for "Rate limit exceeded", compute the
   UTC clear time, wait 5 extra minutes for clock drift).
5. Only merge once CI and the review are both clean.

## 6. Merge — and keep the branch

```bash
gh pr merge <n> --merge
```

Deliberately **no** `--delete-branch`. Branches are kept after merge as a paper trail —
cheap to keep, and useful later for "what exact commits made up this change" without
digging through squashed history.

## 7. Tag the release

Per Rule 4 in `.claude/CLAUDE.md`, releases are tagged `vMAJOR.MINOR.PATCH`, manually,
only from `main`, only once CI is green on `main`:

```bash
git checkout main
git pull
git tag v0.1.0
git push origin v0.1.0
```

There's no automated release pipeline reacting to the tag (that was one of the
findings in step 5) — it's purely a versioning convention, a marker of "this is the
state the project was in."

## 8. This document is an instance of the same process

`TRAINING.md` itself was written on `docs/add-training-readme`, off `main`, and went
through the same PR → CI → merge path as everything above. The process doesn't have a
special case for "it's just docs."

## Summary checklist

- [ ] New repo: bootstrap commit straight to `main`, then branch for everything else.
- [ ] Clone `.claude` template, actually adapt it (placeholders, branch names, project
      specifics) — don't just drop the files in.
- [ ] Verify locally with the same commands CI runs before pushing.
- [ ] Open a PR; treat all CI jobs plus CodeRabbit as required, not advisory.
- [ ] Fix every review finding or log why not; note it under the relevant topic in
      `.claude/CODING_NOTES.md`.
- [ ] Merge without deleting the branch.
- [ ] Tag releases manually from `main` per semver, only once green.
