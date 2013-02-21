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
from plaso.lib import errors
from plaso.lib import event
from plaso.lib import eventdata
from plaso.lib import parser

import pyevt


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
    self.source_long = 'WinEvt'
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
      raise errors.UnableToParseFile('[%s] unable to parse file %s: %s' % (
          self.NAME, file_object.name, exception))

    for evt_record in evt_file.records:
      yield self._ParseRecord(evt_record)

    for evt_record in evt_file.recovered_records:
      yield self._ParseRecord(evt_record, recovered=True)

