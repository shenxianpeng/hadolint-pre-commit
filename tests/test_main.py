from __future__ import annotations

import os
import runpy
import subprocess
import sys
from pathlib import Path

import pytest

from hadolint_py import __main__ as cli

REPO_ROOT = Path(__file__).resolve().parent.parent


class FakeExec:
    """Stand-in for ``os.execvp`` that records calls instead of replacing the process."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, list[str]]] = []

    def __call__(self, file: str, args: list[str]) -> None:
        self.calls.append((file, list(args)))


@pytest.fixture
def fake_exec(monkeypatch: pytest.MonkeyPatch) -> FakeExec:
    fake = FakeExec()
    monkeypatch.setattr(os, 'execvp', fake)
    return fake


@pytest.fixture
def bin_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point ``sys.executable`` at an interpreter inside a fresh, empty bin dir."""
    bin_dir = tmp_path / 'bin'
    bin_dir.mkdir()
    monkeypatch.setattr(sys, 'executable', str(bin_dir / 'python'))
    return bin_dir


@pytest.fixture
def argv(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, 'argv', ['hadolint'])


# --- executable name ---------------------------------------------------------


@pytest.mark.usefixtures('argv')
@pytest.mark.parametrize(
    ('platform', 'expected'),
    [
        ('win32', 'hadolint.exe'),
        ('linux', 'hadolint'),
        ('darwin', 'hadolint'),
        ('cygwin', 'hadolint'),
    ],
)
def test_exe_name_depends_on_platform(
    platform: str,
    expected: str,
    bin_dir: Path,
    fake_exec: FakeExec,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sys, 'platform', platform)

    cli.main()

    assert fake_exec.calls == [(expected, [expected])]


# --- locating the binary -----------------------------------------------------


@pytest.mark.usefixtures('argv')
@pytest.mark.parametrize(
    ('platform', 'exe_name'),
    [('win32', 'hadolint.exe'), ('linux', 'hadolint')],
)
def test_prefers_binary_next_to_interpreter(
    platform: str,
    exe_name: str,
    bin_dir: Path,
    fake_exec: FakeExec,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sys, 'platform', platform)
    candidate = bin_dir / exe_name
    candidate.write_bytes(b'')

    cli.main()

    assert fake_exec.calls == [(str(candidate), [str(candidate)])]


@pytest.mark.usefixtures('argv')
def test_falls_back_to_path_when_candidate_missing(
    bin_dir: Path,
    fake_exec: FakeExec,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sys, 'platform', 'linux')
    assert not (bin_dir / 'hadolint').exists()

    cli.main()

    assert fake_exec.calls == [('hadolint', ['hadolint'])]


