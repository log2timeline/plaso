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
"""This file contains the event formatters manager class."""

import logging

from plaso.formatters import interface
from plaso.lib import utils


class DefaultFormatter(interface.EventFormatter):
  """Default formatter for events that do not have any defined formatter."""

  DATA_TYPE = u'event'
  FORMAT_STRING = u'<WARNING DEFAULT FORMATTER> Attributes: {attribute_driven}'
  FORMAT_STRING_SHORT = u'<DEFAULT> {attribute_driven}'

  def GetMessages(self, event_object):
    """Return a list of messages extracted from an event object."""
    text_pieces = []

    for key, value in event_object.GetValues().items():
      if key in utils.RESERVED_VARIABLES:
        continue
      text_pieces.append(u'{0:s}: {1!s}'.format(key, value))

    event_object.attribute_driven = u' '.join(text_pieces)
    # Due to the way the default formatter behaves it requires the data_type
    # to be set as 'event', otherwise it will complain and deny processing
    # the event.
    # TODO: Change this behavior and allow the default formatter to accept
    # arbitrary data types (as it should).
    old_data_type = getattr(event_object, 'data_type', None)
    event_object.data_type = self.DATA_TYPE
    msg, msg_short = super(DefaultFormatter, self).GetMessages(event_object)
    event_object.data_type = old_data_type
    return msg, msg_short


class EventFormatterManager(object):
  """Class to manage the event formatters."""

  @classmethod
  def GetFormatter(cls, event_object):
    """Retrieves the formatter for a specific event object.

       This function builds a map of data types and the corresponding event
       formatters. At the moment this map is only build once.

    Args:
      event_object: The event object (EventObject) which is used to identify
                    the formatter.

    Returns:
      The corresponding formatter (EventFormatter) if available or None.

    Raises:
      RuntimeError if a duplicate event formatter is found while building
      the map of event formatters.
    """
    if not hasattr(cls, 'event_formatters'):
      cls.event_formatters = {}
      cls.default_formatter = DefaultFormatter()
      for cls_formatter in interface.EventFormatter.classes:
        try:
          formatter = interface.EventFormatter.classes[cls_formatter]()

          # Raise on duplicate formatters.
          if formatter.DATA_TYPE in cls.event_formatters:
            raise RuntimeError((
                u'event formatter for data type: {0:s} defined in: {1:s} and '
                u'{2:s}.').format(
                    formatter.DATA_TYPE, cls_formatter,
                    cls.event_formatters[
                        formatter.DATA_TYPE].__class__.__name__))
          cls.event_formatters[formatter.DATA_TYPE] = formatter
        except RuntimeError as exeception:
          # Ignore broken formatters.
          logging.warning(u'{0:s}'.format(exeception))

      cls.event_formatters.setdefault(None)

    if event_object.data_type in cls.event_formatters:
      return cls.event_formatters[event_object.data_type]
    else:
      logging.warning(
          u'Using default formatter for data type: {0:s}'.format(
              event_object.data_type))
      return cls.default_formatter

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

  @classmethod
  def GetSourceStrings(cls, event_object):
    """Retrieves the formatted source long and short strings for an event.

    Args:
      event_object: The event object (EventObject) which is used to identify
                    the formatter.

    Returns:
      A list that contains the source_short and source_long version of the
      event.
    """
    # TODO: change this to return the long variant first so it is consistent
    # with GetMessageStrings.
    formatter = cls.GetFormatter(event_object)
    if not formatter:
      return u'', u''
    return formatter.GetSources(event_object)
