# Coding Best Practices & Reminders

> **Style rule:** Notes must be clear and concise — 300 characters or less each. Group by topic, not by date. Whenever a PR review (CodeRabbit or human) catches a mistake, add or amend a note here right away so it isn't repeated.

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
