#!/usr/bin/env python
# Copyright 2012 Google Inc.
#
# Originally copied from the GRR project:
# http://code.google.com/p/grr/source/browse/lib/objectfilter.py
# Copied on 11/15/2012
# Minor changes made to make it work in plaso.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""An extension of the objectfilter to provide plaso specific options."""

import binascii
import calendar
import datetime
import dateutil.parser
import logging
import pytz

# TODO: Changes this so it becomes an attribute instead of having backend
# load a front-end library.
from plaso.frontend import presets

from plaso.lib import eventdata
from plaso.lib import objectfilter
from plaso.lib import lexer
from plaso.lib import pfile
from plaso.lib import storage
from plaso.lib import utils

__pychecker__ = 'no-funcdoc'


class PlasoValueExpander(objectfilter.AttributeValueExpander):
  """An expander that gives values based on object attribute names."""

  def _GetMessage(self, obj):
    """Return a properly formatted message string."""
    ret = u''

    try:
      ret, _ = eventdata.EventFormatterManager.GetMessageStrings(obj)
    except KeyError as e:
      logging.warning(u'Unable to correctly assemble event: %s', e)

    return ret

  def _GetValue(self, obj, attr_name):
    ret = getattr(obj, attr_name, None)

    if ret:
      return ret

    # Check if this is a message request and we have a regular EventObject.
    if attr_name == 'message' and not hasattr(obj.attributes, 'MergeForm'):
      return self._GetMessage(obj)

  def _GetAttributeName(self, path):
    return path[0].lower()


class PlasoExpression(objectfilter.BasicExpression):
  """A Plaso specific expression."""
  # A simple dictionary used to swap attributes so other names can be used
  # to reference some core attributes (implementation specific).
  swap_source = {
    'date': 'timestamp',
    'source': 'source_short',
    'description_long': 'message',
    'description': 'message',
    'description_short': 'message_short',
  }

  def Compile(self, filter_implementation):
    self.attribute = self.swap_source.get(self.attribute, self.attribute)
    arguments = [self.attribute]
    op_str = self.operator.lower()
    operator = filter_implementation.OPS.get(op_str, None)

    if not operator:
      raise objectfilter.ParseError(
          'Unknown operator %s provided.' % self.operator)

    # Plaso specific implementation - if we are comparing a timestamp
    # to a value, we use our specific implementation that compares
    # timestamps in a "human readable" format.
    if self.attribute == 'timestamp':
      args = []
      for arg in self.args:
        args.append(DateCompareObject(arg))
      self.args = args

    arguments.extend(self.args)
    expander = filter_implementation.FILTERS['ValueExpander']
    ops = operator(arguments=arguments, value_expander=expander)
    if not self.bool_value:
      if hasattr(ops, 'FlipBool'):
        ops.FlipBool()

    return ops


class ParserList(objectfilter.GenericBinaryOperator):
  """Matches when a parser is inside a predefined list of parsers."""

  def __init__(self, *children, **kwargs):
    """Construct the parser list and retrieve a list of available parsers."""
    super(ParserList, self).__init__(*children, **kwargs)
    self.compiled_list = presets.categories.get(
        self.right_operand, [])

  def Operation(self, x, unused_y):
    """Return a bool depending on the parser list contains the parser."""
    if self.left_operand != 'parser':
      raise objectfilter.MalformedQueryError(
        u'Unable to use keyword "inlist" for other than parser.')

    if x in self.compiled_list:
      return True

    return False


