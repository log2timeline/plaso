# -*- coding: utf-8 -*-
"""The Apple System Log Parser."""

from __future__ import unicode_literals

from dfdatetime import posix_time as dfdatetime_posix_time

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import errors
from plaso.lib import definitions
from plaso.lib import specification
from plaso.parsers import dtfabric_parser
from plaso.parsers import manager


class ASLEventData(events.EventData):
  """Convenience class for an ASL event.

  Attributes:
    computer_name (str): name of the host.
    extra_information (str): extra fields associated to the event.
    facility (str): facility.
    group_id (int): group identifier (GID).
    level (str): level of criticality of the event.
    message_id (int): message identifier.
    message (str): message of the event.
    pid (int): process identifier (PID).
    read_uid (int): user identifier that can read this file, where -1
        represents all.
    read_gid (int): the group identifier that can read this file, where -1
        represents all.
    record_position (int): position of the event record.
    sender (str): sender or process that created the event.
    user_sid (str): user identifier (UID).
  """

  DATA_TYPE = 'mac:asl:event'

  def __init__(self):
    """Initializes event data."""
    super(ASLEventData, self).__init__(data_type=self.DATA_TYPE)
    self.computer_name = None
    self.extra_information = None
    self.facility = None
    self.group_id = None
    self.level = None
    self.message_id = None
    self.message = None
    self.pid = None
    self.read_gid = None
    self.read_uid = None
    self.record_position = None
    self.sender = None
    self.user_sid = None


