# -*- coding: utf-8 -*-
"""Parser for Windows Recycle files, INFO2 and $I/$R pairs."""

import construct

from dfdatetime import filetime as dfdatetime_filetime
from dfdatetime import semantic_time as dfdatetime_semantic_time

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import binary
from plaso.lib import definitions
from plaso.parsers import interface
from plaso.parsers import manager


class WinRecycleBinEventData(events.EventData):
  """Windows Recycle Bin event data.

  Attributes:
    drive_number (int): drive number.
    file_size (int): file size.
    original_filename (str): filename.
    record_index (int): index of the record on which the event is based.
    short_filename (str): short filename.
  """

  DATA_TYPE = u'windows:metadata:deleted_item'

  def __init__(self):
    """Initializes Windows Recycle Bin event data."""
    super(WinRecycleBinEventData, self).__init__(data_type=self.DATA_TYPE)
    self.drive_number = None
    self.file_size = None
    self.original_filename = None
    self.record_index = None
    self.short_filename = None


class WinRecycleBinParser(interface.FileObjectParser):
  """Parses the Windows $Recycle.Bin $I files."""

  NAME = u'recycle_bin'
  DESCRIPTION = u'Parser for Windows $Recycle.Bin $I files.'

  _FILE_HEADER_STRUCT = construct.Struct(
      u'file_header',
      construct.ULInt64(u'format_version'),
      construct.ULInt64(u'file_size'),
      construct.ULInt64(u'deletion_time'))

  _FILENAME_V2_STRUCT = construct.Struct(
      u'filename_v2',
      construct.ULInt32(u'number_of_characters'),
      construct.String(
          u'string', lambda ctx: ctx.number_of_characters * 2))

  def _ReadFilename(self, parser_mediator, file_object, format_version):
    """Reads the filename.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      file_object (FileIO): file-like object.
      format_version (int): format version.

    Returns:
      str: filename
    """
    if format_version == 1:
      return binary.ReadUTF16Stream(file_object)

    try:
      filename_struct = self._FILENAME_V2_STRUCT.parse_stream(file_object)

    except (IOError, construct.FieldError) as exception:
      parser_mediator.ProduceExtractionError(
          u'unable to parse filename with error: {0:s}'.format(exception))
      return

    return binary.ReadUTF16(filename_struct.string)

  def ParseFileObject(self, parser_mediator, file_object, **kwargs):
    """Parses a Windows RecycleBin $Ixx file-like object.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      file_object (dfvfs.FileIO): file-like object.
    """
    # We may have to rely on filenames since this header is very generic.

    # TODO: Rethink this and potentially make a better test.
    filename = parser_mediator.GetFilename()
    if not filename.startswith(u'$I'):
      return

    try:
      header_struct = self._FILE_HEADER_STRUCT.parse_stream(file_object)
    except (IOError, construct.FieldError) as exception:
      parser_mediator.ProduceExtractionError(
          u'unable to parse file header with error: {0:s}'.format(exception))
      return

    if header_struct.format_version not in (1, 2):
      parser_mediator.ProduceExtractionError(
          u'unsupported format version: {0:d}.'.format(
              header_struct.format_version))
      return

    if header_struct.deletion_time == 0:
      date_time = dfdatetime_semantic_time.SemanticTime(u'Not set')
    else:
      date_time = dfdatetime_filetime.Filetime(
          timestamp=header_struct.deletion_time)

    event_data = WinRecycleBinEventData()
    event_data.original_filename = self._ReadFilename(
        parser_mediator, file_object, header_struct.format_version)
    event_data.file_size = header_struct.file_size

    event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_DELETED)
    parser_mediator.ProduceEventWithEventData(event, event_data)


