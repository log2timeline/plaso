# Style Guide

We primarily follow the [Google Python Style Guide](https://github.com/google/styleguide/blob/gh-pages/pyguide.md).

Various Plaso specific additions/variations are:

#### Indentation

* Indent your code blocks with 2 spaces (not 4 as in the style guide).
* In the case of a hanging indent, use four spaces (according to the style guide).

#### Naming

* Use full English words everywhere. For example, use Event not Evt and Description not Desc.
* Acronyms and initialisms should be preserved, such as HTMLParser and not HtmlParser.
* Method and function names follow the following logic (overriding the Google Python Style Guide):


Type | Public | Internal
---- | ---- | ----
Functions | **CapWords()** | **_CapWords()** (protected) and **__CapWords()** (private)

#### Unused function or method arguments

Prefix unused function or method arguments with `unused_`. 

#### Strings

* Quote strings as ' or """ and not "
  * Quote strings in command line arguments (argparse) as "
* Textual strings should be Unicode strings.
  * Use the [unicode_literals](http://python-future.org/unicode_literals.html) module to make all strings unicode by default.
* Use the format() function instead of the %-style of formatting strings.
  * Use positional or parameter format specifiers with typing e.g. '{0:s}' or '{text:s}' instead of '{0}', '{}' or '{:s}'. If we ever want to have language specific output strings we don't need to change the entire codebase (again). It also makes is easier in determining what type every parameter is expected to be.

#### Exceptions

* When catching exceptions use "as exception:" not some alternative form like "as error:" or "as details:"
* Raise exceptions like this: ```raise MyException('Error message')``` or ```raise MyException```.
* Although Python allows for ```try ... except ... else``` we prefer not to use it.
* Make exception messages as useful and descriptive and possible. For example, if an argument is out of an acceptable range, print the invalid value to speed-up debugging.

#### Return statements

Per [PEP8](https://pep8.org/#programming-recommendations): "Be consistent in return statements. Either all return statements in a function should return an expression, or none of them should. If any return statement returns an expression, any return statements where no value is returned should explicitly state this as return None, and an explicit return statement should be present at the end of the function (if reachable)."

* Use `return None` instead of `return` when your function or method is expected to return a value.
* Do not use `return None` in generators.
* Use `return` in a function or method that does not return a value.

#### Docstrings

* Use English, and avoid abbreviations. Use "for example" or "such as" instead of Latin abbreviations like "e.g.".
* We use "Google Style" docstrings see the examples at [this page](http://sphinxcontrib-napoleon.readthedocs.org/en/latest/example_google.html) as well as the notes below. 

There are still a few legacy docstrings in the codebase, here are some examples you might see. Please don't write new code that looks like this:

```python
def AddAnalysisReport(self, analysis_report):
    """Adds an analysis report.
    
    Args:
      analysis_report: a report.
    """
```
This is missing an important detail, the argument type. Is it a string? Some other sort of object? How about this:

```python
def AddAnalysisReport(self, analysis_report):
    """Adds an analysis report.
    
    Args:
      analysis_report: an analysis report object (instance of AnalysisReport)
    """
```
This is overly verbose, and is hard to parse.

Instead do:

```python
def AddAnalysisReport(self, analysis_report, storage_writer=None):
    """Adds an analysis report.
    
    Args:
      analysis_report (AnalysisReport): a report.
      storage_writer (Optional[StorageWriter]): the storage writer must be open, 
          and cannot be closed. If no storage_writer is provided, a new writer 
          will be created.
    """
```

Make sure your arguments descriptions include:

1. The argument(s) type(s);
2. In case of [standard types](https://docs.python.org/3.3/library/stdtypes.html) a description of their format. Note that we use the Python 3 standard types;
3. Description of the meaning of the argument. In other words how the argument is used by the function (or method). If the description exceeds the line limit, indent the next line with 4 spaces.

The meaning can be left out if the function has only a couple arguments and how the arguments are used is obvious from the description as in the example of `AddAnalysisReport`.

A few other tips:

##### Compound types

If a function deals with a compound type (list, dict), document it like so:
```
Args:
  constraints (dict[str, Filter]): constraint name mapped to the filter that implements the constraint.

Returns:
  list[BaseParser]: all relevant parsers.
```

##### Multiple acceptable types

If you need to specify multiple types, use a pipe to separate them. For example:

```
Args:
  path (str|Path): path to tag file.
```

##### Multiple return types

Python simulates multiple arguments being returned by implicitly returning a tuple. Document like so:

```
...
Returns:
  tuple: containing:
     
    str: parser name
    BaseParser: next parser parser
""""
return name, parser
```

##### Special arguments

Arguments like `cls`, `self`, `*args`, `**kwargs` are not expected to be explicitly named in the `Args:` section.

```
  def CopyToIsoFormat(cls, timestamp, timezone=pytz.UTC, raise_error=False):
    """Copies the timestamp to an ISO 8601 formatted string.

    Args:
      timestamp (int): number of micro seconds since January 1, 1970, 00:00:00 UTC.
      timezone (Optional[pytz.timezone]): the result string will be expressed in this timezone.
      raise_error (Optional[bool]): False if OverflowError should be caught when timestamp is out of bounds.

    Returns:
      str: ISO 8601 formatted date and time.
    """
```

##### Class attributes

In addition to the [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html#Comments) please sort class attribute alphabetically by name.

```
class SampleClass(object):
  """Summary of class here.

  Attributes:
      eggs (int): number of eggs we have laid.
      likes_spam (bool): whether we like SPAM or not.
  """
```

##### Constructor

In addition to the [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html#Comments) please sort instance attribute alphabetically by name inside the constructor (`__init__`).

```
class SampleClass(object):
  """Summary of class here."""

  def __init__(self):
    """Summary of method here."""
    self.__private_attribute = None
    self._another_protected_attribute = None
    self._protected_attribute = None
    self.another_public_attribute = None
    self.public_attribute = None
```

##### Keyword arguments

In addition to the [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html#Comments) please sort keyword arguments alphabetically by name.

```
def SampleFunction(alternate=None, keyword=None):
  """Summary of function here.

  Args:
      alternate (Optional[str]): alternate keyword argument.
      keyword (Optional[str]): keyword argument.
  """
```

**Make sure to call keyword argument with their keyword prefix.**

```
SampleFunction(keyword='THEKEY')
```

#### Unit tests

* use ```self.assertEqual``` instead of ```self.assertEquals```, same applies to ```self.assertNotEquals```
* use ```self.assertIsNone(variable)``` instead of ```self.assertEqual(variable, None)```, same applies to ```self.assertNotEqual```

#### Other

* Avoid the use of global variables.
* Use class methods in preference to static methods
  * Use "cls" as the name of the class variable in preference to "klass"
* Use textual pylint overrides e.g. "# pylint: disable=no-self-argument" instead of "# pylint: disable=E0213". For a list of overrides see: http://docs.pylint.org/features.html
* Tags for events need to be strings containing only alphanumeric characters or underscores. One of the reasons for this is better compatibility with other tool, such as [TimeSketch](https://github.com/google/timesketch).
* All new Plaso code needs to be compatible with both Python 3.4+ and Python 2.7+. Plaso's [Python 3 Guide](Python-3-Guide) has some more detail about compatibility issues, and the pylint configuration will also flag some issues.

## Source files

At the start your source files define the encoding, which should be UTF-8, e.g.:
```
# -*- coding: utf-8 -*-
```
Also see: [PEP 0263](https://www.python.org/dev/peps/pep-0263/)

## Linting

Plaso uses pylint 1.7.x to enforce some additional best practices to keep the source code more readable. These are:

* Limit the maximum number of arguments for function or method to 10

## Tests

* Use as much as possible the test functions available in the local test_lib.py instead of writing your own test functions. If you think a test function is missing please add it, or mail the developer list to see if you can get someone else to do it.
* Use `self.CheckTimestamp` for testing timestamp values.

Common test code should be stored in "test library" files, e.g. the parser test library:

    tests/parsers/test_lib.py

We do this for various reasons:

* to remove code duplication in "boiler plate" test code;
* to make the tests more uniform in both look-and-feel but also what is tested;
* improve test coverage;
* isolate core functionality from tests to prevent some future core changes affecting the parsers and plugins too much.

## Rationale

To keep the codebase maintainable and readable, all code is developed using a similar coding style. It ensures:

* the code is easy to maintain and understand. As a developer you'll sometimes find yourself thinking [WTF](http://en.wikipedia.org/wiki/WTF), what is the code supposed to do here. It's really important that you're able to come back to code 5 months later and still quickly understand what it's supposed to be doing. Also for other people that want to contribute it is necessary for them to quickly understand the code. That said, quick-and-dirty solutions might work when you're working on a case, but we'll ban them from the codebase.
* that every developer knows to (largely) expect the same coding style.

We've noticed that some people find the process of having a style guide and a code review process intimidating. We've also noticed that once people get used to it and have gone through the process a few times, they are generally thankful and learn quite a lot during the process, so bear with us.

Having a unified style makes it much easier to maintain the codebase. That means that every developer should be able to make changes in any file in the codebase without worrying about different code styles. 

And if things are unclear, don't hesitate to ask. The developer mailing list is: log2timeline-dev@googlegroups.com
