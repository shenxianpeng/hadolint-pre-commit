"""Tests for the wheel platform tags set in setup.py."""

from __future__ import annotations

import platform
import runpy
from pathlib import Path
from typing import Any

import pytest
import setuptools
from setuptools.dist import Distribution

SETUP_PY = Path(__file__).resolve().parent.parent / 'setup.py'


@pytest.fixture
def setup_calls(monkeypatch: pytest.MonkeyPatch) -> list[dict[str, Any]]:
    """Record ``setup()`` calls instead of running a real build."""
    calls: list[dict[str, Any]] = []
    monkeypatch.setattr(setuptools, 'setup', lambda **kwargs: calls.append(kwargs))
    return calls


@pytest.fixture
def setup_py(setup_calls: list[dict[str, Any]]) -> dict[str, Any]:
    """Run setup.py and return its globals."""
    return runpy.run_path(str(SETUP_PY), run_name='setup_under_test')


# --- platform_tag ------------------------------------------------------------


@pytest.mark.parametrize(
    ('plat', 'machine', 'expected'),
    [
        # PyPI rejects bare linux_* tags.
        ('linux_x86_64', 'x86_64', 'manylinux_2_17_x86_64'),
        ('linux_aarch64', 'aarch64', 'manylinux_2_17_aarch64'),
        # universal2 interpreters (python.org, actions/setup-python) get the
        # real arch of the bundled binary.
        ('macosx_10_15_universal2', 'arm64', 'macosx_11_0_arm64'),
        ('macosx_10_15_universal2', 'x86_64', 'macosx_10_15_x86_64'),
        ('macosx_10_9_universal2', 'x86_64', 'macosx_10_9_x86_64'),
        # Single-arch interpreters already carry the right arch.
        ('macosx_11_0_arm64', 'arm64', 'macosx_11_0_arm64'),
        ('macosx_10_15_x86_64', 'x86_64', 'macosx_10_15_x86_64'),
        ('win_amd64', 'AMD64', 'win_amd64'),
    ],
)
def test_platform_tag(setup_py: dict[str, Any], plat: str, machine: str, expected: str) -> None:
    assert setup_py['platform_tag'](plat, machine) == expected


def test_macos_wheels_get_distinct_tags(setup_py: dict[str, Any]) -> None:
    """Regression test for #37.

    Both macOS runners build with a universal2 interpreter. If the Intel and
    arm64 wheels end up with the same filename, one overwrites the other (or
    both get interleaved) when the publish job collects them.
    """
    platform_tag = setup_py['platform_tag']
    intel = platform_tag('macosx_10_15_universal2', 'x86_64')
    arm = platform_tag('macosx_10_15_universal2', 'arm64')
    assert intel != arm
    assert 'universal2' not in intel
    assert 'universal2' not in arm


# --- bdist_wheel -------------------------------------------------------------


def test_setup_registers_bdist_wheel(setup_py: dict[str, Any], setup_calls: list[dict[str, Any]]) -> None:
    assert setup_calls == [{'cmdclass': {'bdist_wheel': setup_py['bdist_wheel']}}]


def test_wheel_is_not_pure(setup_py: dict[str, Any]) -> None:
    cmd = setup_py['bdist_wheel'](Distribution())
    cmd.ensure_finalized()
    assert cmd.root_is_pure is False


@pytest.mark.parametrize(
    ('machine', 'expected'),
    [('arm64', 'macosx_11_0_arm64'), ('x86_64', 'macosx_10_15_x86_64')],
)
def test_get_tag_on_universal2_interpreter(
    setup_py: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
    machine: str,
    expected: str,
) -> None:
    orig = setup_py['orig_bdist_wheel']
    monkeypatch.setattr(orig, 'get_tag', lambda self: ('cp313', 'cp313', 'macosx_10_15_universal2'))
    monkeypatch.setattr(platform, 'machine', lambda: machine)

    cmd = setup_py['bdist_wheel'](Distribution())
    assert cmd.get_tag() == ('py3', 'none', expected)
