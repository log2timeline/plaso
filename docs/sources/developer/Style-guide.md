# Style Guide

Plaso follows the [log2timeline style guide](https://github.com/log2timeline/l2tdocs/blob/main/process/Style-guide.md).

## Plaso specific style points

### Event data attribute containers

#### Data types

Every event data attribute container defines a data type (DATA_TYPE).

Conventions for the data type names are:

1) If the data type is operating system (or operating system convension such as
POSIX) specific start with the name of operating system or convention.
Currently supported prefixes:

* android
* chromeos
* ios
* linux
* macos
* windows

Otherwise skip the operating system prefix.

2) Next is the name of the application, sub system or data format for example
'chrome', 'windows:registry' or 'windows:evtx'.

TODO: describe which one is preferred and why.

3) What follows are application, sub system or data format specific type
information for example 'windows:evtx:record'.

#### Value types

Values stored in an event data attribute container must be of certain types
otherwise event filtering or output formatting can break. Supported Python types
are:

* bool (also see note below)
* int
* str

A list, of the types previously mentioned types, are supported. **Do not use
dict or binary strings.**

Use a bool sparsely. For now it is preferred to preserve the original type.
For example if -1 represents False and 0 True, store the value as an integer
not as a bool. The message formatter can represent the numeric value as a
human readable string.

### Tests

* Use  the test functions available in the local test_lib.py as much as possible
 nstead of writing your own test functions. If you think a test function is
 missing please add it, or mail the developer list to see if you can get someone
 else to do it.
* Use `self.CheckTimestamp` for testing timestamp values.

Common test code should be stored in "test library" files, for example. the parser test
library is `tests/parsers/test_lib.py`.

We do this for a few reasons:

* to remove code duplication in "boiler plate" test code;
* to make the tests more uniform in both look-and-feel but also what is tested;
* improve test coverage;
* isolate core functionality from tests to prevent some future core changes
affecting the parsers and plugins too much.
