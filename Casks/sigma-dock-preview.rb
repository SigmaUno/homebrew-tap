cask "sigma-dock-preview" do
  version "0.1.2,656f3a4b3b36"
  sha256 "20d974d83a625d51d1e2a272c35b8e1aca5f6364eb98c6698cf5b4a8dcc0f255"

  url "https://github.com/SigmaUno/sigma-dock/releases/download/macos-#{version.csv.second}/SigmaDock-#{version.csv.first}-#{version.csv.second}-universal-test.dmg"
  name "SigmaDock Preview"
  desc "Native workspace for parallel coding agents"
  homepage "https://sigmadock.dev/"

  livecheck do
    skip "Maintainer updates after verified upstream publication"
  end

  conflicts_with cask: "sigmauno/tap/sigma-dock"
  depends_on macos: :ventura

  app "SigmaDock.app"
  binary "#{appdir}/SigmaDock.app/Contents/MacOS/sdk"

  caveats <<~EOS
    Git and an agent CLI must be installed separately.
    This development preview is ad-hoc signed and is not notarized.
    Finish workers before replacing or restarting a running daemon.
    Normal uninstall preserves settings, session history and worktrees.
  EOS
end
