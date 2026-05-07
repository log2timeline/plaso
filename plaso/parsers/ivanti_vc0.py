# -*- coding: utf-8 -*-
"""Parser for Ivanti Connect Secure .vc0 log files."""

import codecs
import ipaddress
import re
import string

from dfdatetime import posix_time as dfdatetime_posix_time

from plaso.containers import events
from plaso.lib import errors
from plaso.lib import specification
from plaso.parsers import interface
from plaso.parsers import manager


class IvantiVC0EventData(events.EventData):
  """Ivanti Connect Secure .vc0 log record.

  Attributes:
    body (str): short record text for formatters.
    hostname (str): appliance hostname.
    ip_address (str): IP address found in the record values.
    line_identifier (str): identifier after the timestamp in the record ID.
    log_file_type (str): log family, such as "access" or "events".
    message_code (str): Ivanti message code.
    realm (str): Ivanti realm.
    record_identifier (str): original record identifier in the form
        hex_timestamp.hex_line_identifier.
    record_values (str): original tab-separated values after the realm field.
    recorded_time (dfdatetime.DateTimeValues): record timestamp.
    source_filename (str): name of the source log file.
    username (str): username found in the record values.
  """

  DATA_TYPE = 'ivanti:connect_secure:vc0:record'

  def __init__(self):
    """Initializes event data."""
    super().__init__(data_type=self.DATA_TYPE)
    self.body = None
    self.hostname = None
    self.ip_address = None
    self.line_identifier = None
    self.log_file_type = None
    self.message_code = None
    self.realm = None
    self.record_identifier = None
    self.record_values = None
    self.recorded_time = None
    self.source_filename = None
    self.username = None


