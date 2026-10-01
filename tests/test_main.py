from __future__ import annotations

import os
import runpy
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from hadolint_py import __main__ as hadolint_main

ROOT = Path(__file__).resolve().parent.parent


def _installed_hadolint() -> str | None:
    exe_name = 'hadolint.exe' if sys.platform == 'win32' else 'hadolint'
    candidate = os.path.join(os.path.dirname(sys.executable), exe_name)
    return candidate if os.path.isfile(candidate) else shutil.which('hadolint')


requires_hadolint = pytest.mark.skipif(
    _installed_hadolint() is None,
    reason='hadolint binary not installed (run `pip install .`)',
)


class Exec(Exception):
    """Stands in for a successful exec, which never returns."""


@pytest.fixture
def execvp(monkeypatch: pytest.MonkeyPatch) -> list[tuple[str, list[str]]]:
    calls: list[tuple[str, list[str]]] = []

    def fake_execvp(file: str, args: list[str]) -> None:
        calls.append((file, args))
        raise Exec

    monkeypatch.setattr(os, 'execvp', fake_execvp)
    return calls


@pytest.fixture
def interpreter_dir(
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
) -> Path:
    """Pretend the running interpreter lives in an empty temporary dir."""
    bindir = tmp_path / 'venv-bin'
    bindir.mkdir()
    monkeypatch.setattr(sys, 'executable', str(bindir / 'python'))
    monkeypatch.setattr(sys, 'platform', 'linux')
    monkeypatch.setattr(sys, 'argv', ['hadolint_py'])
    return bindir


def test_prefers_binary_next_to_the_interpreter(
        interpreter_dir: Path,
        execvp: list[tuple[str, list[str]]],
) -> None:
    binary = interpreter_dir / 'hadolint'
    binary.touch()

    with pytest.raises(Exec):
        hadolint_main.main()

    assert execvp == [(str(binary), [str(binary)])]


def test_forwards_arguments_verbatim(
        interpreter_dir: Path,
        execvp: list[tuple[str, list[str]]],
        monkeypatch: pytest.MonkeyPatch,
) -> None:
    binary = interpreter_dir / 'hadolint'
    binary.touch()
    args = ['--ignore', 'DL3008', '--format=json', 'dir with space/Dockerfile']
    monkeypatch.setattr(sys, 'argv', ['hadolint_py', *args])

    with pytest.raises(Exec):
        hadolint_main.main()

    assert execvp == [(str(binary), [str(binary), *args])]


def test_falls_back_to_path_lookup(
        interpreter_dir: Path,
        execvp: list[tuple[str, list[str]]],
        monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sys, 'argv', ['hadolint_py', 'Dockerfile'])

    with pytest.raises(Exec):
        hadolint_main.main()

    # A bare name makes os.execvp search PATH.
    assert execvp == [('hadolint', ['hadolint', 'Dockerfile'])]


def test_ignores_a_directory_named_like_the_binary(
        interpreter_dir: Path,
        execvp: list[tuple[str, list[str]]],
) -> None:
    (interpreter_dir / 'hadolint').mkdir()

    with pytest.raises(Exec):
        hadolint_main.main()

    assert execvp == [('hadolint', ['hadolint'])]


def test_uses_exe_suffix_on_windows(
        interpreter_dir: Path,
        execvp: list[tuple[str, list[str]]],
        monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sys, 'platform', 'win32')
    (interpreter_dir / 'hadolint').touch()  # not the Windows binary name
    binary = interpreter_dir / 'hadolint.exe'
    binary.touch()

    with pytest.raises(Exec):
        hadolint_main.main()

    assert execvp == [(str(binary), [str(binary)])]


def test_exec_failure_raises_runtime_error(
        interpreter_dir: Path,
        monkeypatch: pytest.MonkeyPatch,
) -> None:
    error = FileNotFoundError(2, 'No such file or directory')

    def fake_execvp(file: str, args: list[str]) -> None:
        raise error

    monkeypatch.setattr(os, 'execvp', fake_execvp)

    with pytest.raises(RuntimeError) as excinfo:
        hadolint_main.main()

    assert str(excinfo.value) == "Failed to execute 'hadolint'"
    assert excinfo.value.__cause__ is error


def test_python_dash_m_runs_main(
        interpreter_dir: Path,
        execvp: list[tuple[str, list[str]]],
        monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Run `python -m hadolint_py --version` in-process; drop the cached
    # module first so runpy executes a fresh copy without warning about it.
    monkeypatch.delitem(sys.modules, 'hadolint_py.__main__', raising=False)
    monkeypatch.setattr(sys, 'argv', ['hadolint_py', '--version'])

    with pytest.raises(Exec):
        runpy.run_module('hadolint_py', run_name='__main__')

    assert execvp == [('hadolint', ['hadolint', '--version'])]


def _python_m_hadolint_py(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        (sys.executable, '-m', 'hadolint_py', *args),
        cwd=ROOT,  # `-m` then imports the source tree's hadolint_py
        capture_output=True,
        text=True,
        check=False,
    )


@requires_hadolint
def test_python_dash_m_runs_the_installed_binary() -> None:
    result = _python_m_hadolint_py('--version')

    assert result.returncode == 0, result.stderr
    assert 'Haskell Dockerfile Linter' in result.stdout
