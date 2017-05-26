# -*- coding: utf-8 -*-
"""Parser for Windows EventLog (EVT) files."""

import pyevt

from dfdatetime import posix_time as dfdatetime_posix_time
from dfdatetime import semantic_time as dfdatetime_semantic_time

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.lib import specification
from plaso.parsers import interface
from plaso.parsers import manager


class WinEvtRecordEventData(events.EventData):
  """Windows EventLog (EVT) record event data.

  Attributes:
    computer_name (str): computer name stored in the event record.
    event_category (int): event category.
    event_identifier (int): event identifier.
    event_type (int): event type.
    facility (int): event facility.
    message_identifier (int): event message identifier.
    record_number (int): event record number.
    recovered (bool): True if the record was recovered.
    severity (int): event severity.
    source_name (str): name of the event source.
    strings (list[str]): event strings.
    user_sid (str): user security identifier (SID) stored in the event record.
  """

  DATA_TYPE = u'windows:evt:record'

  def __init__(self):
    """Initializes event data."""
    super(WinEvtRecordEventData, self).__init__(data_type=self.DATA_TYPE)
    self.computer_name = None
    self.event_category = None
    self.event_identifier = None
    self.event_type = None
    self.facility = None
    self.message_identifier = None
    self.record_number = None
    self.recovered = None
    self.severity = None
    self.source_name = None
    self.strings = None
    self.user_sid = None


class WinEvtParser(interface.FileObjectParser):
  """Parses Windows EventLog (EVT) files."""

  _INITIAL_FILE_OFFSET = None

  NAME = u'winevt'
  DESCRIPTION = u'Parser for Windows EventLog (EVT) files.'

  @classmethod
  def GetFormatSpecification(cls):
    """Retrieves the format specification.

    Returns:
      FormatSpecification: format specification.
    """
    format_specification = specification.FormatSpecification(cls.NAME)
    format_specification.AddNewSignature(b'LfLe', offset=4)
    return format_specification

  def _GetEventData(
      self, parser_mediator, record_index, evt_record, recovered=False):
    """Retrieves event data from the Windows EventLog (EVT) record.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      record_index (int): event record index.
      evt_record (pyevt.record): event record.
      recovered (Optional[bool]): True if the record was recovered.

    Returns:
      WinEvtRecordEventData: event data.
    """
    event_data = WinEvtRecordEventData()

    try:
      event_data.record_number = evt_record.identifier
    except OverflowError as exception:
      parser_mediator.ProduceExtractionError((
          u'unable to read record identifier from event record: {0:d} '
          u'with error: {1:s}').format(record_index, exception))

    try:
      event_identifier = evt_record.event_identifier
    except OverflowError as exception:
      parser_mediator.ProduceExtractionError((
          u'unable to read event identifier from event record: {0:d} '
          u'with error: {1:s}').format(record_index, exception))

      event_identifier = None

    event_data.offset = evt_record.offset
    event_data.recovered = recovered

    # We want the event identifier to match the behavior of that of the EVTX
    # event records.
    if event_identifier is not None:
      event_data.event_identifier = event_identifier & 0xffff
      event_data.facility = (event_identifier >> 16) & 0x0fff
      event_data.severity = event_identifier >> 30
      event_data.message_identifier = event_identifier

    event_data.event_type = evt_record.event_type
    event_data.event_category = evt_record.event_category
    event_data.source_name = evt_record.source_name

    # Computer name is the value stored in the event record and does not
    # necessarily corresponds with the actual hostname.
    event_data.computer_name = evt_record.computer_name
    event_data.user_sid = evt_record.user_security_identifier

    event_data.strings = list(evt_record.strings)

    return event_data

  def _ParseRecord(
      self, parser_mediator, record_index, evt_record, recovered=False):
    """Parses a Windows EventLog (EVT) record.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      record_index (int): event record index.
      evt_record (pyevt.record): event record.
      recovered (Optional[bool]): True if the record was recovered.
    """
    event_data = self._GetEventData(
        parser_mediator, record_index, evt_record, recovered=recovered)

    try:
      creation_time = evt_record.get_creation_time_as_integer()
    except OverflowError as exception:
      parser_mediator.ProduceExtractionError((
          u'unable to read creation time from event record: {0:d} '
          u'with error: {1:s}').format(record_index, exception))

      creation_time = None

    if creation_time:
      date_time = dfdatetime_posix_time.PosixTime(timestamp=creation_time)
      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_CREATION)
      parser_mediator.ProduceEventWithEventData(event, event_data)

    try:
      written_time = evt_record.get_written_time_as_integer()
    except OverflowError as exception:
      parser_mediator.ProduceExtractionError((
          u'unable to read written time from event record: {0:d} '
          u'with error: {1:s}').format(record_index, exception))

      written_time = None

    if written_time:
      date_time = dfdatetime_posix_time.PosixTime(timestamp=written_time)
      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_WRITTEN)
      parser_mediator.ProduceEventWithEventData(event, event_data)

    if not creation_time and not written_time:
      date_time = dfdatetime_semantic_time.SemanticTime(u'Not set')
      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_NOT_A_TIME)
      parser_mediator.ProduceEventWithEventData(event, event_data)

  def _ParseRecords(self, parser_mediator, evt_file):
    """Parses Windows EventLog (EVT) records.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      evt_file (pyevt.file): Windows EventLog (EVT) file.
    """
    for record_index, evt_record in enumerate(evt_file.records):
      if parser_mediator.abort:
        break

      try:
        self._ParseRecord(parser_mediator, record_index, evt_record)
      except IOError as exception:
        parser_mediator.ProduceExtractionError(
            u'unable to parse event record: {0:d} with error: {1:s}'.format(
                record_index, exception))

    for record_index, evt_record in enumerate(evt_file.recovered_records):
      if parser_mediator.abort:
        break

      try:
        self._ParseRecord(
            parser_mediator, record_index, evt_record, recovered=True)
      except IOError as exception:
        parser_mediator.ProduceExtractionError((
            u'unable to parse recovered event record: {0:d} with error: '
            u'{1:s}').format(record_index, exception))

  def ParseFileObject(self, parser_mediator, file_object, **kwargs):
    """Parses a Windows EventLog (EVT) file-like object.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      file_object (dfvfs.FileIO): a file-like object.
    """
    evt_file = pyevt.file()
    evt_file.set_ascii_codepage(parser_mediator.codepage)

    try:
      evt_file.open_file_object(file_object)
    except IOError as exception:
      parser_mediator.ProduceExtractionError(
          u'unable to open file with error: {0:s}'.format(exception))
      return

    try:
      self._ParseRecords(parser_mediator, evt_file)
    finally:
      evt_file.close()


manager.ParsersManager.RegisterParser(WinEvtParser)
