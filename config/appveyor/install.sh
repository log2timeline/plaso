# Script to set up tests on AppVeyor MacOS.

set -e

brew update
brew install python@3.11 tox || true

