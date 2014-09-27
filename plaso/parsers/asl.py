#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2013 The Plaso Project Authors.
# Please see the AUTHORS file for details on individual authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""The Apple System Log Parser."""

import construct
import logging
import os

from plaso.lib import errors
from plaso.lib import event
from plaso.lib import eventdata
from plaso.lib import timelib
from plaso.parsers import interface
from plaso.parsers import manager


__author__ = 'Joaquin Moreno Garijo (Joaquin.MorenoGarijo.2013@live.rhul.ac.uk)'

# TODO: get the real name for the user of the group having the uid or gid.


class AslEvent(event.EventObject):
  """Convenience class for an asl event."""

  DATA_TYPE = 'mac:asl:event'

  def __init__(
      self, timestamp, record_position, message_id,
      level, record_header, read_uid, read_gid, computer_name,
      sender, facility, message, extra_information):
    """Initializes the event object.

    Args:
      timestamp: timestamp of the entry.
      record_position: position where the record start.
      message_id: Identification value for an ASL message.
      level: level of criticity.
      record_header: header of the entry.
        pid: identificaiton number of the process.
        uid: identification number of the owner of the process.
        gid: identification number of the group of the process.
      read_uid: the user ID that can read this file. If -1: all.
      read_gid: the group ID that can read this file. If -1: all.
      computer_name: name of the host.
      sender: the process that insert the event.
      facility: the part of the sender that create the event.
      message: message of the event.
      extra_information: extra fields associated to each entry.
    """
    super(AslEvent, self).__init__()
    self.pid = record_header.pid
    self.user_sid = unicode(record_header.uid)
    self.group_id = record_header.gid
    self.timestamp = timestamp
    self.timestamp_desc = eventdata.EventTimestamp.CREATION_TIME
    self.record_position = record_position
    self.message_id = message_id
    self.level = level
    self.read_uid = read_uid
    self.read_gid = read_gid
    self.computer_name = computer_name
    self.sender = sender
    self.facility = facility
    self.message = message
    self.extra_information = extra_information


