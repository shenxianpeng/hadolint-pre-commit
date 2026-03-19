from __future__ import annotations

# WHY THIS FILE EXISTS
# --------------------
# All project metadata lives in pyproject.toml. This file exists solely to
# override bdist_wheel so that each platform wheel gets a platform-specific
# tag (e.g. linux_x86_64, macosx_arm64) even though the Python code itself
# is pure Python.
#
# Background: this package bundles a pre-built hadolint binary that is
# downloaded at install time via setuptools-download. Because each wheel is
# only valid on one platform, it must carry a platform tag so pip selects the
# right one. Setuptools has no pyproject.toml-native way to override cmdclass,
# so a minimal setup.py is still required.

from setuptools import setup
from setuptools.command.bdist_wheel import bdist_wheel as orig_bdist_wheel


class bdist_wheel(orig_bdist_wheel):
    def finalize_options(self) -> None:
        orig_bdist_wheel.finalize_options(self)
        self.root_is_pure = False

    def get_tag(self) -> tuple[str, str, str]:
        _, _, plat = orig_bdist_wheel.get_tag(self)
        return 'py3', 'none', plat


setup(cmdclass={'bdist_wheel': bdist_wheel})
