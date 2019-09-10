# -*- coding: utf-8 -*-
"""Parser for Windows XML EventLog (EVTX) files."""

from __future__ import unicode_literals

from collections import namedtuple

import pyevtx

from defusedxml import ElementTree
from dfdatetime import filetime as dfdatetime_filetime
from dfdatetime import semantic_time as dfdatetime_semantic_time
from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.lib import py2to3
from plaso.lib import specification
from plaso.parsers import interface
from plaso.parsers import manager


class WinEvtxRecordEventData(events.EventData):
  """Windows XML EventLog (EVTX) record event data.

  Attributes:
    computer_name (str): computer name stored in the event record.
    event_identifier (int): event identifier.
    event_level (int): event level.
    message_identifier (int): event message identifier.
    record_number (int): event record number.
    recovered (bool): True if the record was recovered.
    source_name (str): name of the event source.
    strings (list[str]): event strings.
    strings_parsed ([dict]): parsed information from event strings.
    user_sid (str): user security identifier (SID) stored in the event record.
    xml_string (str): XML representation of the event.
  """

  DATA_TYPE = 'windows:evtx:record'

  def __init__(self):
    """Initializes event data."""
    super(WinEvtxRecordEventData, self).__init__(data_type=self.DATA_TYPE)
    self.computer_name = None
    self.event_identifier = None
    self.event_level = None
    self.message_identifier = None
    self.record_number = None
    self.recovered = None
    self.source_name = None
    self.strings = None
    self.strings_parsed = None
    self.user_sid = None
    self.xml_string = None