class IvantiVC0Parser(interface.FileObjectParser):
  """Parser for Ivanti Connect Secure .vc0 log files."""

  NAME = 'ivanti_vc0'
  DATA_FORMAT = 'Ivanti Connect Secure .vc0 log file'

  _CHUNK_SIZE = 1024 * 1024
  _HEADER_SIZE = 8192
  _HEADER_SIGNATURE = b'\x05\x00\x00\x00\x01\x00\x00\x00'
  _MAXIMUM_BODY_VALUES = 8

  _LOG_FILENAME_RE = re.compile(
      r'^log\.(?P<log_file_type>.+?)\.vc0(?:\.old)?$')
  _MESSAGE_CODE_RE = re.compile(r'^[A-Z]{3}\d{5}$')

  _PRINTABLE_CHARACTERS = frozenset(string.printable)
  _RECORD_SEPARATOR_RE = re.compile(
      r'[\x17\x15\x13\x12\x05\x04\x03\x02\x01\x00]')
  _UNWANTED_CONTROL_CHARACTERS_RE = re.compile(
      r'[\x0b\x1c\x0f\x06\x1e\x08\x10\x1d\x0e\x11\x14\x16\x18\x19\x1f'
      r'\x7f\x1a\x1b\x0c\ufffd]')

  @classmethod
  def GetFormatSpecification(cls):
    """Retrieves the format specification.

    Returns:
      FormatSpecification: format specification.
    """
    format_specification = specification.FormatSpecification(cls.NAME)
    format_specification.AddNewSignature(cls._HEADER_SIGNATURE, offset=0)

    return format_specification

  def _CheckHeader(self, file_object):
    """Checks the .vc0 header signature.

    Args:
      file_object (dfvfs.FileIO): a file-like object.

    Returns:
      bool: True if the header signature matches.
    """
    file_object.seek(0)
    header = file_object.read(len(self._HEADER_SIGNATURE))

    return header == self._HEADER_SIGNATURE

  def _CleanText(self, text):
    """Normalizes .vc0 record text.

    Args:
      text (str): text to clean.

    Returns:
      str: normalized text.
    """
    text = self._RECORD_SEPARATOR_RE.sub('\n', text)
    text = text.replace('\x07', ' ')
    text = self._UNWANTED_CONTROL_CHARACTERS_RE.sub('', text)

    return ''.join([
        character if character in self._PRINTABLE_CHARACTERS else '?'
        for character in text])

  def _CreateBody(self, record_values, ip_address, realm, username):
    """Builds the short body used by formatters.

    Args:
      record_values (list[str]): values after the realm field.
      ip_address (str): IP address found in the record values.
      realm (str): Ivanti realm.
      username (str): username found in the record values.

    Returns:
      str: body or None if not available.
    """
    body_values = [
        value.strip() for value in record_values if value and value.strip()]

    leading_metadata_values = {
        value for value in (ip_address, realm, username) if value}
    while body_values and body_values[0] in leading_metadata_values:
      body_values.pop(0)

    if not body_values:
      return None

    number_of_extra_values = len(body_values) - self._MAXIMUM_BODY_VALUES
    if number_of_extra_values > 0:
      body_values = body_values[:self._MAXIMUM_BODY_VALUES]
      body_values.append(f'... ({number_of_extra_values:d} more fields)')

    return ' | '.join(body_values)

  def _ExtractIPAddress(self, value):
    """Extracts an IP address from a value.

    Args:
      value (str): field value.

    Returns:
      str: IP address or None if not available.
    """
    try:
      ip_address = ipaddress.ip_address(value.strip())
    except ValueError:
      return None

    return str(ip_address)

  def _ExtractLogFileType(self, source_filename):
    """Extracts the log file type from the source filename.

    Args:
      source_filename (str): name of the source log file.

    Returns:
      str: log file type or None if not available.
    """
    if not source_filename:
      return None

    match = self._LOG_FILENAME_RE.match(source_filename)
    if match:
      return match.group('log_file_type')

    return None

  def _ExtractMessageCode(self, fields):
    """Extracts an Ivanti message code from record fields.

    Args:
      fields (list[str]): record fields.

    Returns:
      str: message code or None if not available.
    """
    if len(fields) > 2 and self._MESSAGE_CODE_RE.match(fields[2].strip()):
      return fields[2].strip()

    for field in fields:
      field = field.strip()
      if self._MESSAGE_CODE_RE.match(field):
        return field

    return None

  def _ReadRecords(self, file_object):
    """Reads .vc0 records.

    Args:
      file_object (dfvfs.FileIO): a file-like object.

    Yields:
      str: record string.
    """
    file_object.seek(self._HEADER_SIZE)

    decoder = codecs.getincrementaldecoder('utf-8')(errors='replace')
    record_buffer = ''

    while True:
      data = file_object.read(self._CHUNK_SIZE)
      if not data:
        break

      text = decoder.decode(data)
      text = self._CleanText(text)

      if record_buffer:
        text = ''.join([record_buffer, text])

      records = text.split('\n')
      for record in records[:-1]:
        record = record.strip()
        if record:
          yield record

      record_buffer = records[-1]

    text = decoder.decode(b'', final=True)
    if text:
      record_buffer = ''.join([record_buffer, self._CleanText(text)])

    record = record_buffer.strip()
    if record:
      yield record

  def _ParseRecord(self, parser_mediator, record, source_filename):
    """Parses a .vc0 record.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      record (str): record string.
      source_filename (str): name of the source log file.

    Returns:
      IvantiVC0EventData: event data, or None for unsupported records.
    """
    fields = record.split('\t')
    if len(fields) < 3 or '.' not in fields[0]:
      return None

    record_identifier = fields[0].strip()
    hexadecimal_timestamp, _, line_identifier = record_identifier.partition('.')
    if not hexadecimal_timestamp or not line_identifier:
      return None

    message_code = self._ExtractMessageCode(fields)
    if not message_code:
      return None

    try:
      timestamp = int(hexadecimal_timestamp, 16)
    except ValueError:
      parser_mediator.ProduceExtractionWarning(
          f'invalid VC0 timestamp in record: {record_identifier:s}')
      return None

    event_data = IvantiVC0EventData()
    event_data.hostname = fields[1].strip() or None
    event_data.ip_address = (
        self._ExtractIPAddress(fields[5]) if len(fields) > 5 else None)
    event_data.line_identifier = line_identifier
    event_data.log_file_type = self._ExtractLogFileType(source_filename)
    event_data.message_code = message_code
    event_data.realm = fields[4].strip() if len(fields) > 4 else None
    event_data.record_identifier = record_identifier
    event_data.recorded_time = dfdatetime_posix_time.PosixTime(
        timestamp=timestamp)
    event_data.source_filename = source_filename
    event_data.username = fields[6].strip() if len(fields) > 6 else None
    event_data.username = event_data.username or None

    record_values = fields[5:]
    event_data.record_values = '\t'.join(record_values) or None
    event_data.body = self._CreateBody(
        record_values, event_data.ip_address, event_data.realm,
        event_data.username)

    return event_data

  def ParseFileObject(self, parser_mediator, file_object):
    """Parses an Ivanti Connect Secure .vc0 log file-like object.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      file_object (dfvfs.FileIO): a file-like object.

    Raises:
      WrongParser: when the file cannot be parsed.
    """
    file_size = file_object.get_size()
    if file_size < self._HEADER_SIZE or not self._CheckHeader(file_object):
      raise errors.WrongParser('Not an Ivanti .vc0 log file.')

    # Empty .vc0 logs are valid header-only files. Claim them here so another
    # parser does not try to interpret the header bytes as a different format.
    if file_size == self._HEADER_SIZE:
      return

    source_filename = parser_mediator.GetFilename()

    for record in self._ReadRecords(file_object):
      if parser_mediator.abort:
        break

      event_data = self._ParseRecord(
          parser_mediator, record, source_filename)
      if not event_data:
        continue

      parser_mediator.ProduceEventData(event_data)


manager.ParsersManager.RegisterParser(IvantiVC0Parser)
