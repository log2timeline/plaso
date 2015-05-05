#!/bin/bash
# Script that submits a code for code review.

EXIT_FAILURE=1;
EXIT_MISSING_ARGS=2;
EXIT_SUCCESS=0;

SCRIPTNAME=`basename $0`;

BROWSER_PARAM="";
CACHE_PARAM="";
CL_NUMBER="";
USE_CL_FILE=0;

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
  if test -f ._code_review_number;
  then
    CL_NUMBER=`cat ._code_review_number`
    RESULT=`echo ${CL_NUMBER} | sed -e 's/[0-9]//g'`;

    if ! test -z "${RESULT}";
    then
      echo "File ._code_review_number exists but contains an incorrect CL number.";

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
  echo "             If no CL number is provided the value is read from:";
  echo "             ._code_review_number";
  echo "";

  exit ${EXIT_MISSING_ARGS};
fi

if ! test -f "utils/common.sh";
then
  echo "Unable to find common functions, are you in the wrong directory?";

  exit ${EXIT_FAILURE};
fi

# Source the common library.
. utils/common.sh

# Update auto-generated documentation.
regenerate_docs

# Check if we're on the master branch.
BRANCH=`git branch | grep -e "^[*]" | sed "s/^[*] //"`;

if test "${BRANCH}" != "master";
then
  echo "Submit aborted - current branch is not master.";

  exit ${EXIT_FAILURE};
fi

# Check for double status codes, upload.py cannot handle these correctly.
STATUS_CODES=`git status -s | cut -b1,2 | grep '\S\S' | grep -v '??' | sort | uniq`;

if ! test -z "${STATUS_CODES}";
then
  echo "Submit aborted - detected double git status codes."
  echo "Run: 'git stash && git stash pop'.";

  exit ${EXIT_FAILURE};
fi

# Check if the local repo is in sync with the origin.
git fetch

if test $? -ne 0;
then
  echo "Submit aborted - unable to fetch updates from origin repo";

  exit ${EXIT_FAILURE};
fi

NUMBER_OF_CHANGES=`git log HEAD..origin/master --oneline | wc -l`;

if test $? -ne 0;
then
  echo "Submit aborted - unable to determine if local repo is in sync with origin";

  exit ${EXIT_FAILURE};
fi

if test ${NUMBER_OF_CHANGES} -ne 0;
then
  echo "Submit aborted - local repo out of sync with origin."
  echo "Run: 'git stash && git pull && git stash pop'.";

  exit ${EXIT_FAILURE};
fi

# Check if the linting is correct.
if ! linter;
then
  echo "Submit aborted - fix the issues reported by the linter.";

  exit ${EXIT_FAILURE};
fi

# Check if all the tests pass.
if test -e run_tests.py;
then
  echo "Running tests.";
  python run_tests.py

  if test $? -ne 0;
  then
    echo "Submit aborted - fix the issues reported by the failing test.";

    exit ${EXIT_FAILURE};
  fi
fi

URL_CODEREVIEW="https://codereview.appspot.com";

# Get the description of the change list.
RESULT=`which json_xs`;

# TODO: check if curl exists.
if ! test -z "${RESULT}";
then
  DESCRIPTION=`curl -s ${URL_CODEREVIEW}/api/${CL_NUMBER} | json_xs | grep '"subject"' | awk -F '"' '{print $(NF-1)}'`;
else
  DESCRIPTION=`curl ${URL_CODEREVIEW}/${CL_NUMBER}/ -s | grep "Issue ${CL_NUMBER}" | awk -F ':' '{print $2}' | tail -1`;
fi

if test -z "${DESCRIPTION}";
then
  echo "Submit aborted - unable to find change list with number: ${CL_NUMBER}.";

  exit ${EXIT_FAILURE};
fi

# Update the version information.
echo "Updating version information to match today's date."

if test -f "utils/update_version.sh";
then
  . utils/update_version.sh
fi

COMMIT_DESCRIPTION="Code review: ${CL_NUMBER}: ${DESCRIPTION}";
echo "Submitting ${COMMIT_DESCRIPTION}";

# Check if we need to set --cache.
STATUS_CODES=`git status -s | cut -b1,2 | sed 's/\s//g' | sort | uniq`;

for STATUS_CODE in ${STATUS_CODES};
do
  if test "${STATUS_CODE}" = "A";
  then
    CACHE_PARAM="--cache";
  fi
done

python utils/upload.py \
    --oauth2 ${BROWSER_PARAM} -y -i ${CL_NUMBER} ${CACHE_PARAM} \
    -t "Submitted." -m "Code Submitted." --send_mail

git commit -a -m "${COMMIT_DESCRIPTION}";
git push

if test -f "~/codereview_upload_cookies";
then
  curl -b ~/.codereview_upload_cookies ${URL_CODEREVIEW}/${CL_NUMBER}/close -d  ''
else
  echo "Could not find an authenticated session to codereview. You need to"
  echo "manually close the ticket on the code review site."
fi

if ! test -z "${USE_CL_FILE}" && test -f "._code_review_number";
then
  rm -f ._code_review_number
fi

exit ${EXIT_SUCCESS};
