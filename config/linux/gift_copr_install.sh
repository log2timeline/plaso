#!/usr/bin/env bash
set -e

# Dependencies for running Plaso, alphabetized, one per line.
# This should not include packages only required for testing or development.
PYTHON2_DEPENDENCIES="PyYAML
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
                      pyliblzma
                      python-XlsxWriter
                      python-artifacts
                      python-bencode
                      python-binplist
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
                      python-pefile
                      python-psutil
                      python-pyparsing
                      python-pysqlite
                      python-pytsk3
                      python-requests
                      python-six
                      python2-certifi
                      python2-idna
                      python2-urllib3
                      python2-yara
                      python2-zmq
                      pytz";

# Additional dependencies for running Plaso tests, alphabetized,
# one per line.
TEST_DEPENDENCIES="python-mock";

# Additional dependencies for doing Plaso development, alphabetized,
# one per line.
DEVELOPMENT_DEPENDENCIES="python-sphinx
                          pylint";

# Additional dependencies for doing Plaso debugging, alphabetized,
# one per line.
DEBUG_DEPENDENCIES="libbde-debuginfo
                    libesedb-debuginfo
                    libevt-debuginfo
                    libevtx-debuginfo
                    libewf-debuginfo
                    libfsntfs-debuginfo
                    libfvde-debuginfo
                    libfwnt-debuginfo
                    libfwsi-debuginfo
                    liblnk-debuginfo
                    libmsiecf-debuginfo
                    libolecf-debuginfo
                    libqcow-debuginfo
                    libregf-debuginfo
                    libscca-debuginfo
                    libsigscan-debuginfo
                    libsmdev-debuginfo
                    libsmraw-debuginfo
                    libvhdi-debuginfo
                    libvmdk-debuginfo
                    libvshadow-debuginfo
                    libvslvm-debuginfo";

sudo dnf install dnf-plugins-core
sudo dnf copr enable @gift/dev
sudo dnf install -y ${PYTHON2_DEPENDENCIES}

if [[ "$*" =~ "include-debug" ]]; then
    sudo dnf install -y ${DEBUG_DEPENDENCIES}
fi

if [[ "$*" =~ "include-development" ]]; then
    sudo dnf install -y ${DEVELOPMENT_DEPENDENCIES}
fi

if [[ "$*" =~ "include-test" ]]; then
    sudo dnf install -y ${TEST_DEPENDENCIES}
fi
