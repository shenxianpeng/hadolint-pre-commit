from __future__ import annotations

import runpy
from pathlib import Path
from typing import Any

import pytest
import setuptools
from setuptools.command.bdist_wheel import bdist_wheel as orig_bdist_wheel
from setuptools.dist import Distribution

SETUP_PY = Path(__file__).resolve().parent.parent / 'setup.py'


@pytest.fixture(scope='module')
def setup_kwargs() -> dict[str, Any]:
    """Execute setup.py, capturing the arguments it passes to setup()."""
    captured: dict[str, Any] = {}
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(setuptools, 'setup', lambda **kwargs: captured.update(kwargs))
        runpy.run_path(str(SETUP_PY))
    return captured


@pytest.fixture
def make_cmd(
        setup_kwargs: dict[str, Any],
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
) -> Any:
    monkeypatch.chdir(tmp_path)  # keep any build paths out of the checkout
    cls = setup_kwargs['cmdclass']['bdist_wheel']

    def make(plat_name: str | None = None) -> Any:
        dist = Distribution({'name': 'hadolint-py', 'version': '2.15.1.0'})
        cmd = cls(dist)
        cmd.plat_name = plat_name
        cmd.ensure_finalized()
        return cmd

    return make


def test_setup_registers_custom_bdist_wheel(
        setup_kwargs: dict[str, Any],
) -> None:
    assert set(setup_kwargs) == {'cmdclass'}
    cls = setup_kwargs['cmdclass']['bdist_wheel']
    assert issubclass(cls, orig_bdist_wheel)
    assert cls is not orig_bdist_wheel


def test_wheel_is_never_pure(make_cmd: Any) -> None:
    # The package is pure Python, but each wheel bundles a native binary.
    assert make_cmd().root_is_pure is False


@pytest.mark.parametrize(
    ('plat_name', 'expected'),
    (
        ('linux-x86_64', 'manylinux_2_17_x86_64'),
        ('linux-aarch64', 'manylinux_2_17_aarch64'),
        ('linux_x86_64', 'manylinux_2_17_x86_64'),
    ),
)
def test_linux_tags_become_manylinux(
        make_cmd: Any,
        plat_name: str,
        expected: str,
) -> None:
    # PyPI rejects bare linux_* wheels.
    assert make_cmd(plat_name).get_tag() == ('py3', 'none', expected)


@pytest.mark.parametrize(
    ('plat_name', 'expected'),
    (
        ('macosx-10.9-x86_64', 'macosx_10_9_x86_64'),
        ('macosx-11.0-arm64', 'macosx_11_0_arm64'),
        ('win-amd64', 'win_amd64'),
        # Only a leading linux_ is rewritten.
        ('manylinux_2_17_x86_64', 'manylinux_2_17_x86_64'),
    ),
)
def test_other_platform_tags_are_kept(
        make_cmd: Any,
        plat_name: str,
        expected: str,
) -> None:
    assert make_cmd(plat_name).get_tag() == ('py3', 'none', expected)


def test_native_tag_is_platform_specific(make_cmd: Any) -> None:
    impl, abi, plat = make_cmd().get_tag()

    assert (impl, abi) == ('py3', 'none')
    assert plat != 'any'
    assert not plat.startswith('linux_')
