#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2014 The Plaso Project Authors.
# Please see the AUTHORS file for details on individual authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""This file contains the event formatters interface classes."""

import re

from plaso.lib import errors
from plaso.lib import registry


class EventFormatter(object):
  """Base class to format event type specific data using a format string.

     Define the (long) format string and the short format string by defining
     FORMAT_STRING and FORMAT_STRING_SHORT. The syntax of the format strings
     is similar to that of format() where the place holder for a certain
     event object attribute is defined as {attribute_name}.
  """
  __metaclass__ = registry.MetaclassRegistry
  __abstract = True

  # The data type is a unique identifier for the event data. The current
  # approach is to define it as human readable string in the format
  # root:branch: ... :leaf, e.g. a page visited entry inside a Chrome History
  # database is defined as: chrome:history:page_visited.
  DATA_TYPE = u'internal'

  # The format string.
  FORMAT_STRING = u''
  FORMAT_STRING_SHORT = u''

  # The source short and long strings.
  SOURCE_SHORT = u'LOG'
  SOURCE_LONG = u''

  def __init__(self):
    """Set up the formatter and determine if this is the right formatter."""
    # Forcing the format string to be unicode to make sure we don't
    # try to format it as an ASCII string.
    self.format_string = unicode(self.FORMAT_STRING)
    self.format_string_short = unicode(self.FORMAT_STRING_SHORT)
    self.source_string = unicode(self.SOURCE_LONG)
    self.source_string_short = unicode(self.SOURCE_SHORT)

  def GetMessages(self, event_object):
    """Return a list of messages extracted from an event object.

    The l2t_csv and other formats are dependent on a message field,
    referred to as description_long and description_short in l2t_csv.

    Plaso does not store this field explicitly, it only contains a format
    string and the appropriate attributes.

    This method takes the format string and converts that back into a
    formatted string that can be used for display.

    Args:
      event_object: The event object (EventObject) containing the event
                    specific data.

    Returns:
      A list that contains both the longer and shorter version of the message
      string.

    Raises:
      WrongFormatter: if the event object cannot be formatted by the formatter.
    """
    if self.DATA_TYPE != event_object.data_type:
      raise errors.WrongFormatter(u'Unsupported data type: {0:s}.'.format(
          event_object.data_type))

    event_values = event_object.GetValues()

    try:
      msg = self.format_string.format(**event_values)
    except KeyError as exception:
      msgs = []
      msgs.append(u'Format error: [{0:s}] for: <{1:s}>'.format(
          exception, self.format_string))
      for attr, value in event_object.GetValues().iteritems():
        msgs.append(u'{0}: {1}'.format(attr, value))

      msg = u' '.join(msgs)

    # Strip carriage return and linefeed form the message strings.
    # Using replace function here because it is faster
    # than re.sub() or string.strip().
    msg = msg.replace('\r', u'').replace('\n', u'')

    if not self.format_string_short:
      msg_short = msg
    else:
      try:
        msg_short = self.format_string_short.format(**event_values)
        # Using replace function here because it is faster
        # than re.sub() or string.strip().
        msg_short = msg_short.replace('\r', u'').replace('\n', u'')
      except KeyError:
        msg_short = u'Unable to format short message string: {0:s}'.format(
            self.format_string_short)

    # Truncate the short message string if necessary.
    if len(msg_short) > 80:
      msg_short = u'{0:s}...'.format(msg_short[0:77])

    return msg, msg_short

  def GetSources(self, event_object):
    """Return a list containing source short and long."""
    if self.DATA_TYPE != event_object.data_type:
      raise errors.WrongFormatter('Unsupported data type: {0:s}.'.format(
          event_object.data_type))

    return self.source_string_short, self.source_string


