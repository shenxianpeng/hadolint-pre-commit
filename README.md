# hadolint-pre-commit

[![PyPI version](https://badge.fury.io/py/hadolint-py.svg)](https://badge.fury.io/py/hadolint-py)

A [pre-commit](https://pre-commit.com/) hook for [hadolint](https://github.com/hadolint/hadolint) that automatically downloads and installs the hadolint binary — no manual installation required.

## Usage

Add the following to your `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/shenxianpeng/hadolint-pre-commit
    rev: v2.14.0.1
    hooks:
      - id: hadolint
```

Run `pre-commit install` and the hadolint binary will be downloaded and installed automatically.

## How it works

This package ships the hadolint binary via PyPI using
[setuptools-download](https://github.com/asottile/setuptools-download).
When `pip install hadolint-py` is run (which pre-commit does automatically),
the appropriate pre-built binary for your platform is downloaded from the
official [hadolint GitHub releases](https://github.com/hadolint/hadolint/releases)
and placed in your environment's `bin/` directory.

Supported platforms:

| OS      | Architecture |
|---------|-------------|
| Linux   | x86_64      |
| Linux   | arm64       |
| macOS   | x86_64      |
| macOS   | arm64       |
| Windows | x86_64      |

## Install as a standalone tool

```bash
pip install hadolint-py
hadolint --version
```

