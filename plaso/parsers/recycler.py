# -*- coding: utf-8 -*-
"""Parser for Windows Recycle files, INFO2 and $I/$R pairs."""

import construct

from plaso.events import time_events
from plaso.lib import binary
from plaso.lib import errors
from plaso.lib import eventdata
from plaso.parsers import interface
from plaso.parsers import manager


class WinRecycleEvent(time_events.FiletimeEvent):
  """Convenience class for a Windows Recycle Bin event object."""

  DATA_TYPE = u'windows:metadata:deleted_item'

  def __init__(
      self, filetime, filename_string, filename_utf, record_information,
      record_size, encoding=None):
    """Initializes the event object.

    Args:
      filetime: the FILETIME timestamp value.
      filename_string: the short filename as an extended ASCII string (codepage
                      encoded).
      filename_utf: the filename in Unicode.
      record_information: the record information (instance of
                          construct.Struct).
      record_size: the size of the record.
      encoding: optional codepage used to encode the string with.
    """
    # TODO: pass values directly instead of reading record.
    super(WinRecycleEvent, self).__init__(
        filetime, eventdata.EventTimestamp.DELETED_TIME)

    if u'index' in record_information:
      self.index = record_information.get(u'index', 0)
      self.offset = record_size * self.index
    else:
      self.offset = 0

    self.drive_number = record_information.get(u'drive', None)
    self.file_size = record_information.get(u'filesize', 0)

    if filename_string and encoding:
      try:
        short_filename = filename_string.decode(encoding)
      except UnicodeDecodeError:
        short_filename = filename_string.decode(encoding, errors=u'ignore')
    elif filename_string:
      short_filename = repr(filename_string)
    else:
      short_filename = u''

    if filename_utf:
      self.orig_filename = filename_utf
      if filename_utf != short_filename:
        self.short_filename = short_filename
    else:
      self.orig_filename = short_filename


class WinRecycleBinParser(interface.FileObjectParser):
  """Parses the Windows $Recycle.Bin $I files."""

  NAME = u'recycle_bin'
  DESCRIPTION = u'Parser for Windows $Recycle.Bin $I files.'

  # Define a list of all structs needed.
  # Struct read from:
  # https://code.google.com/p/rifiuti2/source/browse/trunk/src/rifiuti-vista.h
  RECORD_STRUCT = construct.Struct(
      u'record',
      construct.ULInt64(u'filesize'),
      construct.ULInt64(u'filetime'))

  MAGIC_STRUCT = construct.ULInt64(u'magic')

  def ParseFileObject(self, parser_mediator, file_object, **kwargs):
    """Parses a Windows RecycleBin $Ixx file-like object.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      file_object: A file-like object.

    Raises:
      UnableToParseFile: when the file cannot be parsed.
    """
    try:
      magic_header = self.MAGIC_STRUCT.parse_stream(file_object)
    except (construct.FieldError, IOError) as exception:
      raise errors.UnableToParseFile(
          u'Unable to parse $Ixxx file with error: {0:s}'.format(exception))

    if magic_header != 1:
      raise errors.UnableToParseFile(
          u'Not an $Ixxx file, wrong magic header.')

    # We may have to rely on filenames since this header is very generic.
    # TODO: Rethink this and potentially make a better test.
    filename = parser_mediator.GetFilename()
    if not filename.startswith(u'$I'):
      raise errors.UnableToParseFile(
          u'Not an $Ixxx file, filename doesn\'t start with $I.')

    record = self.RECORD_STRUCT.parse_stream(file_object)
    filename_utf = binary.ReadUTF16Stream(file_object)

    filetime = record.get(u'filetime', 0)
    # TODO: handle missing timestamp.
    event_object = WinRecycleEvent(filetime, u'', filename_utf, record, 0)
    parser_mediator.ProduceEvent(event_object)


class WinRecyclerInfo2Parser(interface.FileObjectParser):
  """Parses the Windows Recycler INFO2 file."""

  NAME = u'recycle_bin_info2'
  DESCRIPTION = u'Parser for Windows Recycler INFO2 files.'

  # Define a list of all structs used.
  INT32_LE = construct.ULInt32(u'my_int')

  FILE_HEADER_STRUCT = construct.Struct(
      u'file_header',
      construct.Padding(8),
      construct.ULInt32(u'record_size'))

  # Struct based on (-both unicode and legacy string):
  # https://code.google.com/p/rifiuti2/source/browse/trunk/src/rifiuti.h
  RECORD_STRUCT = construct.Struct(
      u'record',
      construct.ULInt32(u'index'),
      construct.ULInt32(u'drive'),
      construct.ULInt64(u'filetime'),
      construct.ULInt32(u'filesize'))

  STRING_STRUCT = construct.CString(u'legacy_filename')

  # Define a list of needed variables.
  UNICODE_FILENAME_OFFSET = 0x11C
  RECORD_INDEX_OFFSET = 0x108

  def ParseFileObject(self, parser_mediator, file_object, **kwargs):
    """Parses a Windows Recycler INFO2 file-like object.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      file_object: A file-like object.

    Raises:
      UnableToParseFile: when the file cannot be parsed.
    """
    try:
      magic_header = self.INT32_LE.parse_stream(file_object)
    except (construct.FieldError, IOError) as exception:
      raise errors.UnableToParseFile(
          u'Unable to parse INFO2 file with error: {0:s}'.format(exception))

    if magic_header != 5:
      raise errors.UnableToParseFile(
          u'Not an INFO2 file, wrong magic header.')

    # Since this header value is really generic it is hard not to use filename
    # as an indicator too.
    # TODO: Rethink this and potentially make a better test.
    filename = parser_mediator.GetFilename()
    if not filename.startswith(u'INFO2'):
      raise errors.UnableToParseFile(
          u'Not an INFO2 file, filename isn\'t INFO2.')

    file_header = self.FILE_HEADER_STRUCT.parse_stream(file_object)

    # Limit record size to 65536 to be on the safe side.
    record_size = file_header[u'record_size']
    if record_size > 65536:
      parser_mediator.ProduceParseError((
          u'Record size: {0:d} is too large for INFO2. Defaulting to: '
          u'65535').format(record_size))
      record_size = 65535

    # If recordsize is 0x320 then we have UTF/unicode names as well.
    read_unicode_names = False
    if record_size == 0x320:
      read_unicode_names = True

    data = file_object.read(record_size)
    while data:
      if len(data) != record_size:
        break
      filename_string = self.STRING_STRUCT.parse(data[4:])
      record_information = self.RECORD_STRUCT.parse(
          data[self.RECORD_INDEX_OFFSET:])
      if read_unicode_names:
        filename_utf = binary.ReadUTF16(
            data[self.UNICODE_FILENAME_OFFSET:])
      else:
        filename_utf = u''

      filetime = record_information.get(u'filetime', 0)
      # TODO: handle missing timestamp.
      event_object = WinRecycleEvent(
          filetime, filename_string, filename_utf, record_information,
          record_size, encoding=parser_mediator.codepage)
      parser_mediator.ProduceEvent(event_object)

      data = file_object.read(record_size)


manager.ParsersManager.RegisterParsers([
    WinRecycleBinParser, WinRecyclerInfo2Parser])
