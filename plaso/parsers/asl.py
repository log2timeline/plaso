# -*- coding: utf-8 -*-
"""The Apple System Log (ASL) file parser."""

import os

from dfdatetime import posix_time as dfdatetime_posix_time

from plaso.containers import events
from plaso.lib import definitions
from plaso.lib import dtfabric_helper
from plaso.lib import errors
from plaso.lib import specification
from plaso.parsers import interface
from plaso.parsers import manager


class ASLEventData(events.EventData):
  """Apple System Log (ASL) event data.

  Attributes:
    computer_name (str): name of the host.
    extra_information (str): extra fields associated to the event.
    facility (str): facility.
    group_identifier (int): group identifier (GID).
    level (str): level of criticality of the event.
    message (str): message of the event.
    message_identifier (int): message identifier.
    process_identifier (int): process identifier (PID).
    read_group_identifier (int): the group identifier that can read this file,
        where -1 represents all.
    read_user_identifier (int): user identifier that can read this file,
        where -1 represents all.
    record_position (int): position of the event record.
    sender (str): sender or process that created the event.
    user_identifier (int): user identifier (UID).
    written_time (dfdatetime.DateTimeValues): entry written date and time.
  """

  DATA_TYPE = 'macos:asl:entry'

  def __init__(self):
    """Initializes event data."""
    super(ASLEventData, self).__init__(data_type=self.DATA_TYPE)
    self.computer_name = None
    self.extra_information = None
    self.facility = None
    self.group_identifier = None
    self.level = None
    self.message = None
    self.message_identifier = None
    self.process_identifier = None
    self.read_group_identifier = None
    self.read_user_identifier = None
    self.record_position = None
    self.sender = None
    self.user_identifier = None
    self.written_time = None


class ASLFileEventData(events.EventData):
  """Apple System Log (ASL) file event data.

  Attributes:
    creation_time (dfdatetime.DateTimeValues): creation date and time.
    format_version (int): ASL file format version.
    is_dirty (bool): True if the last log entry offset does not match value
        in file header and the file is considered dirty.
  """

  DATA_TYPE = 'macos:asl:file'

  def __init__(self):
    """Initializes event data."""
    super(ASLFileEventData, self).__init__(data_type=self.DATA_TYPE)
    self.creation_time = None
    self.format_version = None
    self.is_dirty = None


class ASLParser(interface.FileObjectParser, dtfabric_helper.DtFabricHelper):
  """Parser for Apple System Log (ASL) files."""

  NAME = 'asl_log'
  DATA_FORMAT = 'Apple System Log (ASL) file'

  _DEFINITION_FILE = os.path.join(
      os.path.dirname(__file__), 'asl.yaml')

  # Most significant bit of a 64-bit string offset.
  _STRING_OFFSET_MSB = 1 << 63

  def _ParseRecord(self, parser_mediator, file_object, record_offset):
    """Parses a record and produces events.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      file_object (file): file-like object.
      record_offset (int): offset of the record relative to the start of
          the file.

    Returns:
      int: next record offset.

    Raises:
      ParseError: if the record cannot be parsed.
    """
    record_map = self._GetDataTypeMap('asl_record')

    try:
      record, record_data_size = self._ReadStructureFromFileObject(
          file_object, record_offset, record_map)
    except (ValueError, errors.ParseError) as exception:
      raise errors.ParseError((
          'Unable to parse record at offset: 0x{0:08x} with error: '
          '{1!s}').format(record_offset, exception))

    hostname = self._ParseRecordString(
        file_object, record.hostname_string_offset)

    sender = self._ParseRecordString(
        file_object, record.sender_string_offset)

    facility = self._ParseRecordString(
        file_object, record.facility_string_offset)

    message = self._ParseRecordString(
        file_object, record.message_string_offset)

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
          file_object, record_extra_field.name_string_offset)

      value = self._ParseRecordString(
          file_object, record_extra_field.value_string_offset)

      if name is not None:
        extra_fields[name] = value

    # TODO: implement determine previous record offset

    timestamp = ((record.written_time * definitions.NANOSECONDS_PER_SECOND) +
                 record.written_time_nanoseconds)

    event_data = ASLEventData()
    event_data.computer_name = hostname
    event_data.extra_information = ', '.join([
        '{0:s}: {1!s}'.format(name, value)
        for name, value in sorted(extra_fields.items())])
    event_data.facility = facility
    event_data.group_identifier = record.group_identifier
    event_data.level = record.alert_level
    event_data.message = message
    event_data.message_identifier = record.message_identifier
    event_data.process_identifier = record.process_identifier
    event_data.read_group_identifier = record.read_group_identifier
    event_data.read_user_identifier = record.read_user_identifier
    event_data.record_position = record_offset
    event_data.sender = sender
    event_data.user_identifier = record.user_identifier
    event_data.written_time = dfdatetime_posix_time.PosixTimeInNanoseconds(
        timestamp=timestamp)

    parser_mediator.ProduceEventData(event_data)

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

  def _ParseRecordString(self, file_object, string_offset):
    """Parses a record string.

    Args:
      file_object (file): file-like object.
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

    record_string_map = self._GetDataTypeMap('asl_record_string')

    try:
      record_string, _ = self._ReadStructureFromFileObject(
          file_object, string_offset, record_string_map)
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
    format_specification.AddNewSignature(
        b'ASL DB\x00\x00\x00\x00\x00\x00', offset=0)
    return format_specification

  def ParseFileObject(self, parser_mediator, file_object):
    """Parses an ASL file-like object.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      file_object (dfvfs.FileIO): file-like object.

    Raises:
      WrongParser: when the file cannot be parsed.
    """
    file_header_map = self._GetDataTypeMap('asl_file_header')

    try:
      file_header, _ = self._ReadStructureFromFileObject(
          file_object, 0, file_header_map)
    except (ValueError, errors.ParseError) as exception:
      raise errors.WrongParser(
          'Unable to parse file header with error: {0!s}'.format(
              exception))

    is_dirty = False
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
        is_dirty = True
        parser_mediator.ProduceRecoveryWarning(
            'last log entry offset does not match value in file header.')

    event_data = ASLFileEventData()
    event_data.format_version = file_header.format_version
    event_data.is_dirty = is_dirty

    if file_header.creation_time:
      event_data.creation_time = dfdatetime_posix_time.PosixTime(
          timestamp=file_header.creation_time)

    parser_mediator.ProduceEventData(event_data)


manager.ParsersManager.RegisterParser(ASLParser)
