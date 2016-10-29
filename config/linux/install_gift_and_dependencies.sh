#!/usr/bin/env bash
set -e

# Dependencies for running Plaso, alphabetized, one per line.
# This should not include packages only required for testing or development.
PLASO_DEPENDENCIES="ipython
                    libbde-python
                    libesedb-python
                    libevt-python
                    libevtx-python
                    libewf-python
                    libfsntfs-python
                    libfvde-python
                    libfwnt-python
                    libfwsi-python
                    liblnk-python
                    libmsiecf-python
                    libolecf-python
                    libqcow-python
                    libregf-python
                    libscca-python
                    libsigscan-python
                    libsmdev-python
                    libsmraw-python
                    libvhdi-python
                    libvmdk-python
                    libvshadow-python
                    libvslvm-python
                    python-artifacts
                    python-bencode
                    python-binplist
                    python-construct
                    python-crypto
                    python-dateutil
                    python-dfdatetime
                    python-dfvfs
                    python-dfwinreg
                    python-dpkt
                    python-efilter
                    python-hachoir-core
                    python-hachoir-metadata
                    python-hachoir-parser
                    python-pefile
                    python-psutil
                    python-pyparsing
                    python-pytsk3
                    python-requests
                    python-six
                    python-tz
                    python-xlsxwriter
                    python-yaml
                    python-yara
                    python-zmq";

# Additional dependencies for running Plaso tests, alphabetized,
# one per line.
TEST_DEPENDENCIES="python-mock";

# Additional dependencies for doing Plaso debugging, alphabetized,
# one per line.
DEBUG_DEPENDENCIES="python-guppy";

# Additional dependencies for doing Plaso development, alphabetized,
# one per line.
DEVELOPMENT_DEPENDENCIES="python-sphinx
                          pylint";

sudo add-apt-repository ppa:gift/dev -y
sudo apt-get update -q
sudo apt-get install -y ${PLASO_DEPENDENCIES}

if [[ "$*" =~ "include-debug" ]]; then
    sudo apt-get install -y ${DEBUG_DEPENDENCIES}
fi

if [[ "$*" =~ "include-development" ]]; then
    sudo apt-get install -y ${DEVELOPMENT_DEPENDENCIES}
fi

if [[ "$*" =~ "include-test" ]]; then
    sudo apt-get install -y ${TEST_DEPENDENCIES}
fi
