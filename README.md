# ORCA Agent

Public distribution and release automation for the ORCA Agent, the cluster-side worker
for the ORCA Hub Services Exposer. The agent source is private; this repository holds the
signed release artifacts and the workflow that builds them.

## Installation

Agents are installed through the OrcaHub UI (Network → Expose Services → Register ORCA
Agent), which generates a short-lived, token-scoped installer. The installer downloads the
version-pinned, checksum-verified artifact for the host's architecture and configures a
systemd unit. Nothing here is installed by hand.

## Release assets

Each release provides, for `linux/amd64` and `linux/arm64`:

- `orca-agent-linux-x86_64.tar.gz`, `orca-agent-linux-aarch64.tar.gz` — self-contained
  binaries that bundle their own Python, built in `manylinux_2_28` (glibc floor 2.28), so
  they run on RHEL 8, Ubuntu 20.04+, and Debian 11+ with no host Python.
- `orca-agent.pyz` — a pure-Python zipapp run by the host `python3` (>= 3.8), used as the
  installer's fallback on hosts where the binary cannot run.
- `orca_agent-<version>-py3-none-any.whl` — for `pip install`.
- `SHA256SUMS`, `SHA256SUMS.sig`, `signing-key.asc`.

### Verify

```bash
gpg --import signing-key.asc
gpg --verify SHA256SUMS.sig SHA256SUMS
sha256sum -c SHA256SUMS
```

Builds also carry a GitHub build-provenance attestation:

```bash
gh attestation verify orca-agent-linux-x86_64.tar.gz --repo sctsivali/orca-agent
```

## How releases are built

The [`release`](.github/workflows/release.yml) workflow fetches the private agent source
into the ephemeral runner (it is never stored here), runs the Python 3.8–3.13 test matrix,
builds the `manylinux_2_28` binaries for amd64 and arm64 with a glibc-floor gate, builds the
zipapp and wheel, signs `SHA256SUMS` with GPG, attests provenance, and publishes the release.

To cut a release: bump the agent version in the private source, then run the workflow
(Actions → release → Run workflow) with `ref` set to the source branch, tag, or SHA. The
release is tagged `v<version>`.

Required repository secrets: `GITLAB_TOKEN` (read-only source access), `GPG_PRIVATE_KEY`,
`GPG_PASSPHRASE`.
