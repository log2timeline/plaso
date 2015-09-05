#!/bin/bash
# Script that submits a code for code review.

EXIT_SUCCESS=0;
EXIT_MISSING_ARGS=2;
EXIT_SUCCESS=0;

SCRIPTNAME=`basename $0`;
NETRC="${HOME}/.netrc";

BROWSER_PARAM="";
USE_CL_FILE=1;
CL_FILENAME="";
BRANCH="";
DIFFBASE="upstream/master";
SHOW_HELP=0;

if test -e ".review" && ! test -d ".review";
then
  echo "Invalid source tree: .review exists but is not a directory.";

  exit ${EXIT_FAILURE};
fi

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

if ! test -f "${NETRC}";
then
  echo "No such file: ${NETRC}";

  exit ${EXIT_FAILURE};
fi

ACCESS_TOKEN=`grep 'github.com' ${NETRC} | awk '{ print $6 }'`;

if test -z "${ACCESS_TOKEN}";
then
  echo "Unable to determine github.com access token from: ${NETRC}";

  exit ${EXIT_FAILURE};
fi

# TODO: add diffbase support?

# Determine if we have the master repo as origin.
HAVE_REMOTE_ORIGIN=have_remote_origin;

while test $# -gt 0;
do
  case $1 in
  --diffbase )
    shift;
    DIFFBASE=$1;
    shift;
    ;;

  --nobrowser | --no-browser | --no_browser )
    BROWSER_PARAM="--no_oauth2_webbrowser";
    shift;
    ;;

  --noclfile | --no-clfile | --no_clfile )
    USE_CL_FILE=0;
    shift;
    ;;

  -h | --help )
    SHOW_HELP=1;
    shift;
    ;;

  *)
    REVIEWERS=$1;
    shift
    ;;
  esac
done

if test ${SHOW_HELP} -ne 0;
then
  echo "Usage: ./${SCRIPTNAME} [--nobrowser] [--noclfile]";
  echo "";
  echo "  --diffbase: the name of the branch to use as diffbase for the CL.";
  echo "              The default is upstream/master";
  echo "";
  echo "  --diffbase: the name of the branch to use as diffbase for the CL.";
  echo "              The default is upstream/master";
  echo "";
  echo "  --nobrowser: forces upload.py not to open a separate browser";
  echo "               process to obtain OAuth2 credentials for Rietveld";
  echo "               (https://codereview.appspot.com).";
  echo "";
  echo "  --noclfile: do not store the resulting CL number in a CL file"
  echo "              stored in .review/";
  echo "";

  exit ${EXIT_SUCCESS};
fi

if ! test -z ${REVIEWERS};
then
  echo "The need to explicitly pass reviewers to this script has been removed.";
  echo "The script now defaults to the maintainers.";
  echo "";
fi

REVIEWERS="kiddi@kiddaland.net,joachim.metz@gmail.com,onager@deerpie.com";
CC="log2timeline-dev@googlegroups.com";

if ! ${HAVE_REMOTE_ORIGIN};
then
  if ! have_remote_upstream;
  then
    echo "Review aborted - missing upstream.";
    echo "Run: 'git remote add upstream https://github.com/log2timeline/${PROJECT_NAME}.git'";

    exit ${EXIT_FAILURE};
  fi
  git fetch upstream;

  if have_master_branch;
  then
    echo "Review aborted - current branch is master.";

    exit ${EXIT_FAILURE};
  fi

  if have_uncommitted_changes;
  then
    echo "Review aborted - detected uncommitted changes.";

    exit ${EXIT_FAILURE};
  fi

  if ! local_repo_in_sync_with_upstream;
  then
    echo "Local repo out of sync with upstream: running 'git pull --rebase upstream master'.":
    git pull --rebase upstream master

    if test $? -ne 0;
    then
      echo "Review aborted - unable to run: 'git pull --rebase upstream master'.";

      exit ${EXIT_FAILURE};
    fi
    git push -f

    if test $? -ne 0;
    then
      echo "Review aborted - unable to run: 'git push -f' after update with upstream.";

      exit ${EXIT_FAILURE};
    fi
  fi

  if ! linting_is_correct_remote_upstream;
  then
    echo "Review aborted - fix the issues reported by the linter.";

    exit ${EXIT_FAILURE};
  fi

else
  if have_double_git_status_codes;
  then
    echo "Review aborted - detected double git status codes."
    echo "Run: 'git stash && git stash pop'.";

    exit ${EXIT_FAILURE};
  fi

  if ! linting_is_correct_remote_origin;
  then
    echo "Review aborted - fix the issues reported by the linter.";

    exit ${EXIT_FAILURE};
  fi
fi

if ! tests_pass;
then
  echo "Review aborted - fix the issues reported by the failing test.";

  exit ${EXIT_FAILURE};
