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


@pytest.fixture
def windows(
        interpreter_dir: Path,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
) -> list[list[str]]:
    """Pretend to run on Windows; record subprocess.call() invocations."""
    calls: list[list[str]] = []

    def fake_call(args: list[str]) -> int:
        calls.append(args)
        return 1  # hadolint found problems

    def fake_execvp(file: str, args: list[str]) -> None:
        raise AssertionError('os.execvp() loses the exit status on Windows')

    empty_path = tmp_path / 'empty-path'
    empty_path.mkdir()
    monkeypatch.setenv('PATH', str(empty_path))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, 'platform', 'win32')
    monkeypatch.setattr(subprocess, 'call', fake_call)
    monkeypatch.setattr(os, 'execvp', fake_execvp)
    return calls


def test_windows_exits_with_hadolint_status(
        interpreter_dir: Path,
        windows: list[list[str]],
        monkeypatch: pytest.MonkeyPatch,
) -> None:
    (interpreter_dir / 'hadolint').touch()  # not the Windows binary name
    binary = interpreter_dir / 'hadolint.exe'
    binary.touch()
    monkeypatch.setattr(sys, 'argv', ['hadolint_py', 'Dockerfile'])

    with pytest.raises(SystemExit) as excinfo:
        hadolint_main.main()

    assert excinfo.value.code == 1
    assert windows == [[str(binary), 'Dockerfile']]


def test_windows_falls_back_to_path_lookup(
        interpreter_dir: Path,
        windows: list[list[str]],
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
) -> None:
    scripts = tmp_path / 'Scripts'
    scripts.mkdir()
    binary = scripts / 'hadolint.exe'
    binary.touch()
    monkeypatch.setenv('PATH', os.pathsep.join(('missing', str(scripts))))

    with pytest.raises(SystemExit) as excinfo:
        hadolint_main.main()

    assert excinfo.value.code == 1
    assert windows == [[str(binary)]]


def test_windows_never_runs_hadolint_from_the_current_directory(
        interpreter_dir: Path,
        windows: list[list[str]],
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = tmp_path / 'project'
    project.mkdir()
    (project / 'hadolint.exe').touch()
    monkeypatch.chdir(project)

    with pytest.raises(RuntimeError) as excinfo:
        hadolint_main.main()

    assert str(excinfo.value) == "Failed to execute 'hadolint.exe'"
    assert isinstance(excinfo.value.__cause__, FileNotFoundError)
    assert windows == []


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


@requires_hadolint
def test_python_dash_m_exits_with_hadolint_status(tmp_path: Path) -> None:
    dockerfile = tmp_path / 'Dockerfile'
    dockerfile.write_text('FROM\n')  # a parse error fails under any config

    result = _python_m_hadolint_py(str(dockerfile))

    assert result.returncode == 1, (result.stdout, result.stderr)
