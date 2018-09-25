# Automated tests

Plaso comes with multiple forms of automated tests:

* unit tests
* end-to-end tests

## Unit tests

The unit tests are intended to detect issues after individual changes (change lists). Unit tests are typically small by nature and only test a specific part of the code.

The unit tests are stored in the `tests` sub directory, in the same directory hierarchy as the plaso module directory, and can be run with:
```
python run_tests.py
```

The unit tests are also run automatically on [Travis-CI](https://travis-ci.org/) and [AppVeyor](https://ci.appveyor.com) after every commit (code submit) to detect cross platform issues. 

## End-to-end tests

The end-to-end tests are intended to test the plaso tools as a user would run them. To run the end-to-end tests you'll need:

* test runner, which is `tests/end-to-end.py`
* end-to-end tests configuration, e.g. `config/end-to-end.ini`
* test data
* reference data, to compare test output against

E.g. to run the predefined end-to-end tests:

```
PYTHONPATH=. python ./tests/end-to-end.py --debug -c config/end-to-end.ini
```

The predefined end-to-end tests are also run automatically on [Travis-CI](https://travis-ci.org/) after every commit (code submit).