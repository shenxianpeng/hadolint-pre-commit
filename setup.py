from __future__ import annotations

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
