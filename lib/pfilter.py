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

from plaso.lib import objectfilter
from plaso.lib import lexer
from plaso.lib import pfile

__pychecker__ = 'no-funcdoc'


class PlasoValueExpander(objectfilter.AttributeValueExpander):
  """An expander that gives values based on object attribute names."""

  def _GetValue(self, obj, attr_name):
    ret = getattr(obj, attr_name, None)

    # Check if this is source_short in a protobuf (an int)
    if attr_name == 'source_short' and type(ret) == int:
      ret = obj.DESCRIPTOR.enum_types_by_name[
          'SourceShort'].values_by_number[obj.source_short].name

    if ret:
      return ret

    # Check if this is an attribute inside the EventObject protobuf.
    if hasattr(obj, 'attributes') and hasattr(obj.attributes, 'MergeFrom'):
      attributes = dict((a.key, a.value) for a in obj.attributes)
      return attributes.get(attr_name, None)

  def _GetAttributeName(self, path):
    return path[0].lower()


### PARSER DEFINITION
class PlasoExpression(objectfilter.BasicExpression):

  # A simple dictionary used to swap attributes so other names can be used
  # to reference some core attributes (implementation specific).
  swap_source = {
    'date': 'timestamp',
    'source': 'source_short',
  }

  def Compile(self, filter_implementation):
    self.attribute = self.swap_source.get(self.attribute, self.attribute)
    arguments = [self.attribute]
    op_str = self.operator.lower()
    operator = filter_implementation.OPS.get(op_str, None)

    if not operator:
      raise objectfilter.ParseError(
          "Unknown operator %s provided." % self.operator)

    # Plaso specific implementation - if we are comparing a timestamp
    # to a value, we use our specific implementation that compares
    # timestamps in a "human readable" format.
    if self.attribute == 'timestamp':
      args = []
      for arg in self.args:
        args.append(DateCompareObject(arg))
      self.args = args

    arguments.extend(self.args)
    expander = filter_implementation.FILTERS["ValueExpander"]
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
  FILTERS.update({"ValueExpander": PlasoValueExpander})


### Plaso Specific

class DateCompareObject(object):
  """A specific class created for date comparison.

  This object takes a date representation, whether that is a direct integer
  datetime object or a string presenting the date, and uses that for comparing
  against timestamps stored in microseconds in UTC Epoch (as used by Plaso).

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
    self.text = pfile.GetUnicodeString(data)
    if type(data) in (int, long):
      self.data = data
    elif type(data) == float:
      self.data = long(data)
    elif type(data) in (str, unicode):
      try:
        dt = dateutil.parser.parse(pfile.GetUnicodeString(data))
        utc_dt = pytz.UTC.localize(dt)
        self.data = calendar.timegm(utc_dt.timetuple()) * int(1e6)
        self.data += utc_dt.microsecond
      except ValueError as e:
        raise ValueError("Date string is wrongly formatted (%s) - %s",
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


