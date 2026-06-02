# ORCA Agent Distribution

Public distribution repository for ORCA Agent release artifacts.

## Release Assets

Each release provides:

- `orca-agent-linux-x86_64.tar.gz`
- `SHA256SUMS`

Optional assets may include:

- `orca-agent-linux-aarch64.tar.gz`
- `SHA256SUMS.sig`
- `signing-key.asc`

## Verification

```bash
sha256sum -c SHA256SUMS
```
