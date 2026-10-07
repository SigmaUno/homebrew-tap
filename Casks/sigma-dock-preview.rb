cask "sigma-dock-preview" do
  version "0.1.1,858b98ce5b6a"
  sha256 "bdd78d16de1e9099fd426d9fdc1de0ecca25db251f08c54c090adbf438403198"

  url "https://github.com/SigmaUno/sigma-dock/releases/download/macos-858b98ce5b6a/SigmaDock-0.1.1-858b98ce5b6a-universal-test.dmg"
  name "SigmaDock Preview"
  desc "Native workspace for parallel coding agents"
  homepage "https://sigmadock.dev/"

  livecheck do
    skip "Maintainer updates after verified upstream publication"
  end

  conflicts_with cask: "sigmauno/tap/sigma-dock"
  depends_on macos: ">= :ventura"

  app "SigmaDock.app"
  binary "#{appdir}/SigmaDock.app/Contents/MacOS/sdk"

  caveats <<~EOS
    Git and an agent CLI must be installed separately.
    This development preview is ad-hoc signed and is not notarized.
    Finish workers before replacing or restarting a running daemon.
    Normal uninstall preserves settings, session history and worktrees.
  EOS
end