class WinEvtxParser(interface.FileObjectParser):
  """Parses Windows XML EventLog (EVTX) files."""

  _INITIAL_FILE_OFFSET = None

  NAME = 'winevtx'
  DESCRIPTION = 'Parser for Windows XML EventLog (EVTX) files.'

  # Mapping from evtx_record.strings entries to meaningful names.
  # This mapping is different for each event_identifier.
  # TODO: make this more generic in context of #158.

  Rule = namedtuple('Rule', ['index', 'name'])

  _EVTX_FIELD_MAP = {
      4624: [
          Rule(0, 'source_user_id'),
          Rule(1, 'source_user_name'),
          Rule(4, 'target_user_id'),
          Rule(5, 'target_user_name'),
          Rule(11, 'target_machine_name'),
          Rule(18, 'target_machine_ip')
      ],
      4648: [
          Rule(0, 'source_user_id'),
          Rule(1, 'source_user_name'),
          Rule(5, 'target_user_name'),
          Rule(8, 'target_machine_name'),
          Rule(12, 'target_machine_ip')
      ]
  }

  def _GetCreationTimeFromXMLString(
      self, parser_mediator, record_index, xml_string):
    """Retrieves the creationg time from the XML string.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      record_index (int): event record index.
      xml_string (str): event XML string.

    Returns:
      str: creation date and time formatted as ISO 8601 or None if not
          available.
    """
    if py2to3.PY_2:
      xml_string = xml_string.encode('utf-8')

    xml_root = ElementTree.fromstring(xml_string)

    system_xml_element = xml_root.find(
        '{http://schemas.microsoft.com/win/2004/08/events/event}System')
    if system_xml_element is None:
      parser_mediator.ProduceExtractionWarning(
          'missing System XML element in event record: {0:d}'.format(
              record_index))
      return None

    time_created_xml_element = system_xml_element.find(
        '{http://schemas.microsoft.com/win/2004/08/events/event}TimeCreated')
    if time_created_xml_element is None:
      parser_mediator.ProduceExtractionWarning(
          'missing TimeCreated XML element in event record: {0:d}'.format(
              record_index))
      return None

    return time_created_xml_element.get('SystemTime')

  def _GetEventDataFromRecord(
      self, parser_mediator, record_index, evtx_record, recovered=False):
    """Extract data from a Windows XML EventLog (EVTX) record.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
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
      parser_mediator.ProduceExtractionWarning((
          'unable to read record identifier from event record: {0:d} '
          'with error: {1!s}').format(record_index, exception))

    try:
      event_identifier = evtx_record.event_identifier
    except OverflowError as exception:
      parser_mediator.ProduceExtractionWarning((
          'unable to read event identifier from event record: {0:d} '
          'with error: {1!s}').format(record_index, exception))

      event_identifier = None

    try:
      event_identifier_qualifiers = evtx_record.event_identifier_qualifiers
    except OverflowError as exception:
      parser_mediator.ProduceExtractionWarning((
          'unable to read event identifier qualifiers from event record: '
          '{0:d} with error: {1!s}').format(record_index, exception))

      event_identifier_qualifiers = None

    event_data.offset = evtx_record.offset
    event_data.recovered = recovered

    if event_identifier is not None:
      event_data.event_identifier = event_identifier

      if event_identifier_qualifiers is not None:
        event_data.message_identifier = (
            (event_identifier_qualifiers << 16) | event_identifier)

    event_data.event_level = evtx_record.event_level
    event_data.source_name = evtx_record.source_name

    # Computer name is the value stored in the event record and does not
    # necessarily corresponds with the actual hostname.
    event_data.computer_name = evtx_record.computer_name
    event_data.user_sid = evtx_record.user_security_identifier

    event_data.strings = list(evtx_record.strings)

    event_data.strings_parsed = {}
    if event_identifier in self._EVTX_FIELD_MAP.keys():
      rules = self._EVTX_FIELD_MAP.get(event_identifier, [])
      for rule in rules:
        if len(evtx_record.strings) <= rule.index:
          parser_mediator.ProduceExtractionWarning((
              'evtx_record.strings has unexpected length of {0:d} '
              '(expected at least {1:d})'.format(
                  len(evtx_record.strings), rule.index)))

        event_data.strings_parsed[rule.name] = evtx_record.strings[rule.index]

    event_data.xml_string = evtx_record.xml_string

    return event_data

  def _ParseRecord(
      self, parser_mediator, record_index, evtx_record, recovered=False):
    """Extract data from a Windows XML EventLog (EVTX) record.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      record_index (int): event record index.
      evtx_record (pyevtx.record): event record.
      recovered (Optional[bool]): True if the record was recovered.
    """
    event_data = self._GetEventDataFromRecord(
        parser_mediator, record_index, evtx_record, recovered=recovered)

    try:
      written_time = evtx_record.get_written_time_as_integer()
    except OverflowError as exception:
      parser_mediator.ProduceExtractionWarning((
          'unable to read written time from event record: {0:d} '
          'with error: {1!s}').format(record_index, exception))

      written_time = None

    if written_time is None:
      date_time = dfdatetime_semantic_time.SemanticTime('Not set')
    else:
      date_time = dfdatetime_filetime.Filetime(timestamp=written_time)

    event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_WRITTEN)
    parser_mediator.ProduceEventWithEventData(event, event_data)

    creation_time_string = self._GetCreationTimeFromXMLString(
        parser_mediator, record_index, event_data.xml_string)
    if creation_time_string:
      date_time = dfdatetime_time_elements.TimeElementsInMicroseconds()

      try:
        date_time.CopyFromStringISO8601(creation_time_string)
      except ValueError as exception:
        parser_mediator.ProduceExtractionWarning(
            'unsupported creation time: {0:s} with error: {1!s}.'.format(
                creation_time_string, exception))
        date_time = None

      if date_time:
        event = time_events.DateTimeValuesEvent(
            date_time, definitions.TIME_DESCRIPTION_CREATION)
        parser_mediator.ProduceEventWithEventData(event, event_data)

  def _ParseRecords(self, parser_mediator, evtx_file):
    """Parses Windows XML EventLog (EVTX) records.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      evtx_file (pyevt.file): Windows XML EventLog (EVTX) file.
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

      except (IOError, ElementTree.ParseError) as exception:
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
        parser_mediator.ProduceExtractionWarning((
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
          and other components, such as storage and dfvfs.
      file_object (dfvfs.FileIO): a file-like object.
    """
    evtx_file = pyevtx.file()
    evtx_file.set_ascii_codepage(parser_mediator.codepage)

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
