## Python 3 Guide

plaso is Python 3 compatible, but not all of its dependencies are.

This page contains information about which Python language features to use to help plaso to stay Python 2.7 compatible and stay Python 3.4 and later compatible.

### Python

See: https://docs.python.org/3/howto/pyporting.html

* exception.message no longer accessible
* dict.sort() no longer works
* more picky about string conversion in format e.g. printing a set as {0:s}
* open() must be passed binary mode
* next() replaced by `__next__()`

* dict iter functions: https://docs.python.org/3.1/whatsnew/3.0.html#views-and-iterators-instead-of-lists
  * What about plistlib._InternalDict.iteritems() ?

```
dict.iteritems() => iter(dict.items())
```

#### Integers

* The result of `\` is a floating point, use divmod() instead (or `\\`)
* `long()` and `1L` no longer work

#### Strings

* % format notation on longer supported, replaced by format and {} notation
* explicitly mark byte strings (b'')
* str is Unicode not bytes so str.decode fails
* Use `__unicode__` in preference of `__str__`
* unicode() is no longer supported
* basestring is no longer supported

Make the default string type Unicode.
```
from __future__ import unicode_literals
```

#### print

In Python 3 print is a function:
```
print "Test" => print("Test")
```

For compatibility with Python 2, and to stop pylint complaining, add the following import:
```
from __future__ import print_function
```

#### StringIO.StringIO

StringIO.StringIO is replaced by io.StringIO and io.BytesIO

#### urllib2

From: https://docs.python.org/2/library/urllib2.html
```
The urllib2 module has been split across several modules in Python 3 named urllib.request and urllib.error.
```

```
if sys.version_info[0] < 3:
  import urllib2 as urllib_error
  from urllib2 import urlopen
else:
  import urllib.error as urllib_error
  from urllib.request import urlopen
```

#### xrange()

xrange() is no longer supported by Python 3 use range() instead:
```
xrange(10) => range(0, 10)
```

#### map()
```
TypeError: 'map' object is not subscriptable
```

E.g.
```
map(int, [1])[0]
```

In Python 3 `map()` returns a `map` where in Python 2 this was a `list` e.g.
```
type(map(int, [1]))
```

A solution is to wrap `map` in a `list`.

Other similar errors are:
```
TypeError: unorderable types: map() < map()
```

#### filter

In Python 3 `filter()` returns a `filter` where in Python 2 this was a `list` e.g.
```
type(filter(None, []))
```

A solution is to wrap `filter` in a `list`.

#### To do

```
from __future__ import absolute_import
```

```
from __future__ import division
```

Octal integers are written in a different form e.g. instead of 0666 now 0o666

### C extensions

See: http://python3porting.com/cextensions.html
