from __future__ import annotations

import os
import subprocess
import sys
from typing import NoReturn


def _which(exe_name: str) -> str | None:
    """Look ``exe_name`` up on PATH only, the way ``os.execvp`` does."""
    for directory in os.get_exec_path():
        path = os.path.join(directory, exe_name)
        if os.path.isfile(path):
            return path
    return None


def main() -> NoReturn:
    exe_name = 'hadolint.exe' if sys.platform == 'win32' else 'hadolint'

    # Prefer the binary installed alongside the current Python interpreter
    # (e.g. inside the pre-commit virtualenv created by `language: python`).
    candidate = os.path.join(os.path.dirname(sys.executable), exe_name)
    if os.path.isfile(candidate):
        exe = candidate
    else:
        # Fall back to whatever is on PATH
        exe = exe_name

    try:
        if sys.platform == 'win32':
            # os.exec*() cannot replace the running process on Windows: it
            # starts the program in a new process and exits at once with
            # status 0, so lint failures would look like success. Run
            # hadolint as a child process and exit with its status instead.
            # A bare name is resolved on PATH here, as os.execvp() does,
            # because CreateProcess() would search the current directory
            # first.
            path = exe if os.path.isabs(exe) else _which(exe)
            if path is None:
                raise FileNotFoundError(exe)
            sys.exit(subprocess.call([path, *sys.argv[1:]]))
        os.execvp(exe, [exe, *sys.argv[1:]])
    except OSError as exc:
        raise RuntimeError(f"Failed to execute {exe!r}") from exc


if __name__ == '__main__':
    main()
