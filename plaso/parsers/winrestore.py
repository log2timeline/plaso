# -*- coding: utf-8 -*-
"""Parser for Windows Restore Point (rp.log) files."""

import os

from dfdatetime import filetime as dfdatetime_filetime

from plaso.containers import events
from plaso.lib import dtfabric_helper
from plaso.lib import errors
from plaso.parsers import interface
from plaso.parsers import manager


class RestorePointEventData(events.EventData):
  """Windows Restore Point event data.

  Attributes:
    creation_time (dfdatetime.DateTimeValues): creation date and time.
    description (str): description.
    restore_point_event_type (str): restore point event type.
    restore_point_type (str): restore point type.
    sequence_number (str): sequence number.
  """

  DATA_TYPE = 'windows:restore_point:info'

  def __init__(self):
    """Initializes Windows Recycle Bin event data."""
    super(RestorePointEventData, self).__init__(data_type=self.DATA_TYPE)
    self.creation_time = None
    self.description = None
    self.restore_point_event_type = None
    self.restore_point_type = None
    self.sequence_number = None


class RestorePointLogParser(
    interface.FileObjectParser, dtfabric_helper.DtFabricHelper):
  """A parser for Windows Restore Point (rp.log) files."""

  NAME = 'rplog'
  DATA_FORMAT = 'Windows Restore Point log (rp.log) file'

  FILTERS = frozenset([
      interface.FileNameFileEntryFilter('rp.log')])

  _DEFINITION_FILE = os.path.join(
      os.path.dirname(__file__), 'winrestore.yaml')

  def ParseFileObject(self, parser_mediator, file_object):
    """Parses a Windows Restore Point (rp.log) log file-like object.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      file_object (dfvfs.FileIO): file-like object.

    Raises:
      WrongParser: when the file cannot be parsed.
    """
    file_size = file_object.get_size()

    file_header_map = self._GetDataTypeMap('rp_log_file_header')

    try:
      file_header, _ = self._ReadStructureFromFileObject(
          file_object, 0, file_header_map)
    except (ValueError, errors.ParseError) as exception:
      raise errors.WrongParser(
          'Unable to parse file header with error: {0!s}'.format(exception))

    file_footer_map = self._GetDataTypeMap('rp_log_file_footer')

    file_footer_offset = file_size - 8

    try:
      file_footer, _ = self._ReadStructureFromFileObject(
          file_object, file_footer_offset, file_footer_map)
    except (ValueError, errors.ParseError) as exception:
      parser_mediator.ProduceExtractionWarning(
          'unable to parse file footer with error: {0!s}'.format(exception))
      return

    event_data = RestorePointEventData()

    # The description in the file header includes the end-of-string character
    # that we need to strip off.
    event_data.description = file_header.description.rstrip('\0')
    event_data.restore_point_event_type = file_header.event_type
    event_data.restore_point_type = file_header.restore_point_type
    event_data.sequence_number = file_header.sequence_number

    if file_footer.creation_time:
      event_data.creation_time = dfdatetime_filetime.Filetime(
          timestamp=file_footer.creation_time)

    parser_mediator.ProduceEventData(event_data)


manager.ParsersManager.RegisterParser(RestorePointLogParser)
