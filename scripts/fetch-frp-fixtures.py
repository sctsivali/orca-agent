#!/usr/bin/env python3
"""Fetch the pinned official FRP archives, verify their checksums, and expose native test binaries."""
from __future__ import annotations

import argparse
import hashlib
import platform
import shutil
import subprocess
import tarfile
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, HTTPSHandler, build_opener


VERSION = '0.68.1'
BASE = f'https://github.com/fatedier/frp/releases/download/v{VERSION}/'
PINNED_SHA256 = {
    'amd64': '4a4e88987d39561e1b3b3b23d0ede48a457eebf76a87231999957e870f5f02b6',
    'arm64': 'e7ad15b0cfe4cf0125df4217778b66cb4426179270967b59900ecb2362d8cd01',
}


class HTTPSOnlyRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, response, code, message, headers, new_url):
        if urlsplit(new_url).scheme != 'https':
            raise RuntimeError('Vendor redirect must preserve HTTPS')
        return super().redirect_request(request, response, code, message, headers, new_url)


def download(url: str, target: Path, maximum_bytes: int) -> None:
    if urlsplit(url).scheme != 'https':
        raise RuntimeError('Vendor download must use HTTPS')
    opener = build_opener(HTTPSHandler(), HTTPSOnlyRedirect())
    with opener.open(url, timeout=30) as response:
        if urlsplit(response.url).scheme != 'https':
            raise RuntimeError('Vendor redirect did not preserve HTTPS')
        remaining = maximum_bytes
        with target.open('wb') as output:
            while True:
                chunk = response.read(min(1024 * 1024, remaining + 1))
                if not chunk:
                    break
                if len(chunk) > remaining:
                    raise RuntimeError('Vendor response exceeded size limit')
                output.write(chunk)
                remaining -= len(chunk)


def digest(path: Path) -> str:
    result = hashlib.sha256()
    with path.open('rb') as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b''):
            result.update(chunk)
    return result.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--all-architectures', action='store_true')
    args = parser.parse_args()
    args.output.mkdir(mode=0o700, parents=True, exist_ok=True)
    native = {'x86_64': 'amd64', 'aarch64': 'arm64'}.get(platform.machine())
    if native is None:
        raise RuntimeError('No approved FRP artifact for this runner architecture')
    architectures = ('amd64', 'arm64') if args.all_architectures else (native,)
    checksums_file = args.output / 'frp_sha256_checksums.txt'
    download(BASE + checksums_file.name, checksums_file, 1024 * 1024)
    checksums = {}
    for line in checksums_file.read_text().splitlines():
        fields = line.split()
        if len(fields) == 2:
            name = fields[1].lstrip('*')
            if name in checksums:
                raise RuntimeError('Ambiguous vendor checksum entry')
            checksums[name] = fields[0]
    for architecture in architectures:
        name = f'frp_{VERSION}_linux_{architecture}.tar.gz'
        archive = args.output / name
        download(BASE + name, archive, 50 * 1024 * 1024)
        if checksums.get(name) != PINNED_SHA256[architecture] or digest(archive) != PINNED_SHA256[architecture]:
            raise RuntimeError('Pinned vendor FRP archive checksum failed')
        print(f'Verified official FRP {VERSION} archive for {architecture}')
        if architecture != native:
            continue
        with tarfile.open(archive) as package:
            for executable in ('frpc', 'frps'):
                name_in_archive = f'frp_{VERSION}_linux_{architecture}/{executable}'
                entry = package.getmember(name_in_archive)
                if not entry.isfile():
                    raise RuntimeError('Expected regular vendor binary')
                with package.extractfile(entry) as source, (args.output / executable).open('wb') as output:
                    shutil.copyfileobj(source, output)
                (args.output / executable).chmod(0o755)
                version = subprocess.check_output([str(args.output / executable), '--version'], text=True, timeout=5).strip()
                if version != VERSION:
                    raise RuntimeError('Extracted FRP binary reported a different version')
        print(f'Verified native FRPC and FRPS {VERSION} for {architecture}')


if __name__ == '__main__':
    main()
