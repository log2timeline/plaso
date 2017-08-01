#!/bin/bash
#
# Script to set up Travis-CI test VM.

COVERALL_DEPENDENCIES="python-coverage python-coveralls python-docopt";

L2TBINARIES_DEPENDENCIES="PyYAML XlsxWriter artifacts bencode binplist certifi chardet construct dateutil dfdatetime dfvfs dfwinreg dpkt efilter hachoir-core hachoir-metadata hachoir-parser idna libbde libesedb libevt libevtx libewf libfsntfs libfvde libfwnt libfwsi liblnk libmsiecf libolecf libqcow libregf libscca libsigscan libsmdev libsmraw libvhdi libvmdk libvshadow libvslvm lzma pefile psutil pycrypto pyparsing pysqlite pytsk3 pytz pyzmq requests six urllib3 yara-python";

L2TBINARIES_TEST_DEPENDENCIES="funcsigs mock pbr";

PYTHON2_DEPENDENCIES="libbde-python libesedb-python libevt-python libevtx-python libewf-python libfsntfs-python libfvde-python libfwnt-python libfwsi-python liblnk-python libmsiecf-python libolecf-python libqcow-python libregf-python libscca-python libsigscan-python libsmdev-python libsmraw-python libvhdi-python libvmdk-python libvshadow-python libvslvm-python python-artifacts python-bencode python-binplist python-certifi python-chardet python-construct python-crypto python-dateutil python-dfdatetime python-dfvfs python-dfwinreg python-dpkt python-efilter python-hachoir-core python-hachoir-metadata python-hachoir-parser python-idna python-lzma python-pefile python-psutil python-pyparsing python-pysqlite python-pytsk3 python-requests python-six python-tz python-urllib3 python-xlsxwriter python-yaml python-yara python-zmq";

PYTHON2_TEST_DEPENDENCIES="python-mock python-tox";

# Exit on error.
set -e;

if test ${TRAVIS_OS_NAME} = "osx";
then
	git clone https://github.com/log2timeline/l2tdevtools.git;

	mv l2tdevtools ../;
	mkdir dependencies;

	PYTHONPATH=../l2tdevtools ../l2tdevtools/tools/update.py --download-directory dependencies --track dev ${L2TBINARIES_DEPENDENCIES} ${L2TBINARIES_TEST_DEPENDENCIES};

elif test ${TRAVIS_OS_NAME} = "linux";
then
	sudo rm -f /etc/apt/sources.list.d/travis_ci_zeromq3-source.list;

	sudo add-apt-repository ppa:gift/dev -y;
	sudo apt-get update -q;
	# Only install the Python 2 dependencies.
	# Also see: https://docs.travis-ci.com/user/languages/python/#Travis-CI-Uses-Isolated-virtualenvs
	sudo apt-get install -y ${COVERALL_DEPENDENCIES} ${PYTHON2_DEPENDENCIES} ${PYTHON2_TEST_DEPENDENCIES};
fi
