#!/usr/bin/env bash
set -e

# Dependencies for running Plaso, alphabetized, one per line.
# This should not include packages only required for testing or development.
PYTHON2_DEPENDENCIES="libbde-python
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
                      python-certifi
                      python-chardet
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
                      python-idna
                      python-lzma
                      python-pefile
                      python-psutil
                      python-pyparsing
                      python-pysqlite
                      python-pytsk3
                      python-requests
                      python-six
                      python-tz
                      python-urllib3
                      python-xlsxwriter
                      python-yaml
                      python-yara
                      python-zmq";

# Additional dependencies for running Plaso tests, alphabetized,
# one per line.
TEST_DEPENDENCIES="python-mock";

# Additional dependencies for doing Plaso development, alphabetized,
# one per line.
DEVELOPMENT_DEPENDENCIES="python-sphinx
                          pylint";

# Additional dependencies for doing Plaso debugging, alphabetized,
# one per line.
DEBUG_DEPENDENCIES="libbde-dbg
                    libbde-python-dbg
                    libesedb-dbg
                    libesedb-python-dbg
                    libevt-dbg
                    libevt-python-dbg
                    libevtx-dbg
                    libevtx-python-dbg
                    libewf-dbg
                    libewf-python-dbg
                    libfsntfs-dbg
                    libfsntfs-python-dbg
                    libfvde-dbg
                    libfvde-python-dbg
                    libfwnt-dbg
                    libfwnt-python-dbg
                    libfwsi-dbg
                    libfwsi-python-dbg
                    liblnk-dbg
                    liblnk-python-dbg
                    libmsiecf-dbg
                    libmsiecf-python-dbg
                    libolecf-dbg
                    libolecf-python-dbg
                    libqcow-dbg
                    libqcow-python-dbg
                    libregf-dbg
                    libregf-python-dbg
                    libscca-dbg
                    libscca-python-dbg
                    libsigscan-dbg
                    libsigscan-python-dbg
                    libsmdev-dbg
                    libsmdev-python-dbg
                    libsmraw-dbg
                    libsmraw-python-dbg
                    libvhdi-dbg
                    libvhdi-python-dbg
                    libvmdk-dbg
                    libvmdk-python-dbg
                    libvshadow-dbg
                    libvshadow-python-dbg
                    libvslvm-dbg
                    libvslvm-python-dbg
                    python-guppy";

sudo add-apt-repository ppa:gift/dev -y
sudo apt-get update -q
sudo apt-get install -y ${PYTHON2_DEPENDENCIES}

if [[ "$*" =~ "include-debug" ]]; then
    sudo apt-get install -y ${DEBUG_DEPENDENCIES}
fi

if [[ "$*" =~ "include-development" ]]; then
    sudo apt-get install -y ${DEVELOPMENT_DEPENDENCIES}
fi

if [[ "$*" =~ "include-test" ]]; then
    sudo apt-get install -y ${TEST_DEPENDENCIES}
fi
