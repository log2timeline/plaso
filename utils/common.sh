#!/bin/bash
# Script that contains common functions for code review checks.

EXIT_FAILURE=1;
EXIT_SUCCESS=0;

FALSE=1;
TRUE=0;

export PROJECT_NAME="plaso";
export GIT_URL="https://github.com/log2timeline/${PROJECT_NAME}.git";

# Function to check if curl is available.
have_curl()
{
  CURL=`which curl 2>/dev/null`;

  if ! test -z "${CURL}";
  then
    return ${TRUE};
  fi
  return ${FALSE};
}

# Function to check for double status codes rietveld does not seem to handle
# these correctly.
have_double_git_status_codes()
{
  STATUS_CODES=`git status -s | cut -b1,2 | grep '\S\S' | grep -v '??' | sort | uniq`;

  if ! test -z "${STATUS_CODES}";
  then
    return ${TRUE};
  fi
  return ${FALSE};
}

# Function to check if we are on the master branch.
have_master_branch()
{
  BRANCH="";
  get_current_branch "BRANCH";

  if test "${BRANCH}" = "master";
  then
    return ${TRUE};
  fi
  return ${FALSE};
}

# Function to check if we have the correct remote origin defined.
have_remote_origin()
{
  REMOTE=`git remote -v | grep 'origin' | awk '{ print $2 }' | sort | uniq`;

  if test "${REMOTE}" = "${GIT_URL}";
  then
    return ${TRUE};
  fi
  return ${FALSE};
}

# Function to check if we have the correct remote upstream defined.
have_remote_upstream()
{
  REMOTE=`git remote -v | grep 'upstream' | awk '{ print $2 }' | sort | uniq`;

  if test "${REMOTE}" = "${GIT_URL}";
  then
    return ${TRUE};
  fi
  return ${FALSE};
}

# Function to check if we have uncommitted changes.
have_uncommitted_changes()
{
  # Ignore the '??' status code.
  GIT_STATUS=`git status -s | grep -v -e '^?? '`;

  if test -z "${GIT_STATUS}";
  then
    return ${FALSE};
  fi
  return ${TRUE};
}

# Function to check if we have uncommitted changes with new files.
have_uncommitted_changes_with_append_status()
{
  RESULT=${FALSE};
  STATUS_CODES=`git status -s | cut -b1,2 | sed 's/\s//g' | sort | uniq`;

  for STATUS_CODE in ${STATUS_CODES};
  do
    if test "${STATUS_CODE}" = "A";
    then
      RESULT=${TRUE};
    fi
  done
  return ${RESULT};
}

# Function to generate the API documentation.
generate_api_documentation()
{
  which sphinx-apidoc >/dev/null 2>&1;

  if test $? -ne ${EXIT_SUCCESS};
  then
    echo "WARNING: missing sphinx-apidoc - unable to update API documentation.";

    return ${FALSE};
  fi

  echo "Updating API documentation.";
  sphinx-apidoc -f -o ./docs "./${PROJECT_NAME}";

  git add ./docs;

  return ${TRUE};
}

# Function to retrieve the name of the current branch.
get_current_branch()
{
  RESULT=`git branch | grep -e "^[*]" | sed "s/^[*] //"`;
  eval "$1='${RESULT}'";
}

# Function to retrieve the description of the last committed change.
get_last_change_description()
{
  RESULT=`git log | head -n5 | tail -n1 | sed 's/^[ ]*//'`;
  eval "$1='${RESULT}'";
}

# Function to check if the linting of the changes is correct.
# Version for usage with remote origin.
linting_is_correct_remote_origin()
{
  # Examples of the output of "git status -s"
  # If a file is added:
  # A utils/common.sh
  # If a file is modified:
  # M utils/common.sh
  # If a file is renamed:
  # R utils/common.sh -> utils/uncommon.sh
  # If a file is modified and renamed:
  # RM utils/common.sh -> utils/uncommon.sh
  AWK_SCRIPT="if (\$1 == \"A\" || \$1 == \"AM\" || \$1 == \"M\" || \$1 == \"MM\") { print \$2; } else if (\$1 == \"R\" || \$1 == \"RM\") { print \$4; }";

  # First find all files that need linter
  FILES=`git status -s | grep -v "^?" | awk "{ ${AWK_SCRIPT} }" | grep "\.py$"`;

  # Determine the current pylint version.
  PYLINT_VERSION=`pylint --version 2> /dev/null | awk '/pylint/ {print $2}' | rev | cut -c2- | rev`;

  # Check if pylint version is < 1.4.0
  # The following sed operation mimics 'sort -V' since it is not available on Mac OS X
  RESULT=`echo -e "${PYLINT_VERSION}\n1.3.99" | sed 's/^[0-9]\./0&/; s/\.\([0-9]\)$/.0\1/; s/\.\([0-9]\)\./.0\1./g;s/\.\([0-9]\)\./.0\1./g' | sort | sed 's/^0// ; s/\.0/./g' | head -n1`;

  if test "${RESULT}" = "${PYLINT_VERSION}";
  then
    echo "pylint verion 1.4.0 or later required.";

    exit ${EXIT_FAILURE};
  fi
  LINTER="pylint --rcfile=utils/pylintrc"

  echo "Running linter on changed files.";

  for FILE in ${FILES};
  do
    if test "${FILE}" = "setup.py" || test "${FILE}" = "utils/upload.py";
    then
      echo "Skipping: ${FILE}";
      continue
    fi

    if test `echo ${FILE} | tail -c8` = "_pb2.py";
    then
      echo "Skipping: ${FILE}";
      continue
    fi

    echo "Checking: ${FILE}";
    ${LINTER} "${FILE}"

    if test $? -ne 0;
    then
      echo "Fix linter errors before proceeding.";
      return ${FALSE};
    fi
  done

  if test $? -ne 0;
  then
    return ${FALSE};
  fi

  echo "Linter clear.";

  return ${TRUE};
}

