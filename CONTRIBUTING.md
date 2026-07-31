# Contributing

## Cutting a release

The package version is derived entirely from the GitHub release tag — the PyPI
version is exactly the tag you enter on the release form (with the leading `v`
stripped). There are **no manual version bumps** and **no command-line steps**.

1. Open [GitHub Releases](https://github.com/shenxianpeng/hadolint-pre-commit/releases)
   and click **Draft a new release** — the release-drafter bot usually has a
   draft ready, so you can also just edit that one.
2. Enter a tag matching the bundled hadolint version, e.g. `v2.15.1.2` —
   GitHub creates the tag for you.
3. Click **Publish release** — the
   [publish workflow](.github/workflows/publish.yml) builds all platform
   wheels and publishes them to PyPI under that exact version.

Tag `v2.15.1.2` → PyPI version `2.15.1.2`.

## Updating the bundled hadolint version

When a new [hadolint release](https://github.com/hadolint/hadolint/releases)
is out:

1. Download the five binaries: `hadolint-linux-x86_64`, `hadolint-linux-arm64`,
   `hadolint-macos-x86_64`, `hadolint-macos-arm64`, `hadolint-windows-x86_64.exe`
2. Compute the `sha256` hash of each binary (e.g. `shasum -a 256 <file>`)
3. Update the URLs and hashes in `setup.cfg`
4. Update the `rev:` examples in `README.md` to the new tag
5. Open a PR; once merged, cut a release as described above
