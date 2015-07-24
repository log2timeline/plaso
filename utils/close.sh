#!/bin/bash
# Script that closes a code review after submit

EXIT_FAILURE=1;
EXIT_MISSING_ARGS=2;
EXIT_SUCCESS=0;

SCRIPTNAME=`basename $0`;

CL_NUMBER="";

if ! test -f "utils/common.sh";
then
  echo "Unable to find common scripts (utils/common.sh).";
  echo "This script can only be run from the root of the source directory.";

  exit ${EXIT_FAILURE};
fi

. utils/common.sh

if ! have_curl;
then
  echo "You'll need to install curl for this script to continue.";

  exit ${EXIT_FAILURE};
fi

# Determine if we have the master repo as origin.
HAVE_REMOTE_ORIGIN=have_remote_origin;

if test $# -ne 1;
then
  echo "Usage: ./${SCRIPTNAME} BRANCH";
  echo "";
  echo "  BRANCH: the branch of the pull request.";
  echo "";

  exit ${EXIT_MISSING_ARGS};
fi

FEATURE_BRANCH=$1;

if ${HAVE_REMOTE_ORIGIN};
then
  echo "Close aborted - invalid origin";

  exit ${EXIT_FAILURE};

fi

if have_uncommitted_changes;
then
  echo "Close aborted - detected uncommitted changes.";

  exit ${EXIT_FAILURE};
fi

git branch | grep "${FEATURE_BRANCH}" > /dev/null;
if test $? -ne 0;
then
  echo "No such branch: ${FEATURE_BRANCH}";

  exit ${EXIT_FAILURE};
fi

CL_FILENAME=".review/${FEATURE_BRANCH}";
if ! test -f ${CL_FILENAME};
then
  echo "Missing review file: ${CL_FILENAME}.";

  exit ${EXIT_FAILURE};
fi

CL_NUMBER=`cat ${CL_FILENAME}`
RESULT=`echo ${CL_NUMBER} | sed -e 's/[0-9]//g'`;

if ! test -z "${RESULT}";
then
  echo "${CL_FILENAME} contains an invalid CL number.";

  exit ${EXIT_FAILURE};
fi

git checkout master
git fetch upstream
git pull --no-edit upstream master

if test $? -ne 0;
then
  echo "Unable to sync with upstream.";

  exit ${EXIT_FAILURE};
fi

git push
git push origin --delete ${FEATURE_BRANCH}
git branch -D ${FEATURE_BRANCH}

URL_CODEREVIEW="https://codereview.appspot.com";
CODEREVIEW_COOKIES="${HOME}/.codereview_upload_cookies";

if test -f "${CODEREVIEW_COOKIES}";
then
  curl -b "${CODEREVIEW_COOKIES}" ${URL_CODEREVIEW}/${CL_NUMBER}/close -d '';
else
  echo "Could not find an authenticated session to codereview.";
  echo "You need to manually close the ticket on the code review site:";
  echo "${URL_CODEREVIEW}/${CL_NUMBER}";
fi

rm -f "${CL_FILENAME}";

exit ${EXIT_SUCCESS};