class ConditionalEventFormatter(EventFormatter):
  """Base class to conditionally format event data using format string pieces.

     Define the (long) format string and the short format string by defining
     FORMAT_STRING_PIECES and FORMAT_STRING_SHORT_PIECES. The syntax of the
     format strings pieces is similar to of the event formatter
     (EventFormatter). Every format string piece should contain a single
     attribute name or none.

     FORMAT_STRING_SEPARATOR is used to control the string which the separate
     string pieces should be joined. It contains a space by default.
  """
  __abstract = True

  # The format string pieces.
  FORMAT_STRING_PIECES = [u'']
  FORMAT_STRING_SHORT_PIECES = [u'']

  # The separator used to join the string pieces.
  FORMAT_STRING_SEPARATOR = u' '

  def __init__(self):
    """Initializes the conditional formatter.

       A map is build of the string pieces and their corresponding attribute
       name to optimize conditional string formatting.

    Raises:
      RuntimeError: when an invalid format string piece is encountered.
    """
    super(ConditionalEventFormatter, self).__init__()

    # The format string can be defined as:
    # {name}, {name:format}, {name!conversion}, {name!conversion:format}
    regexp = re.compile('{[a-z][a-zA-Z0-9_]*[!]?[^:}]*[:]?[^}]*}')
    regexp_name = re.compile('[a-z][a-zA-Z0-9_]*')

    # The format string pieces map is a list containing the attribute name
    # per format string piece. E.g. ["Description: {description}"] would be
    # mapped to: [0] = "description". If the string piece does not contain
    # an attribute name it is treated as text that does not needs formatting.
    self._format_string_pieces_map = []
    for format_string_piece in self.FORMAT_STRING_PIECES:
      result = regexp.findall(format_string_piece)
      if not result:
        # The text format string piece is stored as an empty map entry to
        # keep the index in the map equal to the format string pieces.
        self._format_string_pieces_map.append('')
      elif len(result) == 1:
        # Extract the attribute name.
        attribute_name = regexp_name.findall(result[0])[0]
        self._format_string_pieces_map.append(attribute_name)
      else:
        raise RuntimeError((
            u'Invalid format string piece: [{0:s}] contains more than 1 '
            u'attribute name.').format(format_string_piece))

    self._format_string_short_pieces_map = []
    for format_string_piece in self.FORMAT_STRING_SHORT_PIECES:
      result = regexp.findall(format_string_piece)
      if not result:
        # The text format string piece is stored as an empty map entry to
        # keep the index in the map equal to the format string pieces.
        self._format_string_short_pieces_map.append('')
      elif len(result) == 1:
        # Extract the attribute name.
        attribute_name = regexp_name.findall(result[0])[0]
        self._format_string_short_pieces_map.append(attribute_name)
      else:
        raise RuntimeError((
            u'Invalid short format string piece: [{0:s}] contains more '
            u'than 1 attribute name.').format(format_string_piece))

  def GetMessages(self, event_object):
    """Returns a list of messages extracted from an event object.

    Args:
      event_object: The event object (EventObject) containing the event
                    specific data.

    Returns:
      A list that contains both the longer and shorter version of the message
      string.
    """
    if self.DATA_TYPE != event_object.data_type:
      raise errors.WrongFormatter(u'Unsupported data type: {0:s}.'.format(
          event_object.data_type))

    # Using getattr here to make sure the attribute is not set to None.
    # if A.b = None, hasattr(A, b) is True but getattr(A, b, None) is False.
    string_pieces = []
    for map_index, attribute_name in enumerate(self._format_string_pieces_map):
      if not attribute_name or hasattr(event_object, attribute_name):
        if attribute_name:
          attribute = getattr(event_object, attribute_name, None)
          # If an attribute is an int, yet has zero value we want to include
          # that in the format string, since that is still potentially valid
          # information. Otherwise we would like to skip it.
          if type(attribute) not in (bool, int, long, float) and not attribute:
            continue
        string_pieces.append(self.FORMAT_STRING_PIECES[map_index])
    self.format_string = unicode(
        self.FORMAT_STRING_SEPARATOR.join(string_pieces))

    string_pieces = []
    for map_index, attribute_name in enumerate(
        self._format_string_short_pieces_map):
      if not attribute_name or getattr(event_object, attribute_name, None):
        string_pieces.append(self.FORMAT_STRING_SHORT_PIECES[map_index])
    self.format_string_short = unicode(
        self.FORMAT_STRING_SEPARATOR.join(string_pieces))

    return super(ConditionalEventFormatter, self).GetMessages(event_object)
