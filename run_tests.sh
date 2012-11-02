#!/bin/bash
# A small script that runs all tests

# Export the python path
export PYTHONPATH=.

cd ..
find plaso -name "*_test.py" | while read test_file
do
  echo "---+ $test_file +---"
  PYTHONPATH=. /usr/bin/python ./${test_file}
  if [ $? -ne 0 ]
  then
    echo "TEST FAILED (${test_file})."
    echo "Stopping further testing."
    exit 12
  fi
  echo " "
done
