#!/bin/bash
#
# Script to set up Travis-CI test VM.

EXIT_SUCCESS=0;
EXIT_FAILURE=1;

COVERALL_DEPENDENCIES="python-coverage python-coveralls python-docopt";

PYTHON2_DEPENDENCIES="ipython libbde-python libesedb-python libevt-python libevtx-python libewf-python libfsntfs-python libfwnt-python libfwsi-python liblnk-python libmsiecf-python libolecf-python libqcow-python libregf-python libscca-python libsigscan-python libsmdev-python libsmraw-python libvhdi-python libvmdk-python libvshadow-python python-artifacts python-bencode python-binplist python-construct python-dateutil python-dfdatetime python-dfvfs python-dfwinreg python-dpkt python-hachoir-core python-hachoir-metadata python-hachoir-parser python-mock python-pefile python-protobuf python-psutil python-pyparsing python-pytsk3 python-requests python-six python-xlsxwriter python-yaml python-tz python-zmq";

# Exit on error.
set -e;

if test `uname -s` = 'Linux';
then
	APT_SOURCES="/etc/apt/sources.list.d/travis_ci_zeromq3-source.list";

	if test -f "${APT_SOURCES}";
	then
		sudo rm -f "${APT_SOURCES}";
	fi

	sudo add-apt-repository ppa:gift/dev -y;
	sudo apt-get update -q;
	sudo apt-get install -y ${COVERALL_DEPENDENCIES} ${PYTHON2_DEPENDENCIES};
fi

sudo pip install ipython --upgrade;

