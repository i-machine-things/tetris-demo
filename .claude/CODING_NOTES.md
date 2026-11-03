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
