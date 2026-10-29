from __future__ import annotations

# WHY THIS FILE EXISTS
# --------------------
# All project metadata lives in pyproject.toml. This file exists solely to
# override bdist_wheel so that each platform wheel gets a platform-specific
# tag (e.g. manylinux_2_17_x86_64, macosx_11_0_arm64) even though the Python
# code itself is pure Python.
#
# Background: this package bundles a pre-built hadolint binary that is
# downloaded at install time via setuptools-download. Because each wheel is
# only valid on one platform, it must carry a platform tag so pip selects the
# right one. Setuptools has no pyproject.toml-native way to override cmdclass,
# so a minimal setup.py is still required.
#
# Linux note: PyPI rejects bare linux_* tags. We map them to manylinux_2_17_*
# because hadolint ships statically linked binaries that run on any modern
# Linux distribution (glibc >= 2.17).
#
# macOS note: python.org and actions/setup-python interpreters are universal2
# builds, so setuptools tags every macOS wheel *_universal2 — on Intel and on
# Apple Silicon alike. The bundled hadolint binary is single-arch, so we
# replace universal2 with the real arch. Without this, the Intel and arm64
# wheels share one filename and overwrite each other when published (#37).

import platform

from setuptools import setup
from setuptools.command.bdist_wheel import bdist_wheel as orig_bdist_wheel


def platform_tag(plat: str, machine: str) -> str:
    """Return the wheel platform tag for a hadolint binary built for ``machine``.

    ``plat`` is the tag setuptools derives from the running interpreter and
    ``machine`` is ``platform.machine()``, which is also what setup.cfg's
    setuptools-download markers use to pick the binary.
    """
    if plat.startswith('linux_'):
        return plat.replace('linux_', 'manylinux_2_17_', 1)
    if plat.startswith('macosx_') and plat.endswith('_universal2'):
        if machine == 'arm64':
            # Apple Silicon starts at macOS 11; pip accepts no older arm64 tag.
            return 'macosx_11_0_arm64'
        return plat[: -len('universal2')] + machine
    return plat


class bdist_wheel(orig_bdist_wheel):
    def finalize_options(self) -> None:
        orig_bdist_wheel.finalize_options(self)
        self.root_is_pure = False

    def get_tag(self) -> tuple[str, str, str]:
        _, _, plat = orig_bdist_wheel.get_tag(self)
        return 'py3', 'none', platform_tag(plat, platform.machine())


setup(cmdclass={'bdist_wheel': bdist_wheel})
