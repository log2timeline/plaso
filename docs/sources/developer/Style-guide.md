# Style Guide

Plaso follows the [log2timeline style guide](https://github.com/log2timeline/l2tdocs/blob/master/process/Style-guide.md).

## Plaso specific style points

### Tests

* Use as much as possible the test functions available in the local test_lib.py instead of writing your own test functions. If you think a test function is missing please add it, or mail the developer list to see if you can get someone else to do it.
* Use `self.CheckTimestamp` for testing timestamp values.

Common test code should be stored in "test library" files, e.g. the parser test library:

    tests/parsers/test_lib.py

We do this for various reasons:

* to remove code duplication in "boiler plate" test code;
* to make the tests more uniform in both look-and-feel but also what is tested;
* improve test coverage;
* isolate core functionality from tests to prevent some future core changes affecting the parsers and plugins too much.