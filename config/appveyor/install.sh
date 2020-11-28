# Script to set up tests on AppVeyor MacOS.

set -e

brew update
brew install tox || true

