# -*- coding: utf-8 -*-
"""Parser for Systemd journal files."""

from __future__ import unicode_literals

import os

import construct

from dfdatetime import posix_time as dfdatetime_posix_time

try:
  import lzma
except ImportError:
  from backports import lzma

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.lib import errors
from plaso.parsers import interface
from plaso.parsers import manager


class SystemdJournalEventData(events.EventData):
  """Systemd journal event data.

  Attributes:
    body (str): message body.
    hostname (str): hostname.
    pid (int): process identifier (PID).
    reporter (str): reporter.
  """

  DATA_TYPE = 'systemd:journal'

  def __init__(self):
    """Initializes event data."""
    super(SystemdJournalEventData, self).__init__(data_type=self.DATA_TYPE)
    self.body = None
    self.hostname = None
    self.pid = None
    self.reporter = None


class SystemdJournalParser(interface.FileObjectParser):
  """Parses Systemd Journal files."""

  NAME = 'systemd_journal'

  DESCRIPTION = 'Parser for Systemd Journal files.'

  _OBJECT_COMPRESSED_FLAG = 0x00000001

  # Unfortunately this doesn't help us knowing about the "dirtiness" or
  # "corrupted" file state.
  # A file can be in any of these states and still be corrupted, for example, by
  # an unexpected shut down. Once journald detects one of these, it will
  # "rotate" the corrupted journal file, an store it away, and change the status
  # to STATE_OFFLINE.
  # STATE_ONLINE means the file wasn't closed, but the journal can still be in a
  # clean state.
  _JOURNAL_STATE = construct.Enum(
      construct.ULInt8('state'),
      STATE_OFFLINE=0,
      STATE_ONLINE=1,
      STATE_ARCHIVED=2
  )

  _OBJECT_HEADER_TYPE = construct.Enum(
      construct.ULInt8('type'),
      UNUSED=0,
      DATA=1,
      FIELD=2,
      ENTRY=3,
      DATA_HASH_TABLE=4,
      FIELD_HASH_TABLE=5,
      ENTRY_ARRAY=6,
      TAG=7
  )

  _ULInt64 = construct.ULInt64('int')

  _OBJECT_HEADER = construct.Struct(
      'object_header',
      _OBJECT_HEADER_TYPE,
      construct.ULInt8('flags'),
      construct.Bytes('reserved', 6),
      construct.ULInt64('size')
  )

  _OBJECT_HEADER_SIZE = _OBJECT_HEADER.sizeof()

  _DATA_OBJECT = construct.Struct(
      'data_object',
      construct.ULInt64('hash'),
      construct.ULInt64('next_hash_offset'),
      construct.ULInt64('next_field_offset'),
      construct.ULInt64('entry_offset'),
      construct.ULInt64('entry_array_offset'),
      construct.ULInt64('n_entries')
  )

  _DATA_OBJECT_SIZE = _DATA_OBJECT.sizeof()

  _ENTRY_ITEM = construct.Struct(
      'entry_item',
      construct.ULInt64('object_offset'),
      construct.ULInt64('hash')
  )

  _ENTRY_OBJECT = construct.Struct(
      'entry_object',
      construct.ULInt64('seqnum'),
      construct.ULInt64('realtime'),
      construct.ULInt64('monotonic'),
      construct.Struct(
          'boot_id',
          construct.Bytes('bytes', 16),
          construct.ULInt64('qword1'),
          construct.ULInt64('qword2')),
      construct.ULInt64('xor_hash'),
      construct.Rename('object_items', construct.GreedyRange(_ENTRY_ITEM))
  )

  _JOURNAL_HEADER = construct.Struct(
      'journal_header',
      construct.Const(construct.String('signature', 8), b'LPKSHHRH'),
      construct.ULInt32('compatible_flags'),
      construct.ULInt32('incompatible_flags'),
      _JOURNAL_STATE,
      construct.Bytes('reserved', 7),
      construct.Bytes('file_id', 16),
      construct.Bytes('machine_id', 16),
      construct.Bytes('boot_id', 16),
      construct.Bytes('seqnum_id', 16),
      construct.ULInt64('header_size'),
      construct.ULInt64('arena_size'),
      construct.ULInt64('data_hash_table_offset'),
      construct.ULInt64('data_hash_table_size'),
      construct.ULInt64('field_hash_table_offset'),
      construct.ULInt64('field_hash_table_size'),
      construct.ULInt64('tail_object_offset'),
      construct.ULInt64('n_objects'),
      construct.ULInt64('n_entries'),
      construct.ULInt64('tail_entry_seqnum'),
      construct.ULInt64('head_entry_seqnum'),
      construct.ULInt64('entry_array_offset'),
      construct.ULInt64('head_entry_realtime'),
      construct.ULInt64('tail_entry_realtime'),
      construct.ULInt64('tail_entry_monotonic'),
      # Added in format version 187
      construct.ULInt64('n_data'),
      construct.ULInt64('n_fields'),
      # Added in format version 189
      construct.ULInt64('n_tags'),
      construct.ULInt64('n_entry_arrays')
  )

  def __init__(self):
    """Initializes a parser object."""
    super(SystemdJournalParser, self).__init__()
    self._max_journal_file_offset = 0

  def _ParseObjectHeader(self, file_object, offset):
    """Parses a Systemd journal object header structure.

    Args:
      file_object (dfvfs.FileIO): a file-like object.
      offset (int): offset to the object header.

    Returns:
      tuple[construct.Struct, int]: parsed object header and size of the
          object payload (data) that follows.
    """
    file_object.seek(offset, os.SEEK_SET)
    object_header_data = file_object.read(self._OBJECT_HEADER_SIZE)
    object_header = self._OBJECT_HEADER.parse(object_header_data)
    payload_size = object_header.size - self._OBJECT_HEADER_SIZE
    return (object_header, payload_size)

  def _ParseItem(self, file_object, offset):
    """Parses a Systemd journal DATA object.

    This method will read, and decompress if needed, the content of a DATA
    object.

    Args:
      file_object (dfvfs.FileIO): a file-like object.
      offset (int): offset to the DATA object.

    Returns:
      tuple[str, str]: key and value of this item.

    Raises:
      ParseError: When an unexpected object type is parsed.
    """
    object_header, payload_size = self._ParseObjectHeader(file_object, offset)
    file_object.read(self._DATA_OBJECT_SIZE)

    if object_header.type != 'DATA':
      raise errors.ParseError(
          'Expected an object of type DATA, but got {0:s}'.format(
              object_header.type))

    event_data = file_object.read(payload_size - self._DATA_OBJECT_SIZE)
    if object_header.flags & self._OBJECT_COMPRESSED_FLAG:
      event_data = lzma.decompress(event_data)

    event_string = event_data.decode('utf-8')
    event_key, event_value = event_string.split('=', 1)
    return (event_key, event_value)

  def _ParseJournalEntry(self, parser_mediator, file_object, offset):
    """Parses a Systemd journal ENTRY object.

    This method will generate an event per ENTRY object.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      file_object (dfvfs.FileIO): a file-like object.
      offset (int): offset of the ENTRY object.

    Raises:
      ParseError: When an unexpected object type is parsed.
    """
    object_header, payload_size = self._ParseObjectHeader(file_object, offset)

    entry_object_data = file_object.read(payload_size)
    entry_object = self._ENTRY_OBJECT.parse(entry_object_data)

    if object_header.type != 'ENTRY':
      raise errors.ParseError(
          'Expected an object of type ENTRY, but got {0:s}'.format(
              object_header.type))

    fields = {}
    for item in entry_object.object_items:
      if item.object_offset < self._max_journal_file_offset:
        raise errors.ParseError(
            'object offset should be after hash tables ({0:d} < {1:d})'.format(
                offset, self._max_journal_file_offset))
      key, value = self._ParseItem(file_object, item.object_offset)
      fields[key] = value

    reporter = fields.get('SYSLOG_IDENTIFIER', None)
    if reporter and reporter != 'kernel':
      pid = fields.get('_PID', fields.get('SYSLOG_PID', None))
    else:
      pid = None

    event_data = SystemdJournalEventData()
    event_data.body = fields['MESSAGE']
    event_data.hostname = fields['_HOSTNAME']
    event_data.pid = pid
    event_data.reporter = reporter

    date_time = dfdatetime_posix_time.PosixTimeInMicroseconds(
        timestamp=entry_object.realtime)
    event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_WRITTEN)
    parser_mediator.ProduceEventWithEventData(event, event_data)

  def _ParseEntries(self, file_object, offset):
    """Parses Systemd journal ENTRY_ARRAY objects.

    Args:
      file_object (dfvfs.FileIO): a file-like object.
      offset (int): offset of the ENTRY_ARRAY object.

    Returns:
      list[dict]: every ENTRY objects offsets.

    Raises:
      ParseError: When an unexpected object type is parsed.
    """
    entry_offsets = []
    object_header, payload_size = self._ParseObjectHeader(file_object, offset)

    if object_header.type != 'ENTRY_ARRAY':
      raise errors.ParseError(
          'Expected an object of type ENTRY_ARRAY, but got {0:s}'.format(
              object_header.type))

    next_array_offset = self._ULInt64.parse_stream(file_object)
    entry_offests_numbers, _ = divmod((payload_size - 8), 8)
    for entry_offset in range(entry_offests_numbers):
      entry_offset = self._ULInt64.parse_stream(file_object)
      if entry_offset != 0:
        entry_offsets.append(entry_offset)

    if next_array_offset != 0:
      next_entry_offsets = self._ParseEntries(file_object, next_array_offset)
      entry_offsets.extend(next_entry_offsets)

    return entry_offsets

  def ParseFileObject(self, parser_mediator, file_object, **kwargs):
    """Parses a Systemd journal file-like object.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      file_object (dfvfs.FileIO): a file-like object.

    Raises:
      UnableToParseFile: when the header cannot be parsed.
    """
    try:
      journal_header = self._JOURNAL_HEADER.parse_stream(file_object)
    except construct.ConstructError as exception:
      raise errors.UnableToParseFile(
          'Unable to parse journal header with error: {0!s}'.format(exception))

    max_data_hash_table_offset = (
        journal_header.data_hash_table_offset +
        journal_header.data_hash_table_size)
    max_field_hash_table_offset = (
        journal_header.field_hash_table_offset +
        journal_header.field_hash_table_size)
    self._max_journal_file_offset = max(
        max_data_hash_table_offset, max_field_hash_table_offset)

    entries_offsets = self._ParseEntries(
        file_object, journal_header.entry_array_offset)

    for entry_offset in entries_offsets:
      try:
        self._ParseJournalEntry(parser_mediator, file_object, entry_offset)
      except errors.ParseError as exception:
        parser_mediator.ProduceExtractionError((
            'Unable to complete parsing journal file: {0:s} at offset '
            '0x{1:08x}').format(exception, entry_offset))
        return
      except construct.ConstructError as exception:
        raise errors.UnableToParseFile((
            'Unable to parse journal header at offset: 0x{0:08x} with '
            'error: {1:s}').format(entry_offset, exception))


manager.ParsersManager.RegisterParser(SystemdJournalParser)
