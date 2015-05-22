#!/bin/bash
# Script to test the plaso extraction and output tools, namely
# log2timeline.py, pinfo.py and psort.py
#
# For more information see:
# https://github.com/log2timeline/plaso/wiki/Testing

EXIT_FAILURE=1;
EXIT_SUCCESS=0;

list_contains()
{
  LIST=$1;
  SEARCH=$2;

  for LINE in $LIST;
  do
    if test $LINE = $SEARCH;
    then
      return ${EXIT_SUCCESS};
    fi
  done

  return ${EXIT_FAILURE};
}

MODULE_DIR=".";
TOOLS_DIR="./tools";

while test $# -gt 0;
do
  case $1 in
  --module )
    MODULE_DIR=$2;
    shift
    shift
    ;;

  --tools ) 
    TOOLS_DIR=$2;
    shift
    shift
    ;;

  *)
    break
    ;;
  esac
done

TEST_DATA_DIR=$1;
RESULTS_DIR=$2;

if test -z ${TEST_DATA_DIR} || test -z ${RESULTS_DIR};
then
  echo "Usage: $0 [--module PATH] [--tools PATH] TEST_DATA RESULTS";
  echo "";
  echo "  --module PATH: the plaso module directory, e.g.";
  echo "                 /usr/lib/python2.7/site-packages/plaso";
  echo "  --tools PATH:  the plaso tools directory, e.g.";
  echo "                 /usr/bin";
  echo "";
  echo "  TEST_DATA:     the test data directory. This directory contains ";
  echo "                 the test configurations, input and reference data.";
  echo "  RESULTS:       the test results directory. This directory contain ";
  echo "                 the test results.";

  exit ${EXIT_FAILURE};
fi;

if ! test -d "${TOOLS_DIR}";
then
  echo "Missing plaso tools directory: ${TOOLS_DIR}";

  exit ${EXIT_FAILURE};
fi

if ! test -d "${TEST_DATA_DIR}";
then
  echo "Missing test data directory: ${TEST_DATA_DIR}";

  exit ${EXIT_FAILURE};
fi

if ! test -d "${RESULTS_DIR}";
then
  echo "Missing results directory: ${RESULTS_DIR}";

  exit ${EXIT_FAILURE};
fi

PYTHONPATH="PYTHONPATH=${MODULE_DIR}";

LOG2TIMELINE="${TOOLS_DIR}/log2timeline.py";
PINFO="${TOOLS_DIR}/pinfo.py";
PSORT="${TOOLS_DIR}/psort.py";

# TODO: change plaso to support a list of profiling types, e.g.
# --profiling_type=parsers,serializers
PROFILING_OPTIONS="--profile --profiling_type=parsers";

DATE=`date +"%Y-%m-%dT%H:%M:%S"`;
VERSION=`eval ${PYTHONPATH} ${LOG2TIMELINE} --version 2>&1 | awk '{ print $NF }'`;

TEST_CONFIG_DIR="${TEST_DATA_DIR}/.extract_and_output";
RESULT_SET_DIR="${RESULTS_DIR}/${DATE}-${VERSION}";

if ! test -d "${TEST_CONFIG_DIR}";
then
  mkdir -p "${TEST_CONFIG_DIR}";

  if ! test -d "${TEST_CONFIG_DIR}";
  then
    echo "Unable to create test configuration directory: ${TEST_CONFIG_DIR}";

    exit ${EXIT_FAILURE};
  fi
fi

if test -d "${RESULT_SET_DIR}";
then
  echo "Result set directory: ${RESULT_SET_DIR} already exists.";

  exit ${EXIT_FAILURE};
fi

echo "Creating result set directory: ${RESULT_SET_DIR}";
mkdir -p "${RESULT_SET_DIR}";

if ! test -d "${RESULT_SET_DIR}";
then
  echo "Unable to create result set directory: ${RESULT_SET_DIR}";

  exit ${EXIT_FAILURE};
fi

OLDIFS=$IFS;
IFS="
";

IGNORE_LIST="";

if test -f "${TEST_CONFIG_DIR}/ignore";
then
  IGNORE_LIST=`cat "${TEST_CONFIG_DIR}/ignore" | sed '/^#/d'`;
fi

