# -*- coding: utf-8 -*-
"""An extension of the objectfilter to provide plaso specific options."""

from __future__ import unicode_literals

import calendar
import datetime
import logging
import re

from plaso.formatters import manager as formatters_manager
from plaso.formatters import mediator as formatters_mediator

from plaso.lib import definitions
from plaso.lib import errors
from plaso.lib import objectfilter
from plaso.lib import py2to3
from plaso.lib import timelib

# pylint: disable=missing-type-doc,missing-return-type-doc,missing-return-doc


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


class PlasoValueExpander(objectfilter.AttributeValueExpander):
  """An expander that gives values based on object attribute names."""

  def _GetMessage(self, event_object):
    """Returns a properly formatted message string.

    Args:
      event_object: the event object (instance od EventObject).

    Returns:
      A formatted message string.
    """
    # TODO: move this somewhere where the mediator can be instantiated once.
    formatter_mediator = formatters_mediator.FormatterMediator()

    result = ''
    try:
      result, _ = formatters_manager.FormattersManager.GetMessageStrings(
          formatter_mediator, event_object)
    except KeyError as exception:
      logging.warning(
          'Unable to correctly assemble event with error: {0!s}'.format(
              exception))

    return result

  def _GetSources(self, event_object):
    """Returns properly formatted source strings.

    Args:
      event_object: the event object (instance od EventObject).
    """
    try:
      source_short, source_long = (
          formatters_manager.FormattersManager.GetSourceStrings(event_object))
    except KeyError as exception:
      logging.warning(
          'Unable to correctly assemble event with error: {0!s}'.format(
              exception))

    return source_short, source_long

  def _GetValue(self, obj, attr_name):
    ret = getattr(obj, attr_name, None)

    if ret:
      if isinstance(ret, dict):
        ret = DictObject(ret)

      if attr_name == 'tag':
        return ret.labels

      return ret

    # Check if this is a message request and we have a regular EventObject.
    if attr_name == 'message':
      return self._GetMessage(obj)

    # Check if this is a source_short request.
    if attr_name in ('source', 'source_short'):
      source_short, _ = self._GetSources(obj)
      return source_short

    # Check if this is a source_long request.
    if attr_name in ('source_long', 'sourcetype'):
      _, source_long = self._GetSources(obj)
      return source_long

    return None

  def _GetAttributeName(self, path):
    return path[0].lower()


class PlasoExpression(objectfilter.BasicExpression):
  """A Plaso specific expression."""
  # A simple dictionary used to swap attributes so other names can be used
  # to reference some core attributes (implementation specific).
  swap_source = {
      'date': 'timestamp',
      'datetime': 'timestamp',
      'time': 'timestamp',
      'description_long': 'message',
      'description': 'message',
      'description_short': 'message_short',
  }

  def Compile(self, filter_implementation):
    """Compiles the filter implementation.

    Args:
      filter_implementation: a filter object (instance of objectfilter.TODO).

    Returns:
      A filter operator (instance of TODO).

    Raises:
      ParserError: if an unknown operator is provided.
    """
    self.attribute = self.swap_source.get(self.attribute, self.attribute)
    arguments = [self.attribute]
    op_str = self.operator.lower()
    operator = filter_implementation.OPS.get(op_str, None)

    if not operator:
      raise errors.ParseError('Unknown operator {0:s} provided.'.format(
          self.operator))

    # Plaso specific implementation - if we are comparing a timestamp
    # to a value, we use our specific implementation that compares
    # timestamps in a "human readable" format.
    if self.attribute == 'timestamp':
      args = []
      for argument in self.args:
        args.append(DateCompareObject(argument))
      self.args = args

    for argument in self.args:
      if isinstance(argument, DateCompareObject):
        if 'Less' in str(operator):
          TimeRangeCache.SetUpperTimestamp(argument.data)
        else:
          TimeRangeCache.SetLowerTimestamp(argument.data)
    arguments.extend(self.args)
    expander = filter_implementation.FILTERS['ValueExpander']
    ops = operator(arguments=arguments, value_expander=expander)
    if not self.bool_value:
      if hasattr(ops, 'FlipBool'):
        ops.FlipBool()

    return ops


class PlasoAttributeFilterImplementation(objectfilter.BaseFilterImplementation):
  """Does field name access on the lowercase version of names.

  Useful to only access attributes and properties with Google's python naming
  style.
  """

  FILTERS = {}
  FILTERS.update(objectfilter.BaseFilterImplementation.FILTERS)
  FILTERS.update({'ValueExpander': PlasoValueExpander})
  OPS = objectfilter.OP2FN


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
      data: A string, datetime object or an integer containing the number
            of micro seconds since January 1, 1970, 00:00:00 UTC.

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
    """A simple comparison operation."""
    try:
      x_date = DateCompareObject(x)

      # The following implements a Python3 compatible:
      # cmp(self.data, x_date.data)
      return (self.data > x_date.data) - (self.data < x_date.data)
    except ValueError:
      return False

  def __le__(self, x):
    """Less or equal comparison."""
    return self.data <= x

  def __lt__(self, x):
    """Less comparison"""
    return self.data < x

  def __ge__(self, x):
    """Greater or equal comparison."""
    return self.data >= x

  def __gt__(self, x):
    """Greater comparison."""
    return self.data > x

  def __eq__(self, x):
    """Check if equal."""
    return x == self.data

  def __ne__(self, x):
    """Check if not equal."""
    return x != self.data

  def __str__(self):
    """Return a string representation of the object."""
    return self.text


class BaseParser(objectfilter.Parser):
  """Plaso version of the Parser."""

  expression_cls = PlasoExpression


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
