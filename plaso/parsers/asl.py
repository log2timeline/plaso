# -*- coding: utf-8 -*-
"""The Apple System Log Parser."""

import os

import construct

from plaso.containers import time_events
from plaso.lib import errors
from plaso.lib import eventdata
from plaso.lib import py2to3
from plaso.parsers import interface
from plaso.parsers import manager


__author__ = 'Joaquin Moreno Garijo (Joaquin.MorenoGarijo.2013@live.rhul.ac.uk)'


class ASLEvent(time_events.PosixTimeEvent):
  """Convenience class for an ASL event.

  Attributes:
    computer_name: a string containing the name of the host.
    extra_information: a string containing extra fields associated
                       to the event.
    facility: a string containing the facility.
    group_id: an integer containing the group identifer (GID).
    level: a string containing the level of criticality of the event.
    message_id: an integer containing the message identifier.
    message: a string containing the message of the event.
    pid: an integer containing the process identifier (PID).
    read_uid: the user ID that can read this file. If -1: all.
    read_gid: the group ID that can read this file. If -1: all.
    record_position: an integer containing the position of the event record.
    sender: a string containing the sender or process that created the event.
    user_sid: a string containing the user identifier (UID).
  """

  DATA_TYPE = u'mac:asl:event'

  def __init__(
      self, posix_time, offset, message_id, level, pid, uid, gid,
      read_uid, read_gid, computer_name, sender, facility, message,
      extra_information, micro_seconds=0):
    """Initializes the event object.

    Args:
      posix_time: the POSIX time value, which contains the number of seconds
                  since January 1, 1970 00:00:00 UTC.
      offset: an integer containing the offset of the event record.
      message_id: an integer containing the message identifier.
      level: a string containing the level of criticality of the event.
      pid: an integer containing the process identifier (PID).
      uid: an integer containing the user identifier (UID).
      gid: an integer containing the group identifier (GID).
      read_uid: the user ID that can read this file. If -1: all.
      read_gid: the group ID that can read this file. If -1: all.
      computer_name: a string containing the name of the host.
      sender: a string containing the sender or process that created the event.
      facility: a string containing the facility.
      message: a string containing the message of the event.
      extra_information: a string containing extra fields associated
                         to the event.
      micro_seconds: optional number of micro seconds.
    """
    super(ASLEvent, self).__init__(
        posix_time, eventdata.EventTimestamp.CREATION_TIME,
        micro_seconds=micro_seconds)
    self.computer_name = computer_name
    self.extra_information = extra_information
    self.facility = facility
    self.group_id = gid
    self.level = level
    self.message_id = message_id
    self.message = message
    self.pid = pid
    self.read_gid = read_gid
    self.read_uid = read_uid
    self.record_position = offset
    self.sender = sender
    # Note that the user_sid value is expected to be a string.
    self.user_sid = u'{0:d}'.format(uid)


