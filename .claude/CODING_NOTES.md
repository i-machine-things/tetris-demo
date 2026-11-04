# Coding Best Practices & Reminders

> **Style rule:** Notes must be clear and concise — no filler, no restating the obvious — but long enough to carry the actual lesson: what went wrong, why, and the fix. A one-line rule without that context gets re-broken the next time someone hits a similar case. Group by topic, not by date. Whenever a PR review (CodeRabbit or human) catches a mistake, add or amend a note here right away so it isn't repeated.

## Resource Cleanup (PyQt6)

- **Schedule `deleteLater()` from inside `closeEvent()`/`aboutToQuit`, while the event loop is still running** — not after `app.exec()` returns. Deferred deletion needs a live loop to actually process; a trailing `app.processEvents()` call doesn't reliably make up for calling it too late. (origin: PyInstaller executables staying locked after close)
- Use context managers for file handling; release locks before exit; clean up temp files.
- Stop and join background threads before exit; cancel pending operations.
- Verify cleanup by testing the built executable can be deleted/moved/replaced immediately after closing — if it's locked, cleanup is incomplete.
- **`bootloader_ignore_signals=True` (PyInstaller `.spec`) only matters when a supervisor/parent process sends OS signals to manage shutdown** — it's not a general cleanup fix. If you set it, verify shutdown still behaves correctly under that supervisor. (CodeRabbit, tetris-demo PR #1)

### Example (PyQt6)

```python
def closeEvent(self, event):
    for module in self.modules:
        try:
            module.cleanup()
        except Exception as e:
            print(f"Error cleaning up module: {e}")
    self.save_settings()
    self.deleteLater()  # scheduled now, while the loop is still live
    event.accept()
    QApplication.quit()

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
```

## Qt / PyQt6 UI Patterns

- **A `QMainWindow` doesn't automatically have keyboard focus just because `.show()` was called** — controls can silently do nothing until the user clicks into the window. Set `setFocusPolicy(Qt.FocusPolicy.StrongFocus)` and call `self.setFocus()` from a `showEvent` override. (CodeRabbit, tetris-demo PR #1)
- **Qt's key-repeat re-fires `keyPressEvent` for a held key** — one-shot actions (pause, hard-drop) need to check `event.isAutoRepeat()` and ignore repeats; movement keys should keep repeating normally. (CodeRabbit, tetris-demo PR #1)

## Packaging (PyInstaller)

