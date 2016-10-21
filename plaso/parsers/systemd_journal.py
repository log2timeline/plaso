# -*- coding: utf-8 -*-
"""Parser for Systemd journal files."""

import construct

from dfvfs.compression.xz_decompressor import XZDecompressor
from plaso.containers import time_events
from plaso.containers import text_events
from plaso.lib import eventdata
from plaso.lib import timelib
from plaso.parsers import interface
from plaso.parsers import manager

class SystemdJournalEvent(text_events.TextEvent):
  """Convenience class for a Systemd journal event."""
  DATA_TYPE = u'systemd:journal:event'

class SystemdJournalUserlandEvent(SystemdJournalEvent):
  """Convenience class for a Systemd journal Userland event."""

  DATA_TYPE = u'systemd:journal:userland'
#    self.journal_size_available = getattr(event_dict, 'AVAILABLE', None)
#    self.journal_size_available_text = getattr(event_dict, 'AVAILABLE_PRETTY', None)
#    self.current_use = getattr(event_dict, 'CURRENT_USE', None)
#    self.current_use_text = getattr(event_dict, 'CURRENT_USE_PRETTY', None)
#    self.disk_available = getattr(event_dict, 'DISK_AVAILABLE', None)
#    self.disk_available_text = getattr(event_dict, 'DISK_AVAILABLE_PRETTY', None)
#    self.disk_keep_free = getattr(event_dict, 'DISK_KEEP_FREE', None)
#    self.disk_keep_free_text = getattr(event_dict, 'DISK_KEEP_FREE_PRETTY', None)
#    self.journal_name = getattr(event_dict, 'JOURNAL_NAME', None)
#    self.journal_path = getattr(event_dict, 'JOURNAL_PATH', None)
#    self.limit = getattr(event_dict, 'LIMIT', None)
#    self.limit_text = getattr(event_dict, 'LIMIT_PRETTY', None)


class SystemdJournalParser(interface.FileObjectParser):
  """Parses Systemd Journal files."""

  NAME = u'systemd_journal'
  DESCRIPTION = u'Parser for Systemd Journal files.'

  _OBJECT_COMPRESSED_FLAG = 0x00000001

  _OBJECT_HEADER_TYPE = construct.Enum(
      construct.ULInt8(u'type'),
      UNUSED = 0,
      DATA = 1,
      FIELD = 2,
      ENTRY = 3,
      DATA_HASH_TABLE = 4,
      FIELD_HASH_TABLE = 5,
      ENTRY_ARRAY = 6,
      TAG = 7
  )

  _ULInt64 = construct.Struct(u'int', construct.ULInt64(u'int'))

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
    'entry_item',
    construct.ULInt64(u'object_offset'),
    construct.ULInt64(u'hash')
  )

  _ENTRY_OBJECT = construct.Struct(
     u'entry_object',
     construct.ULInt64(u'seqnum'),
     construct.ULInt64(u'realtime'),
     construct.ULInt64(u'monotonic'),
     construct.Struct(u'boot_id',
            construct.Bytes('bytes',16),
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
    construct.ULInt8(u'state'),
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


  def _ParseObjectHeader(self, offset):
    self.journal_file.seek(offset)
    object_header_data = self.journal_file.read(self._OBJECT_HEADER_SIZE)
    object_header = self._OBJECT_HEADER.parse(object_header_data)
    payload_size = object_header.size - self._OBJECT_HEADER_SIZE
    return (object_header, payload_size)

  def _ParseItem(self, offset):
    object_header, payload_size = self._ParseObjectHeader(offset)
    # _ = self._DATA_OBJECT.parse(self.journal_file.read(self._DATA_OBJECT_SIZE))
    _ = self.journal_file.read(self._DATA_OBJECT_SIZE)

    if object_header.type == u'DATA':
      event_data = self.journal_file.read(payload_size - self._DATA_OBJECT_SIZE)
      if object_header.flags & self._OBJECT_COMPRESSED_FLAG:
        xzd = XZDecompressor()
        event_data = xzd.Decompress(event_data)[0]

      return event_data.decode(u'utf-8').split(u'=', 1)

    else:
      raise Exception('Expected an object of type DATA, but got {0:s}'.format(
          object_header.type))

  def _ParseJournalEntry(self, parser_mediator, offset):
    object_header, payload_size = self._ParseObjectHeader(offset)

    entry_object_data = self.journal_file.read(payload_size)
    entry_object = self._ENTRY_OBJECT.parse(entry_object_data)

    fields=dict()
    if object_header.type == u'ENTRY':
      for item in entry_object.object_items:
        key, value = self._ParseItem(item.object_offset)
        fields[key] = value
    else:
      raise Exception('Expected an object of type ENTRY, but got {0:s}'.format(
          object_header.type))

    # Already a number of microseconds since 1970-01-01, in UTC
    timestamp=entry_object.realtime

    event_class = SystemdJournalEvent
    if 'SYSLOG_IDENTIFIER' in fields:
      if fields['SYSLOG_IDENTIFIER']!='kernel':
        if not '_PID' in fields:
          fields['_PID'] = fields['SYSLOG_PID']
        event_class = SystemdJournalUserlandEvent

    parser_mediator.ProduceEvent(event_class(timestamp, offset, fields))

  def _ParseEntries(self,offset=None):
    entry_offsets = []
    if not offset:
      # First call
      offset = self.journal_header.entry_array_offset
    object_header, payload_size = self._ParseObjectHeader(offset)
    if object_header.type == 'ENTRY_ARRAY':
      next_array_offset = self._ULInt64.parse(self.journal_file.read(8)).int
      entry_offests_numbers = (payload_size - 8) / 8
      for entry_offset in range(entry_offests_numbers):
        entry_offset = self._ULInt64.parse(self.journal_file.read(8)).int
        if entry_offset != 0:
          entry_offsets.append(entry_offset)
      if next_array_offset == 0:
        return entry_offsets
      else:
        return entry_offsets + self._ParseEntries(offset=next_array_offset)
    else:
      raise Exception('Expected an object of type ENTRY_ARRAY, but got {0:s}'.
                      format(object_header.type))

  def ParseFileObject(self, parser_mediator, file_object, **kwargs):
    """Parses a Systemd journal file-like object.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      file_object (dfvfs.FileIO): a file-like object.
    """

    self.journal_file = file_object

    data = self.journal_file.read(self._JOURNAL_HEADER_SIZE)
    self.journal_header = self._JOURNAL_HEADER.parse(data)

    entries_offsets = self._ParseEntries()
    for entry_offset in entries_offsets:
      #time, event_data = self._ParseJournalEntry(entry_offset)
      self._ParseJournalEntry(parser_mediator, entry_offset)


manager.ParsersManager.RegisterParser(SystemdJournalParser)
