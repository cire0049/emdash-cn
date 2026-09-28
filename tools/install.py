#!/usr/bin/env python3
"""Install under the updater's stable filename, retaining the versioned original."""
import argparse
import json
import os
import pathlib
import shutil
import tempfile
import uuid
from build import ROOT, SOURCE_SHA, sha

LAUNCHER = pathlib.Path.home() / '.local/bin/emdash'


def switch(link, expected, target):
    if not link.is_symlink() or link.resolve() != expected.resolve():
        raise ValueError('Launcher changed since inspection; refusing to replace it')
    if not target.is_file():
        raise ValueError('Target does not exist')
    staged = link.with_name(link.name + '.cn-' + uuid.uuid4().hex)
    try:
        staged.symlink_to(target)
        if not link.is_symlink() or link.resolve() != expected.resolve():
            raise ValueError('Launcher changed during switch')
        os.replace(staged, link)
    finally:
        staged.unlink(missing_ok=True)


def publish(candidate, target, expected_sha, allowed_existing):
    if target.is_symlink():
        raise ValueError('Installed binary is an unexpected symlink')
    if target.exists():
        current_sha = sha(target)
        if current_sha == expected_sha:
            return
        if current_sha not in allowed_existing:
            raise ValueError('Installed binary changed; refusing to overwrite it')
    if candidate.resolve() == target.resolve():
        raise ValueError('Cannot replace a changed binary using itself')
    with tempfile.NamedTemporaryFile(prefix='.emdash-cn-', dir=target.parent, delete=False) as f:
        staged = pathlib.Path(f.name)
    try:
        shutil.copyfile(candidate, staged)
        if sha(staged) != expected_sha:
            raise ValueError('Copied artifact checksum mismatch')
        staged.chmod(0o755)
        if target.exists() and sha(target) not in allowed_existing:
            raise ValueError('Installed binary changed during installation')
        os.replace(staged, target)
    finally:
        staged.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--restore', action='store_true')
    args = parser.parse_args()
    record = ROOT / 'verification/installation.json'
    installed = json.loads(record.read_text()) if record.exists() else {}
    manifest = {}
    if args.restore and installed:
        original = pathlib.Path(installed['original'])
        localized = pathlib.Path(installed['localized'])
        original_sha = installed.get('sourceSha256', SOURCE_SHA)
    else:
        manifest = json.loads((ROOT / 'verification/build.json').read_text())
        original = pathlib.Path(manifest['source'])
        original_sha = manifest.get('sourceSha256', SOURCE_SHA)
        localized = original.parent / 'emdash-x86_64.AppImage'
    if sha(original) != original_sha:
        raise ValueError('Original installation checksum changed')
    if original.resolve() == localized.resolve():
        raise ValueError('The original must have a separate, versioned backup path')
    target = original if args.restore else localized
    if not LAUNCHER.is_symlink():
        raise ValueError('Launcher is not the managed symlink')
    current = LAUNCHER.resolve()
    known = {original.resolve(), localized.resolve()}
    if installed:
        known.update(pathlib.Path(installed[k]).resolve() for k in ('original', 'localized'))
    if current not in known:
        raise ValueError('Launcher changed since inspection; refusing to replace it')
    if not args.restore:
        candidate = pathlib.Path(manifest['output'])
        if sha(candidate) != manifest['outputSha256']:
            raise ValueError('Localized installation checksum changed')
        allowed = {original_sha}
        if installed.get('localizedSha256') and pathlib.Path(installed['localized']).resolve() == localized.resolve():
            allowed.add(installed['localizedSha256'])
        publish(candidate, localized, manifest['outputSha256'], allowed)
    if current != target.resolve():
        switch(LAUNCHER, current, target)
    state = {
        'launcher': str(LAUNCHER), 'active': str(target),
        'original': str(original), 'localized': str(localized),
        'sourceSha256': original_sha,
        'localizedSha256': manifest.get('outputSha256', installed.get('localizedSha256')),
        'version': manifest.get('version', installed.get('version'))
    }
    staged = record.with_suffix('.json.new')
    staged.write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n')
    os.replace(staged, record)
    print('Active:', LAUNCHER.resolve())


if __name__ == '__main__':
    main()
