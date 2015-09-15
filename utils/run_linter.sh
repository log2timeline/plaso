#!/bin/bash
# Script that runs the linter on all files.

EXIT_FAILURE=1;
EXIT_SUCCESS=0;

DIFFBASE="upstream/master";
SHOW_HELP=0;

if ! test -f "utils/common.sh";
then
  echo "Unable to find common scripts (utils/common.sh).";
  echo "This script can only be run from the root of the source directory.";

  exit ${EXIT_FAILURE};
fi

# Exports GIT_URL and PROJECT_NAME.
. utils/common.sh

while test $# -gt 0;
do
  case $1 in
  --diffbase )
    shift;
    DIFFBASE=$1;
    shift;
    ;;

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
  echo "Usage: ./${SCRIPTNAME} [--diffbase DIFFBASE] [--help]";
  echo "";
  echo "  --diffbase: the name of the branch to use as diffbase for the CL.";
  echo "              The default is upstream/master";
  echo "";
  echo "  --help: shows this help.";
  echo "";

  exit ${EXIT_SUCCESS};
fi

if ! linting_is_correct_remote_origin;
then
  echo "Linting aborted - fix the reported issues.";

  exit ${EXIT_FAILURE};
fi

# Determine if we have the master repo as origin.
HAVE_REMOTE_ORIGIN=have_remote_origin;

if ! ${HAVE_REMOTE_ORIGIN};
then
  if ! have_remote_upstream;
  then
    echo "Linting aborted - missing upstream.";
    echo "Run: 'git remote add upstream https://github.com/log2timeline/${PROJECT_NAME}.git'";

    exit ${EXIT_FAILURE};
  fi
  git fetch upstream;

  if ! linting_is_correct_remote_diffbase ${DIFFBASE};
  then
    echo "Linting aborted - fix the reported issues.";

    exit ${EXIT_FAILURE};
  fi
fi

exit ${EXIT_SUCCESS};

