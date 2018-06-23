# -*- coding: utf-8 -*-
"""Basic Security Module (BSM) event auditing file parser."""

from __future__ import unicode_literals

from dfdatetime import posix_time as dfdatetime_posix_time

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.lib import errors
from plaso.parsers import dtfabric_parser
from plaso.parsers import manager
from plaso.unix import bsmtoken


class BSMEventData(events.EventData):
  """Basic Security Module (BSM) audit event data.

  Attributes:
    event_type (str): text with identifier that represents the type of
        the event.
    extra_tokens (dict[str, dict[str, str]]): event extra tokens.
    record_length (int): record length in bytes (trailer number).
    return_value (str): processed return value and exit status.
  """

  DATA_TYPE = 'bsm:event'

  def __init__(self):
    """Initializes event data."""
    super(BSMEventData, self).__init__(data_type=self.DATA_TYPE)
    self.event_type = None
    self.extra_tokens = None
    self.record_length = None
    self.return_value = None


class BSMParser(dtfabric_parser.DtFabricBaseParser):
  """Parser for BSM files."""

  NAME = 'bsm_log'
  DESCRIPTION = 'Parser for BSM log files.'

  _DEFINITION_FILE = 'bsm.yaml'

  # BSM supported version (0x0b = 11).
  AUDIT_HEADER_VERSION = 11

  # Token types with unknown data format:
  # 0x12: AUT_OHEADER
  _DATA_TYPE_MAP_PER_TOKEN_TYPE = {
      0x11: 'bsm_token_data_other_file32',
      0x13: 'bsm_token_data_trailer',
      0x14: 'bsm_token_data_header32',
      0x15: 'bsm_token_data_header32_ex',
      0x21: 'bsm_token_data_data',
      0x22: 'bsm_token_data_ipc',
      0x23: 'bsm_token_data_path',
      0x24: 'bsm_token_data_subject32',
      0x26: 'bsm_token_data_subject32',
      0x27: 'bsm_token_data_return32',
      0x28: 'bsm_token_data_text',
      0x29: 'bsm_token_data_opaque',
      0x2a: 'bsm_token_data_in_addr',
      0x2b: 'bsm_token_data_ip',
      0x2c: 'bsm_token_data_iport',
      0x2d: 'bsm_token_data_arg32',
      0x2f: 'bsm_token_data_seq',
      0x52: 'bsm_token_data_exit',
      0x60: 'bsm_token_data_zonename',
      0x71: 'bsm_token_data_arg64',
      0x72: 'bsm_token_data_return64',
      0x75: 'bsm_token_data_subject64',
      0x77: 'bsm_token_data_subject64',
      0x7a: 'bsm_token_data_subject32_ex',
      0x7b: 'bsm_token_data_subject32_ex',
      0x7c: 'bsm_token_data_subject64_ex',
      0x7d: 'bsm_token_data_subject64_ex',
      0x7f: 'bsm_token_data_socket_ex',
  }

  _HEADER_TOKEN_TYPES = frozenset([0x14, 0x15])

  _TRAILER_TOKEN_TYPE = 0x13

  _TRAILER_TOKEN_SIGNATURE = 0xb105

  _TOKEN_TYPE_STRINGS = {
      0x11: 'BSM_TOKEN_FILE',
      0x13: 'BSM_TOKEN_TRAILER',
      0x14: 'BSM_HEADER32',
      0x15: 'BSM_HEADER32_EX',
      0x21: 'BSM_TOKEN_DATA',
      0x22: 'BSM_TOKEN_IPC',
      0x23: 'BSM_TOKEN_PATH',
      0x24: 'BSM_TOKEN_SUBJECT32',
      0x26: 'BSM_TOKEN_PROCESS32',
      0x27: 'BSM_TOKEN_RETURN32',
      0x28: 'BSM_TOKEN_TEXT',
      0x29: 'BSM_TOKEN_OPAQUE',
      0x2a: 'BSM_TOKEN_IN_ADDR',
      0x2b: 'BSM_TOKEN_IP',
      0x2c: 'BSM_TOKEN_IPORT',
      0x2d: 'BSM_TOKEN_ARG32',
      0x2f: 'BSM_TOKEN_SEQ',
      0x60: 'BSM_TOKEN_ZONENAME',
      0x71: 'BSM_TOKEN_ARG64',
      0x75: 'BSM_TOKEN_SUBJECT64',
      0x77: 'BSM_TOKEN_PROCESS64',
      0x7a: 'BSM_TOKEN_SUBJECT32_EX',
      0x7b: 'BSM_TOKEN_PROCESS32_EX',
      0x7c: 'BSM_TOKEN_SUBJECT64_EX',
      0x7d: 'BSM_TOKEN_PROCESS64_EX',
      0x7f: 'BSM_TOKEN_SOCKET_EX'}

  def _FormatTokenData(self, token_type, token_data):
    """Formats the token data as a dictionary of values.

    Args:
      token_type (int): token type.
      token_data (object): token data.

    Returns:
      dict[str, str]: token values.
    """
    if token_type == 0x11:
      # TODO: if this timestamp is useful, it must be extracted as a separate
      # event object.
      timestamp = token_data.microseconds + (
          token_data.timestamp * definitions.MICROSECONDS_PER_SECOND)
      date_time = dfdatetime_posix_time.PosixTimeInMicroseconds(
          timestamp=timestamp)
      date_time_string = date_time.CopyToDateTimeString()

      return {
          'string': token_data.name.rstrip('\x00'),
          'timestamp': date_time_string}

    elif token_type == 0x21:
      format_string = bsmtoken.BSM_TOKEN_DATA_PRINT.get(
          token_data.data_format, 'UNKNOWN')

      if token_data.data_format == 4:
        data = bytes(bytearray(token_data.data)).split(b'\x00')[0]
        data = data.decode('utf-8')
      else:
        data = ''.join(['{0:02x}'.format(byte) for byte in token_data.data])
      return {
          'format': format_string,
          'data': data}

    elif token_type == 0x22:
      return {
          'object_type': token_data.object_type,
          'object_id': token_data.object_identifier}

    elif token_type == 0x23:
      return {'path': token_data.path.rstrip('\x00')}

    elif token_type in (0x24, 0x26, 0x75, 0x77, 0x7a, 0x7b, 0x7c, 0x7d):
      if token_type in (0x24, 0x26, 0x75, 0x77) or token_data.net_type == 4:
        ip_address = self._FormatPackedIPv4Address(token_data.ip_address)
      elif token_data.net_type == 16:
        ip_address = self._FormatPackedIPv6Address(token_data.ip_address)
      else:
        ip_address = 'unknown'

      return {
          'aid': token_data.audit_user_identifier,
          'euid': token_data.effective_user_identifier,
          'egid': token_data.effective_group_identifier,
          'uid': token_data.real_user_identifier,
          'gid': token_data.real_group_identifier,
          'pid': token_data.process_identifier,
          'session_id': token_data.session_identifier,
          'terminal_port': token_data.terminal_port,
          'terminal_ip': ip_address}

    elif token_type in (0x27, 0x52, 0x72):
      error_string = bsmtoken.BSM_ERRORS.get(token_data.status, 'UNKNOWN')
      return {
          'error': error_string,
          'token_status': token_data.status,
          'call_status': token_data.return_value}

    elif token_type == 0x28:
      return {'text': token_data.text.rstrip('\x00')}

    elif token_type == 0x29:
      data = ''.join(['{0:02x}'.format(byte) for byte in token_data.data])
      return {'data': data}

    elif token_type == 0x2a:
      ip_address = self._FormatPackedIPv4Address(token_data.ip_address)
      return {'ip': ip_address}

    elif token_type == 0x2b:
      data = ''.join(['{0:02x}'.format(byte) for byte in token_data.data])
      return {'IPv4_Header': data}

    elif token_type == 0x2c:
      return {'port_number': token_data.port_number}

    elif token_type in (0x2d, 0x71):
      return {
          'string': token_data.argument_value.rstrip('\x00'),
          'num_arg': token_data.argument_index,
          'is': token_data.argument_name}

    elif token_type == 0x2f:
      return {'sequence_number': token_data.sequence_number}

    # elif token_type in (0x31, 0x3e, 0x73):
    #   return {
    #       'mode': token_data.file_mode,
    #       'uid': token_data.user_identifier,
    #       'gid': token_data.group_identifier,
    #       'system_id': token_data.file_system_id,
    #       'node_id': token_data.file_system_node_id,
    #       'device': token_data.device}

    # elif token_type in (0x3c, 0x3d):
    #   arguments = []
    #   for _ in range(0, token):
    #     sub_token = self.BSM_TOKEN_EXEC_ARGUMENT.parse_stream(file_object)
    #     string = self._CopyUtf8ByteArrayToString(sub_token.text)
    #     arguments.append(string)
    #   return {'arguments': ' '.join(arguments)}

    elif token_type == 0x60:
      return {'name': token_data.name.rstrip('\x00')}

    elif token_type == 0x7f:
      if token_data.socket_domain == 10:
        local_ip_address = self._FormatPackedIPv6Address(
            token_data.local_ip_address)
        remote_ip_address = self._FormatPackedIPv6Address(
            token_data.remote_ip_address)
      else:
        local_ip_address = self._FormatPackedIPv4Address(
            token_data.local_ip_address)
        remote_ip_address = self._FormatPackedIPv4Address(
            token_data.remote_ip_address)

      return {
          'from': local_ip_address,
          'from_port': token_data.local_port,
          'to': remote_ip_address,
          'to_port': token_data.remote_port}

    # elif bsm_type in (
    #       'BSM_TOKEN_AUT_SOCKINET32', 'BSM_TOKEN_AUT_SOCKINET128'):
    #   protocol = bsmtoken.BSM_PROTOCOLS.get(token_data.net_type, 'UNKNOWN')
    #   if bsm_type == 'BSM_TOKEN_AUT_SOCKINET32':
    #     ip_address = self._FormatPackedIPv4Address(token_data.ip_addresss)
    #   elif bsm_type == 'BSM_TOKEN_AUT_SOCKINET128':
    #     ip_address = self._FormatPackedIPv6Address(token_data.ip_addresss)
    #   return {
    #       'protocols': protocol,
    #       'net_type': token_data.net_type,
    #       'port': token_data.port_number,
    #       'address': ip_address}

    # elif bsm_type == 'BSM_TOKEN_ADDR_EXT':
    #   protocol = bsmtoken.BSM_PROTOCOLS.get(token.net_type, 'UNKNOWN')
    #   ip_address = self._FormatPackedIPv6Address(token_data.ip_address)
    #   return {
    #       'protocols': protocol,
    #       'net_type': token.net_type,
    #       'address': ip_address}

    # elif token_type in (0x34, 0x3b):
    #   arguments = []
    #   for _ in range(token):
    #     arguments.append(
    #         self._RawToUTF8(
    #             self.BSM_TOKEN_DATA_INTEGER.parse_stream(file_object)))
    #   return {bsm_type: ','.join(arguments)}

    # elif bsm_type == 'BSM_TOKEN_IPC_PERM':
    #   return {bsm_type: {
    #       'user_id': token.user_id,
    #       'group_id': token.group_id,
    #       'creator_user_id': token.creator_user_id,
    #       'creator_group_id': token.creator_group_id,
    #       'access': token.access_mode}}

    # elif bsm_type == 'BSM_TOKEN_SOCKET_UNIX':
    #   string = self._CopyUtf8ByteArrayToString(token.path)
    #   return {bsm_type: {'family': token.family, 'path': string}}

    return {}

  def _ParseRecord(self, parser_mediator, file_object):
    """Parses an event record.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      file_object (dfvfs.FileIO): file-like object.

    Raises:
      ParseError: if the event record cannot be read.
    """
    header_record_offset = file_object.tell()
    token_type, token_data = self._ParseToken(file_object, header_record_offset)

    if token_type not in self._HEADER_TOKEN_TYPES:
      raise errors.ParseError(
          'Unsupported header token type: 0x{0:02x}'.format(token_type))

    # TODO: move event type string lookup into formatter.
    event_type_string = bsmtoken.BSM_AUDIT_EVENT.get(
        token_data.event_type, 'UNKNOWN')
    event_type = '{0:s} ({1:d})'.format(
        event_type_string, token_data.event_type)

    timestamp = token_data.microseconds + (
        token_data.timestamp * definitions.MICROSECONDS_PER_SECOND)

    header_record_size = token_data.record_size
    record_end_offset = header_record_offset + header_record_size

    # TODO: make this a list since an event record could contain multiple
    # tokens of the same type and has no specific order.
    event_tokens = {}
    return_token_values = None

    file_offset = file_object.tell()
    while file_offset < record_end_offset:
      token_type, token_data = self._ParseToken(file_object, file_offset)
      if not token_data:
        raise errors.ParseError('Unsupported token type: 0x{0:02x}'.format(
            token_type))

      file_offset = file_object.tell()

      if token_type == self._TRAILER_TOKEN_TYPE:
        break

      token_type_string = self._TOKEN_TYPE_STRINGS.get(token_type, 'UNKNOWN')
      token_values = self._FormatTokenData(token_type, token_data)
      event_tokens[token_type_string] = token_values

      if token_type in (0x27, 0x72):
        return_token_values = token_values

    if token_data.signature != self._TRAILER_TOKEN_SIGNATURE:
      raise errors.ParseError('Unsupported signature in trailer token.')

    if token_data.record_size != header_record_size:
      raise errors.ParseError(
          'Mismatch of event record size between header and trailer token.')

    event_data = BSMEventData()
    event_data.event_type = event_type
    event_data.extra_tokens = event_tokens
    event_data.offset = header_record_offset
    event_data.record_length = header_record_size
    event_data.return_value = return_token_values

    date_time = dfdatetime_posix_time.PosixTimeInMicroseconds(
        timestamp=timestamp)
    event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_CREATION)
    parser_mediator.ProduceEventWithEventData(event, event_data)

  def _ParseToken(self, file_object, file_offset):
    """Parses a token.

    Args:
      file_object (dfvfs.FileIO): file-like object.
      file_offset (int): offset of the token relative to the start of
          the file-like object.

    Returns:
      tuple[int, object]: token type and token data or None if the token
          type is not supported.
    """
    token_type_map = self._GetDataTypeMap('uint8')

    token_type, _ = self._ReadStructureFromFileObject(
        file_object, file_offset, token_type_map)

    token_data = None
    token_data_map_name = self._DATA_TYPE_MAP_PER_TOKEN_TYPE.get(
        token_type, None)
    if token_data_map_name:
      token_data_map = self._GetDataTypeMap(token_data_map_name)

      token_data, _ = self._ReadStructureFromFileObject(
          file_object, file_offset + 1, token_data_map)

    return token_type, token_data

  def ParseFileObject(self, parser_mediator, file_object, **kwargs):
    """Parses a BSM file-like object.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      file_object (dfvfs.FileIO): a file-like object.

    Raises:
      UnableToParseFile: when the file cannot be parsed.
    """
    file_offset = file_object.get_offset()
    file_size = file_object.get_size()
    while file_offset < file_size:
      try:
        self._ParseRecord(parser_mediator, file_object)
      except errors.ParseError as exception:
        if file_offset == 0:
          raise errors.UnableToParseFile(
              'Unable to parse first event record with error: {0!s}'.format(
                  exception))

        # TODO: skip to next event record.

      file_offset = file_object.get_offset()


manager.ParsersManager.RegisterParser(BSMParser)
