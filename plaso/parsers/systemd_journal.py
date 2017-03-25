# -*- coding: utf-8 -*-
"""Parser for Systemd journal files."""

import lzma

import construct

from plaso.containers import text_events
from plaso.lib import errors
from plaso.parsers import interface
from plaso.parsers import manager


class SystemdJournalEvent(text_events.TextEvent):
  """Convenience class for a Systemd journal event."""

  # TODO: Change Event type when event data has been refactored.
  DATA_TYPE = u'systemd:journal:event'


class SystemdJournalUserlandEvent(SystemdJournalEvent):
  """Convenience class for a Systemd journal Userland event."""

  # This class will be formatted with the process' PID.
  DATA_TYPE = u'systemd:journal:userland'


class SystemdJournalParser(interface.FileObjectParser):
  """Parses Systemd Journal files."""

  NAME = u'systemd_journal'

  DESCRIPTION = u'Parser for Systemd Journal files.'

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
      construct.ULInt8(u'state'),
      STATE_OFFLINE=0,
      STATE_ONLINE=1,
      STATE_ARCHIVED=2
  )

  _OBJECT_HEADER_TYPE = construct.Enum(
      construct.ULInt8(u'type'),
      UNUSED=0,
      DATA=1,
      FIELD=2,
      ENTRY=3,
      DATA_HASH_TABLE=4,
      FIELD_HASH_TABLE=5,
      ENTRY_ARRAY=6,
      TAG=7
  )

  _ULInt64 = construct.ULInt64(u'int')

  _OBJECT_HEADER = construct.Struct(
      u'object_header',
      _OBJECT_HEADER_TYPE,
      construct.ULInt8(u'flags'),
      construct.Bytes(u'reserved', 6),
      construct.ULInt64(u'size')
  )

  _OBJECT_HEADER_SIZE = _OBJECT_HEADER.sizeof()

  _DATA_OBJECT = construct.Struct(
      u'data_object',
      construct.ULInt64(u'hash'),
      construct.ULInt64(u'next_hash_offset'),
      construct.ULInt64(u'next_field_offset'),
      construct.ULInt64(u'entry_offset'),
      construct.ULInt64(u'entry_array_offset'),
      construct.ULInt64(u'n_entries')
  )

  _DATA_OBJECT_SIZE = _DATA_OBJECT.sizeof()

  _ENTRY_ITEM = construct.Struct(
      u'entry_item',
      construct.ULInt64(u'object_offset'),
      construct.ULInt64(u'hash')
  )

  _ENTRY_OBJECT = construct.Struct(
      u'entry_object',
      construct.ULInt64(u'seqnum'),
      construct.ULInt64(u'realtime'),
      construct.ULInt64(u'monotonic'),
      construct.Struct(
          u'boot_id',
          construct.Bytes(u'bytes', 16),
          construct.ULInt64(u'qword1'),
          construct.ULInt64(u'qword2')),
      construct.ULInt64(u'xor_hash'),
      construct.Rename(u'object_items', construct.GreedyRange(_ENTRY_ITEM))
  )

  _JOURNAL_HEADER = construct.Struct(
      u'journal_header',
      construct.Const(construct.String(u'signature', 8), b'LPKSHHRH'),
      construct.ULInt32(u'compatible_flags'),
      construct.ULInt32(u'incompatible_flags'),
      _JOURNAL_STATE,
      construct.Bytes(u'reserved', 7),
      construct.Bytes(u'file_id', 16),
      construct.Bytes(u'machine_id', 16),
      construct.Bytes(u'boot_id', 16),
      construct.Bytes(u'seqnum_id', 16),
      construct.ULInt64(u'header_size'),
      construct.ULInt64(u'arena_size'),
      construct.ULInt64(u'data_hash_table_offset'),
      construct.ULInt64(u'data_hash_table_size'),
      construct.ULInt64(u'field_hash_table_offset'),
      construct.ULInt64(u'field_hash_table_size'),
      construct.ULInt64(u'tail_object_offset'),
      construct.ULInt64(u'n_objects'),
      construct.ULInt64(u'n_entries'),
      construct.ULInt64(u'tail_entry_seqnum'),
      construct.ULInt64(u'head_entry_seqnum'),
      construct.ULInt64(u'entry_array_offset'),
      construct.ULInt64(u'head_entry_realtime'),
      construct.ULInt64(u'tail_entry_realtime'),
      construct.ULInt64(u'tail_entry_monotonic'),
      # Added in 187
      construct.ULInt64(u'n_data'),
      construct.ULInt64(u'n_fields'),
      # Added in 189
      construct.ULInt64(u'n_tags'),
      construct.ULInt64(u'n_entry_arrays')
  )

  _JOURNAL_HEADER_SIZE = _JOURNAL_HEADER.sizeof()

  def __init__(self):
    """Initializes a parser object."""
    super(SystemdJournalParser, self).__init__()
    self._max_journal_file_offset = 0
    self._journal_file = None
    self._journal_header = None

  def _ParseObjectHeader(self, offset):
    """Parses a Systemd journal object header structure.

    Args:
      offset (int): offset to the object header.

    Returns:
      tuple[construct.Struct, int]: the parsed object header and size of the
        followong object's payload.
    """
    self._journal_file.seek(offset)
    object_header_data = self._journal_file.read(self._OBJECT_HEADER_SIZE)
    object_header = self._OBJECT_HEADER.parse(object_header_data)
    payload_size = object_header.size - self._OBJECT_HEADER_SIZE
    return (object_header, payload_size)

  def _ParseItem(self, offset):
    """Parses a Systemd journal DATA object.

    This method will read, and decompress if needed, the content of a DATA
    object.

    Args:
      offset (int): offset to the DATA object.

    Returns:
      tuple[str,str]: key and value of this item.

    Raises:
      ParseError: When an unexpected object type is parsed.
    """
    object_header, payload_size = self._ParseObjectHeader(offset)
    self._journal_file.read(self._DATA_OBJECT_SIZE)

    if object_header.type != u'DATA':
      raise errors.ParseError(
          u'Expected an object of type DATA, but got {0:s}'.format(
              object_header.type))

    event_data = self._journal_file.read(payload_size - self._DATA_OBJECT_SIZE)
    if object_header.flags & self._OBJECT_COMPRESSED_FLAG:
      event_data = lzma.decompress(event_data)

    event_string = event_data.decode(u'utf-8')
    event_key, event_value = event_string.split(u'=', 1)
    return (event_key, event_value)

  def _ParseJournalEntry(self, parser_mediator, offset):
    """Parses a Systemd journal ENTRY object.

    This method will generate an event per ENTRY object.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      offset (int): offset of the ENTRY object.

    Raises:
      ParseError: When an unexpected object type is parsed.
    """
    object_header, payload_size = self._ParseObjectHeader(offset)

    entry_object_data = self._journal_file.read(payload_size)
    entry_object = self._ENTRY_OBJECT.parse(entry_object_data)

    if object_header.type != u'ENTRY':
      raise errors.ParseError(
          u'Expected an object of type ENTRY, but got {0:s}'.format(
              object_header.type))

    fields = {}
    for item in entry_object.object_items:
      if item.object_offset < self._max_journal_file_offset:
        raise errors.ParseError(
            u'object offset should be after hash tables ({0:d} < {1:d})'.format(
                offset, self._max_journal_file_offset))
      key, value = self._ParseItem(item.object_offset)
      fields[key] = value

    # The realtime attribute is a number of microseconds since 1970-01-01, in
    # UTC, so we don't need to convert it.
    timestamp = entry_object.realtime

    event_class = SystemdJournalEvent
    syslog_identifier = fields.get(u'SYSLOG_IDENTIFIER', None)
    if syslog_identifier and syslog_identifier != u'kernel':
      if u'_PID' not in fields:
        fields[u'_PID'] = fields[u'SYSLOG_PID']
      event_class = SystemdJournalUserlandEvent

    parser_mediator.ProduceEvent(event_class(timestamp, offset, fields))

  def _ParseEntries(self, offset=None):
    """Parses Systemd journal ENTRY_ARRAY objects.

    Args:
      offset (int): offset of the ENTRY_ARRAY object.

    Returns:
      list: A list of dict() containing every ENTRY objects offsets.

    Raises:
      ParseError: When an unexpected object type is parsed.
    """
    entry_offsets = []
    if not offset:
      offset = self._journal_header.entry_array_offset
    object_header, payload_size = self._ParseObjectHeader(offset)

    if object_header.type != u'ENTRY_ARRAY':
      raise errors.ParseError(
          u'Expected an object of type ENTRY_ARRAY, but got {0:s}'.format(
              object_header.type))

    next_array_offset = self._ULInt64.parse_stream(self._journal_file)
    entry_offests_numbers = (payload_size - 8) / 8
    for entry_offset in range(entry_offests_numbers):
      entry_offset = self._ULInt64.parse_stream(self._journal_file)
      if entry_offset != 0:
        entry_offsets.append(entry_offset)

    if next_array_offset != 0:
      entry_offsets.extend(self._ParseEntries(offset=next_array_offset))

    return entry_offsets

  def ParseFileObject(self, parser_mediator, file_object, **kwargs):
    """Parses a Systemd journal file-like object.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      file_object (dfvfs.FileIO): a file-like object.

    Raises:
      UnableToParseFile: when the header cannot be parsed.
    """
    self._journal_file = file_object

    journal_header_data = self._journal_file.read(self._JOURNAL_HEADER_SIZE)
    try:
      self._journal_header = self._JOURNAL_HEADER.parse(journal_header_data)
    except construct.ConstructError as exception:
      raise errors.UnableToParseFile(
          u'Unable to parse journal header with error: {0:s}'.format(exception))

    max_data_hash_table_offset = (
        self._journal_header.data_hash_table_offset +
        self._journal_header.data_hash_table_size)
    max_field_hash_table_offset = (
        self._journal_header.field_hash_table_offset +
        self._journal_header.field_hash_table_size)
    self._max_journal_file_offset = max(
        max_data_hash_table_offset, max_field_hash_table_offset)

    entries_offsets = self._ParseEntries()
    for entry_offset in entries_offsets:
      try:
        self._ParseJournalEntry(parser_mediator, entry_offset)
      except construct.ConstructError as exception:
        raise errors.UnableToParseFile(
            u'Unable to parse journal header with error: {0:s}'.format(
                exception))


manager.ParsersManager.RegisterParser(SystemdJournalParser)
