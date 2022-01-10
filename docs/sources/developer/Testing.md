# Testing

Plaso comes with multiple forms of tests:

* unit tests
* end-to-end tests

## Unit tests

The unit tests are intended to detect issues after individual changes (pull
requests). Unit tests are typically small by nature and only test a specific
part of the code.

The unit tests are stored in the `tests` sub directory, in the same parent
directory as the plaso module directory. The unit tests can be run with:

```
python run_tests.py
```

Or if you have tox installed:

```
tox -epy310
```

The unit tests are also run on [GitHub](https://github.com/log2timeline/plaso/actions)
and [AppVeyor](https://ci.appveyor.com/project/log2timeline/plaso) after every
pull request or commit to detect issues early.

## End-to-end tests

The end-to-end tests are intended to test the Plaso tools as a user would run
them. To run the end-to-end tests you'll need:

* the end-to-end test runner script, which is `tests/end-to-end.py`
* end-to-end tests configuration, for example `config/end-to-end.ini`
* location of the reference data, to compare test output against
* location of the result data
* location of the source data

For example, to run the predefined end-to-end tests:

```
PYTHONPATH=. python ./tests/end-to-end.py --debug -c config/end-to-end.ini --references-directory test_reference_data --results-directory test_results --sources-directory test_source_data
```

The predefined end-to-end tests are also run automatically on [GitHub](https://github.com/log2timeline/plaso/actions)
after every commit (code submit).

### Running end-to-end tests with Docker

To run end-to-end tests with Docker you'll need:

* Linux with Docker installed
* the end-to-end test Docker script, which is `config/end_to_end/run_tests_with_docker.sh`
* location of the end-to-end tests configurations
* location of the result data
* location of the source data

```
./config/end_to_end/run_tests_with_docker.sh /greendale/configs /greendale/sources /greendale/results
```

