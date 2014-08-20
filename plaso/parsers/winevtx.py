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
"""Parser for Windows XML EventLog (EVTX) files."""

import logging

import pyevtx

from plaso.events import time_events
from plaso.lib import errors
from plaso.lib import eventdata
from plaso.parsers import interface


class WinEvtxRecordEvent(time_events.FiletimeEvent):
  """Convenience class for a Windows XML EventLog (EVTX) record event."""
  DATA_TYPE = 'windows:evtx:record'

  def __init__(self, evtx_record, recovered=False):
    """Initializes the event.

    Args:
      evtx_record: The EVTX record (pyevtx.record).
      recovered: Boolean value to indicate the record was recovered, False
                 by default.
    """
    try:
      timestamp = evtx_record.get_written_time_as_integer()
    except OverflowError as exception:
      logging.warning(
          u'Unable to read the timestamp from record with error: {0:s}'.format(
              exception))
      timestamp = 0

    super(WinEvtxRecordEvent, self).__init__(
        timestamp, eventdata.EventTimestamp.WRITTEN_TIME)

    self.recovered = recovered
    self.offset = evtx_record.offset
    try:
      self.record_number = evtx_record.identifier
    except OverflowError as exception:
      logging.warning(
          u'Unable to assign the record number with error: {0:s}.'.format(
              exception))

    try:
      self.event_identifier = evtx_record.event_identifier
    except OverflowError as exception:
      logging.warning(
          u'Unable to assign the event identifier with error: {0:s}.'.format(
              exception))

    self.event_level = evtx_record.event_level
    self.source_name = evtx_record.source_name
    # Computer name is the value stored in the event record and does not
    # necessarily corresponds with the actual hostname.
    self.computer_name = evtx_record.computer_name
    self.user_sid = evtx_record.user_security_identifier

    self.strings = list(evtx_record.strings)

    self.xml_string = evtx_record.xml_string


class WinEvtxParser(interface.BaseParser):
  """Parses Windows XML EventLog (EVTX) files."""

  NAME = 'winevtx'

  def __init__(self, pre_obj):
    """Initializes the parser.

    Args:
      pre_obj: pre-parsing object.
    """
    super(WinEvtxParser, self).__init__(pre_obj)
    self._codepage = getattr(self._pre_obj, 'codepage', 'cp1252')

  def Parse(self, file_entry):
    """Extract data from a Windows XML EventLog (EVTX) file.

    Args:
      file_entry: A file entry object.

    Yields:
      An event object (WinEvtxRecordEvent) that contains the parsed data.
    """
    file_object = file_entry.GetFileObject()
    evtx_file = pyevtx.file()
    evtx_file.set_ascii_codepage(self._codepage)

    try:
      evtx_file.open_file_object(file_object)
    except IOError as exception:
      raise errors.UnableToParseFile(
          u'[{0:s}] unable to parse file {1:s} with error: {2:s}'.format(
              self.parser_name, file_entry.name, exception))

    for record_index in range(0, evtx_file.number_of_records):
      try:
        evtx_record = evtx_file.get_record(record_index)
        yield WinEvtxRecordEvent(evtx_record)
      except IOError as exception:
        logging.warning((
            u'[{0:s}] unable to parse event record: {1:d} in file: {2:s} '
            u'with error: {3:s}').format(
                self.parser_name, record_index, file_entry.name, exception))

    for record_index in range(0, evtx_file.number_of_recovered_records):
      try:
        evtx_record = evtx_file.get_recovered_record(record_index)
        yield WinEvtxRecordEvent(evtx_record, recovered=True)
      except IOError as exception:
        logging.debug((
            u'[{0:s}] unable to parse recovered event record: {1:d} in file: '
            u'{2:s} with error: {3:s}').format(
                self.parser_name, record_index, file_entry.name, exception))

    file_object.close()
