# Script to set up tests on AppVeyor MacOS.

set -e

brew update -q
brew install -q gettext gnu-sed python@3.12 tox || true