class AslParser(interface.BaseParser):
  """Parser for ASL log files."""

  NAME = 'asl_log'
  DESCRIPTION = u'Parser for ASL log files.'

  ASL_MAGIC = 'ASL DB\x00\x00\x00\x00\x00\x00'

  # If not right assigned, the value is "-1".
  ASL_NO_RIGHTS = 'ffffffff'

  # Priority level (criticity)
  ASL_MESSAGE_PRIORITY = {
      0 : 'EMERGENCY',
      1 : 'ALERT',
      2 : 'CRITICAL',
      3 : 'ERROR',
      4 : 'WARNING',
      5 : 'NOTICE',
      6 : 'INFO',
      7 : 'DEBUG'}

  # ASL File header.
  # magic: magic number that identify ASL files.
  # version: version of the file.
  # offset: first record in the file.
  # timestamp: epoch time when the first entry was written.
  # last_offset: last record in the file.
  ASL_HEADER_STRUCT = construct.Struct(
      'asl_header_struct',
      construct.String('magic', 12),
      construct.UBInt32('version'),
      construct.UBInt64('offset'),
      construct.UBInt64('timestamp'),
      construct.UBInt32('cache_size'),
      construct.UBInt64('last_offset'),
      construct.Padding(36))

  # The record structure is:
  # [HEAP][STRUCTURE][4xExtraField][2xExtraField]*[PreviousEntry]
  # Record static structure.
  # tam_entry: it contains the number of bytes from this file position
  #            until the end of the record, without counts itself.
  # next_offset: next record. If is equal to 0x00, it is the last record.
  # asl_message_id: integer that has the numeric identification of the event.
  # timestamp: Epoch integer that has the time when the entry was created.
  # nanosecond: nanosecond to add to the timestamp.
  # level: level of priority.
  # pid: process identification that ask to save the record.
  # uid: user identification that has lunched the process.
  # gid: group identification that has lunched the process.
  # read_uid: identification id of a user. Only applied if is not -1 (all FF).
  #           Only root and this user can read the entry.
  # read_gid: the same than read_uid, but for the group.
  ASL_RECORD_STRUCT = construct.Struct(
      'asl_record_struct',
      construct.Padding(2),
      construct.UBInt32('tam_entry'),
      construct.UBInt64('next_offset'),
      construct.UBInt64('asl_message_id'),
      construct.UBInt64('timestamp'),
      construct.UBInt32('nanosec'),
      construct.UBInt16('level'),
      construct.UBInt16('flags'),
      construct.UBInt32('pid'),
      construct.UBInt32('uid'),
      construct.UBInt32('gid'),
      construct.UBInt32('read_uid'),
      construct.UBInt32('read_gid'),
      construct.UBInt64('ref_pid'))

  ASL_RECORD_STRUCT_SIZE = ASL_RECORD_STRUCT.sizeof()

  # 8-byte fields, they can be:
  # - String: [Nibble = 1000 (8)][Nibble = Length][7 Bytes = String].
  # - Integer: integer that has the byte position in the file that points
  #            to an ASL_RECORD_DYN_VALUE struct. If the value of the integer
  #            is equal to 0, it means that it has not data (skip).

  # If the field is a String, we use this structure to decode each
  # integer byte in the corresponding character (ASCII Char).
  ASL_OCTET_STRING = construct.ExprAdapter(
      construct.Octet('string'),
      encoder=lambda obj, ctx: ord(obj),
      decoder=lambda obj, ctx: chr(obj))

  # Field string structure. If the first bit is 1, it means that it
  # is a String (1000) = 8, then the next nibble has the number of
  # characters. The last 7 bytes are the number of bytes.
  ASL_STRING = construct.BitStruct(
      'string',
      construct.Flag('type'),
      construct.Bits('filler', 3),
      construct.If(
          lambda ctx: ctx.type,
          construct.Nibble('string_length')),
      construct.If(
          lambda ctx: ctx.type,
          construct.Array(7, ASL_OCTET_STRING)))

  # 8-byte pointer to a byte position in the file.
  ASL_POINTER = construct.UBInt64('pointer')

  # Dynamic data structure pointed by a pointer that contains a String:
  # [2 bytes padding][4 bytes lenght of String][String].
  ASL_RECORD_DYN_VALUE = construct.Struct(
      'asl_record_dyn_value',
      construct.Padding(2),
      construct.PascalString(
          'value',
          length_field=construct.UBInt32('length')))

  def Parse(self, parser_context, file_entry):
    """Extract entries from an ASL file.

    Args:
      parser_context: A parser context object (instance of ParserContext).
      file_entry: A file entry object (instance of dfvfs.FileEntry).
    """
    file_object = file_entry.GetFileObject()
    file_object.seek(0, os.SEEK_SET)

    try:
      header = self.ASL_HEADER_STRUCT.parse_stream(file_object)
    except (IOError, construct.FieldError) as exception:
      file_object.close()
      raise errors.UnableToParseFile(
          u'Unable to parse ASL Header with error: {0:s}.'.format(exception))

    if header.magic != self.ASL_MAGIC:
      file_object.close()
      raise errors.UnableToParseFile(u'Not an ASL Header, unable to parse.')

    # Get the first and the last entry.
    offset = header.offset
    old_offset = header.offset
    last_offset_header = header.last_offset

    # If the ASL file has entries.
    if offset:
      event_object, offset = self.ReadAslEvent(file_object, offset)
      while event_object:
        parser_context.ProduceEvent(
            event_object, parser_name=self.NAME, file_entry=file_entry)

        # TODO: an anomaly object must be emitted once that is implemented.
        # Sanity check, the last read element must be the same as
        # indicated by the header.
        if offset == 0 and old_offset != last_offset_header:
          logging.warning(u'Parsing ended before the header ends.')
        old_offset = offset
        event_object, offset = self.ReadAslEvent(file_object, offset)

    file_object.close()

  def ReadAslEvent(self, file_object, offset):
    """Returns an AslEvent from a single ASL entry.

    Args:
      file_object: a file-like object that points to an ASL file.
      offset: offset where the static part of the entry starts.

    Returns:
      An event object constructed from a single ASL record.
    """
    # The heap of the entry is saved to try to avoid seek (performance issue).
    # It has the real start position of the entry.
    dynamic_start = file_object.tell()
    dynamic_part = file_object.read(offset - file_object.tell())

    if not offset:
      return None, None

    try:
      record_header = self.ASL_RECORD_STRUCT.parse_stream(file_object)
    except (IOError, construct.FieldError) as exception:
      logging.warning(
          u'Unable to parse ASL event with error: {0:s}'.format(exception))
      return None, None

    # Variable tam_fields = is the real length of the dynamic fields.
    # We have this: [Record_Struct] + [Dynamic_Fields] + [Pointer_Entry_Before]
    # In Record_Struct we have a field called tam_entry, where it has the number
    # of bytes until the end of the entry from the position that the field is.
    # The tam_entry is between the 2th and the 6th byte in the [Record_Struct].
    # tam_entry = ([Record_Struct]-6)+[Dynamic_Fields]+[Pointer_Entry_Before]
    # Also, we do not need [Point_Entry_Before] and then we delete the size of
    # [Point_Entry_Before] that it is 8 bytes (8):
    # tam_entry = ([Record_Struct]-6)+[Dynamic_Fields]+[Pointer_Entry_Before]
    # [Dynamic_Fields] = tam_entry - [Record_Struct] + 6 - 8
    # [Dynamic_Fields] = tam_entry - [Record_Struct] - 2
    tam_fields = record_header.tam_entry - self.ASL_RECORD_STRUCT_SIZE - 2

    # Dynamic part of the entry that contains minimal four fields of 8 bytes
    # plus 2x[8bytes] fields for each extra ASL_Field.
    # The four first fields are always the Host, Sender, Facility and Message.
    # After the four first fields, the entry might have extra ASL_Fields.
    # For each extra ASL_field, it has a pair of 8-byte fields where the first
    # 8 bytes contains the name of the extra ASL_field and the second 8 bytes
    # contains the text of the exta field.
    # All of this 8-byte field can be saved using one of these three differents
    # types:
    # - Null value ('0000000000000000'): nothing to do.
    # - String: It is string if first bit = 1 or first nibble = 8 (1000).
    #           Second nibble has the length of string.
    #           The next 7 bytes have the text characters of the string
    #           padding the end with null characters: '0x00'.
    #           Example: [8468 6964 6400 0000]
    #                    [8] String, [4] length, value: [68 69 64 64] = hidd.
    # - Pointer: static position in the file to a special struct
    #            implemented as an ASL_RECORD_DYN_VALUE.
    #            Example: [0000 0000 0000 0077]
    #            It points to the file position 0x077 that has a
    #            ASL_RECORD_DYN_VALUE structure.
    values = []
    while tam_fields > 0:
      try:
        raw_field = file_object.read(8)
      except (IOError, construct.FieldError) as exception:
        logging.warning(
            u'Unable to parse ASL event with error: {0:d}'.format(exception))
        return None, None
      try:
        # Try to read as a String.
        field = self.ASL_STRING.parse(raw_field)
        values.append(''.join(field.string[0:field.string_length]))
        # Go to parse the next extra field.
        tam_fields -= 8
        continue
      except ValueError:
        pass
      # If it is not a string, it must be a pointer.
      try:
        field = self.ASL_POINTER.parse(raw_field)
      except ValueError as exception:
        logging.warning(
            u'Unable to parse ASL event with error: {0:s}'.format(exception))
        return None, None
      if field != 0:
        # The next IF ELSE is only for performance issues, avoiding seek.
        # If the pointer points a lower position than where the actual entry
        # starts, it means that it points to a previuos entry.
        pos = field - dynamic_start
        # Bigger or equal 0 means that the data is in the actual entry.
        if pos >= 0:
          try:
            values.append((self.ASL_RECORD_DYN_VALUE.parse(
                dynamic_part[pos:])).value.partition('\x00')[0])
          except (IOError, construct.FieldError) as exception:
            logging.warning(
                u'Unable to parse ASL event with error: {0:s}'.format(
                    exception))
            return None, None
        else:
          # Only if it is a pointer that points to the
          # heap from another entry we use the seek method.
          main_position = file_object.tell()
          # If the pointer is in a previous entry.
          if main_position > field:
            file_object.seek(field - main_position, os.SEEK_CUR)
            try:
              values.append((self.ASL_RECORD_DYN_VALUE.parse_stream(
                  file_object)).value.partition('\x00')[0])
            except (IOError, construct.FieldError):
              logging.warning((
                  u'The pointer at {0:d} (0x{0:x}) points to invalid '
                  u'information.').format(
                      main_position - self.ASL_POINTER.sizeof()))
            # Come back to the position in the entry.
            _ = file_object.read(main_position - file_object.tell())
          else:
            _ = file_object.read(field - main_position)
            values.append((self.ASL_RECORD_DYN_VALUE.parse_stream(
                file_object)).value.partition('\x00')[0])
            # Come back to the position in the entry.
            file_object.seek(main_position - file_object.tell(), os.SEEK_CUR)
      # Next extra field: 8 bytes more.
      tam_fields -= 8

    # Read the last 8 bytes of the record that points to the previous entry.
    _ = file_object.read(8)

    # Parsed section, we translate the read data to an appropriate format.
    microsecond = record_header.nanosec // 1000
    timestamp = timelib.Timestamp.FromPosixTimeWithMicrosecond(
        record_header.timestamp, microsecond)
    record_position = offset
    message_id = record_header.asl_message_id
    level = u'{0} ({1})'.format(
        self.ASL_MESSAGE_PRIORITY[record_header.level], record_header.level)
    # If the value is -1 (FFFFFFFF), it can be read by everyone.
    if record_header.read_uid != int(self.ASL_NO_RIGHTS, 16):
      read_uid = record_header.read_uid
    else:
      read_uid = 'ALL'
    if record_header.read_gid != int(self.ASL_NO_RIGHTS, 16):
      read_gid = record_header.read_gid
    else:
      read_gid = 'ALL'

    # Parsing the dynamic values (text or pointers to position with text).
    # The first four are always the host, sender, facility, and message.
    computer_name = values[0]
    sender = values[1]
    facility = values[2]
    message = values[3]

    # If the entry has an extra fields, they works as a pairs:
    # The first is the name of the field and the second the value.
    extra_information = ''
    if len(values) > 4:
      values = values[4:]
      for index in xrange(0, len(values) // 2):
        extra_information += (u'[{0}: {1}]'.format(
            values[index * 2], values[(index * 2) + 1]))

    # Return the event and the offset for the next entry.
    return AslEvent(timestamp, record_position, message_id,
        level, record_header, read_uid, read_gid, computer_name,
        sender, facility, message, extra_information), record_header.next_offset


manager.ParsersManager.RegisterParser(AslParser)
