from __future__ import annotations

from setuptools import setup

try:
    from setuptools.command.bdist_wheel import bdist_wheel as orig_bdist_wheel
except ImportError:
    cmdclass = {}
else:
    class bdist_wheel(orig_bdist_wheel):
        def finalize_options(self) -> None:
            orig_bdist_wheel.finalize_options(self)
            # Mark as not a pure Python package so the wheel gets a platform tag;
            # this project bundles a platform-specific hadolint binary/script.
            self.root_is_pure = False

        def get_tag(self) -> tuple[str, str, str]:
            _, _, plat = orig_bdist_wheel.get_tag(self)
            # The Python modules are pure Python (py3/none); the platform tag comes
            # from the bundled platform-specific hadolint binary/script.
            return 'py3', 'none', plat

    cmdclass = {'bdist_wheel': bdist_wheel}

setup(cmdclass=cmdclass)