fi

if test ${USE_CL_FILE} -ne 0;
then
  get_current_branch "BRANCH";

  CL_FILENAME=".review/${BRANCH}";

  if test -f ${CL_FILENAME};
  then
    echo "Review aborted - CL file already exitst: ${CL_FILENAME}";
    echo "Do you already have a code review pending for the current branch?";

    exit ${EXIT_FAILURE};
  fi
fi

if ! ${HAVE_REMOTE_ORIGIN};
then
  get_current_branch "BRANCH";

  git push --set-upstream origin ${BRANCH};

  if test $? -ne 0;
  then
    echo "Unable to push to origin";
    echo "";
  
    exit ${EXIT_FAILURE};
  fi

  DESCRIPTION="";
  get_last_change_description "DESCRIPTION";

  echo "Automatic generated description of code review request:";
  echo "${DESCRIPTION}";
  echo "";

  echo "Hit enter to use the automatic description or enter an alternative";
  echo "description of code review request:";
  read INPUT_DESCRIPTION

  if ! test -z "${INPUT_DESCRIPTION}";
  then
    DESCRIPTION=${INPUT_DESCRIPTION};
  fi

  if ! test -z "${BROWSER_PARAM}";
  then
    echo "Upload server: codereview.appspot.com (change with -s/--server)";
    echo "Go to the following link in your browser:";
    echo "";
    echo "    https://codereview.appspot.com/get-access-token";
    echo "";
    echo "and copy the access token.";
    echo "";
    echo -n "Enter access token: ";
  fi

  TEMP_FILE=`mktemp .tmp_${PROJECT_NAME}_code_review.XXXXXX`;

  python utils/upload.py \
      --oauth2 ${BROWSER_PARAM} \
      --send_mail -r ${REVIEWERS} --cc ${CC} \
      -t "${DESCRIPTION}" -y -- ${DIFFBASE} | tee ${TEMP_FILE};

  CL=`cat ${TEMP_FILE} | grep codereview.appspot.com | awk -F '/' '/created/ {print $NF}'`;
  cat ${TEMP_FILE};
  rm -f ${TEMP_FILE};

  if test -z ${CL};
  then
    echo "Unable to upload code change for review.";

    exit ${EXIT_FAILURE};
  fi

  if test -z "${BRANCH}";
  then
    get_current_branch "BRANCH";
  fi

  ORGANIZATION=`git remote -v | grep 'origin' | sed 's?^.*https://github.com/\([^/]*\)/.*$?\1?' | sort | uniq`;

  POST_DATA="{
  \"title\": \"${CL}: ${DESCRIPTION}\",
  \"body\": \"[Code review: ${CL}: ${DESCRIPTION}](https://codereview.appspot.com/${CL}/)\",
  \"head\": \"${ORGANIZATION}:${BRANCH}\",
  \"base\": \"master\"
}";

  echo "Creating pull request.";
  curl -s --data "${POST_DATA}" https://api.github.com/repos/log2timeline/${PROJECT_NAME}/pulls?access_token=${ACCESS_TOKEN} >/dev/null;

  if test $? -ne 0;
  then
    echo "Unable to create pull request.";
    echo "";

    exit ${EXIT_FAILURE};
  fi

else
  echo "Enter a description of code review request:";
  read DESCRIPTION

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

  if ! test -z "${BROWSER_PARAM}";
  then
    echo "Upload server: codereview.appspot.com (change with -s/--server)";
    echo "Go to the following link in your browser:";
    echo "";
    echo "    https://codereview.appspot.com/get-access-token";
    echo "";
    echo "and copy the access token.";
    echo "";
    echo -n "Enter access token: ";
  fi

  TEMP_FILE=`mktemp .tmp_${PROJECT_NAME}_code_review.XXXXXX`;

  python utils/upload.py \
      --oauth2 ${BROWSER_PARAM} ${CACHE_PARAM} \
      --send_mail -r ${REVIEWERS} --cc ${CC} \
      -m "${DESCRIPTION}" -t "${DESCRIPTION}" -y | tee ${TEMP_FILE};

  CL=`cat ${TEMP_FILE} | grep codereview.appspot.com | awk -F '/' '/created/ {print $NF}'`;
  cat ${TEMP_FILE};
  rm -f ${TEMP_FILE};

  if test -z ${CL};
  then
    echo "Unable to upload code change for review.";

    exit ${EXIT_FAILURE};
  fi
fi

if test ${USE_CL_FILE} -ne 0;
then
  if ! test -e ".review";
  then
    mkdir .review;
  fi

  echo ${CL} > ${CL_FILENAME};

  echo "";
  echo "Saved code review number for future updates.";
fi

exit ${EXIT_SUCCESS};
