#!/bin/bash
# Plaso uninstallation script for macOS.

EXIT_SUCCESS=0;
EXIT_FAILURE=1;

SCRIPT_NAME=`basename $0`;
DEPENDENCIES_ONLY=0;
SHOW_HELP=0;

echo "===============================================================";
echo "              Plaso macOS uninstallation script";
echo "===============================================================";

while test $# -gt 0;
do
  case $1 in
  -h | --help )
    SHOW_HELP=1;
    shift;
    ;;

  *)
    ;;
  esac
done

if test ${SHOW_HELP} -ne 0;
then
  echo "Usage: ./${SCRIPT_NAME} [--help]";
  echo "";
  echo "  --help: shows this help.";
  echo "";
  echo "";

  exit ${EXIT_SUCCESS};
fi

if test "$USER" != "root";
then
  echo "This script requires root privileges. Running: sudo.";

  sudo echo > /dev/null;
  if test $? -ne 0;
  then
    echo "Do you have root privileges?";

    exit ${EXIT_FAILURE};
  fi
fi

VOLUME_NAME="/Volumes/@VOLUMENAME@";

if ! test -d ${VOLUME_NAME};
then
  echo "Unable to find installation volume: ${VOLUME_NAME}";

  exit ${EXIT_FAILURE};
fi

echo "Uninstalling packages.";

for PACKAGE in `find ${VOLUME_NAME} -name "*.pkg"`;
do
  # TODO: implement.
  # Get package names: /usr/sbin/pkgutil --packages
  # Get files in package: /usr/sbin/pkgutil --files NAME
  # Remove files and directories.
  # Forget package: /usr/sbin/pkgutil --forget NAME
done

echo "Done.";

exit ${EXIT_SUCCESS};

