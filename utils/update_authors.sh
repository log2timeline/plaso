#!/bin/bash
# Script to update the authors information.

cat > AUTHORS <<EOT
# Names should be added to this file with this pattern:
#
# For individuals:
#   Name (email address)
#
# For organizations:
#   Organization (fnmatch pattern)
#
# See python fnmatch module documentation for more information.

Google Inc. (*@google.com)
EOT

git log --format='%aN (%aE)' | tac | awk '!seen[$0]++' >> AUTHORS;

