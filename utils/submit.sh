#!/bin/bash
# Script that submits a code for code review.

EXIT_FAILURE=1;
EXIT_MISSING_ARGS=2;
EXIT_SUCCESS=0;

SCRIPTNAME=`basename $0`;

BROWSER_PARAM="";
CL_NUMBER="";
USE_CL_FILE=0;
CL_FILENAME="";

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

while test $# -gt 0;
do
  case $1 in
  --nobrowser | --no-browser | --no_browser )
    BROWSER_PARAM="--no_oauth2_webbrowser";
    shift;
    ;;

  *)
    CL_NUMBER=$1;
    shift
    ;;
  esac
done

if test -z "${CL_NUMBER}";
then
  BRANCH="";
  get_current_branch "BRANCH";

  CL_FILENAME=".review/${BRANCH}";

  if test -f ${CL_FILENAME};
  then
    CL_NUMBER=`cat ${CL_FILENAME}`
    RESULT=`echo ${CL_NUMBER} | sed -e 's/[0-9]//g'`;

    if ! test -z "${RESULT}";
    then
      echo "${CL_FILENAME} contains an invalid CL number.";

      exit ${EXIT_FAILURE};
    fi
    USE_CL_FILE=1;
  fi
fi

if test -z "${CL_NUMBER}";
then
  echo "Usage: ./${SCRIPTNAME} [--nobrowser] CL_NUMBER";
  echo "";
  echo "  CL_NUMBER: optional change list (CL) number that is to be submitted.";
  echo "             If no CL number is provided the value is read from the";
  echo "             corresponding file in: .review/";
  echo "";
  echo "  --nobrowser: forces upload.py not to open a separate browser";
  echo "               process to obtain OAuth2 credentials for Rietveld";
  echo "               (https://codereview.appspot.com).";
  echo "";

  exit ${EXIT_MISSING_ARGS};
fi

if ! ${HAVE_REMOTE_ORIGIN};
then
  echo "Submit aborted - no need to use the submit script. Instead use";
  echo "the update script to update the code review or the close script";
  echo "to close the code review after it has been submitted by one of";
  echo "the git repository maintainers.";

  exit ${EXIT_FAILURE};
fi

if ! have_master_branch;
then
  echo "Submit aborted - current branch is not master.";

  exit ${EXIT_FAILURE};
fi

if have_double_git_status_codes;
then
  echo "Submit aborted - detected double git status codes."
  echo "Run: 'git stash && git stash pop'.";

  exit ${EXIT_FAILURE};
fi

if ! local_repo_in_sync_with_origin;
then
  echo "Submit aborted - local repo out of sync with origin."
  echo "Run: 'git stash && git pull && git stash pop'.";

  exit ${EXIT_FAILURE};
fi

if ! linting_is_correct_remote_origin;
then
  echo "Submit aborted - fix the issues reported by the linter.";

  exit ${EXIT_FAILURE};
fi

if ! tests_pass;
then
  echo "Submit aborted - fix the issues reported by the failing test.";

  exit ${EXIT_FAILURE};
fi

URL_CODEREVIEW="https://codereview.appspot.com";

# Get the description of the change list.

# This will convert newlines into spaces.
CODEREVIEW=`curl -s ${URL_CODEREVIEW}/api/${CL_NUMBER}`;

DESCRIPTION=`echo ${CODEREVIEW} | sed 's/^.*"subject":"\(.*\)","created.*$/\1/'`;

if test -z "${DESCRIPTION}" || test "${DESCRIPTION}" = "${CODEREVIEW}";
then
  echo "Submit aborted - unable to find change list with number: ${CL_NUMBER}.";

  exit ${EXIT_FAILURE};
fi

COMMIT_DESCRIPTION="Code review: ${CL_NUMBER}: ${DESCRIPTION}";
echo "Submitting ${COMMIT_DESCRIPTION}";

# Need to change the status on codereview before commit.
python utils/upload.py \
    --oauth2 ${BROWSER_PARAM} ${CACHE_PARAM} --send_mail -i ${CL_NUMBER} \
    -m "Code Submitted." -t "Submitted." -y;

if test -f "utils/update_version.sh";
then
  . utils/update_version.sh
fi

# Check if we need to set --cache.
STATUS_CODES=`git status -s | cut -b1,2 | sed 's/\s//g' | sort | uniq`;

CACHE_PARAM="";
for STATUS_CODE in ${STATUS_CODES};
do
  if test "${STATUS_CODE}" = "A";
  then
    CACHE_PARAM="--cache";
  fi
done

git commit -a -m "${COMMIT_DESCRIPTION}";
git push

if test $? -ne 0;
then
  echo "Submit aborted - unable to run: 'git push'.";

  exit ${EXIT_FAILURE};
fi

CODEREVIEW_COOKIES="${HOME}/.codereview_upload_cookies";

if test -f "${CODEREVIEW_COOKIES}";
then
  curl -b "${CODEREVIEW_COOKIES}" ${URL_CODEREVIEW}/${CL_NUMBER}/close -d  '';
else
  echo "Could not find an authenticated session to codereview.";
  echo "You need to manually close the ticket on the code review site:";
  echo "${URL_CODEREVIEW}/${CL_NUMBER}";
fi

if ! test -z "${USE_CL_FILE}" && test -f "${CL_FILENAME}";
then
  rm -f ${CL_FILENAME};
fi

exit ${EXIT_SUCCESS};