# Function to check if the linting is correct.
# Version for usage with remote upstream
linting_is_correct_remote_upstream()
{
  # Determine the current pylint version.
  PYLINT_VERSION=`pylint --version 2> /dev/null | awk '/pylint/ {print $2}' | rev | cut -c2- | rev`;

  # Check if pylint version is < 1.4.0
  # The following sed operation mimics 'sort -V' since it is not available on Mac OS X
  RESULT=`echo -e "${PYLINT_VERSION}\n1.3.99" | sed 's/^[0-9]\./0&/; s/\.\([0-9]\)$/.0\1/; s/\.\([0-9]\)\./.0\1./g;s/\.\([0-9]\)\./.0\1./g' | sort | sed 's/^0// ; s/\.0/./g' | head -n1`;

  if test "${RESULT}" = "${PYLINT_VERSION}";
  then
    echo "pylint verion 1.4.0 or later required.";

    exit ${EXIT_FAILURE};
  fi
  echo "Running linter.";

  LINTER="pylint --rcfile=utils/pylintrc";
  RESULT=${TRUE};

  FILES=`git diff --name-only upstream/master | grep "\.py$"`;

  for FILE in ${FILES};
  do
    if test "${FILE}" = "setup.py" || test "${FILE}" = "utils/upload.py";
    then
      echo "Skipping: ${FILE}";
      continue
    fi

    if test `echo ${FILE} | tail -c8` = "_pb2.py";
    then
      echo "Skipping: ${FILE}";
      continue
    fi

    if ! test -f "${FILE}";
    then
      echo "Skipping: ${FILE}";
      continue
    fi

    echo "Checking: ${FILE}";
    ${LINTER} "${FILE}";

    if test $? -ne 0;
    then
      # TODO: allow lint all before erroring.
      echo "Fix linter errors before proceeding.";

      return ${FALSE};
    fi
  done

  if test $? -ne 0;
  then
    RESULT=${FALSE};
  fi
  return ${RESULT};
}

# Function to check if the local repo is in sync with the origin.
local_repo_in_sync_with_origin()
{
  git fetch origin master >/dev/null 2>&1;

  if test $? -ne 0;
  then
    echo "Unable to fetch updates from origin.";

    exit ${EXIT_FAILURE};
  fi
  NUMBER_OF_CHANGES=`git log HEAD..origin/master --oneline | wc -l`;

  if test $? -ne 0;
  then
    echo "Unable to determine if local repo is in sync with origin.";

    exit ${EXIT_FAILURE};
  fi

  if test ${NUMBER_OF_CHANGES} -eq 0;
  then
    return ${TRUE};
  fi
  return ${FALSE};
}

# Function to check if the local repo is in sync with the upstream
local_repo_in_sync_with_upstream()
{
  # Fetch the entire upstream repo information not only that of
  # the master branch. Otherwise the information about the current upstream
  # HEAD is not updated.
  git fetch upstream >/dev/null 2>&1;

  if test $? -ne 0;
  then
    echo "Unable to fetch updates from upstream";

    exit ${EXIT_FAILURE};
  fi
  NUMBER_OF_CHANGES=`git log HEAD..upstream/master --oneline | wc -l`;

  if test $? -ne 0;
  then
    echo "Unable to determine if local repo is in sync with upstream";

    exit ${EXIT_FAILURE};
  fi

  if test ${NUMBER_OF_CHANGES} -eq 0;
  then
    return ${TRUE};
  fi
  return ${FALSE};
}

# Function to check if the tests pass.
# Note that the function will also return true (0) if the run_tests.py script
# cannot be found.
tests_pass()
{
  if ! test -e run_tests.py;
  then
    return ${TRUE};
  fi

  echo "Running tests.";
  python run_tests.py

  if test $? -eq 0;
  then
    return ${TRUE};
  fi
  return ${FALSE};
}
