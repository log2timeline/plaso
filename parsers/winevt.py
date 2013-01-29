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
"""Parser for Windows EventLog (EVT) files."""
import pyevt

from plaso.lib import errors
from plaso.lib import event
from plaso.lib import eventdata
from plaso.lib import parser


class WinEvtRecordEventContainer(event.EventContainer):
  """Convenience class for a Windows EventLog (EVT) record event container."""
  def __init__(self, evt_record, recovered=False):
    """Initializes the event container.

    Args:
      evt_record: The EVT record (pyevt.record).
      recovered: Boolean value to indicate the record was recovered, False
                 by default.
    """
    super(WinEvtRecordEventContainer, self).__init__()
    self.data_type = 'windows:evt:record'

    # TODO: refactor to formatter.
    self.source_long = 'WinEvtParser'
    self.source_short = 'EVT'

    self.recovered = recovered
    self.offset = evt_record.offset
    self.record_number = evt_record.identifier
    self.event_identifier = evt_record.event_identifier
    self.event_type = evt_record.event_type
    self.event_category = evt_record.event_category
    self.source_name = evt_record.source_name
    # Computer name is the value stored in the event record and does not
    # necessarily corresponds with the actual hostname.
    self.computer_name = evt_record.computer_name
    self.user_sid = evt_record.user_security_identifier

    self.strings = list(evt_record.strings)


class WinEvtParser(parser.PlasoParser):
  """Parses Windows EventLog (EVT) files."""
  NAME = 'WinEvt'
  PARSER_TYPE = 'EVT'

  def _ParseRecord(self, evt_record, recovered=False):
    """Extract data from a Windows EventLog (EVT) record.

       Every record is stored in an event container with 2 sub event objects
       one for each timestamp.

    Args:
      evt_record: An event record (pyevt.record).
      recovered: Boolean value to indicate the record was recovered, False
                 by default.

    Returns:
      An event container (WinEvtRecordEventContainer) that contains the parsed
      data.
    """
    event_container = WinEvtRecordEventContainer(evt_record, recovered)

    event_container.Append(event.PosixTimeEvent(
        evt_record.get_creation_time_as_integer(),
        eventdata.EventTimestamp.CREATION_TIME,
        event_container.data_type))

    event_container.Append(event.PosixTimeEvent(
        evt_record.get_written_time_as_integer(),
        eventdata.EventTimestamp.WRITTEN_TIME,
        event_container.data_type))

    return event_container

  def Parse(self, file_object):
    """Extract data from a Windows EventLog (EVT) file.

       A separate event container is returned for every record to limit
       memory consumption.

    Args:
      file_object: A file-like object to read data from.

    Yields:
      An event container (EventContainer) that contains the parsed data.
    """
    evt_file = pyevt.file()
    evt_file.set_ascii_codepage(getattr(self._pre_obj, 'codepage', 'cp1252'))

    try:
      evt_file.open_file_object(file_object)
    except IOError as exception:
      raise errors.UnableToParseFile("[%s] unable to parse file %s: %s" % (
          self.NAME, file_object.name, exception))

    for evt_record in evt_file.records:
      yield self._ParseRecord(evt_record)

    for evt_record in evt_file.recovered_records:
      yield self._ParseRecord(evt_record, recovered=True)


class WinEvtFormatter(eventdata.ConditionalEventFormatter):
  """Define the formatting for Windows EventLog (EVT) record."""
  DATA_TYPE = 'windows:evt:record'

  FORMAT_STRING_PIECES = [
      u'[0x{event_identifier:08x}]',
      u'Record Number: {record_number}',
      u'Event Type: {event_type_string}',
      u'Event Category: {event_category}',
      u'Source Name: {source_name}',
      u'Computer Name: {computer_name}',
      u'User SID: {user_sid}',
      u'Strings: {strings}']

  FORMAT_STRING_SHORT_PIECES = [
      u'[{event_identifier}]',
      u'Strings: {strings}']

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
    # Update event object with the event type string.
    event_object.event_type_string = self.GetEventTypeString(
        event_object.event_type)

    return super(WinEvtFormatter, self).GetMessages(event_object)
