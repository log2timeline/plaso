#!/bin/bash
# Script that updates a change list for code review.

EXIT_FAILURE=1;
EXIT_MISSING_ARGS=2;
EXIT_SUCCESS=0;

SCRIPTNAME=`basename $0`;

BROWSER_PARAM="";
CL_NUMBER="";
DIFFBASE="upstream/master";

if ! test -f "utils/common.sh";
then
  echo "Unable to find common scripts (utils/common.sh).";
  echo "This script can only be run from the root of the source directory.";

  exit ${EXIT_FAILURE};
fi

. utils/common.sh

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
    CL_NUMBER=`cat ${CL_FILENAME}`;
    RESULT=`echo ${CL_NUMBER} | sed -e 's/[0-9]//g'`;

    if ! test -z "${RESULT}";
    then
      echo "${CL_FILENAME} contains an invalid CL number.";

      exit ${EXIT_FAILURE};
    fi
  fi
fi

if test -z "${CL_NUMBER}";
then
  echo "Usage: ./${SCRIPTNAME} [--nobrowser] [CL_NUMBER]";
  echo "";
  echo "  CL_NUMBER: optional change list (CL) number that is to be updated.";
  echo "             If no CL number is provided the value is read from the";
  echo "             corresponding file in: .review/";
  echo "";
  echo "  --diffbase: the name of the branch to use as diffbase for the CL.";
  echo "              The default is upstream/master";
  echo "";
  echo "  --nobrowser: forces upload.py not to open a separate browser";
  echo "               process to obtain OAuth2 credentials for Rietveld";
  echo "               (https://codereview.appspot.com).";
  echo "";

  exit ${EXIT_MISSING_ARGS};
fi

if ! ${HAVE_REMOTE_ORIGIN};
then
  if ! have_remote_upstream;
  then
    echo "Update aborted - missing upstream.";
    echo "Run: 'git remote add upstream https://github.com/log2timeline/${PROJECT_NAME}.git'";

    exit ${EXIT_FAILURE};
  fi
  git fetch upstream;

  if have_master_branch;
  then
    echo "Update aborted - current branch is master.";

    exit ${EXIT_FAILURE};
  fi

  if have_uncommitted_changes;
  then
    echo "Update aborted - detected uncommitted changes.";

    exit ${EXIT_FAILURE};
  fi

  if ! local_repo_in_sync_with_upstream;
  then
    echo "Local repo out of sync with upstream: running 'git pull --rebase upstream master'.":
    git pull --rebase upstream master

    if test $? -ne 0;
    then
      echo "Update aborted - unable to run: 'git pull --rebase upstream master'.";

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
    echo "Update aborted - fix the issues reported by the linter.";

    exit ${EXIT_FAILURE};
  fi
else
  if have_double_git_status_codes;
  then
    echo "Update aborted - detected double git status codes."
    echo "Run: 'git stash && git stash pop'.";

    exit ${EXIT_FAILURE};
  fi

  if ! linting_is_correct_remote_origin;
  then
    echo "Update aborted - fix the issues reported by the linter.";

    exit ${EXIT_FAILURE};
  fi
fi

if ! tests_pass;
then
  echo "Update aborted - fix the issues reported by the failing test.";

  exit ${EXIT_FAILURE};
fi

if ! ${HAVE_REMOTE_ORIGIN};
then
  git push;

  if test $? -ne 0;
  then
    echo "Unable to push to origin";
    echo "";
  
    exit ${EXIT_FAILURE};
  fi

  DESCRIPTION="";
  get_last_change_description "DESCRIPTION";

  python utils/upload.py \
      --oauth2 ${BROWSER_PARAM} -i ${CL_NUMBER} -m "Code updated." \
      -t "${DESCRIPTION}" -y -- ${DIFFBASE};

else
  CACHE_PARAM="";
  if have_uncommitted_changes_with_append_status;
  then
    CACHE_PARAM="--cache";
  fi
  echo -n "Short description of the update: ";
  read DESCRIPTION

  python utils/upload.py \
      --oauth2 ${BROWSER_PARAM} ${CACHE_PARAM} -i ${CL_NUMBER} \
      -m "Code updated." -t "${DESCRIPTION}" -y;
fi

exit ${EXIT_SUCCESS};
