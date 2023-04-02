# -*- coding: utf-8 -*-
"""Parser for Windows XML EventLog (EVTX) files."""

import pyevtx

from dfdatetime import filetime as dfdatetime_filetime

from plaso.containers import events
from plaso.lib import specification
from plaso.parsers import interface
from plaso.parsers import manager


class WinEvtxRecordEventData(events.EventData):
  """Windows XML EventLog (EVTX) record event data.

  Attributes:
    creation_time (dfdatetime.DateTimeValues): event record creation date
        and time.
    computer_name (str): computer name stored in the event record.
    event_identifier (int): event identifier.
    event_level (int): event level.
    event_version (int): event version.
    message_identifier (int): event message identifier.
    offset (int): offset of the EVTX record relative to the start of the file,
        from which the event data was extracted.
    provider_identifier (str): identifier of the EventLog provider.
    record_number (int): event record number.
    recovered (bool): True if the record was recovered.
    source_name (str): name of the event source.
    strings (list[str]): event strings.
    user_sid (str): user security identifier (SID) stored in the event record.
    written_time (dfdatetime.DateTimeValues): event record written date and
        time.
    xml_string (str): XML representation of the event.
  """

  DATA_TYPE = 'windows:evtx:record'

  def __init__(self):
    """Initializes event data."""
    super(WinEvtxRecordEventData, self).__init__(data_type=self.DATA_TYPE)
    self.creation_time = None
    self.computer_name = None
    self.event_identifier = None
    self.event_level = None
    self.event_version = None
    self.message_identifier = None
    self.offset = None
    self.provider_identifier = None
    self.record_number = None
    self.recovered = None
    self.source_name = None
    self.strings = None
    self.user_sid = None
    self.written_time = None
    self.xml_string = None


class WinEvtxParser(interface.FileObjectParser):
  """Parses Windows XML EventLog (EVTX) files."""

  _INITIAL_FILE_OFFSET = None

  NAME = 'winevtx'
  DATA_FORMAT = 'Windows XML EventLog (EVTX) file'

  def _GetEventDataFromRecord(
      self, parser_mediator, record_index, evtx_record, recovered=False):
    """Extract data from a Windows XML EventLog (EVTX) record.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      record_index (int): event record index.
      evtx_record (pyevtx.record): event record.
      recovered (Optional[bool]): True if the record was recovered.

    Return:
      WinEvtxRecordEventData: event data.
    """
    event_data = WinEvtxRecordEventData()

    try:
      event_data.record_number = evtx_record.identifier
    except OverflowError as exception:
      warning_message = (
          'unable to read record identifier from event record: {0:d} '
          'with error: {1!s}').format(record_index, exception)
      if recovered:
        parser_mediator.ProduceRecoveryWarning(warning_message)
      else:
        parser_mediator.ProduceExtractionWarning(warning_message)

    try:
      event_identifier = evtx_record.event_identifier
    except OverflowError as exception:
      warning_message = (
          'unable to read event identifier from event record: {0:d} '
          'with error: {1!s}').format(record_index, exception)
      if recovered:
        parser_mediator.ProduceRecoveryWarning(warning_message)
      else:
        parser_mediator.ProduceExtractionWarning(warning_message)

      event_identifier = None

    try:
      event_identifier_qualifiers = evtx_record.event_identifier_qualifiers
    except OverflowError as exception:
      warning_message = (
          'unable to read event identifier qualifiers from event record: '
          '{0:d} with error: {1!s}').format(record_index, exception)
      if recovered:
        parser_mediator.ProduceRecoveryWarning(warning_message)
      else:
        parser_mediator.ProduceExtractionWarning(warning_message)

      event_identifier_qualifiers = None

    event_data.offset = evtx_record.offset
    event_data.recovered = recovered

    if event_identifier is not None:
      event_data.event_identifier = event_identifier

      event_data.message_identifier = event_identifier
      if event_identifier_qualifiers is not None:
        event_data.message_identifier |= event_identifier_qualifiers << 16

    if evtx_record.provider_identifier:
      event_data.provider_identifier = evtx_record.provider_identifier.lower()

    event_data.event_level = evtx_record.event_level
    event_data.event_version = evtx_record.event_version
    event_data.source_name = evtx_record.source_name

    # Computer name is the value stored in the event record and does not
    # necessarily correspond with the actual hostname.
    event_data.computer_name = evtx_record.computer_name
    event_data.user_sid = evtx_record.user_security_identifier

    event_data.strings = list(evtx_record.strings)

    event_data.xml_string = evtx_record.xml_string

    return event_data

  def _ParseRecord(
      self, parser_mediator, record_index, evtx_record, recovered=False):
    """Extract data from a Windows XML EventLog (EVTX) record.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      record_index (int): event record index.
      evtx_record (pyevtx.record): event record.
      recovered (Optional[bool]): True if the record was recovered.
    """
    event_data = self._GetEventDataFromRecord(
        parser_mediator, record_index, evtx_record, recovered=recovered)

    try:
      creation_time = evtx_record.get_creation_time_as_integer()
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
      event_data.creation_time = dfdatetime_filetime.Filetime(
          timestamp=creation_time)

    try:
      written_time = evtx_record.get_written_time_as_integer()
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
      event_data.written_time = dfdatetime_filetime.Filetime(
          timestamp=written_time)

    parser_mediator.ProduceEventData(event_data)

  def _ParseRecords(self, parser_mediator, evtx_file):
    """Parses Windows XML EventLog (EVTX) records.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      evtx_file (pyevtx.file): Windows XML EventLog (EVTX) file.
    """
    # To handle errors when parsing a Windows XML EventLog (EVTX) file in the
    # most granular way the following code iterates over every event record.
    # The call to evt_file.get_record() and access to members of evt_record
    # should be called within a try-except.

    for record_index in range(evtx_file.number_of_records):
      if parser_mediator.abort:
        break

      try:
        evtx_record = evtx_file.get_record(record_index)
        self._ParseRecord(parser_mediator, record_index, evtx_record)

      except IOError as exception:
        parser_mediator.ProduceExtractionWarning(
            'unable to parse event record: {0:d} with error: {1!s}'.format(
                record_index, exception))

    for record_index in range(evtx_file.number_of_recovered_records):
      if parser_mediator.abort:
        break

      try:
        evtx_record = evtx_file.get_recovered_record(record_index)
        self._ParseRecord(
            parser_mediator, record_index, evtx_record, recovered=True)

      except IOError as exception:
        parser_mediator.ProduceRecoveryWarning((
            'unable to parse recovered event record: {0:d} with error: '
            '{1!s}').format(record_index, exception))

  @classmethod
  def GetFormatSpecification(cls):
    """Retrieves the format specification.

    Returns:
      FormatSpecification: format specification.
    """
    format_specification = specification.FormatSpecification(cls.NAME)
    format_specification.AddNewSignature(b'ElfFile\x00', offset=0)
    return format_specification

  def ParseFileObject(self, parser_mediator, file_object):
    """Parses a Windows XML EventLog (EVTX) file-like object.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      file_object (dfvfs.FileIO): a file-like object.
    """
    code_page = parser_mediator.GetCodePage()

    evtx_file = pyevtx.file()
    evtx_file.set_ascii_codepage(code_page)

    try:
      evtx_file.open_file_object(file_object)
    except IOError as exception:
      parser_mediator.ProduceExtractionWarning(
          'unable to open file with error: {0!s}'.format(exception))
      return

    try:
      self._ParseRecords(parser_mediator, evtx_file)
    finally:
      evtx_file.close()


manager.ParsersManager.RegisterParser(WinEvtxParser)
