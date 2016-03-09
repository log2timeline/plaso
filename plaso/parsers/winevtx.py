# -*- coding: utf-8 -*-
"""Parser for Windows XML EventLog (EVTX) files."""

import pyevtx

from plaso import dependencies
from plaso.containers import time_events
from plaso.lib import eventdata
from plaso.lib import specification
from plaso.parsers import interface
from plaso.parsers import manager


dependencies.CheckModuleVersion(u'pyevtx')


class WinEvtxRecordEvent(time_events.FiletimeEvent):
  """Convenience class for a Windows XML EventLog (EVTX) record event.

  Attributes:
    computer_name: the computer name stored in the event record.
    event_identifier: the event identifier.
    event_level: the event level.
    message_identifier: the event message identifier.
    offset: the data offset of the event record with in the file.
    record_number: the event record number.
    recovered: boolean value to indicate the record was recovered.
    source_name: the name of the event source.
    strings: array of event strings.
    user_sid: the user security identifier (SID) stored in the event record.
    xml_string: XML representation of the event.
  """

  DATA_TYPE = u'windows:evtx:record'

  def __init__(
      self, timestamp, evtx_record, record_number, event_identifier,
      event_identifier_qualifiers, recovered=False):
    """Initializes the event.

    Args:
      timestamp: the FILETIME value for the timestamp.
      evtx_record: the EVTX record (instance of pyevtx.record).
      record_number: the event record number.
      event_identifier: the event identifier.
      event_identifier_qualifiers: the event identifier qualifiers.
      recovered: optional boolean value to indicate the record was recovered.
    """
    super(WinEvtxRecordEvent, self).__init__(
        timestamp, eventdata.EventTimestamp.WRITTEN_TIME)

    self.offset = evtx_record.offset
    self.recovered = recovered

    if record_number is not None:
      self.record_number = evtx_record.identifier

    if event_identifier is not None:
      self.event_identifier = event_identifier

      if event_identifier_qualifiers is not None:
        self.message_identifier = (
            (event_identifier_qualifiers << 16) | event_identifier)

    self.event_level = evtx_record.event_level
    self.source_name = evtx_record.source_name

    # Computer name is the value stored in the event record and does not
    # necessarily corresponds with the actual hostname.
    self.computer_name = evtx_record.computer_name
    self.user_sid = evtx_record.user_security_identifier

    self.strings = list(evtx_record.strings)

    self.xml_string = evtx_record.xml_string


class WinEvtxParser(interface.FileObjectParser):
  """Parses Windows XML EventLog (EVTX) files."""

  _INITIAL_FILE_OFFSET = None

  NAME = u'winevtx'
  DESCRIPTION = u'Parser for Windows XML EventLog (EVTX) files.'

  @classmethod
  def GetFormatSpecification(cls):
    """Retrieves the format specification."""
    format_specification = specification.FormatSpecification(cls.NAME)
    format_specification.AddNewSignature(b'ElfFile\x00', offset=0)
    return format_specification

  def _ParseRecord(
      self, parser_mediator, record_index, evtx_record, recovered=False):
    """Extract data from a Windows XML EventLog (EVTX) record.

    Args:
      parser_mediator: a parser mediator object (instance of ParserMediator).
      record_index: the event record index.
      evtx_record: an event record (instance of pyevtx.record).
      recovered: optional boolean value to indicate the record was recovered.
    """
    try:
      record_number = evtx_record.identifier
    except OverflowError as exception:
      parser_mediator.ProduceParseError((
          u'unable to read record identifier from event record: {0:d} '
          u'with error: {1:s}').format(record_index, exception))

      record_number = None

    try:
      event_identifier = evtx_record.event_identifier
    except OverflowError as exception:
      parser_mediator.ProduceParseError((
          u'unable to read event identifier from event record: {0:d} '
          u'with error: {1:s}').format(record_index, exception))

      event_identifier = None

    try:
      event_identifier_qualifiers = evtx_record.event_identifier_qualifiers
    except OverflowError as exception:
      parser_mediator.ProduceParseError((
          u'unable to read event identifier qualifiers from event record: '
          u'{0:d} with error: {1:s}').format(record_index, exception))

      event_identifier_qualifiers = None

    try:
      written_time = evtx_record.get_written_time_as_integer()
    except OverflowError as exception:
      parser_mediator.ProduceParseError((
          u'unable to read written time from event record: {0:d} '
          u'with error: {1:s}').format(record_index, exception))

      written_time = None

    if written_time is not None:
      event_object = WinEvtxRecordEvent(
          written_time, evtx_record, record_number, event_identifier,
          event_identifier_qualifiers, recovered=recovered)
      parser_mediator.ProduceEvent(event_object)

    # TODO: what if written_time is None.

  def ParseFileObject(self, parser_mediator, file_object, **kwargs):
    """Parses a Windows XML EventLog (EVTX) file-like object.

    Args:
      parser_mediator: a parser mediator object (instance of ParserMediator).
      file_object: a file-like object.
    """
    evtx_file = pyevtx.file()
    evtx_file.set_ascii_codepage(parser_mediator.codepage)

    try:
      evtx_file.open_file_object(file_object)
    except IOError as exception:
      parser_mediator.ProduceParseError(
          u'unable to open file with error: {0:s}'.format(exception))
      return

    for record_index, evtx_record in enumerate(evtx_file.records):
      try:
        self._ParseRecord(parser_mediator, record_index, evtx_record)
      except IOError as exception:
        parser_mediator.ProduceParseError(
            u'unable to parse event record: {0:d} with error: {1:s}'.format(
                record_index, exception))

    for record_index, evtx_record in enumerate(evtx_file.recovered_records):
      try:
        self._ParseRecord(
            parser_mediator, record_index, evtx_record, recovered=True)
      except IOError as exception:
        parser_mediator.ProduceParseError((
            u'unable to parse recovered event record: {0:d} with error: '
            u'{1:s}').format(record_index, exception))

    evtx_file.close()


manager.ParsersManager.RegisterParser(WinEvtxParser)
