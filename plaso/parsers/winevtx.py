# -*- coding: utf-8 -*-
"""Parser for Windows XML EventLog (EVTX) files."""

import logging

import pyevtx

from plaso.events import time_events
from plaso.lib import errors
from plaso.lib import eventdata
from plaso.parsers import interface
from plaso.parsers import manager


if pyevtx.get_version() < '20141112':
  raise ImportWarning('WinEvtxParser requires at least pyevtx 20141112.')


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
      event_identifier = evtx_record.event_identifier
    except OverflowError as exception:
      event_identifier = None
      logging.warning(
          u'Unable to assign the event identifier with error: {0:s}.'.format(
              exception))

    try:
      event_identifier_qualifiers = evtx_record.event_identifier_qualifiers
    except OverflowError as exception:
      event_identifier_qualifiers = None
      logging.warning((
          u'Unable to assign the event identifier qualifiers with error: '
          u'{0:s}.').format(exception))

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


class WinEvtxParser(interface.BaseParser):
  """Parses Windows XML EventLog (EVTX) files."""

  NAME = 'winevtx'
  DESCRIPTION = u'Parser for Windows XML EventLog (EVTX) files.'

  def Parse(self, parser_mediator, **kwargs):
    """Extract data from a Windows XML EventLog (EVTX) file.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).

    Raises:
      UnableToParseFile: when the file cannot be parsed.
    """


    file_object = parser_mediator.GetFileObject()
    evtx_file = pyevtx.file()
    evtx_file.set_ascii_codepage(parser_mediator.codepage)

    try:
      evtx_file.open_file_object(file_object)
    except IOError as exception:
      evtx_file.close()
      file_object.close()
      raise errors.UnableToParseFile(
          u'[{0:s}] unable to parse file {1:s} with error: {2:s}'.format(
              self.NAME, parser_mediator.GetDisplayName(), exception))

    for record_index in range(0, evtx_file.number_of_records):
      try:
        evtx_record = evtx_file.get_record(record_index)
        event_object = WinEvtxRecordEvent(evtx_record)
        parser_mediator.ProduceEvent(event_object)
      except IOError as exception:
        logging.warning((
            u'[{0:s}] unable to parse event record: {1:d} in file: {2:s} '
            u'with error: {3:s}').format(
                self.NAME, record_index, parser_mediator.GetDisplayName(),
                exception))

    for record_index in range(0, evtx_file.number_of_recovered_records):
      try:
        evtx_record = evtx_file.get_recovered_record(record_index)
        event_object = WinEvtxRecordEvent(evtx_record, recovered=True)
        parser_mediator.ProduceEvent(event_object)
      except IOError as exception:
        logging.debug((
            u'[{0:s}] unable to parse recovered event record: {1:d} in file: '
            u'{2:s} with error: {3:s}').format(
                self.NAME, record_index, parser_mediator.GetDisplayName(),
                exception))

    evtx_file.close()
    file_object.close()


manager.ParsersManager.RegisterParser(WinEvtxParser)
