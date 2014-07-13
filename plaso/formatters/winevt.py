#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2013 The Plaso Project Authors.
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
"""Formatter for Windows EventLog (EVT) files."""

from plaso.lib import errors
from plaso.formatters import interface


class WinEvtFormatter(interface.ConditionalEventFormatter):
  """Define the formatting for Windows EventLog (EVT) record."""

  DATA_TYPE = 'windows:evt:record'

  FORMAT_STRING_PIECES = [
      u'[{event_identifier} /',
      u'0x{event_identifier:08x}]',
      u'Record Number: {record_number}',
      u'Event Type: {event_type_string}',
      u'Event Category: {event_category}',
      u'Source Name: {source_name}',
      u'Computer Name: {computer_name}',
      u'Strings: {strings}']

  FORMAT_STRING_SHORT_PIECES = [
      u'[0x{event_identifier:08x}]',
      u'Strings: {strings}']

  SOURCE_LONG = 'WinEVT'
  SOURCE_SHORT = 'EVT'

  # Mapping of the numeric event types to a descriptive string.
  _EVENT_TYPES = [u'Error event', u'Warning event', u'Information event',
                  u'Success Audit event', u'Failure Audit event']

  def GetEventTypeString(self, event_type):
    """Retrieves a string representation of the event type.

    Args:
      event_type: The numeric event type.

    Returns:
      An Unicode string containing a description of the event type.
    """
    if event_type >= 0 and event_type < len(self._EVENT_TYPES):
      return self._EVENT_TYPES[event_type]
    return u'Unknown {0:d}'.format(event_type)

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

    # Update event object with the event type string.
    event_object.event_type_string = self.GetEventTypeString(
        event_object.event_type)

    return super(WinEvtFormatter, self).GetMessages(event_object)
