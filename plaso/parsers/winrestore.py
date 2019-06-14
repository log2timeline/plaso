# -*- coding: utf-8 -*-
"""Parser for Windows Restore Point (rp.log) files."""

from __future__ import unicode_literals

from dfdatetime import filetime as dfdatetime_filetime
from dfdatetime import semantic_time as dfdatetime_semantic_time

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.lib import errors
from plaso.parsers import dtfabric_parser
from plaso.parsers import interface
from plaso.parsers import manager


class RestorePointEventData(events.EventData):
  """Windows Restore Point event data.

  Attributes:
    description (str): description.
    restore_point_event_type (str): restore point event type.
    restore_point_type (str): restore point type.
    sequence_number (str): sequence number.
  """

  DATA_TYPE = 'windows:restore_point:info'

  def __init__(self):
    """Initializes Windows Recycle Bin event data."""
    super(RestorePointEventData, self).__init__(data_type=self.DATA_TYPE)
    self.description = None
    self.restore_point_event_type = None
    self.restore_point_type = None
    self.sequence_number = None


class RestorePointLogParser(dtfabric_parser.DtFabricBaseParser):
  """A parser for Windows Restore Point (rp.log) files."""

  NAME = 'rplog'
  DESCRIPTION = 'Parser for Windows Restore Point (rp.log) files.'

  FILTERS = frozenset([
      interface.FileNameFileEntryFilter('rp.log')])

  _DEFINITION_FILE = 'winrestore.yaml'

  def ParseFileObject(self, parser_mediator, file_object):
    """Parses a Windows Restore Point (rp.log) log file-like object.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      file_object (dfvfs.FileIO): file-like object.

    Raises:
      UnableToParseFile: when the file cannot be parsed.
    """
    file_size = file_object.get_size()

    file_header_map = self._GetDataTypeMap('rp_log_file_header')

    try:
      file_header, _ = self._ReadStructureFromFileObject(
          file_object, 0, file_header_map)
    except (ValueError, errors.ParseError) as exception:
      raise errors.UnableToParseFile(
          'Unable to parse file header with error: {0!s}'.format(
              exception))

    file_footer_map = self._GetDataTypeMap('rp_log_file_footer')

    file_footer_offset = file_size - file_footer_map.GetByteSize()

    try:
      file_footer, _ = self._ReadStructureFromFileObject(
          file_object, file_footer_offset, file_footer_map)
    except (ValueError, errors.ParseError) as exception:
      parser_mediator.ProduceExtractionWarning(
          'unable to parse file footer with error: {0!s}'.format(exception))
      return

    # The description in the file header includes the end-of-string character
    # that we need to strip off.
    description = file_header.description.rstrip('\0')

    if file_footer.creation_time == 0:
      date_time = dfdatetime_semantic_time.SemanticTime('Not set')
    else:
      date_time = dfdatetime_filetime.Filetime(
          timestamp=file_footer.creation_time)

    event_data = RestorePointEventData()
    event_data.description = description
    event_data.restore_point_event_type = file_header.event_type
    event_data.restore_point_type = file_header.restore_point_type
    event_data.sequence_number = file_header.sequence_number

    event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_CREATION)
    parser_mediator.ProduceEventWithEventData(event, event_data)


manager.ParsersManager.RegisterParser(RestorePointLogParser)
