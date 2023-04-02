# -*- coding: utf-8 -*-
"""Parser for Windows Recycle files, INFO2 and $I/$R pairs."""

import os

from dfdatetime import filetime as dfdatetime_filetime

from plaso.containers import events
from plaso.lib import dtfabric_helper
from plaso.lib import errors
from plaso.parsers import interface
from plaso.parsers import manager


class WinRecycleBinEventData(events.EventData):
  """Windows Recycle Bin event data.

  Attributes:
    deletion_time (dfdatetime.DateTimeValues): file entry deletion date
        and time.
    drive_number (int): drive number.
    file_size (int): file size.
    offset (int): offset of the Recycle Bin record relative to the start of
        the file, from which the event data was extracted.
    original_filename (str): filename.
    record_index (int): index of the record, from which the event data was
        extracted.
    short_filename (str): short filename.
  """

  DATA_TYPE = 'windows:metadata:deleted_item'

  def __init__(self):
    """Initializes Windows Recycle Bin event data."""
    super(WinRecycleBinEventData, self).__init__(data_type=self.DATA_TYPE)
    self.deletion_time = None
    self.drive_number = None
    self.file_size = None
    self.offset = None
    self.original_filename = None
    self.record_index = None
    self.short_filename = None


class WinRecycleBinParser(
    interface.FileObjectParser, dtfabric_helper.DtFabricHelper):
  """Parses the Windows $Recycle.Bin $I files."""

  NAME = 'recycle_bin'
  DATA_FORMAT = 'Windows $Recycle.Bin $I file'

  _DEFINITION_FILE = os.path.join(
      os.path.dirname(__file__), 'recycler.yaml')

  _SUPPORTED_FORMAT_VERSIONS = (1, 2)

  def _ParseOriginalFilename(self, file_object, format_version):
    """Parses the original filename.

    Args:
      file_object (FileIO): file-like object.
      format_version (int): format version.

    Returns:
      str: filename or None on error.

    Raises:
      ParseError: if the original filename cannot be read.
    """
    file_offset = file_object.tell()

    if format_version == 1:
      data_type_map = self._GetDataTypeMap(
          'recycle_bin_metadata_utf16le_string')
    else:
      data_type_map = self._GetDataTypeMap(
          'recycle_bin_metadata_utf16le_string_with_size')

    try:
      original_filename, _ = self._ReadStructureFromFileObject(
          file_object, file_offset, data_type_map)
    except (ValueError, errors.ParseError) as exception:
      raise errors.ParseError(
          'Unable to parse original filename with error: {0!s}'.format(
              exception))

    if format_version == 1:
      return original_filename.rstrip('\x00')

    return original_filename.string.rstrip('\x00')

  def ParseFileObject(self, parser_mediator, file_object):
    """Parses a Windows Recycle.Bin metadata ($I) file-like object.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      file_object (dfvfs.FileIO): file-like object.

    Raises:
      WrongParser: when the file cannot be parsed.
    """
    # We may have to rely on filenames since this header is very generic.

    # TODO: Rethink this and potentially make a better test.
    filename = parser_mediator.GetFilename()
    if not filename.startswith('$I'):
      raise errors.WrongParser('Filename must start with $I.')

    file_header_map = self._GetDataTypeMap('recycle_bin_metadata_file_header')

    try:
      file_header, _ = self._ReadStructureFromFileObject(
          file_object, 0, file_header_map)
    except (ValueError, errors.ParseError) as exception:
      raise errors.WrongParser((
          'Unable to parse Windows Recycle.Bin metadata file header with '
          'error: {0!s}').format(exception))

    if file_header.format_version not in self._SUPPORTED_FORMAT_VERSIONS:
      raise errors.WrongParser(
          'Unsupported format version: {0:d}.'.format(
              file_header.format_version))

    event_data = WinRecycleBinEventData()
    event_data.file_size = file_header.original_file_size

    try:
      event_data.original_filename = self._ParseOriginalFilename(
          file_object, file_header.format_version)
    except (ValueError, errors.ParseError) as exception:
      parser_mediator.ProduceExtractionWarning(
          'unable to parse original filename with error: {0!s}.'.format(
              exception))

    if file_header.deletion_time:
      event_data.deletion_time = dfdatetime_filetime.Filetime(
          timestamp=file_header.deletion_time)

    parser_mediator.ProduceEventData(event_data)


