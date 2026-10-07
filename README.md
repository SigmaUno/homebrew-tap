# SigmaUno Homebrew tap

Homebrew distribution for [SigmaDock](https://sigmadock.dev), a native workspace for parallel coding agents.

## Development preview

```sh
brew tap SigmaUno/tap
brew install --cask sigma-dock-preview
sdk --help
```

Preview installers are pinned, universal Apple silicon/Intel snapshots for macOS 13+. They are ad-hoc signed and not notarized. Gatekeeper may block downloads. Use the [local build instructions](https://github.com/SigmaUno/sigma-dock/blob/main/docs/MACOS.md) if needed; this tap does not disable Gatekeeper or strip quarantine. Install Git and your agent CLI separately.

The app is `SigmaDock.app`. The tap links its bundled `sdk` CLI. Closing the UI leaves workers running; finish workers before restarting/replacing the daemon during upgrades.

## Stable channel — pending Apple qualification

The `sigma-dock` cask will be added after Developer ID signing, notarization and clean-Mac qualification in [issue #7](https://github.com/SigmaUno/sigma-dock/issues/7). No test installer is promoted into the stable channel. Once available:

```sh
brew tap SigmaUno/tap
brew install --cask sigma-dock
brew upgrade --cask sigma-dock
brew uninstall --cask sigma-dock
```

Normal upgrade/uninstall preserves application settings, session history and worktrees. There is deliberately no `zap` or daemon kill hook. User-created worktrees must be archived through the app or CLI before any manual cleanup. `sdk` may conflict with an existing executable of that name; resolve that before installation.

## Release maintenance

Run on a Mac with Python 3, `gh` access to the public upstream, Xcode command-line tools and Homebrew:

```sh
python3 scripts/update_cask.py --tag vVERSION --channel stable
brew style --cask sigmauno/tap/sigma-dock
brew audit --cask --online sigmauno/tap/sigma-dock
```

The generator refuses drafts, prereleases, non-version tags and test assets for stable. It requires a matching universal DMG and published checksum, downloads and checks the bytes, verifies Apple stapling, Developer ID/hardened runtime, Gatekeeper acceptance and both architectures before writing the cask. It never commits or pushes automatically. Review and commit the generated update only after upstream release qualification; immutable tags/assets must not be overwritten. There is no cross-repository publishing token requirement.

For an explicitly separate preview: `python3 scripts/update_cask.py --tag macos-COMMIT --channel preview`. Preview generation verifies the snapshot commit, universal asset selection and SHA-256 without asserting Apple notarization.

CI checks the cask syntax/style and exercises install, bundled daemon launch, CLI access, upgrade/reinstall and uninstall on Apple silicon and Intel. Check that workflow before merging updates. A true version-to-version stable upgrade and browser-download Gatekeeper qualification remain release checks once production assets exist.

Cask syntax follows the [Homebrew Cask Cookbook](https://docs.brew.sh/Cask-Cookbook).

Preview audits explicitly exclude only `github_prerelease_version`: prereleases are the purpose of that channel. Stable audits have no such exclusion. Version interpolation in URLs preserves the pinned version/commit and explicit checksums.
