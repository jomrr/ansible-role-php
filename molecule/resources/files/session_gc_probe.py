"""Exercise the deployed session cleanup service against aged and live data."""

import os
from pathlib import Path
import subprocess
import sys
import time


def main() -> None:
    """Check actual deletion, retention, and unenrollment without waiting for expiry."""
    directory = Path(sys.argv[1])
    enrolled = sys.argv[2] == "enrolled"
    stale = directory / "sess_moleculestale"
    recent = directory / "sess_moleculerecent"
    outside = directory.parent / "sess_moleculeoutside"
    files = [stale, recent, outside]
    for path in files:
        path.write_text("cleanup fixture", encoding="utf-8")
    old = time.time() - 7200
    os.utime(stale, (old, old))
    os.utime(outside, (old, old))
    try:
        subprocess.run(
            ["systemctl", "start", "php-ansible-session-gc.service"], check=True
        )
        assert stale.exists() != enrolled, "Cleanup did not respect registered paths"
        assert recent.exists(), "Cleanup deleted an unexpired session"
        assert outside.exists(), "Cleanup escaped its registered directory"
    finally:
        for path in files:
            path.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