class WinRecyclerInfo2Parser(
    interface.FileObjectParser, dtfabric_helper.DtFabricHelper):
  """Parses the Windows Recycler INFO2 file."""

  NAME = 'recycle_bin_info2'
  DATA_FORMAT = 'Windows Recycler INFO2 file'

  _DEFINITION_FILE = os.path.join(
      os.path.dirname(__file__), 'recycler.yaml')

  _RECORD_INDEX_OFFSET = 0x104
  _UNICODE_FILENAME_OFFSET = 0x118

  def _ParseInfo2Record(
      self, parser_mediator, file_object, record_offset, record_size):
    """Parses an INFO-2 record.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      file_object (dfvfs.FileIO): file-like object.
      record_offset (int): record offset.
      record_size (int): record size.

    Raises:
      ParseError: if the record cannot be read.
    """
    record_data = self._ReadData(file_object, record_offset, record_size)

    record_map = self._GetDataTypeMap('recycler_info2_file_entry')

    try:
      record = self._ReadStructureFromByteStream(
          record_data, record_offset, record_map)
    except (ValueError, errors.ParseError) as exception:
      raise errors.ParseError((
          'Unable to map record data at offset: 0x{0:08x} with error: '
          '{1!s}').format(record_offset, exception))

    code_page = parser_mediator.GetCodePage()

    # The original filename can contain remnant data after the end-of-string
    # character.
    ascii_filename = record.original_filename.split(b'\x00')[0]

    try:
      ascii_filename = ascii_filename.decode(code_page)
    except UnicodeDecodeError:
      ascii_filename = ascii_filename.decode(code_page, errors='replace')

      parser_mediator.ProduceExtractionWarning(
          'unable to decode original filename.')

    unicode_filename = None
    if record_size > 280:
      record_offset += 280
      utf16_string_map = self._GetDataTypeMap(
          'recycler_info2_file_entry_utf16le_string')

      try:
        unicode_filename = self._ReadStructureFromByteStream(
            record_data[280:], record_offset, utf16_string_map)
      except (ValueError, errors.ParseError) as exception:
        raise errors.ParseError((
            'Unable to map record data at offset: 0x{0:08x} with error: '
            '{1!s}').format(record_offset, exception))

    event_data = WinRecycleBinEventData()
    event_data.drive_number = record.drive_number
    event_data.original_filename = unicode_filename or ascii_filename
    event_data.file_size = record.original_file_size
    event_data.offset = record_offset
    event_data.record_index = record.index

    if ascii_filename != unicode_filename:
      event_data.short_filename = ascii_filename

    if record.deletion_time:
      event_data.deletion_time = dfdatetime_filetime.Filetime(
          timestamp=record.deletion_time)

    parser_mediator.ProduceEventData(event_data)

  def ParseFileObject(self, parser_mediator, file_object):
    """Parses a Windows Recycler INFO2 file-like object.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      file_object (dfvfs.FileIO): file-like object.

    Raises:
      WrongParser: when the file cannot be parsed.
    """
    # Since this header value is really generic it is hard not to use filename
    # as an indicator too.

    # TODO: Rethink this and potentially make a better test.
    filename = parser_mediator.GetFilename()
    if not filename.startswith('INFO2'):
      return

    file_header_map = self._GetDataTypeMap('recycler_info2_file_header')

    try:
      file_header, _ = self._ReadStructureFromFileObject(
          file_object, 0, file_header_map)
    except (ValueError, errors.ParseError) as exception:
      raise errors.WrongParser((
          'Unable to parse Windows Recycler INFO2 file header with '
          'error: {0!s}').format(exception))

    if file_header.unknown1 != 5:
      parser_mediator.ProduceExtractionWarning('unsupported format signature.')
      return

    file_entry_size = file_header.file_entry_size
    if file_entry_size not in (280, 800):
      parser_mediator.ProduceExtractionWarning(
          'unsupported file entry size: {0:d}'.format(file_entry_size))
      return

    file_offset = file_object.get_offset()
    file_size = file_object.get_size()

    while file_offset < file_size:
      self._ParseInfo2Record(
          parser_mediator, file_object, file_offset, file_entry_size)

      file_offset += file_entry_size


manager.ParsersManager.RegisterParsers([
    WinRecycleBinParser, WinRecyclerInfo2Parser])
