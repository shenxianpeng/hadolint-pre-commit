# Contributing to hadolint-pre-commit

Thank you for your interest in contributing! Contributions of all kinds are welcome — bug reports, feature requests, documentation improvements, and code changes.

## Reporting issues

Before opening an issue, please check the [existing issues](https://github.com/shenxianpeng/hadolint-pre-commit/issues) to avoid duplicates.

When reporting a bug, please include:

- Your OS and architecture (e.g. macOS arm64, Ubuntu x86_64, Windows x86_64)
- Python version (`python --version`)
- pre-commit version (`pre-commit --version`)
- The relevant section of your `.pre-commit-config.yaml`
- The full output of the failing hook

## Updating hadolint to a new version

When hadolint publishes a new release, follow these steps:

1. Download each platform binary from the [hadolint releases page](https://github.com/hadolint/hadolint/releases).
2. Compute the SHA-256 hash for each binary:
   ```bash
   sha256sum hadolint-linux-x86_64
   sha256sum hadolint-linux-arm64
   sha256sum hadolint-macos-x86_64
   sha256sum hadolint-macos-arm64
   sha256sum hadolint-windows-x86_64.exe
   ```
3. Update the `url` and `sha256` values for each platform in `setup.cfg`.
4. Open a pull request with the changes.

## Development setup

```bash
git clone https://github.com/shenxianpeng/hadolint-pre-commit
cd hadolint-pre-commit
pip install -e .
hadolint --version
```

## Pull request guidelines

- Keep pull requests focused on a single change.
- Update the README if your change affects usage or configuration.
- Ensure the CI checks pass before requesting review.

## Releasing a new version

Releases are driven by git tags. To cut a release:

1. Create and push a tag following the `v<hadolint-version>.<patch>` scheme (e.g. `v2.14.0.2`):
   ```bash
   git tag v2.14.0.2
   git push origin v2.14.0.2
   ```
2. This triggers the **Publish to PyPI** workflow, which builds platform-specific wheels and publishes them automatically.
3. The [Release Drafter](https://github.com/release-drafter/release-drafter) workflow prepares the GitHub Release notes automatically.
