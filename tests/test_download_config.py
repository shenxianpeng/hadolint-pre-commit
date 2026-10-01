"""Consistency checks for the hadolint binaries pinned in setup.cfg.

setuptools-download fetches the binary for the build platform at wheel build
time (and when pre-commit installs the hook from source) and rejects it
unless its sha256 matches. These tests catch copy/paste mistakes when the
pinned hadolint version is bumped.
"""
from __future__ import annotations

import collections
import configparser
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

# (sys_platform, platform_machine) -> (installed script, release asset)
PLATFORMS = {
    ('linux', 'x86_64'): ('hadolint', 'hadolint-linux-x86_64'),
    ('linux', 'aarch64'): ('hadolint', 'hadolint-linux-arm64'),
    ('darwin', 'x86_64'): ('hadolint', 'hadolint-macos-x86_64'),
    ('darwin', 'arm64'): ('hadolint', 'hadolint-macos-arm64'),
    ('win32', 'AMD64'): ('hadolint.exe', 'hadolint-windows-x86_64.exe'),
}
RELEASE_URL = re.compile(
    r'https://github\.com/hadolint/hadolint/releases/download/'
    r'v(?P<version>\d+\.\d+\.\d+)/(?P<asset>[^/]+)',
)
# Same sub-section syntax setuptools-download parses.
SUBSECTION = re.compile(r'^\[([^]\n]+)\]$', re.MULTILINE)


def _download_scripts() -> list[tuple[str, dict[str, str]]]:
    cfg = configparser.ConfigParser(interpolation=None)
    cfg.read(ROOT / 'setup.cfg', encoding='utf-8')
    parts = SUBSECTION.split(
        cfg['setuptools_download']['download_scripts'].strip(),
    )
    assert parts[0] == ''

    entries = []
    for path, body in zip(parts[1::2], parts[2::2]):
        values = {}
        for line in body.strip().splitlines():
            key, value = line.split('=', 1)
            values[key.strip()] = value.strip()
        entries.append((path, values))
    return entries


def _platform(marker: str) -> tuple[str, str]:
    env = {}
    for chunk in marker.split(' and '):
        key, op, value = chunk.split()
        assert op == '=='
        env[key] = value.strip('"')
    assert set(env) == {'sys_platform', 'platform_machine'}
    return env['sys_platform'], env['platform_machine']


ENTRIES = _download_scripts()
IDS = ['-'.join(_platform(values['marker'])) for _, values in ENTRIES]


def _bundled_version() -> str:
    versions = {
        m['version']
        for _, values in ENTRIES
        if (m := RELEASE_URL.fullmatch(values['url']))
    }
    assert len(versions) == 1, versions
    return versions.pop()


def test_each_supported_platform_gets_exactly_one_binary() -> None:
    counts = collections.Counter(
        _platform(values['marker']) for _, values in ENTRIES
    )
    assert counts == dict.fromkeys(PLATFORMS, 1)


@pytest.mark.parametrize(('path', 'values'), ENTRIES, ids=IDS)
def test_binary_is_an_official_hadolint_release_asset(
        path: str,
        values: dict[str, str],
) -> None:
    match = RELEASE_URL.fullmatch(values['url'])
    assert match, values['url']
    expected_path, expected_asset = PLATFORMS[_platform(values['marker'])]
    assert (path, match['asset']) == (expected_path, expected_asset)


@pytest.mark.parametrize(('path', 'values'), ENTRIES, ids=IDS)
def test_binary_is_pinned_by_sha256(
        path: str,
        values: dict[str, str],
) -> None:
    assert re.fullmatch(r'[0-9a-f]{64}', values['sha256'])


def test_sha256_pins_are_distinct() -> None:
    hashes = [values['sha256'] for _, values in ENTRIES]
    assert len(set(hashes)) == len(hashes)


def test_all_binaries_come_from_the_same_release() -> None:
    assert re.fullmatch(r'\d+\.\d+\.\d+', _bundled_version())


def test_all_binaries_share_one_group() -> None:
    # setuptools-download fails the install on a platform that matches no
    # entry of a group, instead of silently installing no binary.
    assert {values['group'] for _, values in ENTRIES} == {'hadolint-binary'}


def test_readme_rev_matches_the_bundled_hadolint_version() -> None:
    readme = (ROOT / 'README.md').read_text(encoding='utf-8')
    revs = re.findall(r'^\s*rev: v(\d+\.\d+\.\d+)\.\d+$', readme, re.MULTILINE)
    assert revs
    assert set(revs) == {_bundled_version()}


def test_hook_runs_the_downloaded_binary() -> None:
    hooks = (ROOT / '.pre-commit-hooks.yaml').read_text(encoding='utf-8')
    assert re.search(r'^\s*language: python$', hooks, re.MULTILINE)
    entry = re.search(r'^\s*entry: (\S+)$', hooks, re.MULTILINE)
    assert entry
    scripts = {path for path, _ in ENTRIES}
    assert scripts == {entry[1], f'{entry[1]}.exe'}
