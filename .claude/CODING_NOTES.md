# Coding Best Practices & Reminders

## Resource Cleanup & Temporary Files

**IMPORTANT**: Always add proper cleanup code in programs to prevent lingering temp files after closing.

### Best Practices:

1. **GUI Applications (PyQt, Tkinter, etc.)**
   - Implement `closeEvent()` handler to cleanup resources on window close
   - Call `deleteLater()` on widgets from `closeEvent()`/`aboutToQuit` — while the event loop is still
     running, so the deferred-delete event actually gets processed. Calling it after `app.exec()` has
     already returned is unreliable; don't rely on a trailing `app.processEvents()` to make up for it.

2. **File Handling**
   - Use context managers (`with` statements) for file operations
   - Explicitly close file handles when not using context managers
   - Release file locks before program exit
   - Clean up temporary files in temp directories

3. **Background Threads & Workers**
   - Stop and join all background threads before exit
   - Cancel any pending operations
   - Clean up thread-specific resources

4. **Testing Cleanup**
   - After closing the program, verify the executable can be:
     - Deleted immediately
     - Moved to another location
     - Replaced with a new version
   - If the file is locked, cleanup code is missing or incomplete

### Example Implementation (PyQt6):

```python
def closeEvent(self, event):
    """Handle window close event - ensure proper cleanup"""
    # Cleanup modules/components
    for module in self.modules:
        try:
            module.cleanup()
        except Exception as e:
            print(f"Error cleaning up module: {e}")

    # Save state
    self.save_settings()

    # Schedule deletion now, while the event loop is still running.
    self.deleteLater()
    event.accept()
    QApplication.quit()

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()

    exit_code = app.exec()  # returns once the window above has closed and scheduled its own cleanup

    sys.exit(exit_code)
```

### PyInstaller Specific:

`bootloader_ignore_signals=True` makes the bootloader stop forwarding OS signals (e.g. SIGTERM) to the
packaged app — only relevant if a supervisor or parent process group sends signals to manage shutdown.
It is not a general-purpose cleanup fix; if you set it, verify shutdown still behaves correctly under
that supervisor (e.g. the app still exits when asked, and your `closeEvent`/cleanup still runs).

```python
exe = EXE(
    ...
    bootloader_ignore_signals=True,
    ...
)
```

## Date: 2025-12-16
This note was created based on issues encountered with PyInstaller executables remaining locked after closing.
