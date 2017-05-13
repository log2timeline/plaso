#!/bin/bash
#
# Script to set up Travis-CI test VM.

COVERALL_DEPENDENCIES="python-coverage python-coveralls python-docopt";

L2TBINARIES_DEPENDENCIES="PyYAML XlsxWriter artifacts bencode binplist construct dfdatetime dfvfs dfwinreg dpkt efilter hachoir_core hachoir_metadata hachoir_parser libbde libesedb libevt libevtx libewf libfsntfs libfvde libfwnt libfwsi liblnk libmsiecf libolecf libqcow libregf libscca libsigscan libsmdev libsmraw libvhdi libvmdk libvshadow libvslvm lzma pefile psutil pycrypto pyparsing pysqlite python-dateutil pytsk3 pytz pyzmq requests six yara-python";

L2TBINARIES_TEST_DEPENDENCIES="funcsigs mock pbr";

PYTHON2_DEPENDENCIES="libbde-python libesedb-python libevt-python libevtx-python libewf-python libfsntfs-python libfvde-python libfwnt-python libfwsi-python liblnk-python libmsiecf-python libolecf-python libqcow-python libregf-python libscca-python libsigscan-python libsmdev-python libsmraw-python libvhdi-python libvmdk-python libvshadow-python libvslvm-python python-artifacts python-bencode python-binplist python-construct python-crypto python-dateutil python-dfdatetime python-dfvfs python-dfwinreg python-dpkt python-efilter python-hachoir-core python-hachoir-metadata python-hachoir-parser python-lzma python-pefile python-psutil python-pyparsing python-pysqlite python-pytsk3 python-requests python-six python-tz python-xlsxwriter python-yaml python-yara python-zmq";

PYTHON2_TEST_DEPENDENCIES="python-mock";

PYTHON3_DEPENDENCIES="libbde-python3 libesedb-python3 libevt-python3 libevtx-python3 libewf-python3 libfsntfs-python3 libfvde-python3 libfwnt-python3 libfwsi-python3 liblnk-python3 libmsiecf-python3 libolecf-python3 libqcow-python3 libregf-python3 libscca-python3 libsigscan-python3 libsmdev-python3 libsmraw-python3 libvhdi-python3 libvmdk-python3 libvshadow-python3 libvslvm-python3 python3-artifacts python3-bencode python3-construct python3-crypto python3-dateutil python3-dfdatetime python3-dfvfs python3-dfwinreg python3-dpkt python3-efilter python3-psutil python3-pyparsing python3-pytsk3 python3-requests python3-six python3-tz python3-xlsxwriter python3-yaml python3-yara python3-zmq";

PYTHON3_TEST_DEPENDENCIES="python3-mock";

# Exit on error.
set -e;

if test `uname -s` = "Darwin";
then
	git clone https://github.com/log2timeline/l2tdevtools.git;

	mv l2tdevtools ../;
	mkdir dependencies;

	PYTHONPATH=../l2tdevtools ../l2tdevtools/tools/update.py --download-directory=dependencies ${L2TBINARIES_DEPENDENCIES} ${L2TBINARIES_TEST_DEPENDENCIES};

elif test `uname -s` = "Linux";
then
	sudo rm -f /etc/apt/sources.list.d/travis_ci_zeromq3-source.list;

	sudo add-apt-repository ppa:gift/dev -y;
	sudo apt-get update -q;
	sudo apt-get install -y ${COVERALL_DEPENDENCIES} ${PYTHON2_DEPENDENCIES} ${PYTHON2_TEST_DEPENDENCIES} ${PYTHON3_DEPENDENCIES} ${PYTHON3_TEST_DEPENDENCIES};
fi
