#!/usr/bin/env python3
"""Generate a pinned cask from verified upstream release assets."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import urllib.request

REPO = 'SigmaUno/sigma-dock'
ROOT = Path(__file__).resolve().parents[1]


def select(release, channel):
    tag = release['tag_name']
    if release.get('draft'):
        raise ValueError('Draft releases cannot be installed')
    if channel == 'stable':
        if release.get('prerelease') or not re.fullmatch(r'v\d+\.\d+\.\d+', tag):
            raise ValueError('Stable requires a non-prerelease semantic version tag')
        pattern = r'SigmaDock-(\d+\.\d+\.\d+)-([0-9a-f]{12})-universal\.dmg'
    else:
        if not re.fullmatch(r'macos-[0-9a-f]{12}', tag):
            raise ValueError('Preview requires an immutable macos-COMMIT snapshot')
        pattern = r'SigmaDock-(\d+\.\d+\.\d+)-([0-9a-f]{12})-universal-test\.dmg'
    assets = [a for a in release['assets'] if re.fullmatch(pattern, a['name'])]
    if len(assets) != 1:
        raise ValueError('Expected one universal installer for this channel')
    asset = assets[0]
    version, commit = re.fullmatch(pattern, asset['name']).groups()
    if channel == 'stable' and tag != 'v' + version:
        raise ValueError('Release tag and installer version differ')
    if channel == 'preview' and tag != 'macos-' + commit:
        raise ValueError('Snapshot tag and installer commit differ')
    expected = f'https://github.com/{REPO}/releases/download/{tag}/{asset["name"]}'
    if asset['browser_download_url'] != expected:
        raise ValueError('Installer must use the immutable upstream release URL')
    checksum = next((a for a in release['assets'] if a['name'] == asset['name'] + '.sha256'), None)
    if not checksum or checksum['browser_download_url'] != expected + '.sha256':
        raise ValueError('Published checksum asset is required')
    return asset, checksum, version, commit


def render(channel, asset, version, commit, digest):
    token = 'sigma-dock' if channel == 'stable' else 'sigma-dock-preview'
    other = 'sigma-dock-preview' if channel == 'stable' else 'sigma-dock'
    display_version = version if channel == 'stable' else version + ',' + commit
    url = asset['browser_download_url'].replace(version, '#{version}' if channel == 'stable' else '#{version.csv.first}').replace(commit, '#{version.csv.second}' if channel == 'preview' else commit)
    caveat = 'Git and an agent CLI must be installed separately.'
    if channel == 'preview':
        caveat += '\n    This development preview is ad-hoc signed and is not notarized.'
    return f'''cask "{token}" do
  version "{display_version}"
  sha256 "{digest}"

  url "{url}"
  name "SigmaDock{' Preview' if channel == 'preview' else ''}"
  desc "Native workspace for parallel coding agents"
  homepage "https://sigmadock.dev/"

  livecheck do
    skip "Maintainer updates after verified upstream publication"
  end

  conflicts_with cask: "sigmauno/tap/{other}"
  depends_on macos: :ventura

  app "SigmaDock.app"
  binary "#{{appdir}}/SigmaDock.app/Contents/MacOS/sdk"

  caveats <<~EOS
    {caveat}
    Finish workers before replacing or restarting a running daemon.
    Normal uninstall preserves settings, session history and worktrees.
  EOS
end
'''


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--tag', required=True)
    p.add_argument('--channel', choices=['stable', 'preview'], default='stable')
    args = p.parse_args()
    release = json.loads(subprocess.check_output(['gh', 'api', f'repos/{REPO}/releases/tags/{args.tag}']))
    try:
        asset, checksum, version, commit = select(release, args.channel)
    except ValueError as error:
        p.error(str(error))
    with tempfile.TemporaryDirectory(prefix='sigmadock-cask-') as folder:
        folder = Path(folder)
        with urllib.request.urlopen(checksum['browser_download_url'], timeout=60) as response:
            checksum_text = response.read(4096).decode()
        match = re.fullmatch(r'([0-9a-f]{64})\s+' + re.escape(asset['name']) + r'\s*', checksum_text)
        if not match:
            p.error('Checksum contents must name exactly the selected installer')
        digest = match[1]
        dmg = folder / asset['name']
        urllib.request.urlretrieve(asset['browser_download_url'], dmg)
        with dmg.open('rb') as stream:
            actual = hashlib.sha256()
            for block in iter(lambda: stream.read(1024 * 1024), b''):
                actual.update(block)
        if actual.hexdigest() != digest:
            p.error('Downloaded installer checksum mismatch')
        if asset.get('digest') and asset['digest'] != 'sha256:' + digest:
            p.error('GitHub asset digest differs from the published checksum')
        if args.channel == 'stable':
            if sys.platform != 'darwin':
                p.error('Stable promotion must run on macOS for signing and notarization verification')
            subprocess.run(['xcrun', 'stapler', 'validate', str(dmg)], check=True)
            mount = folder / 'mount'
            subprocess.run(['hdiutil', 'attach', '-readonly', '-nobrowse', '-mountpoint', str(mount), str(dmg)], check=True)
            try:
                app = mount / 'SigmaDock.app'
                subprocess.run(['codesign', '--verify', '--deep', '--strict', str(app)], check=True)
                signature = subprocess.check_output(['codesign', '--display', '--verbose=4', str(app)], stderr=subprocess.STDOUT, text=True)
                if 'Authority=Developer ID Application:' not in signature or 'runtime' not in signature:
                    p.error('Stable app must use Developer ID signing and hardened runtime')
                subprocess.run(['spctl', '--assess', '--type', 'execute', '--verbose=4', str(app)], check=True)
                for binary in ['sigma-dock', 'sigmadockd', 'sigmadock-mcp', 'sdk']:
                    arches = set(subprocess.check_output(['lipo', '-archs', str(app / 'Contents/MacOS' / binary)], text=True).split())
                    if arches != {'arm64', 'x86_64'}:
                        p.error('Every stable bundled executable must be universal')
            finally:
                subprocess.run(['hdiutil', 'detach', str(mount)], check=True)
    token = 'sigma-dock' if args.channel == 'stable' else 'sigma-dock-preview'
    output = ROOT / 'Casks' / (token + '.rb')
    output.parent.mkdir(exist_ok=True)
    output.write_text(render(args.channel, asset, version, commit, digest))
    print(output)


if __name__ == '__main__':
    main()
