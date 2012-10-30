#!/bin/bash
# A small script that runs all tests

# Export the python path
export PYTHONPATH=.

cd ..
find plaso -name "*_test.py" | while read test_file
do
  echo "--- $test_file ---"
  python ./plaso/frontend/psort_test.py
done
