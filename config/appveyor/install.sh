# Script to set up tests on AppVeyor MacOS.

set -e

brew untap homebrew/homebrew-cask-versions
brew update -q
brew install -q gettext gnu-sed python@${PYTHON_VERSION} tox || true

