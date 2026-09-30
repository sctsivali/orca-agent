#!/usr/bin/env python3
from __future__ import annotations

import os
import shutil
import sys
import unittest
from pathlib import Path


root = Path.cwd()
source = root / 'src' / 'orca-agent'
fixtures = Path(os.environ['ORCA_TEST_FRP_DIR'])
for name in ('gpg', 'gpgconf', 'openssl'):
    if not shutil.which(name):
        raise SystemExit(f'Required integration tool is unavailable: {name}')
for name in ('frpc', 'frps'):
    if not (fixtures / name).is_file():
        raise SystemExit(f'Required verified FRP fixture is unavailable: {name}')
if not (root / 'src' / 'backend/src/services/agent-installer-script.ts').is_file():
    raise SystemExit('The source checkout omitted the actual installer script')
sys.path.insert(0, str(source))
suite = unittest.defaultTestLoader.discover(str(source / 'tests'))
result = unittest.TextTestRunner(verbosity=2).run(suite)
if result.skipped:
    print('Release rejected: an integration scenario was skipped', file=sys.stderr)
    for test, reason in result.skipped:
        print(f'{test}: {reason}', file=sys.stderr)
if result.testsRun < 40:
    print('Release rejected: incomplete test discovery', file=sys.stderr)
raise SystemExit(0 if result.wasSuccessful() and not result.skipped and result.testsRun >= 40 else 1)
