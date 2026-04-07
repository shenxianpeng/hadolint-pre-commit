# Security Policy

## Supported versions

Only the latest release is actively maintained.

## Reporting a vulnerability

Please **do not** open a public GitHub issue for security vulnerabilities.

Instead, report security issues by emailing the maintainer directly or by using [GitHub's private vulnerability reporting](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing/privately-reporting-a-security-vulnerability) feature on this repository.

Please include:

- A description of the vulnerability and its potential impact
- Steps to reproduce
- Any suggested mitigations

You can expect an acknowledgement within 72 hours.

## Binary integrity

The `hadolint` binaries distributed by this package are downloaded directly from the official [hadolint GitHub releases](https://github.com/hadolint/hadolint/releases). Each binary's SHA-256 hash is pinned in `setup.cfg` and verified at install time by `setuptools-download`. No third-party mirrors are used.