- **`pyinstaller --onefile` on a GUI app spawns two processes at runtime, not one.** The visible process (the one with a `MainWindowTitle`) is a child of a short-lived bootloader process that unpacks the bundle to a temp dir — both show up under the same name in Task Manager / `Get-Process`. Don't assume a single matching process means something's wrong; check `MainWindowHandle`/`MainWindowTitle` to find the real one. (tetris-demo, Windows `.exe` packaging)
- **`--windowed` (a.k.a. `--noconsole`) is required for a PyQt6 GUI app** — without it, PyInstaller attaches a console window alongside the real one. PyInstaller's own `hook-PyQt6.py` and the `pyi_rth_pyqt6` runtime hook handle bundling Qt's plugins automatically; no manual `--add-data` was needed for this project's `QApplication`/`QMainWindow`/`QPainter` usage. (tetris-demo)
- **A newly-spawned window can open on a non-primary monitor** — a screen-bounds capture of `[System.Windows.Forms.Screen]::PrimaryScreen` can miss it entirely even though the process and window are both healthy. Confirm via `GetWindowRect` on the window handle (X/Y far outside the primary screen's resolution is the tell) before assuming a launch failed; `PrintWindow` captures a specific window's content directly and works regardless of which monitor it's on. (tetris-demo, verifying the PyInstaller build)

## CI / GitHub Actions

- **Set `permissions: contents: read` at the workflow's top level** unless a job genuinely needs more — the default `GITHUB_TOKEN` scope is broader than most CI jobs require. (CodeRabbit, tetris-demo PR #1)
- **When counting commits since the last release tag, match only `v*` tags** (`git describe --tags --match "v*" --abbrev=0`) and handle the no-tag-yet case explicitly (fall back to the full log) — an unfiltered `git describe --tags` can pick up a non-release tag. (tetris-demo PR #1)
- **Don't claim a tag push "triggers a release workflow" in rules/docs unless that workflow actually exists in the repo** — tagging can be a pure versioning convention with zero automation behind it. (tetris-demo PR #1)
- **CodeRabbit isn't a job "defined in" `.github/workflows/ci.yml`** — it's a separate GitHub App that reviews PRs on its own, independent of anything in that workflow file. When describing the required checks on a PR, name the workflow's actual jobs (lint, tests, build, ...) separately from CodeRabbit rather than implying the YAML defines all of them. (CodeRabbit, tetris-demo PR #2)

## Python Testing & Imports

- **A bare `pytest` invocation doesn't put the repo root on `sys.path` the way `python -m pytest` does** — if `tests/` has no `__init__.py`, pytest's default import mode prepends `tests/` itself, not the repo root, so `from mypackage import ...` raises `ModuleNotFoundError` even though CI (which sets `PYTHONPATH`) passes fine. Document and run `python -m pytest`, not plain `pytest`. (CodeRabbit, tetris-demo PR #1)

## CodeRabbit Review Process

- **`gh pr checks <n>` showing CodeRabbit as "skipping" doesn't mean the existing review is stale** — CodeRabbit edits its one main summary comment in place on each run rather than posting a new one; "skipping" just means no *new* run happened (often because nothing changed since the last one, not only rate-limiting). Before assuming a re-review is needed, check that comment's `coveredCommitId`/`sourceCommitId` metadata (or its "Merge Risk ... up to `<short-sha>`" line) against the PR's current HEAD — if they match, the existing review already covers everything, findings and all. (tetris-demo PR #1 — several retrigger attempts were wasted on an already-current review before this was caught.)
- **CodeRabbit's pre-merge "Docstring Coverage" check flags 0% coverage on undocumented functions with cyclomatic complexity ≥ 2.** Not actioned here: this project's style is self-explanatory names plus comments only where the *why* isn't obvious (see `main.py`/`tetris/*.py`), not blanket docstrings — a deliberate choice, not an oversight. (CodeRabbit, tetris-demo PR #1)
- **CodeRabbit auto-resolves individual review threads once it detects the fix in a later commit — no manual reply needed.** It appends "✅ Addressed in commit `<sha>`" to the thread and flips `isResolved: true`. This happens even while the PR-level check stays "skipping" (rate-limited) — thread resolution is apparently evaluated independently of a full summary re-review. Check via GraphQL: `pullRequest(number: N) { reviewThreads(first: 50) { nodes { isResolved comments(first: 1) { nodes { databaseId body } } } } }`. Faster than waiting on the rate-limited full review to confirm a specific fix landed. (tetris-demo PR #2)
- **The edited-in-place summary comment's "## Findings" section only lists *newly raised* findings from the most recent review pass — not a cumulative list of everything still open.** Reading just that section after each review undercounts outstanding work: 4 findings from PR #2's very first review (file-path/working-directory instructions, "private branch" wording, `git init` ordering, a placeholder smoke-test command) went unaddressed for several review cycles because later passes' findings sections didn't re-mention them. Use the GraphQL `reviewThreads` query above to see every thread's `isResolved` state at once, not just the latest summary. (tetris-demo PR #2)

## Documentation Accuracy

- **A beginner-friendly analogy shouldn't assert something factually wrong, even for accessibility.** Describing a Git branch as "a parallel, separate copy of the project's files" is an inaccurate mental model (a branch is a movable pointer to a commit; Git computes its contents from shared history, nothing is duplicated on disk) — reword to what actually matters day-to-day ("an independent line of development, isolated from the main version until merged") instead of a concretely wrong physical description. (human review, tetris-demo PR #2)
- **A generated artifact (PDF, report, etc.) with hand-maintained content separate from its "source" document needs an explicit note saying so** — otherwise reviewers reasonably assume one is derived from the other and will flag silent drift as a bug. State the relationship (independently maintained, re-sync manually on substantive changes) in both directions: in the generator's docstring and in the source document's reference to the generated output. (human review, tetris-demo PR #2)
- **A generator that silently skips missing input (an image, a data file, etc.) produces an incomplete output with no signal anything went wrong.** Print a warning (or fail loudly, depending on how critical the input is) instead of a bare existence check that falls through silently. (human review, tetris-demo PR #2)