class ASLParser(interface.FileObjectParser):
  """Parser for ASL log files."""

  _INITIAL_FILE_OFFSET = None

  NAME = u'asl_log'
  DESCRIPTION = u'Parser for ASL log files.'

  _ASL_MAGIC = b'ASL DB\x00\x00\x00\x00\x00\x00'

  # ASL File header.
  # magic: magic number that identify ASL files.
  # version: version of the file.
  # offset: first record in the file.
  # timestamp: time when the first entry was written.
  #     Contains the number of seconds since January 1, 1970 00:00:00 UTC.
  # last_offset: last record in the file.
  _ASL_HEADER_STRUCT = construct.Struct(
      u'asl_header_struct',
      construct.String(u'magic', 12),
      construct.UBInt32(u'version'),
      construct.UBInt64(u'offset'),
      construct.UBInt64(u'timestamp'),
      construct.UBInt32(u'cache_size'),
      construct.UBInt64(u'last_offset'),
      construct.Padding(36))

  # The record structure is:
  # [HEAP][STRUCTURE][4xExtraField][2xExtraField]*[PreviousEntry]
  # Record static structure.
  # tam_entry: it contains the number of bytes from this file position
  #            until the end of the record, without counts itself.
  # next_offset: next record. If is equal to 0x00, it is the last record.
  # asl_message_id: integer that has the numeric identification of the event.
  # timestamp: the entry creation date and time.
  #     Contains the number of seconds since January 1, 1970 00:00:00 UTC.
  # nanosecond: nanosecond to add to the timestamp.
  # level: level of priority.
  # pid: process identification that ask to save the record.
  # uid: user identification that has lunched the process.
  # gid: group identification that has lunched the process.
  # read_uid: identification id of a user. Only applied if is not -1 (all FF).
  #           Only root and this user can read the entry.
  # read_gid: the same than read_uid, but for the group.
  _ASL_RECORD_STRUCT = construct.Struct(
      u'asl_record_struct',
      construct.Padding(2),
      construct.UBInt32(u'tam_entry'),
      construct.UBInt64(u'next_offset'),
      construct.UBInt64(u'asl_message_id'),
      construct.UBInt64(u'timestamp'),
      construct.UBInt32(u'nanosec'),
      construct.UBInt16(u'level'),
      construct.UBInt16(u'flags'),
      construct.UBInt32(u'pid'),
      construct.UBInt32(u'uid'),
      construct.UBInt32(u'gid'),
      construct.UBInt32(u'read_uid'),
      construct.UBInt32(u'read_gid'),
      construct.UBInt64(u'ref_pid'))

  _ASL_RECORD_STRUCT_SIZE = _ASL_RECORD_STRUCT.sizeof()

  # 8-byte fields, they can be:
  # - String: [Nibble = 1000 (8)][Nibble = Length][7 Bytes = String].
  # - Integer: integer that has the byte position in the file that points
  #            to an ASL_RECORD_DYN_VALUE struct. If the value of the integer
  #            is equal to 0, it means that it has not data (skip).

  # If the field is a String, we use this structure to decode each
  # integer byte in the corresponding character (ASCII Char).
  _ASL_OCTET_STRING = construct.ExprAdapter(
      construct.Octet(u'string'),
      encoder=lambda obj, ctx: ord(obj),
      decoder=lambda obj, ctx: chr(obj))

  # Field string structure. If the first bit is 1, it means that it
  # is a String (1000) = 8, then the next nibble has the number of
  # characters. The last 7 bytes are the number of bytes.
  _ASL_STRING = construct.BitStruct(
      u'string',
      construct.Flag(u'type'),
      construct.Bits(u'filler', 3),
      construct.If(
          lambda ctx: ctx.type,
          construct.Nibble(u'string_length')),
      construct.If(
          lambda ctx: ctx.type,
          construct.Array(7, _ASL_OCTET_STRING)))

  # 8-byte pointer to a byte position in the file.
  _ASL_POINTER = construct.UBInt64(u'pointer')

  # Dynamic data structure pointed by a pointer that contains a String:
  # [2 bytes padding][4 bytes size of String][String].
  _ASL_RECORD_DYN_VALUE = construct.Struct(
      u'asl_record_dyn_value',
      construct.Padding(2),
      construct.UBInt32(u'size'),
      construct.Bytes(u'value', lambda ctx: ctx.size))

  def ParseFileObject(self, parser_mediator, file_object, **kwargs):
    """Parses an ALS file-like object.

    Args:
      parser_mediator: a parser mediator object (instance of ParserMediator).
      file_object: a file-like object.

    Raises:
      UnableToParseFile: when the file cannot be parsed.
    """
    file_object.seek(0, os.SEEK_SET)

    try:
      header = self._ASL_HEADER_STRUCT.parse_stream(file_object)
    except (IOError, construct.FieldError) as exception:
      raise errors.UnableToParseFile(
          u'Unable to parse ASL Header with error: {0:s}.'.format(exception))

    if header.magic != self._ASL_MAGIC:
      raise errors.UnableToParseFile(u'Not an ASL Header, unable to parse.')

    offset = header.offset
    if not offset:
      return

    header_last_offset = header.last_offset

    previous_offset = offset
    event_object, offset = self.ReadASLEvent(
        parser_mediator, file_object, offset)
    while event_object:
      # Sanity check, the last read element must be the same as
      # indicated by the header.
      if offset == 0 and previous_offset != header_last_offset:
        parser_mediator.ProduceParseError(
            u'Unable to parse header. Last element header does not match '
            u'header offset.')
      previous_offset = offset
      event_object, offset = self.ReadASLEvent(
          parser_mediator, file_object, offset)

  def ReadASLEvent(self, parser_mediator, file_object, offset):
    """Reads an ASL record at a specific offset.

    Args:
      parser_mediator: a parser mediator object (instance of ParserMediator).
      file_object: a file-like object that points to an ASL file.
      offset: an integer containing the offset of the ASL record.

    Returns:
      A tuple of an event object extracted from the ASL record,
      and the offset to the next ASL record in the file.
    """
    # The heap of the entry is saved to try to avoid seek (performance issue).
    # It has the real start position of the entry.
    dynamic_data_offset = file_object.tell()

    try:
      dynamic_data = file_object.read(offset - dynamic_data_offset)
    except IOError as exception:
      parser_mediator.ProduceParseError(
          u'unable to read ASL record dynamic data with error: {0:s}'.format(
              exception))
      return None, None

    if not offset:
      return None, None

    try:
      record_struct = self._ASL_RECORD_STRUCT.parse_stream(file_object)
    except (IOError, construct.FieldError) as exception:
      parser_mediator.ProduceParseError(
          u'unable to parse ASL record with error: {0:s}'.format(exception))
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
    tam_fields = record_struct.tam_entry - self._ASL_RECORD_STRUCT_SIZE - 2

    # Dynamic part of the entry that contains minimal four fields of 8 bytes
    # plus 2 x [8 bytes] fields for each extra ASL_Field.
    # The four first fields are always the Host, Sender, Facility and Message.
    # After the four first fields, the entry might have extra ASL_Fields.
    # For each extra ASL_field, it has a pair of 8-byte fields where the first
    # 8 bytes contains the name of the extra ASL_field and the second 8 bytes
    # contains the text of the extra field.
    # All of this 8-byte field can be saved using one of these three different
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
        field_data = file_object.read(8)
      except IOError as exception:
        parser_mediator.ProduceParseError(
            u'unable to read ASL field with error: {0:s}'.format(exception))
        return None, None

      # Try to read the field data as a string.
      try:
        asl_string_struct = self._ASL_STRING.parse(field_data)
        string_data = b''.join(
            asl_string_struct.string[0:asl_string_struct.string_length])
        values.append(string_data)

        # Go to parse the next extra field.
        tam_fields -= 8
        continue

      except ValueError:
        pass

      # If the field is not a string it must be a pointer.
      try:
        pointer_value = self._ASL_POINTER.parse(field_data)
      except ValueError as exception:
        parser_mediator.ProduceParseError(
            u'unable to parse ASL field with error: {0:s}'.format(exception))
        return None, None

      if not pointer_value:
        # Next extra field: 8 bytes more.
        tam_fields -= 8
        continue

      # The next IF ELSE is only for performance issues, avoiding seek.
      # If the pointer points a lower position than where the actual entry
      # starts, it means that it points to a previous entry.
      pos = pointer_value - dynamic_data_offset

      # Greater or equal 0 means that the data is in the actual entry.
      if pos >= 0:
        try:
          dyn_value_struct = self._ASL_RECORD_DYN_VALUE.parse(
              dynamic_data[pos:])
          dyn_value = dyn_value_struct.value.partition(b'\x00')[0]
          values.append(dyn_value)

        except (IOError, construct.FieldError) as exception:
          parser_mediator.ProduceParseError((
              u'unable to parse ASL record dynamic value with error: '
              u'{0:s}').format(exception))
          return None, None

      else:
        # Only if it is a pointer that points to the
        # heap from another entry we use the seek method.
        main_position = file_object.tell()

        # If the pointer is in a previous entry.
        if main_position > pointer_value:
          file_object.seek(pointer_value - main_position, os.SEEK_CUR)

          try:
            dyn_value_struct = self._ASL_RECORD_DYN_VALUE.parse_stream(
                file_object)
            dyn_value = dyn_value_struct.value.partition(b'\x00')[0]
            values.append(dyn_value)

          except (IOError, construct.FieldError):
            parser_mediator.ProduceParseError((
                u'the pointer at {0:d} (0x{0:08x}) points to invalid '
                u'information.').format(
                    main_position - self._ASL_POINTER.sizeof()))

          # Come back to the position in the entry.
          _ = file_object.read(main_position - file_object.tell())

        else:
          _ = file_object.read(pointer_value - main_position)

          dyn_value_struct = self._ASL_RECORD_DYN_VALUE.parse_stream(
              file_object)
          dyn_value = dyn_value_struct.value.partition(b'\x00')[0]
          values.append(dyn_value)

          # Come back to the position in the entry.
          file_object.seek(main_position - file_object.tell(), os.SEEK_CUR)

      # Next extra field: 8 bytes more.
      tam_fields -= 8

    # Read the last 8 bytes of the record that points to the previous entry.
    _ = file_object.read(8)

    # Parsed section, we translate the read data to an appropriate format.
    micro_seconds, _ = divmod(record_struct.nanosec, 1000)

    # Parsing the dynamic values (text or pointers to position with text).
    # The first four are always the host, sender, facility, and message.
    number_of_values = len(values)
    if number_of_values < 4:
      parser_mediator.ProduceParseError(
          u'less than four values read from an ASL event.')

    computer_name = u'N/A'
    sender = u'N/A'
    facility = u'N/A'
    message = u'N/A'

    if number_of_values >= 1:
      computer_name = values[0].decode(u'utf-8')

    if number_of_values >= 2:
      sender = values[1].decode(u'utf-8')

    if number_of_values >= 3:
      facility = values[2].decode(u'utf-8')

    if number_of_values >= 4:
      message = values[3].decode(u'utf-8')

    # If the entry has an extra fields, they works as a pairs:
    # The first is the name of the field and the second the value.
    extra_information = u''
    if number_of_values > 4 and number_of_values % 2 == 0:
      # Taking all the extra attributes and merging them together,
      # eg: a = [1, 2, 3, 4] will look like "1: 2, 3: 4".
      try:
        extra_values = map(py2to3.UNICODE_TYPE, values[4:])
        extra_information = u', '.join(
            map(u': '.join, zip(extra_values[0::2], extra_values[1::2])))
      except UnicodeDecodeError as exception:
        parser_mediator.ProduceParseError(
            u'Unable to decode all ASL values in the extra information fields.')

    event_object = ASLEvent(
        record_struct.timestamp, offset, record_struct.asl_message_id,
        record_struct.level, record_struct.pid, record_struct.uid,
        record_struct.gid, record_struct.read_uid, record_struct.read_gid,
        computer_name, sender, facility, message, extra_information,
        micro_seconds=micro_seconds)
    parser_mediator.ProduceEvent(event_object)

    return (event_object, record_struct.next_offset)


manager.ParsersManager.RegisterParser(ASLParser)
