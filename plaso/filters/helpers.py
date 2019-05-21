# -*- coding: utf-8 -*-
"""The event filter expression parser helper functions and classes."""

from __future__ import unicode_literals

import calendar
import codecs
import datetime
import re

from plaso.lib import definitions
from plaso.lib import errors
from plaso.lib import py2to3
from plaso.lib import timelib


def GetUnicodeString(value):
  """Attempts to convert the argument to a Unicode string.

  Args:
    value (list|int|bytes|str): value to convert.

  Returns:
    str: string representation of the argument.
  """
  if isinstance(value, list):
    value = [GetUnicodeString(item) for item in value]
    return ''.join(value)

  if isinstance(value, py2to3.INTEGER_TYPES):
    value = '{0:d}'.format(value)

  if not isinstance(value, py2to3.UNICODE_TYPE):
    return codecs.decode(value, 'utf8', 'ignore')
  return value


class DateCompareObject(object):
  """A specific class created for date comparison.

  This object takes a date representation, whether that is a direct integer
  datetime object or a string presenting the date, and uses that for comparing
  against timestamps stored in microseconds in in microseconds since
  Jan 1, 1970 00:00:00 UTC.

  This makes it possible to use regular comparison operators for date,
  irrelevant of the format the date comes in, since plaso stores all timestamps
  in the same format, which is an integer/long, it is a simple manner of
  changing the input into the same format (int) and compare that.
  """

  def __init__(self, data):
    """Take a date object and use that for comparison.

    Args:
      data (int|str|datetime.datetime): A date and time string, datetime object
          or an integer containing the number of micro seconds since
          January 1, 1970, 00:00:00 UTC.

    Raises:
      ValueError: if the date string is invalid.
    """
    if isinstance(data, py2to3.INTEGER_TYPES):
      self.data = data
      self.text = '{0:d}'.format(data)

    elif isinstance(data, float):
      self.data = py2to3.LONG_TYPE(data)
      self.text = '{0:f}'.format(data)

    elif isinstance(data, py2to3.STRING_TYPES):
      if isinstance(data, py2to3.BYTES_TYPE):
        self.text = data.decode('utf-8', errors='ignore')
      else:
        self.text = data

      try:
        self.data = timelib.Timestamp.FromTimeString(self.text)
      except (ValueError, errors.TimestampError):
        raise ValueError('Wrongly formatted date string: {0:s}'.format(
            self.text))

    elif isinstance(data, datetime.datetime):
      posix_time = int(calendar.timegm(data.utctimetuple()))
      self.data = (
          posix_time * definitions.MICROSECONDS_PER_SECOND) + data.microsecond
      self.text = '{0!s}'.format(data)

    elif isinstance(data, DateCompareObject):
      self.data = data.data
      self.text = '{0!s}'.format(data)

    else:
      raise ValueError('Unsupported type: {0:s}.'.format(type(data)))

  def __cmp__(self, x):
    """A simple comparison operation.

    Args:
      x (object): object to compare against.

    Returns:
      bool: True if self is equal to the object.
    """
    try:
      x_date = DateCompareObject(x)

      # The following implements a Python3 compatible:
      # cmp(self.data, x_date.data)
      return (self.data > x_date.data) - (self.data < x_date.data)
    except ValueError:
      return False

  def __le__(self, x):
    """Less or equal comparison.

    Args:
      x (object): object to compare against.

    Returns:
      bool: True if self is less than or equal to the object.
    """
    return self.data <= x

  def __lt__(self, x):
    """Less comparison.

    Args:
      x (object): object to compare against.

    Returns:
      bool: True if self is less than the object.
    """
    return self.data < x

  def __ge__(self, x):
    """Greater or equal comparison.

    Args:
      x (object): object to compare against.

    Returns:
      bool: True if self is greater than or equal to the object.
    """
    return self.data >= x

  def __gt__(self, x):
    """Greater comparison.

    Args:
      x (object): object to compare against.

    Returns:
      bool: True if self is greater than the object.
    """
    return self.data > x

  def __eq__(self, x):
    """Check if equal.

    Args:
      x (object): object to compare against.

    Returns:
      bool: True if self is equal to the object.
    """
    return x == self.data

  def __ne__(self, x):
    """Check if not equal.

    Args:
      x (object): object to compare against.

    Returns:
      bool: True if self is not equal to the object.
    """
    return x != self.data

  def __str__(self):
    """Retrieves a string representation of the object.

    Returns:
      str: string representation of the object.
    """
    return self.text


class DictObject(object):
  # There's a backslash in the class docstring, so as not to confuse Sphinx.
  # pylint: disable=anomalous-backslash-in-string
  """A simple object representing a dict object.

  To filter against an object that is stored as a dictionary the dict
  is converted into a simple object. Since keys can contain spaces
  and/or other symbols they are stripped out to make filtering work
  like it is another object.

  Example dict::

    {'A value': 234,
     'this (my) key_': 'value',
     'random': True,
    }

  This object would then allow access to object.thismykey that would access
  the key 'this (my) key\_' inside the dict.
  """

  _STRIP_KEY_RE = re.compile(r'[ (){}+_=\-<>[\]]')

  def __init__(self, dict_object):
    """Initialize the object and build a secondary dict."""
    # TODO: Move some of this code to a more value typed system.
    self._dict_object = dict_object

    self._dict_translated = {}
    for key, value in dict_object.items():
      key = self._StripKey(key)
      self._dict_translated[key] = value

  def _StripKey(self, key):
    """Strips a key form symbols to use within a dictionary.

    Args:
      key (str): key to strip.

    Returns:
      str: stripped key.
    """
    return self._STRIP_KEY_RE.sub('', key.lower())

  def __getattr__(self, attr):
    """Return back entries from the dictionary."""
    if attr in self._dict_object:
      return self._dict_object.get(attr)

    # Special case of getting all the key/value pairs.
    if attr == '__all__':
      ret = []
      for key, value in self._dict_translated.items():
        ret.append('{}:{}'.format(key, value))
      return ' '.join(ret)

    test = self._StripKey(attr)
    if test in self._dict_translated:
      return self._dict_translated.get(test)

    return None


class TimeRangeCache(object):
  """A class that stores time ranges from filters."""

  MAX_INT64 = 2**64-1

  @classmethod
  def SetLowerTimestamp(cls, timestamp):
    """Sets the lower bound timestamp."""
    if not hasattr(cls, '_lower'):
      cls._lower = timestamp
      return

    if timestamp < cls._lower:
      cls._lower = timestamp

  @classmethod
  def SetUpperTimestamp(cls, timestamp):
    """Sets the upper bound timestamp."""
    if not hasattr(cls, '_upper'):
      cls._upper = timestamp
      return

    if timestamp > cls._upper:
      cls._upper = timestamp

  @classmethod
  def GetTimeRange(cls):
    """Return the first and last timestamp of filter range."""
    first = getattr(cls, '_lower', 0)
    last = getattr(cls, '_upper', cls.MAX_INT64)

    if first < last:
      return first, last

    return last, first
