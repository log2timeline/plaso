# -*- coding: utf-8 -*-
"""Parser for Windows EventLog (EVT) files."""

import logging

import pyevt

from plaso.events import time_events
from plaso.lib import errors
from plaso.lib import eventdata
from plaso.parsers import interface
from plaso.parsers import manager


class WinEvtRecordEvent(time_events.PosixTimeEvent):
  """Convenience class for a Windows EventLog (EVT) record event."""

  DATA_TYPE = u'windows:evt:record'

  def __init__(
      self, timestamp, timestamp_description, evt_record, recovered=False):
    """Initializes the event.

    Args:
      timestamp: The POSIX timestamp value.
      timestamp_description: A description string for the timestamp value.
      evt_record: The EVT record (pyevt.record).
      recovered: Boolean value to indicate the record was recovered, False
                 by default.
    """
    super(WinEvtRecordEvent, self).__init__(timestamp, timestamp_description)

    self.recovered = recovered
    self.offset = evt_record.offset

    try:
      self.record_number = evt_record.identifier
    except OverflowError as exception:
      logging.warning(
          u'Unable to assign the record identifier with error: {0:s}.'.format(
              exception))
    try:
      event_identifier = evt_record.event_identifier
    except OverflowError as exception:
      event_identifier = None
      logging.warning(
          u'Unable to assign the event identifier with error: {0:s}.'.format(
              exception))

    # We are only interest in the event identifier code to match the behavior
    # of EVTX event records.
    if event_identifier is not None:
      self.event_identifier = event_identifier & 0xffff
      self.facility = (event_identifier >> 16) & 0x0fff
      self.severity = event_identifier >> 30
      self.message_identifier = event_identifier

    self.event_type = evt_record.event_type
    self.event_category = evt_record.event_category
    self.source_name = evt_record.source_name

    # Computer name is the value stored in the event record and does not
    # necessarily corresponds with the actual hostname.
    self.computer_name = evt_record.computer_name
    self.user_sid = evt_record.user_security_identifier

    self.strings = list(evt_record.strings)


class WinEvtParser(interface.SingleFileBaseParser):
  """Parses Windows EventLog (EVT) files."""

  _INITIAL_FILE_OFFSET = None

  NAME = u'winevt'
  DESCRIPTION = u'Parser for Windows EventLog (EVT) files.'

  def _ParseRecord(self, parser_mediator, evt_record, recovered=False):
    """Extract data from a Windows EventLog (EVT) record.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      evt_record: An event record (pyevt.record).
      recovered: Boolean value to indicate the record was recovered, False
                 by default.
    """
    try:
      creation_time = evt_record.get_creation_time_as_integer()
    except OverflowError as exception:
      logging.warning(
          u'Unable to read the timestamp from record with error: {0:s}'.format(
              exception))
      creation_time = 0

    if creation_time:
      event_object = WinEvtRecordEvent(
          creation_time, eventdata.EventTimestamp.CREATION_TIME,
          evt_record, recovered)
      parser_mediator.ProduceEvent(event_object)

    try:
      written_time = evt_record.get_written_time_as_integer()
    except OverflowError as exception:
      logging.warning(
          u'Unable to read the timestamp from record with error: {0:s}'.format(
              exception))
      written_time = 0

    if written_time:
      event_object = WinEvtRecordEvent(
          written_time, eventdata.EventTimestamp.WRITTEN_TIME,
          evt_record, recovered)
      parser_mediator.ProduceEvent(event_object)

  def ParseFileObject(self, parser_mediator, file_object, **kwargs):
    """Parses a Windows EventLog (EVT) file-like object.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      file_object: A file-like object.

    Raises:
      UnableToParseFile: when the file cannot be parsed.
    """
    file_name = parser_mediator.GetDisplayName()
    evt_file = pyevt.file()
    evt_file.set_ascii_codepage(parser_mediator.codepage)

    try:
      evt_file.open_file_object(file_object)
    except IOError as exception:
      raise errors.UnableToParseFile(
          u'[{0:s}] unable to parse file {1:s} with error: {2:s}'.format(
              self.NAME, file_name, exception))

    for record_index in range(0, evt_file.number_of_records):
      try:
        evt_record = evt_file.get_record(record_index)
        self._ParseRecord(parser_mediator, evt_record,)
      except IOError as exception:
        logging.warning((
            u'[{0:s}] unable to parse event record: {1:d} in file: {2:s} '
            u'with error: {3:s}').format(
                self.NAME, record_index, file_name, exception))

    for record_index in range(0, evt_file.number_of_recovered_records):
      try:
        evt_record = evt_file.get_recovered_record(record_index)
        self._ParseRecord(parser_mediator, evt_record, recovered=True)
      except IOError as exception:
        logging.info((
            u'[{0:s}] unable to parse recovered event record: {1:d} in file: '
            u'{2:s} with error: {3:s}').format(
                self.NAME, record_index, file_name, exception))

    evt_file.close()


manager.ParsersManager.RegisterParser(WinEvtParser)
