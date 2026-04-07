# hadolint-pre-commit

[![CI](https://github.com/shenxianpeng/hadolint-pre-commit/actions/workflows/ci.yml/badge.svg)](https://github.com/shenxianpeng/hadolint-pre-commit/actions/workflows/ci.yml)
[![PyPI version](https://badge.fury.io/py/hadolint-py.svg)](https://badge.fury.io/py/hadolint-py)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/hadolint-py)](https://pypi.org/project/hadolint-py/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://pre-commit.com/)

A [pre-commit](https://pre-commit.com/) hook for [hadolint](https://github.com/hadolint/hadolint) that **automatically downloads and installs the hadolint binary** — no manual installation required.

## Background

The official `hadolint/hadolint` repository provides a pre-commit hook configuration, but it does **not** auto-install the `hadolint` binary. Users who add it to their `.pre-commit-config.yaml` are met with:

```
Executable `hadolint` not found
```

This is a [known, long-standing issue](https://github.com/hadolint/hadolint/issues/886) that affects everyone who tries to use `hadolint` as a zero-dependency pre-commit hook. The official hook assumes you have already installed `hadolint` separately (e.g. via `brew install hadolint`), which defeats the purpose of a self-contained pre-commit integration.

**This project solves that problem.** It distributes the official, pre-built `hadolint` binary through PyPI as a platform-specific wheel. When pre-commit sets up the hook environment, it runs `pip install hadolint-py` automatically — and your binary is ready to use.

## Usage

Add the following to your `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/shenxianpeng/hadolint-pre-commit
    rev: v2.14.0.1
    hooks:
      - id: hadolint
```

Run `pre-commit install` and the `hadolint` binary will be downloaded and installed automatically. That's it.

### Passing arguments

You can pass any [hadolint CLI argument](https://github.com/hadolint/hadolint#cli) via the `args` key:

```yaml
repos:
  - repo: https://github.com/shenxianpeng/hadolint-pre-commit
    rev: v2.14.0.1
    hooks:
      - id: hadolint
        args: [--ignore, DL3008, --ignore, DL3009]
```

### Using a configuration file

hadolint supports a [`.hadolint.yaml`](https://github.com/hadolint/hadolint#configure) file in your project root. Create it alongside your Dockerfiles:

```yaml
# .hadolint.yaml
ignore:
  - DL3008  # Pin versions in apt-get install
  - DL3009  # Delete the apt-get lists after installing

failure-threshold: warning
trustedRegistries:
  - docker.io
  - gcr.io
```

When a `.hadolint.yaml` is present, hadolint picks it up automatically — no extra `args` needed.

## How it works

This package ships the `hadolint` binary via PyPI using
[setuptools-download](https://github.com/asottile/setuptools-download).
When `pip install hadolint-py` is run (which pre-commit does automatically),
the appropriate pre-built binary for your platform is downloaded from the
official [hadolint GitHub releases](https://github.com/hadolint/hadolint/releases)
and placed in your environment's `bin/` directory (or `Scripts/` on Windows).

### Supported platforms

| OS      | Architecture |
|---------|-------------|
| Linux   | x86_64      |
| Linux   | arm64       |
| macOS   | x86_64      |
| macOS   | arm64       |
| Windows | x86_64      |

## Comparison with alternatives

| Approach | Auto-installs binary | Works offline after install | Cross-platform | Zero extra setup |
|---|---|---|---|---|
| **This project** | ✅ | ✅ | ✅ | ✅ |
| `hadolint/hadolint` official hook | ❌ (requires pre-installed `hadolint`) | ✅ | ✅ | ❌ |
| `brew install hadolint` + system hook | ❌ (manual step) | ✅ | ⚠️ macOS only | ❌ |
| Docker-based hook | ✅ | ✅ | ✅ | ❌ (requires Docker) |

## Install as a standalone tool

You can also use `hadolint-py` outside of pre-commit as a standalone CLI tool:

```bash
pip install hadolint-py
hadolint --version
hadolint Dockerfile
```

## Contributing

Contributions are welcome! Please open an issue or pull request on [GitHub](https://github.com/shenxianpeng/hadolint-pre-commit).

## License

[MIT](LICENSE)

