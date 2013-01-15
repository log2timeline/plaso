#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2012 Google Inc. All Rights Reserved.
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
"""A place to store information about events, such as format strings, etc."""

import re

from plaso.lib import errors
from plaso.lib import registry


class EventFormatterManager(object):
  """Class to manage the event formatters."""

  __pychecker__ = 'unusednames=cls'
  @classmethod
  def GetFormatterIdentifier(cls, event_object):
    """Retrieves the formatter identifier fo the event object.

    Args:
      event_object: The event object (EventObject).

    Returns:
      A Unicode string containing the formatter identifier.
    """
    # TODO: this implementation will break if multiple event data object
    # from the same parser with the same timestamp description are used.
    # There is also no need to keep this parser specific.
    # after refactoring change this to a "source_short:data_type"
    return u'%s:%s:%s' % (
        getattr(event_object, 'parser', 'UNKNOWN'),
        getattr(event_object, 'source_long', 'NO SOURCE'),
        getattr(event_object, 'timestamp_desc', 'NO TIMEDESC'))

  __pychecker__ = 'unusednames=cls'
  @classmethod
  def GetFormatter(cls, event_object):
    """Retrieves the formatter for a specific event object.

    Args:
      event_object: The event object (EventObject) which is used to identify
                    the formatter.

    Returns:
      The corresponding formatter (EventFormatter) if available or None.
    """
    # TODO: this should be changed into a dict lookup based on the id.
    for cl in EventFormatter.classes:
      try:
        formatter = EventFormatter.classes[cl](event_object)
        return formatter
      except errors.WrongFormatter:
        pass

  @classmethod
  def GetMessageStrings(cls, event_object):
    """Retrieves the formatted message strings for a specific event object.

    Args:
      event_object: The event object (EventObject) which is used to identify
                    the formatter.

    Returns:
      A list that contains both the longer and shorter version of the message
      string.
    """
    formatter = cls.GetFormatter(event_object)
    if not formatter:
      return u'', u''
    return formatter.GetMessages(event_object)


class EventFormatter(object):
  """Base class to format event type specific data using a format string."""

  __metaclass__ = registry.MetaclassRegistry
  __abstract = True

  # The indentifier for the formatter (a regular expression)
  ID_RE = re.compile('None', re.DOTALL)

  # The format string.
  FORMAT_STRING = u''
  FORMAT_STRING_SHORT = u''

  def __init__(self, event_object):
    """Set up the formatter and determine if this is the right formatter."""
    # TODO: remove this once the EventFormatterManager can do a dict based
    # lookup.
    signature = EventFormatterManager.GetFormatterIdentifier(event_object)
    if not self.ID_RE.match(signature):
      raise errors.WrongFormatter('Required formatter: %s.' % signature)

    self.format_string = self.FORMAT_STRING
    self.format_string_short = self.FORMAT_STRING_SHORT

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
    signature = EventFormatterManager.GetFormatterIdentifier(event_object)

    if not self.ID_RE.match(signature):
      raise errors.WrongFormatter('Required formatter: %s.' % signature)

    # TODO: refactor.
    base_attributes = {}
    base_attributes.update(event_object.attributes)

    extra_attributes = {}
    extra_attributes.update(event_object.attributes)

    try:
      msg = self.format_string.format(**extra_attributes)
    except KeyError as e:
      msgs = []
      msgs.append(u'Error in format string [%s]' % e)
      msgs.append(u'<%s>' % self.format_string)
      for attr, value in base_attributes.items():
        msgs.append(u'{0}: {1}'.format(attr, value))

      msg = u' '.join(msgs)

    # Adjust the message string.
    msg = msg.replace('\r', '').replace('\n', '')

    if self.format_string_short:
      try:
        msg_short = self.format_string_short.format(
            **extra_attributes).replace('\r', '').replace('\n', '')
      except KeyError:
        msg_short = (
            u'Unable to format string: %s') % self.format_string_short
    else:
      if len(msg) > 80:
        msg_short = u'%s...' % msg[0:77]
      else:
        msg_short = msg

    return msg, msg_short


class ConditionalEventFormatter(object):
  """Base class to conditionally format event data."""
  __abstract = True

  FORMAT_STRING_PIECES = []


class TextFormatter(EventFormatter):
  """Base class to format text-based event data."""
  __abstract = True

  FORMAT_STRING = u'{body}'


class RegistryFormatter(EventFormatter):
  """A simple implementation of a text based formatter."""
  __abstract = True

  FORMAT_STRING = u'[{keyname}] {text}'
  FORMAT_STRING_ALTERNATIVE = u'{text}'
