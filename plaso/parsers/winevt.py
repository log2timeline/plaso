# -*- coding: utf-8 -*-
"""Parser for Windows EventLog (EVT) files."""

import pyevt

from dfdatetime import posix_time as dfdatetime_posix_time

from plaso.containers import events
from plaso.lib import specification
from plaso.parsers import interface
from plaso.parsers import manager


class WinEvtRecordEventData(events.EventData):
  """Windows EventLog (EVT) record event data.

  Attributes:
    creation_time (dfdatetime.DateTimeValues): event record creation date
        and time.
    computer_name (str): computer name stored in the event record.
    event_category (int): event category.
    event_identifier (int): event identifier.
    event_type (int): event type.
    facility (int): event facility.
    message_identifier (int): event message identifier.
    offset (int): offset of the event record relative to the start of the file,
        from which the event data was extracted.
    record_number (int): event record number.
    recovered (bool): True if the record was recovered.
    severity (int): event severity.
    source_name (str): name of the event source.
    strings (list[str]): event strings.
    user_sid (str): user security identifier (SID) stored in the event record.
    written_time (dfdatetime.DateTimeValues): event record written date and
        time.
  """

  DATA_TYPE = 'windows:evt:record'

  def __init__(self):
    """Initializes event data."""
    super(WinEvtRecordEventData, self).__init__(data_type=self.DATA_TYPE)
    self.creation_time = None
    self.computer_name = None
    self.event_category = None
    self.event_identifier = None
    self.event_type = None
    self.facility = None
    self.message_identifier = None
    self.offset = None
    self.record_number = None
    self.recovered = None
    self.severity = None
    self.source_name = None
    self.strings = None
    self.user_sid = None
    self.written_time = None


class WinEvtParser(interface.FileObjectParser):
  """Parses Windows EventLog (EVT) files."""

  _INITIAL_FILE_OFFSET = None

  NAME = 'winevt'
  DATA_FORMAT = 'Windows EventLog (EVT) file'

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
          and other components, such as storage and dfVFS.
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
      warning_message = (
          'unable to read record identifier from event record: {0:d} '
          'with error: {1!s}').format(record_index, exception)
      if recovered:
        parser_mediator.ProduceRecoveryWarning(warning_message)
      else:
        parser_mediator.ProduceExtractionWarning(warning_message)

    try:
      event_identifier = evt_record.event_identifier
    except OverflowError as exception:
      warning_message = (
          'unable to read event identifier from event record: {0:d} '
          'with error: {1!s}').format(record_index, exception)
      if recovered:
        parser_mediator.ProduceRecoveryWarning(warning_message)
      else:
        parser_mediator.ProduceExtractionWarning(warning_message)

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
    # necessarily correspond with the actual hostname.
    event_data.computer_name = evt_record.computer_name
    event_data.user_sid = evt_record.user_security_identifier

    event_data.strings = list(evt_record.strings)

    return event_data

  def _ParseRecord(
      self, parser_mediator, record_index, evt_record, recovered=False):
    """Parses a Windows EventLog (EVT) record.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      record_index (int): event record index.
      evt_record (pyevt.record): event record.
      recovered (Optional[bool]): True if the record was recovered.
    """
    event_data = self._GetEventData(
        parser_mediator, record_index, evt_record, recovered=recovered)

    try:
      creation_time = evt_record.get_creation_time_as_integer()
    except OverflowError as exception:
      warning_message = (
          'unable to read creation time from event record: {0:d} '
          'with error: {1!s}').format(record_index, exception)
      if recovered:
        parser_mediator.ProduceRecoveryWarning(warning_message)
      else:
        parser_mediator.ProduceExtractionWarning(warning_message)

      creation_time = None

    if creation_time:
      event_data.creation_time = dfdatetime_posix_time.PosixTime(
          timestamp=creation_time)

    try:
      written_time = evt_record.get_written_time_as_integer()
    except OverflowError as exception:
      warning_message = (
          'unable to read written time from event record: {0:d} '
          'with error: {1!s}').format(record_index, exception)
      if recovered:
        parser_mediator.ProduceRecoveryWarning(warning_message)
      else:
        parser_mediator.ProduceExtractionWarning(warning_message)

      written_time = None

    if written_time:
      event_data.written_time = dfdatetime_posix_time.PosixTime(
          timestamp=written_time)

    parser_mediator.ProduceEventData(event_data)

  def _ParseRecords(self, parser_mediator, evt_file):
    """Parses Windows EventLog (EVT) records.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      evt_file (pyevt.file): Windows EventLog (EVT) file.
    """
    # To handle errors when parsing a Windows EventLog (EVT) file in the most
    # granular way the following code iterates over every event record. The
    # call to evt_file.get_record() and access to members of evt_record should
    # be called within a try-except.

    for record_index in range(evt_file.number_of_records):
      if parser_mediator.abort:
        break

      try:
        evt_record = evt_file.get_record(record_index)
        self._ParseRecord(parser_mediator, record_index, evt_record)
      except IOError as exception:
        parser_mediator.ProduceExtractionWarning(
            'unable to parse event record: {0:d} with error: {1!s}'.format(
                record_index, exception))

    for record_index in range(evt_file.number_of_recovered_records):
      if parser_mediator.abort:
        break

      try:
        evt_record = evt_file.get_recovered_record(record_index)
        self._ParseRecord(
            parser_mediator, record_index, evt_record, recovered=True)
      except IOError as exception:
        parser_mediator.ProduceRecoveryWarning((
            'unable to parse recovered event record: {0:d} with error: '
            '{1!s}').format(record_index, exception))

  def ParseFileObject(self, parser_mediator, file_object):
    """Parses a Windows EventLog (EVT) file-like object.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      file_object (dfvfs.FileIO): a file-like object.
    """
    code_page = parser_mediator.GetCodePage()

    evt_file = pyevt.file()
    evt_file.set_ascii_codepage(code_page)

    try:
      evt_file.open_file_object(file_object)
    except IOError as exception:
      parser_mediator.ProduceExtractionWarning(
          'unable to open file with error: {0!s}'.format(exception))
      return

    try:
      self._ParseRecords(parser_mediator, evt_file)
    finally:
      evt_file.close()


manager.ParsersManager.RegisterParser(WinEvtParser)
