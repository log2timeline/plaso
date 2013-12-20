#!/usr/bin/python
# -*- coding: utf-8 -*-
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
"""Parser for Windows EventLog (EVT) files."""
import logging

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

    self.recovered = recovered
    self.offset = evt_record.offset
    try:
      self.record_number = evt_record.identifier
    except OverflowError as e:
      logging.warning(u'Unable to assign the record  identifier [%s].', e)
    try:
      self.event_identifier = evt_record.event_identifier
    except OverflowError as e:
      logging.warning(u'Unable to assign the event identifier [%s].', e)
    self.event_type = evt_record.event_type
    self.event_category = evt_record.event_category
    self.source_name = evt_record.source_name
    # Computer name is the value stored in the event record and does not
    # necessarily corresponds with the actual hostname.
    self.computer_name = evt_record.computer_name
    self.user_sid = evt_record.user_security_identifier

    self.strings = list(evt_record.strings)


class WinEvtParser(parser.BaseParser):
  """Parses Windows EventLog (EVT) files."""

  NAME = 'winevt'

  def __init__(self, pre_obj, config):
    """Initializes the parser.

    Args:
      pre_obj: pre-parsing object.
      config: Configuration object.
    """
    super(WinEvtParser, self).__init__(pre_obj, config)
    self._codepage = getattr(self._pre_obj, 'codepage', 'cp1252')

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

    try:
      creation_time = evt_record.get_creation_time_as_integer()
    except OverflowError as e:
      logging.warning(
          u'Unable to read the timestamp from record, error: %s', e)
      creation_time = 0
    event_container.Append(event.PosixTimeEvent(
        creation_time, eventdata.EventTimestamp.CREATION_TIME,
        event_container.data_type))

    try:
      written_time = evt_record.get_written_time_as_integer()
    except OverflowError as e:
      logging.warning(
          u'Unable to read the timestamp from record, error: %s', e)
      written_time = 0
    event_container.Append(event.PosixTimeEvent(
        written_time, eventdata.EventTimestamp.WRITTEN_TIME,
        event_container.data_type))

    return event_container

  def Parse(self, file_object):
    """Extract data from a Windows EventLog (EVT) file.

       A separate event container is returned for every record to limit
       memory consumption.

    Args:
      file_object: A file-like object to read data from.

    Yields:
      An event container (WinEvtRecordEventContainer) that contains
      the parsed data.
    """
    evt_file = pyevt.file()
    evt_file.set_ascii_codepage(self._codepage)

    try:
      evt_file.open_file_object(file_object)
    except IOError as exception:
      raise errors.UnableToParseFile('[%s] unable to parse file %s: %s' % (
          self.parser_name, file_object.name, exception))

    for record_index in range(0, evt_file.number_of_records):
      try:
        evt_record = evt_file.get_record(record_index)
        yield self._ParseRecord(evt_record)
      except IOError as exception:
        logging.warning(
            '[%s] unable to parse event record: %d in file: %s: %s' % (
            self.parser_name, record_index, file_object.name, exception))

    for record_index in range(0, evt_file.number_of_recovered_records):
      try:
        evt_record = evt_file.get_recovered_record(record_index)
        yield self._ParseRecord(evt_record, recovered=True)
      except IOError as exception:
        logging.info((
            u'[%s] unable to parse recovered event record: %d in file: %s: '
            u'%s') % (
                self.parser_name, record_index, file_object.name, exception))
