# -*- coding: utf-8 -*-
"""Parser for Windows EventLog (EVT) files."""

import pyevt

from plaso import dependencies
from plaso.containers import time_events
from plaso.lib import eventdata
from plaso.lib import specification
from plaso.parsers import interface
from plaso.parsers import manager


dependencies.CheckModuleVersion(u'pyevt')


class WinEvtRecordEvent(time_events.PosixTimeEvent):
  """Convenience class for a Windows EventLog (EVT) record event.

  Attributes:
    computer_name (str): computer name stored in the event record.
    event_category (int): event category.
    event_identifier (int): event identifier.
    event_type (int): event type.
    facility (int): event facility.
    message_identifier (int): event message identifier.
    offset (int): data offset of the event record with in the file.
    record_number (int): event record number.
    recovered (bool): True if the record was recovered.
    severity (int): event severity.
    source_name (str): name of the event source.
    strings (list[str]): event strings.
    user_sid (str): user security identifier (SID) stored in the event record.
  """

  DATA_TYPE = u'windows:evt:record'

  def __init__(
      self, posix_time, timestamp_description, evt_record, record_number,
      event_identifier, recovered=False):
    """Initializes the event.

    Args:
      posix_time (int): POSIX time value, which contains the number of seconds
          since January 1, 1970 00:00:00 UTC.
      timestamp_description (str): description of the usage of the timestamp
          value.
      evt_record (pyevt.record): event record.
      record_number (int): event record number.
      event_identifier (int): event identifier.
      recovered (Optional[bool]): True if the record was recovered.
    """
    super(WinEvtRecordEvent, self).__init__(posix_time, timestamp_description)

    self.offset = evt_record.offset
    self.recovered = recovered

    if record_number is not None:
      self.record_number = evt_record.identifier

    # We want the event identifier to match the behavior of that of the EVTX
    # event records.
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

  def _ParseRecord(
      self, parser_mediator, record_index, evt_record, recovered=False):
    """Extract data from a Windows EventLog (EVT) record.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      record_index (int): event record index.
      evt_record (pyevt.record): event record.
      recovered (Optional[bool]): True if the record was recovered.
    """
    try:
      record_number = evt_record.identifier
    except OverflowError as exception:
      parser_mediator.ProduceExtractionError((
          u'unable to read record identifier from event record: {0:d} '
          u'with error: {1:s}').format(record_index, exception))

      record_number = None

    try:
      event_identifier = evt_record.event_identifier
    except OverflowError as exception:
      parser_mediator.ProduceExtractionError((
          u'unable to read event identifier from event record: {0:d} '
          u'with error: {1:s}').format(record_index, exception))

      event_identifier = None

    try:
      creation_time = evt_record.get_creation_time_as_integer()
    except OverflowError as exception:
      parser_mediator.ProduceExtractionError((
          u'unable to read creation time from event record: {0:d} '
          u'with error: {1:s}').format(record_index, exception))

      creation_time = None

    if creation_time is not None:
      event_object = WinEvtRecordEvent(
          creation_time, eventdata.EventTimestamp.CREATION_TIME,
          evt_record, record_number, event_identifier, recovered=recovered)
      parser_mediator.ProduceEvent(event_object)

    try:
      written_time = evt_record.get_written_time_as_integer()
    except OverflowError as exception:
      parser_mediator.ProduceExtractionError((
          u'unable to read written time from event record: {0:d} '
          u'with error: {1:s}').format(record_index, exception))

      written_time = None

    if written_time is not None:
      event_object = WinEvtRecordEvent(
          written_time, eventdata.EventTimestamp.WRITTEN_TIME,
          evt_record, record_number, event_identifier, recovered=recovered)
      parser_mediator.ProduceEvent(event_object)

    # TODO: what if both creation_time and written_time are None.

  def ParseFileObject(self, parser_mediator, file_object, **kwargs):
    """Parses a Windows EventLog (EVT) file-like object.

    Args:
      parser_mediator (ParserMediator): parser mediator.
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

    evt_file.close()


manager.ParsersManager.RegisterParser(WinEvtParser)