RESULT=${EXIT_SUCCESS};
for TEST_SET in `ls -1 ${TEST_DATA_DIR}`;
do
  TEST_DIR="${TEST_DATA_DIR}/${TEST_SET}";

  if ! test -d "${TEST_DIR}";
  then
    continue;
  fi

  if list_contains "${IGNORE_LIST}" "${TEST_SET}";
  then
    continue;
  fi

  if test -f "${TEST_CONFIG_DIR}/${TEST_SET}/files";
  then
    TEST_FILES=`cat "${TEST_CONFIG_DIR}/${TEST_SET}/files" | sed "s?^?${TEST_DIR}/?"`;
  else
    TEST_FILES=`ls -1 "${TEST_DIR}" | sed "s?^?${TEST_DIR}/?" | tr '\n' ' '`;
  fi

  if test -f "${TEST_CONFIG_DIR}/${TEST_SET}/options";
  then
    OPTIONS=`cat "${TEST_CONFIG_DIR}/${TEST_SET}/options" | sed '/^#/d'`;
  else
    # Need a space here otherwise the test options loop is not run.
    OPTIONS=" ";
  fi

  mkdir "${RESULT_SET_DIR}/${TEST_SET}";

  for TEST_FILE in ${TEST_FILES};
  do
    TEST_PREFIX_NAME=`basename ${TEST_FILE} | sed 's/[.][^.]*$//'`;

    TEST_OPTIONS_SET=1;
    for TEST_OPTIONS in ${OPTIONS};
    do
      TEST_PREFIX="${RESULT_SET_DIR}/${TEST_SET}/${TEST_PREFIX_NAME}";

      STORAGE_FILE="${TEST_PREFIX}-${TEST_OPTIONS_SET}.plaso";
      LOG_FILE="${TEST_PREFIX}-${TEST_OPTIONS_SET}.log";
      OUTPUT_FILE="${TEST_PREFIX}-log2timeline-${TEST_OPTIONS_SET}.log.gz";

      # Note that output log files are gzip compressed to take up less space.

      if test "${TEST_OPTIONS}" != " ";
      then
        echo "Running: log2timeline ${TEST_OPTIONS} on ${TEST_FILE}";
      else
        echo "Running: log2timeline on ${TEST_FILE}";
      fi
      eval ${PYTHONPATH} ${LOG2TIMELINE} ${TEST_OPTIONS} ${PROFILING_OPTIONS} --log-file "${LOG_FILE}" "${STORAGE_FILE}" "${TEST_FILE}" 2>&1 | gzip - > "${OUTPUT_FILE}";

      if ! test -z "${PROFILING_OPTIONS}";
      then
        for CSV_FILE in *.csv;
        do
          mv "${CSV_FILE}" "${TEST_PREFIX}-${CSV_FILE}";
        done
      fi

      if test $? -ne ${EXIT_SUCCESS};
      then
        RESULT=${EXIT_FAILURE};
        echo "FAILED";
        continue
      fi

      OUTPUT_FILE="${TEST_PREFIX}-pinfo-${TEST_OPTIONS_SET}.log.gz";

      echo "Running: pinfo on ${STORAGE_FILE}";
      eval ${PYTHONPATH} ${PINFO} "${STORAGE_FILE}" 2>&1 | gzip - > "${OUTPUT_FILE}";

      if test $? -ne ${EXIT_SUCCESS};
      then
        RESULT=${EXIT_FAILURE};
        echo "FAILED";
        continue
      fi

      COMPARE_STORAGE_FILE="${TEST_CONFIG_DIR}/${TEST_SET}/${TEST_PREFIX_NAME}-${TEST_OPTIONS_SET}.plaso";
      OUTPUT_FILE="${TEST_PREFIX}-pinfo-compare-${TEST_OPTIONS_SET}.log.gz";

      if test -f "${COMPARE_STORAGE_FILE}";
      then
        echo "Running: pinfo --compare on ${STORAGE_FILE}";
        eval ${PYTHONPATH} ${PINFO} --compare "${COMPARE_STORAGE_FILE}" "${STORAGE_FILE}" 2>&1 | gzip - > "${OUTPUT_FILE}";

        if test $? -ne ${EXIT_SUCCESS};
        then
          RESULT=${EXIT_FAILURE};
          echo "FAILED";
          continue
        fi
      fi

      OUTPUT_FILE="${TEST_PREFIX}-psort-${TEST_OPTIONS_SET}.log.gz";

      echo "Running: psort on ${STORAGE_FILE}";
      eval ${PYTHONPATH} ${PSORT} "${STORAGE_FILE}" 2>&1 | gzip - > "${OUTPUT_FILE}";

      if test $? -ne ${EXIT_SUCCESS};
      then
        RESULT=${EXIT_FAILURE};
        echo "FAILED";
        continue
      fi

      TEST_OPTIONS_SET=`expr ${TEST_OPTIONS_SET} + 1`;
    done
  done
done

IFS=$OLDIFS;

if test ${RESULT} -eq ${EXIT_SUCCESS};
then
  echo "SUCCESS";
fi

exit ${RESULT};

