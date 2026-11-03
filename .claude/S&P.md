# Standards & Practices — CodeRabbit Review Log

<!--
Add entries here each time a CodeRabbit or human review surfaces a new finding.
Format:

## YYYY-MM-DD — `path/to/file` (short description)

**Review:** WHAT WAS FLAGGED
**Result:** outcome / resolution

### Findings

1. **Title**
   - Detail
   - Fix applied
-->

## 2026-11-03 — `tetris/widget.py`, `main.py`, `.github/workflows/ci.yml`, `.claude/CLAUDE.md`, `.claude/CODING_NOTES.md` (PR #1 initial review)

**Review:** CodeRabbit's first-pass review of the PyQt6 scaffold PR — 7 findings (1 major, 6 minor).
**Result:** all fixed on the same branch before merge.

### Findings

1. **GameWindow never requests keyboard focus (major)**
   - `QMainWindow` doesn't reliably grab keyboard focus just by calling `.show()`, so arrow/space/P
     input could silently do nothing until the user clicked into the window.
   - Fix: `setFocusPolicy(Qt.FocusPolicy.StrongFocus)` in `__init__`, plus a `showEvent` override
     that calls `self.setFocus()`.

2. **Held P/Space keys re-trigger one-shot actions**
   - Qt's key-repeat kept toggling pause and re-hard-dropping while a key was held.
   - Fix: `keyPressEvent` now ignores `event.isAutoRepeat()` for `Key_P` and `Key_Space`; movement
     keys still repeat normally.

3. **`main.py` scheduled cleanup after the event loop already stopped**
   - `window.deleteLater(); app.processEvents()` ran *after* `app.exec()` returned — the same
     anti-pattern flagged in finding 4 below, just in the actual app code instead of the docs.
     `GameWindow.closeEvent` already stops the timer, so the extra calls were dead weight.
   - Fix: trimmed `main()` to `app.exec()` → `sys.exit(...)`.

4. **`CODING_NOTES.md` example scheduled `deleteLater()` after `app.exec()` returned**
   - Deferred deletion needs a running event loop to actually process; calling it after `exec()`
     returns and relying on one `processEvents()` call to flush it is unreliable.
   - Fix: moved `deleteLater()` into the `closeEvent()` example, called while the loop is still up.

5. **`CODING_NOTES.md` presented `bootloader_ignore_signals=True` as generic cleanup advice**
   - It only matters when a supervisor/parent process group sends signals to manage shutdown, and
     isn't a general "better cleanup" switch.
   - Fix: reworded to scope it to that case and added a note to verify shutdown behavior if set.

6. **CI workflow had no `permissions:` block**
   - Default `GITHUB_TOKEN` permissions are broader than this workflow needs.
   - Fix: added top-level `permissions: contents: read`.

7. **`CLAUDE.md` claimed pushing a `v*` tag "triggers the release workflow"**
   - No release workflow exists in this repo — tagging is a manual convention only.
   - Fix: reworded Rule 4 to say so explicitly, and fixed the version-bump-count baseline command to
     match only `v*` tags (`git describe --tags --match "v*" --abbrev=0`) with a fallback for the
     no-tag-yet case.
