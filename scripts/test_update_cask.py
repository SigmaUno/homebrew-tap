import unittest
from update_cask import select, render


def release(stable=True):
    version, commit = '1.2.3', '0123456789ab'
    tag = 'v' + version if stable else 'macos-' + commit
    name = f'SigmaDock-{version}-{commit}-universal' + ('' if stable else '-test') + '.dmg'
    url = f'https://github.com/SigmaUno/sigma-dock/releases/download/{tag}/{name}'
    return {'tag_name': tag, 'prerelease': not stable, 'assets': [
        {'name': name, 'browser_download_url': url},
        {'name': name + '.sha256', 'browser_download_url': url + '.sha256'}]}


class Policy(unittest.TestCase):
    def test_stable_rejects_prerelease_and_snapshot(self):
        for candidate in [release(False), dict(release(), prerelease=True)]:
            with self.assertRaises(ValueError):
                select(candidate, 'stable')

    def test_checks_tag_version_checksum_and_origin(self):
        for change in ['tag', 'checksum', 'origin']:
            candidate = release()
            if change == 'tag': candidate['tag_name'] = 'v1.2.4'
            if change == 'checksum': candidate['assets'].pop()
            if change == 'origin': candidate['assets'][0]['browser_download_url'] = 'https://example.com/untrusted.dmg'
            with self.assertRaises(ValueError):
                select(candidate, 'stable')

    def test_channels_are_separate_and_preserve_state(self):
        for channel in ['stable', 'preview']:
            asset, _, version, commit = select(release(channel == 'stable'), channel)
            text = render(channel, asset, version, commit, 'a' * 64)
            self.assertIn('binary "#{appdir}/SigmaDock.app/Contents/MacOS/sdk"', text)
            self.assertIn('macos: :ventura', text)
            self.assertNotIn('zap ', text)
            self.assertNotRegex(text, r'(?m)^  (?:uninstall|zap)\b')
            self.assertNotIn(':no_check', text)


if __name__ == '__main__':
    unittest.main()
