from __future__ import annotations

import os
import sys
from typing import NoReturn


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
        os.execvp(exe, [exe, *sys.argv[1:]])
    except OSError as exc:
        raise RuntimeError(f"Failed to execute {exe!r}") from exc


if __name__ == '__main__':
    main()