class WinRecyclerInfo2Parser(interface.FileObjectParser):
  """Parses the Windows Recycler INFO2 file."""

  NAME = u'recycle_bin_info2'
  DESCRIPTION = u'Parser for Windows Recycler INFO2 files.'

  _FILE_HEADER_STRUCT = construct.Struct(
      u'file_header',
      construct.ULInt32(u'unknown1'),
      construct.ULInt32(u'unknown2'),
      construct.ULInt32(u'unknown3'),
      construct.ULInt32(u'record_size'),
      construct.ULInt32(u'unknown4'))

  _RECYCLER_RECORD_STRUCT = construct.Struct(
      u'recycler_record',
      construct.ULInt32(u'index'),
      construct.ULInt32(u'drive_number'),
      construct.ULInt64(u'deletion_time'),
      construct.ULInt32(u'file_size'))

  _ASCII_STRING = construct.CString(u'string')

  _RECORD_INDEX_OFFSET = 0x104
  _UNICODE_FILENAME_OFFSET = 0x118

  def _ParseRecord(
      self, parser_mediator, file_object, record_offset, record_size):
    """Parses an INFO-2 record.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      file_object (dfvfs.FileIO): file-like object.
      record_offset (int): record offset.
      record_size (int): record size.
    """
    record_data = file_object.read(record_size)

    try:
      ascii_filename = self._ASCII_STRING.parse(record_data)

    except (IOError, construct.FieldError) as exception:
      parser_mediator.ProduceExtractionError((
          u'unable to parse recycler ASCII filename at offset: 0x{0:08x} '
          u'with error: {1:s}').format(record_offset, exception))

    try:
      recycler_record_struct = self._RECYCLER_RECORD_STRUCT.parse(
          record_data[self._RECORD_INDEX_OFFSET:])
    except (IOError, construct.FieldError) as exception:
      parser_mediator.ProduceExtractionError((
          u'unable to parse recycler index record at offset: 0x{0:08x} '
          u'with error: {1:s}').format(
              record_offset + self._RECORD_INDEX_OFFSET, exception))

    unicode_filename = None
    if record_size == 800:
      unicode_filename = binary.ReadUTF16(
          record_data[self._UNICODE_FILENAME_OFFSET:])

    ascii_filename = None
    if ascii_filename and parser_mediator.codepage:
      try:
        ascii_filename = ascii_filename.decode(parser_mediator.codepage)
      except UnicodeDecodeError:
        ascii_filename = ascii_filename.decode(
            parser_mediator.codepage, errors=u'replace')

    elif ascii_filename:
      ascii_filename = repr(ascii_filename)

    if recycler_record_struct.deletion_time == 0:
      date_time = dfdatetime_semantic_time.SemanticTime(u'Not set')
    else:
      date_time = dfdatetime_filetime.Filetime(
          timestamp=recycler_record_struct.deletion_time)

    event_data = WinRecycleBinEventData()
    event_data.drive_number = recycler_record_struct.drive_number
    event_data.original_filename = unicode_filename or ascii_filename
    event_data.file_size = recycler_record_struct.file_size
    event_data.offset = record_offset
    event_data.record_index = recycler_record_struct.index
    event_data.short_filename = ascii_filename

    event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_DELETED)
    parser_mediator.ProduceEventWithEventData(event, event_data)

  def ParseFileObject(self, parser_mediator, file_object, **kwargs):
    """Parses a Windows Recycler INFO2 file-like object.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      file_object (dfvfs.FileIO): file-like object.
    """
    # Since this header value is really generic it is hard not to use filename
    # as an indicator too.

    # TODO: Rethink this and potentially make a better test.
    filename = parser_mediator.GetFilename()
    if not filename.startswith(u'INFO2'):
      return

    try:
      file_header_struct = self._FILE_HEADER_STRUCT.parse_stream(file_object)
    except (construct.FieldError, IOError) as exception:
      parser_mediator.ProduceExtractionError(
          u'unable to parse file header with error: {0:s}'.format(exception))
      return

    if file_header_struct.unknown1 != 5:
      parser_mediator.ProduceExtractionError(u'unsupport format signature.')
      return

    record_size = file_header_struct.record_size
    if record_size not in (280, 800):
      parser_mediator.ProduceExtractionError(
          u'unsupported record size: {0:d}'.format(record_size))
      return

    record_offset = self._FILE_HEADER_STRUCT.sizeof()
    file_size = file_object.get_size()

    while record_offset < file_size:
      self._ParseRecord(
          parser_mediator, file_object, record_offset, record_size)

      record_offset += record_size


manager.ParsersManager.RegisterParsers([
    WinRecycleBinParser, WinRecyclerInfo2Parser])