@pytest.mark.usefixtures('argv')
def test_candidate_must_be_a_regular_file(
    bin_dir: Path,
    fake_exec: FakeExec,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A directory called ``hadolint`` next to the interpreter is not a binary."""
    monkeypatch.setattr(sys, 'platform', 'linux')
    (bin_dir / 'hadolint').mkdir()

    cli.main()

    assert fake_exec.calls == [('hadolint', ['hadolint'])]


@pytest.mark.usefixtures('argv')
def test_ignores_binary_for_other_platform(
    bin_dir: Path,
    fake_exec: FakeExec,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """On win32 only ``hadolint.exe`` counts; a bare ``hadolint`` is ignored."""
    monkeypatch.setattr(sys, 'platform', 'win32')
    (bin_dir / 'hadolint').write_bytes(b'')

    cli.main()

    assert fake_exec.calls == [('hadolint.exe', ['hadolint.exe'])]


# --- argument forwarding -----------------------------------------------------


def test_forwards_all_arguments(
    bin_dir: Path,
    fake_exec: FakeExec,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sys, 'platform', 'linux')
    args = ['--ignore', 'DL3008', '--failure-threshold', 'warning', 'Dockerfile']
    monkeypatch.setattr(sys, 'argv', ['hadolint', *args])

    cli.main()

    assert fake_exec.calls == [('hadolint', ['hadolint', *args])]


def test_argv0_is_replaced_by_the_resolved_exe(
    bin_dir: Path,
    fake_exec: FakeExec,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The wrapper's own argv[0] is dropped; the child's argv[0] is the exe."""
    monkeypatch.setattr(sys, 'platform', 'linux')
    candidate = bin_dir / 'hadolint'
    candidate.write_bytes(b'')
    monkeypatch.setattr(sys, 'argv', ['/somewhere/else/hadolint-wrapper', '--version'])

    cli.main()

    assert fake_exec.calls == [(str(candidate), [str(candidate), '--version'])]


def test_arguments_are_forwarded_verbatim(
    bin_dir: Path,
    fake_exec: FakeExec,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Nothing is parsed, re-quoted or deduplicated on the way through."""
    monkeypatch.setattr(sys, 'platform', 'linux')
    args = ['--ignore', 'DL3008', '--ignore', 'DL3008', '', 'path with spaces/Dockerfile', '-']
    monkeypatch.setattr(sys, 'argv', ['hadolint', *args])

    cli.main()

    (_, forwarded), = fake_exec.calls
    assert forwarded[1:] == args


# --- error handling ----------------------------------------------------------


@pytest.mark.usefixtures('argv')
@pytest.mark.parametrize(
    'cause',
    [
        FileNotFoundError(2, 'No such file or directory'),
        PermissionError(13, 'Permission denied'),
        OSError('generic failure'),
    ],
    ids=lambda exc: type(exc).__name__,
)
def test_oserror_is_wrapped_in_runtime_error(
    cause: OSError,
    bin_dir: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sys, 'platform', 'linux')

    def failing_exec(file: str, args: list[str]) -> None:
        raise cause

    monkeypatch.setattr(os, 'execvp', failing_exec)

    with pytest.raises(RuntimeError) as excinfo:
        cli.main()

    assert str(excinfo.value) == "Failed to execute 'hadolint'"
    assert excinfo.value.__cause__ is cause


@pytest.mark.usefixtures('argv')
def test_runtime_error_names_the_full_candidate_path(
    bin_dir: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sys, 'platform', 'linux')
    candidate = bin_dir / 'hadolint'
    candidate.write_bytes(b'')
    cause = PermissionError(13, 'Permission denied')

    def failing_exec(file: str, args: list[str]) -> None:
        raise cause

    monkeypatch.setattr(os, 'execvp', failing_exec)

    with pytest.raises(RuntimeError) as excinfo:
        cli.main()

    assert str(excinfo.value) == f'Failed to execute {str(candidate)!r}'
    assert excinfo.value.__cause__ is cause


@pytest.mark.usefixtures('argv')
def test_non_oserror_exceptions_propagate_unchanged(
    bin_dir: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sys, 'platform', 'linux')

    def failing_exec(file: str, args: list[str]) -> None:
        raise ValueError('embedded null byte')

    monkeypatch.setattr(os, 'execvp', failing_exec)

    with pytest.raises(ValueError, match='embedded null byte'):
        cli.main()


# --- `python -m hadolint_py` -------------------------------------------------


def test_running_as_main_module_calls_main(
    bin_dir: Path,
    fake_exec: FakeExec,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sys, 'platform', 'linux')
    monkeypatch.setattr(sys, 'argv', ['hadolint', '--version'])
    # runpy warns if the module is already imported (it is, at the top of this
    # file); drop it for the duration of the test, monkeypatch restores it.
    monkeypatch.delitem(sys.modules, 'hadolint_py.__main__', raising=False)

    runpy.run_module('hadolint_py', run_name='__main__')

    assert fake_exec.calls == [('hadolint', ['hadolint', '--version'])]


@pytest.mark.usefixtures('argv')
def test_importing_the_module_does_not_exec(
    bin_dir: Path,
    fake_exec: FakeExec,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sys, 'platform', 'linux')
    monkeypatch.delitem(sys.modules, 'hadolint_py.__main__', raising=False)

    # Same code path as `import hadolint_py.__main__`: __name__ is the dotted
    # module name, so the `if __name__ == '__main__'` guard must not fire.
    namespace = runpy.run_module('hadolint_py')

    assert namespace['__name__'] == 'hadolint_py.__main__'
    assert fake_exec.calls == []


@pytest.mark.skipif(
    sys.platform == 'win32',
    reason='needs a shell script as fake hadolint and a symlinked interpreter',
)
def test_end_to_end_process_is_replaced_by_hadolint_on_path(tmp_path: Path) -> None:
    """Run ``python -m hadolint_py`` for real, with a fake ``hadolint`` first on PATH.

    The interpreter is invoked through a symlink in an otherwise empty directory
    so that a real hadolint installed next to python (e.g. in CI) is not picked
    up. The fake script's exit code reaching us proves the process was replaced
    rather than spawned.
    """
    fake_bin = tmp_path / 'fake-bin'
    fake_bin.mkdir()
    script = fake_bin / 'hadolint'
    script.write_text('#!/bin/sh\necho "fake hadolint: $*"\nexit 3\n')
    script.chmod(0o755)

    shadow_bin = tmp_path / 'shadow-bin'
    shadow_bin.mkdir()
    python = shadow_bin / 'python'
    python.symlink_to(sys.executable)

    env = {**os.environ, 'PATH': f'{fake_bin}{os.pathsep}{os.environ.get("PATH", "")}'}
    proc = subprocess.run(
        [str(python), '-m', 'hadolint_py', '--ignore', 'DL3008', 'Dockerfile'],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 3, proc.stderr
    assert proc.stdout == 'fake hadolint: --ignore DL3008 Dockerfile\n'