class PlasoAttributeFilterImplementation(objectfilter.BaseFilterImplementation):
  """Does field name access on the lowercase version of names.

  Useful to only access attributes and properties with Google's python naming
  style.
  """

  FILTERS = {}
  FILTERS.update(objectfilter.BaseFilterImplementation.FILTERS)
  FILTERS.update({'ValueExpander': PlasoValueExpander})
  OPS = objectfilter.OP2FN
  OPS.update({'inlist': ParserList,})


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
      data: A string, datetime object or an integer that
      represents the time to compare against. Time should be stored
      as microseconds since UTC in Epoch format.

    """
    self.text = utils.GetUnicodeString(data)
    if type(data) in (int, long):
      self.data = data
    elif type(data) == float:
      self.data = long(data)
    elif type(data) in (str, unicode):
      try:
        dt = dateutil.parser.parse(utils.GetUnicodeString(data))
        utc_dt = pytz.UTC.localize(dt)
        self.data = calendar.timegm(utc_dt.timetuple()) * int(1e6)
        self.data += utc_dt.microsecond
      except ValueError as e:
        raise ValueError('Date string is wrongly formatted (%s) - %s',
                         data, e)
    elif type(data) == datetime.datetime:
      self.data = calendar.timegm(data.timetuple()) * int(1e6)
    elif isinstance(DateCompareObject, data):
      self.data = data.data
    else:
      raise ValueError('Type not supported [%s].' % type(data))

  def __cmp__(self, x):
    """A simple comparison operation."""
    try:
      x_date = DateCompareObject(x)
      return cmp(self.data, x_date.data)
    except ValueError:
      return False

  def __le__(self, x):
    """Less or equal comparison."""
    return self.data <= x

  def __ge__(self, x):
    """Greater or equal comparison."""
    return self.data >= x

  def __eq__(self, x):
    """Check if equal."""
    return x == self.data

  def __ne__(self, x):
    """Check if not equal."""
    return x != self.data

  def __str__(self):
    """Return a string representation of the object."""
    return self.text


class PlasoParser(objectfilter.Parser):
  """Plaso version of the Parser."""

  expression_cls = PlasoExpression


class TrueObject(object):
  """A simple object that always returns true for all comparison.

  This object is used for testing certain conditions inside filter queries.
  By returning true for all comparisons this object can be used to evaluate
  specific portions of a filter query.
  """

  def __init__(self, txt=''):
    """Save the text object so it can be used when comparing text."""
    self.txt = txt

  def __eq__(self, unused_x):
    """Return true for tests of equality."""
    return True

  def __gt__(self, unused_x):
    """Return true for checks for greater."""
    return True

  def __ge__(self, unused_x):
    """Return true for checks for greater or equal."""
    return True

  def __lt__(self, unused_x):
    """Return true for checks of less."""
    return True

  def __le__(self, unused_x):
    """Return true for checks of less or equal."""
    return True

  def __ne__(self, unused_x):
    """Return true for all not equal comparisons."""
    return True

  def __iter__(self):
    """Return a generator so a test for the in keyword can be used."""
    yield self

  def __str__(self):
    """Return a string to make regular expression searches possible.

    Returns:
      A string that containes the original query with some of the matches
      expanded, perhaps several times.
    """
    # Regular expressions in pfilter may include the following escapes:
    #     "\\'\"rnbt\.ws":
    txt = self.txt
    if '\.' in self.txt:
      txt += self.txt.replace('\.', ' _ text _ ')

    if '\b' in self.txt:
      txt += self.txt.replace('\b', ' ')

    if '\s' in self.txt:
      txt += self.txt.replace('\s', ' ')

    return txt


class MockTestFilter(object):
  """A mock test filter object used to test certain portion of test queries.

  The logic behind this object is that a single attribute can be isolated
  for comparison. That is to say all calls to attributes will lead to a TRUE
  response, except those attributes that are specifically stated in the
  constructor. This way it is simple to test for instance whether or not
  to include a parser at all, before actually running the tool. The same applies
  to filtering out certain filenames, etc.
  """

  def __init__(self, query, **kwargs):
    """Constructor, only valid attribute is the parser one."""
    self.attributes = kwargs
    self.txt = query

  def __getattr__(self, attr):
    """Return TrueObject for all requests except for stored attributes."""
    if attr in self.attributes:
      return self.attributes.get(attr, None)

    return TrueObject(self.txt)


def GetMatcher(query):
  """Return a filter match object for a given query."""
  matcher = None
  try:
    parser = PlasoParser(query).Parse()
    matcher = parser.Compile(
        PlasoAttributeFilterImplementation)
  except objectfilter.ParseError as e:
    logging.error('Filter <%s> malformed: %s', query, e)

  return matcher
