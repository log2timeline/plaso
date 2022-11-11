# -*- coding: utf-8 -*-
"""Parser for Systemd journal files."""

import lzma
import os

from dfdatetime import posix_time as dfdatetime_posix_time

from lz4 import block as lz4_block

from plaso.containers import events
from plaso.lib import dtfabric_helper
from plaso.lib import errors
from plaso.lib import specification
from plaso.parsers import interface
from plaso.parsers import manager


class SystemdJournalEventData(events.EventData):
  """Systemd journal event data.

  Attributes:
    body (str): message body.
    hostname (str): hostname.
    pid (int): process identifier (PID).
    reporter (str): reporter.
    written_time (dfdatetime.DateTimeValues): date and time the log entry
        was written.
  """

  DATA_TYPE = 'systemd:journal'

  def __init__(self):
    """Initializes event data."""
    super(SystemdJournalEventData, self).__init__(data_type=self.DATA_TYPE)
    self.body = None
    self.hostname = None
    self.pid = None
    self.reporter = None
    self.written_time = None


class SystemdJournalParser(
    interface.FileObjectParser, dtfabric_helper.DtFabricHelper):
  """Parses Systemd Journal files."""

  NAME = 'systemd_journal'
  DATA_FORMAT = 'Systemd journal file'

  _DEFINITION_FILE = os.path.join(
      os.path.dirname(__file__), 'systemd_journal.yaml')

  _OBJECT_COMPRESSED_FLAG_XZ = 1
  _OBJECT_COMPRESSED_FLAG_LZ4 = 2

  _OBJECT_TYPE_UNUSED = 0
  _OBJECT_TYPE_DATA = 1
  _OBJECT_TYPE_FIELD = 2
  _OBJECT_TYPE_ENTRY = 3
  _OBJECT_TYPE_DATA_HASH_TABLE = 4
  _OBJECT_TYPE_FIELD_HASH_TABLE = 5
  _OBJECT_TYPE_ENTRY_ARRAY = 6
  _OBJECT_TYPE_TAG = 7

  _SUPPORTED_FILE_HEADER_SIZES = frozenset([208, 224, 240])

  def __init__(self):
    """Initializes a parser."""
    super(SystemdJournalParser, self).__init__()
    self._maximum_journal_file_offset = 0

  def _ParseDataObject(self, file_object, file_offset):
    """Parses a data object.

    Args:
      file_object (dfvfs.FileIO): a file-like object.
      file_offset (int): offset of the data object relative to the start
          of the file-like object.

    Returns:
      bytes: data.

    Raises:
      ParseError: if the data object cannot be parsed.
    """
    data_object_map = self._GetDataTypeMap('systemd_journal_data_object')

    try:
      data_object, _ = self._ReadStructureFromFileObject(
          file_object, file_offset, data_object_map)
    except (ValueError, errors.ParseError) as exception:
      raise errors.ParseError((
          'Unable to parse data object at offset: 0x{0:08x} with error: '
          '{1!s}').format(file_offset, exception))

    if data_object.object_type != self._OBJECT_TYPE_DATA:
      raise errors.ParseError('Unsupported object type: {0:d}.'.format(
          data_object.object_type))

    if data_object.object_flags not in (
        0, self._OBJECT_COMPRESSED_FLAG_XZ, self._OBJECT_COMPRESSED_FLAG_LZ4):
      raise errors.ParseError('Unsupported object flags: 0x{0:02x}.'.format(
          data_object.object_flags))

    # The data is read separately for performance reasons.
    data_size = data_object.data_size - 64
    data = file_object.read(data_size)

    if data_object.object_flags & self._OBJECT_COMPRESSED_FLAG_XZ:
      data = lzma.decompress(data)

    elif data_object.object_flags & self._OBJECT_COMPRESSED_FLAG_LZ4:
      uncompressed_size_map = self._GetDataTypeMap('uint32le')

      try:
        uncompressed_size = self._ReadStructureFromByteStream(
            data, file_offset + 64, uncompressed_size_map)
      except (ValueError, errors.ParseError) as exception:
        raise errors.ParseError((
            'Unable to parse LZ4 uncompressed size at offset: 0x{0:08x} with '
            'error: {1!s}').format(file_offset + 64, exception))

      data = lz4_block.decompress(data[8:], uncompressed_size=uncompressed_size)

    return data

  def _ParseEntryArrayObject(self, file_object, file_offset):
    """Parses an entry array object.

    Args:
      file_object (dfvfs.FileIO): a file-like object.
      file_offset (int): offset of the entry array object relative to the start
          of the file-like object.

    Returns:
      systemd_journal_entry_array_object: entry array object.

    Raises:
      ParseError: if the entry array object cannot be parsed.
    """
    entry_array_object_map = self._GetDataTypeMap(
        'systemd_journal_entry_array_object')

    try:
      entry_array_object, _ = self._ReadStructureFromFileObject(
          file_object, file_offset, entry_array_object_map)
    except (ValueError, errors.ParseError) as exception:
      raise errors.ParseError((
          'Unable to parse entry array object at offset: 0x{0:08x} with error: '
          '{1!s}').format(file_offset, exception))

    if entry_array_object.object_type != self._OBJECT_TYPE_ENTRY_ARRAY:
      raise errors.ParseError('Unsupported object type: {0:d}.'.format(
          entry_array_object.object_type))

    if entry_array_object.object_flags != 0:
      raise errors.ParseError('Unsupported object flags: 0x{0:02x}.'.format(
          entry_array_object.object_flags))

    return entry_array_object

  def _ParseEntryObject(self, file_object, file_offset):
    """Parses an entry object.

    Args:
      file_object (dfvfs.FileIO): a file-like object.
      file_offset (int): offset of the entry object relative to the start
          of the file-like object.

    Returns:
      systemd_journal_entry_object: entry object.

    Raises:
      ParseError: if the entry object cannot be parsed.
    """
    entry_object_map = self._GetDataTypeMap('systemd_journal_entry_object')

    try:
      entry_object, _ = self._ReadStructureFromFileObject(
          file_object, file_offset, entry_object_map)
    except (ValueError, errors.ParseError) as exception:
      raise errors.ParseError((
          'Unable to parse entry object at offset: 0x{0:08x} with error: '
          '{1!s}').format(file_offset, exception))

    if entry_object.object_type != self._OBJECT_TYPE_ENTRY:
      raise errors.ParseError('Unsupported object type: {0:d}.'.format(
          entry_object.object_type))

    if entry_object.object_flags != 0:
      raise errors.ParseError('Unsupported object flags: 0x{0:02x}.'.format(
          entry_object.object_flags))

    return entry_object

  def _ParseEntryObjectOffsets(self, file_object, file_offset):
    """Parses entry array objects for the offset of the entry objects.

    Args:
      file_object (dfvfs.FileIO): a file-like object.
      file_offset (int): offset of the first entry array object relative to
          the start of the file-like object.

    Returns:
      list[int]: offsets of the entry objects.
    """
    entry_array_object = self._ParseEntryArrayObject(file_object, file_offset)

    entry_object_offsets = list(entry_array_object.entry_object_offsets)
    while entry_array_object.next_entry_array_offset != 0:
      entry_array_object = self._ParseEntryArrayObject(
          file_object, entry_array_object.next_entry_array_offset)
      entry_object_offsets.extend(entry_array_object.entry_object_offsets)

    return entry_object_offsets

  def _ParseJournalEntry(self, file_object, file_offset):
    """Parses a journal entry.

    This method will generate an event per ENTRY object.

    Args:
      file_object (dfvfs.FileIO): a file-like object.
      file_offset (int): offset of the entry object relative to the start
          of the file-like object.

    Returns:
      dict[str, objects]: entry items per key.

    Raises:
      ParseError: when an object offset is out of bounds.
    """
    entry_object = self._ParseEntryObject(file_object, file_offset)

    # The data is read separately for performance reasons.
    entry_item_map = self._GetDataTypeMap('systemd_journal_entry_item')

    file_offset += 64
    data_end_offset = file_offset + entry_object.data_size - 64

    fields = {'real_time': entry_object.real_time}

    while file_offset < data_end_offset:
      try:
        entry_item, entry_item_data_size = self._ReadStructureFromFileObject(
            file_object, file_offset, entry_item_map)
      except (ValueError, errors.ParseError) as exception:
        raise errors.ParseError((
            'Unable to parse entry item at offset: 0x{0:08x} with error: '
            '{1!s}').format(file_offset, exception))

      file_offset += entry_item_data_size

      if entry_item.object_offset < self._maximum_journal_file_offset:
        raise errors.ParseError(
            'object offset should be after hash tables ({0:d} < {1:d})'.format(
                entry_item.object_offset, self._maximum_journal_file_offset))

      event_data = self._ParseDataObject(file_object, entry_item.object_offset)
      event_string = event_data.decode('utf-8')
      key, value = event_string.split('=', 1)
      fields[key] = value

    return fields

  @classmethod
  def GetFormatSpecification(cls):
    """Retrieves the format specification.

    Returns:
      FormatSpecification: format specification.
    """
    format_specification = specification.FormatSpecification(cls.NAME)
    format_specification.AddNewSignature(b'LPKSHHRH', offset=0)
    return format_specification

  def ParseFileObject(self, parser_mediator, file_object):
    """Parses a Systemd journal file-like object.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      file_object (dfvfs.FileIO): a file-like object.

    Raises:
      WrongParser: when the header cannot be parsed.
    """
    file_header_map = self._GetDataTypeMap('systemd_journal_file_header')

    try:
      file_header, _ = self._ReadStructureFromFileObject(
          file_object, 0, file_header_map)
    except (ValueError, errors.ParseError) as exception:
      raise errors.WrongParser(
          'Unable to parse file header with error: {0!s}'.format(
              exception))

    if file_header.header_size not in self._SUPPORTED_FILE_HEADER_SIZES:
      raise errors.WrongParser(
          'Unsupported file header size: {0:d}.'.format(
              file_header.header_size))

    data_hash_table_end_offset = (
        file_header.data_hash_table_offset +
        file_header.data_hash_table_size)
    field_hash_table_end_offset = (
        file_header.field_hash_table_offset +
        file_header.field_hash_table_size)
    self._maximum_journal_file_offset = max(
        data_hash_table_end_offset, field_hash_table_end_offset)

    entry_object_offsets = self._ParseEntryObjectOffsets(
        file_object, file_header.entry_array_offset)

    for entry_object_offset in entry_object_offsets:
      if entry_object_offset == 0:
        continue

      try:
        fields = self._ParseJournalEntry(file_object, entry_object_offset)
      except errors.ParseError as exception:
        parser_mediator.ProduceExtractionWarning((
            'Unable to parse journal entry at offset: 0x{0:08x} with '
            'error: {1!s}').format(entry_object_offset, exception))
        return

      date_time = dfdatetime_posix_time.PosixTimeInMicroseconds(
          timestamp=fields['real_time'])

      event_data = SystemdJournalEventData()

      event_data.body = fields.get('MESSAGE', None)
      event_data.hostname = fields.get('_HOSTNAME', None)
      event_data.reporter = fields.get('SYSLOG_IDENTIFIER', None)
      event_data.written_time = date_time

      if event_data.reporter and event_data.reporter != 'kernel':
        event_data.pid = fields.get('_PID', fields.get('SYSLOG_PID', None))

      parser_mediator.ProduceEventData(event_data)


manager.ParsersManager.RegisterParser(SystemdJournalParser)