class ASLParser(dtfabric_parser.DtFabricBaseParser):
  """Parser for ASL log files."""

  NAME = 'asl_log'
  DESCRIPTION = 'Parser for ASL log files.'

  _DEFINITION_FILE = 'asl.yaml'

  _FILE_SIGNATURE = b'ASL DB\x00\x00\x00\x00\x00\x00'

  # Most significant bit of a 64-bit string offset.
  _STRING_OFFSET_MSB = 1 << 63

  def _ParseRecord(self, parser_mediator, file_object, record_offset):
    """Parses a record and produces events.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      file_object (file): file-like object.
      record_offset (int): offset of the record relative to the start of
          the file.

    Returns:
      int: next record offset.

    Raises:
      ParseError: if the record cannot be parsed.
    """
    record_strings_data_offset = file_object.tell()
    record_strings_data_size = record_offset - record_strings_data_offset

    record_strings_data = self._ReadData(
        file_object, record_strings_data_offset, record_strings_data_size)

    record_map = self._GetDataTypeMap('asl_record')

    try:
      record, record_data_size = self._ReadStructureFromFileObject(
          file_object, record_offset, record_map)
    except (ValueError, errors.ParseError) as exception:
      raise errors.UnableToParseFile((
          'Unable to parse record at offset: 0x{0:08x} with error: '
          '{1!s}').format(record_offset, exception))

    hostname = self._ParseRecordString(
        record_strings_data, record_strings_data_offset,
        record.hostname_string_offset)

    sender = self._ParseRecordString(
        record_strings_data, record_strings_data_offset,
        record.sender_string_offset)

    facility = self._ParseRecordString(
        record_strings_data, record_strings_data_offset,
        record.facility_string_offset)

    message = self._ParseRecordString(
        record_strings_data, record_strings_data_offset,
        record.message_string_offset)

    file_offset = record_offset + record_data_size
    additional_data_size = record.data_size + 6 - record_data_size

    if additional_data_size % 8 != 0:
      raise errors.ParseError(
          'Invalid record additional data size: {0:d}.'.format(
              additional_data_size))

    additional_data = self._ReadData(
        file_object, file_offset, additional_data_size)

    extra_fields = {}
    for additional_data_offset in range(0, additional_data_size - 8, 16):
      record_extra_field = self._ParseRecordExtraField(
          additional_data[additional_data_offset:], file_offset)

      file_offset += 16

      name = self._ParseRecordString(
          record_strings_data, record_strings_data_offset,
          record_extra_field.name_string_offset)

      value = self._ParseRecordString(
          record_strings_data, record_strings_data_offset,
          record_extra_field.value_string_offset)

      if name is not None:
        extra_fields[name] = value

    # TODO: implement determine previous record offset

    event_data = ASLEventData()
    event_data.computer_name = hostname
    event_data.extra_information = ', '.join([
        '{0:s}: {1:s}'.format(name, value)
        for name, value in sorted(extra_fields.items())])
    event_data.facility = facility
    event_data.group_id = record.group_identifier
    event_data.level = record.alert_level
    event_data.message_id = record.message_identifier
    event_data.message = message
    event_data.pid = record.process_identifier
    event_data.read_gid = record.real_group_identifier
    event_data.read_uid = record.real_user_identifier
    event_data.record_position = record_offset
    event_data.sender = sender
    # Note that the user_sid value is expected to be a string.
    event_data.user_sid = '{0:d}'.format(record.user_identifier)

    microseconds, _ = divmod(record.written_time_nanoseconds, 1000)
    timestamp = (record.written_time * 1000000) + microseconds

    # TODO: replace by PosixTimeInNanoseconds.
    date_time = dfdatetime_posix_time.PosixTimeInMicroseconds(
        timestamp=timestamp)
    # TODO: replace by written time.
    event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_CREATION)
    parser_mediator.ProduceEventWithEventData(event, event_data)

    return record.next_record_offset

  def _ParseRecordExtraField(self, byte_stream, file_offset):
    """Parses a record extra field.

    Args:
      byte_stream (bytes): byte stream.
      file_offset (int): offset of the record extra field relative to
          the start of the file.

    Returns:
      asl_record_extra_field: record extra field.

    Raises:
      ParseError: if the record extra field cannot be parsed.
    """
    extra_field_map = self._GetDataTypeMap('asl_record_extra_field')

    try:
      record_extra_field = self._ReadStructureFromByteStream(
          byte_stream, file_offset, extra_field_map)
    except (ValueError, errors.ParseError) as exception:
      raise errors.ParseError((
          'Unable to parse record extra field at offset: 0x{0:08x} with error: '
          '{1!s}').format(file_offset, exception))

    return record_extra_field

  def _ParseRecordString(
      self, record_strings_data, record_strings_data_offset, string_offset):
    """Parses a record string.

    Args:
      record_strings_data (bytes): record strings data.
      record_strings_data_offset (int): offset of the record strings data
          relative to the start of the file.
      string_offset (int): offset of the string relative to the start of
          the file.

    Returns:
      str: record string or None if string offset is 0.

    Raises:
      ParseError: if the record string cannot be parsed.
    """
    if string_offset == 0:
      return None

    if string_offset & self._STRING_OFFSET_MSB:
      if (string_offset >> 60) != 8:
        raise errors.ParseError('Invalid inline record string flag.')

      string_size = (string_offset >> 56) & 0x0f
      if string_size >= 8:
        raise errors.ParseError('Invalid inline record string size.')

      string_data = bytes(bytearray([
          string_offset >> (8 * byte_index) & 0xff
          for byte_index in range(6, -1, -1)]))

      try:
        return string_data[:string_size].decode('utf-8')
      except UnicodeDecodeError as exception:
        raise errors.ParseError(
            'Unable to decode inline record string with error: {0!s}.'.format(
                exception))

    data_offset = string_offset - record_strings_data_offset
    record_string_map = self._GetDataTypeMap('asl_record_string')

    try:
      record_string = self._ReadStructureFromByteStream(
          record_strings_data[data_offset:], string_offset, record_string_map)
    except (ValueError, errors.ParseError) as exception:
      raise errors.ParseError((
          'Unable to parse record string at offset: 0x{0:08x} with error: '
          '{1!s}').format(string_offset, exception))

    return record_string.string.rstrip('\x00')

  @classmethod
  def GetFormatSpecification(cls):
    """Retrieves the format specification.

    Returns:
      FormatSpecification: format specification.
    """
    format_specification = specification.FormatSpecification(cls.NAME)
    format_specification.AddNewSignature(cls._FILE_SIGNATURE, offset=0)
    return format_specification

  def ParseFileObject(self, parser_mediator, file_object):
    """Parses an ASL file-like object.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      file_object (dfvfs.FileIO): file-like object.

    Raises:
      UnableToParseFile: when the file cannot be parsed.
    """
    file_header_map = self._GetDataTypeMap('asl_file_header')

    try:
      file_header, _ = self._ReadStructureFromFileObject(
          file_object, 0, file_header_map)
    except (ValueError, errors.ParseError) as exception:
      raise errors.UnableToParseFile(
          'Unable to parse file header with error: {0!s}'.format(
              exception))

    if file_header.signature != self._FILE_SIGNATURE:
      raise errors.UnableToParseFile('Invalid file signature.')

    # TODO: generate event for creation time.

    file_size = file_object.get_size()

    if file_header.first_log_entry_offset > 0:
      last_log_entry_offset = 0
      file_offset = file_header.first_log_entry_offset

      while file_offset < file_size:
        last_log_entry_offset = file_offset

        try:
          file_offset = self._ParseRecord(
              parser_mediator, file_object, file_offset)
        except errors.ParseError as exception:
          parser_mediator.ProduceExtractionWarning(
              'unable to parse record with error: {0!s}'.format(exception))
          return

        if file_offset == 0:
          break

      if last_log_entry_offset != file_header.last_log_entry_offset:
        parser_mediator.ProduceExtractionWarning(
            'last log entry offset does not match value in file header.')


manager.ParsersManager.RegisterParser(ASLParser)
