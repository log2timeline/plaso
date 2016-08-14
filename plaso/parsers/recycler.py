# -*- coding: utf-8 -*-
"""Parser for Windows Recycle files, INFO2 and $I/$R pairs."""

import construct

from plaso.containers import time_events
from plaso.lib import binary
from plaso.lib import eventdata
from plaso.parsers import interface
from plaso.parsers import manager


class WinRecycleEvent(time_events.FiletimeEvent):
  """Convenience class for a Windows Recycle Bin event.

  Attributes:
    drive_number (int): drive number.
    file_size (int): file size.
    offset (int): offset of the record on which the event is based.
    original_filename (str): filename.
    record_index (int): index of the record on which the event is based.
    short_filename (str): short filename.
  """

  DATA_TYPE = u'windows:metadata:deleted_item'

  def __init__(
      self, filetime, filename, file_size, ascii_filename=None,
      drive_number=None, offset=None, record_index=None):
    """Initializes an event.

    Args:
      filetime (int): FILETIME timestamp value.
      filename (str): filename.
      file_size (int): file size.
      ascii_filename (Optional[str]): typically the short filename stored
          as an ASCII string, which is set when the INFO2 record contains
          an ASCII filename.
      drive_number (Optional[int]): drive number.
      offset (Optional[int]): offset of the record on which the event is based.
      record_index (Optional[int]): index of the record on which the event is
          based.
    """
    super(WinRecycleEvent, self).__init__(
        filetime, eventdata.EventTimestamp.DELETED_TIME)
    self.drive_number = drive_number
    self.file_size = file_size
    self.offset = offset
    self.original_filename = filename or ascii_filename
    self.record_index = record_index
    self.short_filename = ascii_filename


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

    filename = None
    if header_struct.format_version == 1:
      filename = binary.ReadUTF16Stream(file_object)

    else:
      try:
        filename_struct = self._FILENAME_V2_STRUCT.parse_stream(file_object)
        filename = binary.ReadUTF16(filename_struct.string)

      except (IOError, construct.FieldError) as exception:
        parser_mediator.ProduceExtractionError(
            u'unable to parse filename with error: {0:s}'.format(exception))
        return

    event = WinRecycleEvent(
        header_struct.deletion_time, filename, header_struct.file_size)
    parser_mediator.ProduceEvent(event)


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

    data = file_object.read(record_size)
    while len(data) == record_size:
      try:
        ascii_filename = self._ASCII_STRING.parse(data)

      except (IOError, construct.FieldError) as exception:
        parser_mediator.ProduceExtractionError((
            u'unable to parse recycler ASCII filename at offset: 0x{0:08x} '
            u'with error: {1:s}').format(record_offset, exception))

      try:
        recycler_record_struct = self._RECYCLER_RECORD_STRUCT.parse(
            data[self._RECORD_INDEX_OFFSET:])
      except (IOError, construct.FieldError) as exception:
        parser_mediator.ProduceExtractionError((
            u'unable to parse recycler index record at offset: 0x{0:08x} '
            u'with error: {1:s}').format(
                record_offset + self._RECORD_INDEX_OFFSET, exception))

      unicode_filename = None
      if record_size == 800:
        unicode_filename = binary.ReadUTF16(
            data[self._UNICODE_FILENAME_OFFSET:])

      ascii_filename = None
      if ascii_filename and parser_mediator.codepage:
        try:
          ascii_filename = ascii_filename.decode(parser_mediator.codepage)
        except UnicodeDecodeError:
          ascii_filename = ascii_filename.decode(
              parser_mediator.codepage, errors=u'replace')

      elif ascii_filename:
        ascii_filename = repr(ascii_filename)

      event = WinRecycleEvent(
          recycler_record_struct.deletion_time, unicode_filename,
          recycler_record_struct.file_size, ascii_filename=ascii_filename,
          drive_number=recycler_record_struct.drive_number,
          offset=record_offset, record_index=recycler_record_struct.index)
      parser_mediator.ProduceEvent(event)

      record_offset += record_size
      data = file_object.read(record_size)


manager.ParsersManager.RegisterParsers([
    WinRecycleBinParser, WinRecyclerInfo2Parser])
