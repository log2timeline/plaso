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
      0x32: 'bsm_token_data_ipc_perm',
      0x3e: 'bsm_token_data_attr32',
      0x52: 'bsm_token_data_exit',
      0x60: 'bsm_token_data_zonename',
      0x71: 'bsm_token_data_arg64',
      0x72: 'bsm_token_data_return64',
      0x73: 'bsm_token_data_attr64',
      0x74: 'bsm_token_data_header64',
      0x75: 'bsm_token_data_subject64',
      0x77: 'bsm_token_data_subject64',
      0x79: 'bsm_token_data_header64_ex',
      0x7a: 'bsm_token_data_subject32_ex',
      0x7b: 'bsm_token_data_subject32_ex',
      0x7c: 'bsm_token_data_subject64_ex',
      0x7d: 'bsm_token_data_subject64_ex',
      0x7e: 'bsm_token_data_in_addr_ex',
      0x7f: 'bsm_token_data_socket_ex',
      0x80: 'bsm_token_data_sockinet32',
      0x81: 'bsm_token_data_sockinet64',
      0x82: 'bsm_token_data_sockunix',
  }

  _TOKEN_TYPES = {
      0x00: 'AUT_INVALID',
      0x11: 'AUT_OTHER_FILE32',
      0x12: 'AUT_OHEADER',
      0x13: 'AUT_TRAILER',
      0x14: 'AUT_HEADER32',
      0x15: 'AUT_HEADER32_EX',
      0x21: 'AUT_DATA',
      0x22: 'AUT_IPC',
      0x23: 'AUT_PATH',
      0x24: 'AUT_SUBJECT32',
      0x25: 'AUT_XATPATH',
      0x26: 'AUT_PROCESS32',
      0x27: 'AUT_RETURN32',
      0x28: 'AUT_TEXT',
      0x29: 'AUT_OPAQUE',
      0x2a: 'AUT_IN_ADDR',
      0x2b: 'AUT_IP',
      0x2c: 'AUT_IPORT',
      0x2d: 'AUT_ARG32',
      0x2e: 'AUT_SOCKET',
      0x2f: 'AUT_SEQ',
      0x30: 'AUT_ACL',
      0x31: 'AUT_ATTR',
      0x32: 'AUT_IPC_PERM',
      0x33: 'AUT_LABEL',
      0x34: 'AUT_GROUPS',
      0x35: 'AUT_ACE',
      0x36: 'AUT_SLABEL',
      0x37: 'AUT_CLEAR',
      0x38: 'AUT_PRIV',
      0x39: 'AUT_UPRIV',
      0x3a: 'AUT_LIAISON',
      0x3b: 'AUT_NEWGROUPS',
      0x3c: 'AUT_EXEC_ARGS',
      0x3d: 'AUT_EXEC_ENV',
      0x3e: 'AUT_ATTR32',
      0x3f: 'AUT_UNAUTH',
      0x40: 'AUT_XATOM',
      0x41: 'AUT_XOBJ',
      0x42: 'AUT_XPROTO',
      0x43: 'AUT_XSELECT',
      0x44: 'AUT_XCOLORMAP',
      0x45: 'AUT_XCURSOR',
      0x46: 'AUT_XFONT',
      0x47: 'AUT_XGC',
      0x48: 'AUT_XPIXMAP',
      0x49: 'AUT_XPROPERTY',
      0x4a: 'AUT_XWINDOW',
      0x4b: 'AUT_XCLIENT',
      0x51: 'AUT_CMD',
      0x52: 'AUT_EXIT',
      0x60: 'AUT_ZONENAME',
      0x70: 'AUT_HOST',
      0x71: 'AUT_ARG64',
      0x72: 'AUT_RETURN64',
      0x73: 'AUT_ATTR64',
      0x74: 'AUT_HEADER64',
      0x75: 'AUT_SUBJECT64',
      0x76: 'AUT_SERVER64',
      0x77: 'AUT_PROCESS64',
      0x78: 'AUT_OTHER_FILE64',
      0x79: 'AUT_HEADER64_EX',
      0x7a: 'AUT_SUBJECT32_EX',
      0x7b: 'AUT_PROCESS32_EX',
      0x7c: 'AUT_SUBJECT64_EX',
      0x7d: 'AUT_PROCESS64_EX',
      0x7e: 'AUT_IN_ADDR_EX',
      0x7f: 'AUT_SOCKET_EX',
      0x80: 'AUT_SOCKINET32',
      0x81: 'AUT_SOCKINET128',
      0x82: 'AUT_SOCKUNIX'}

  _HEADER_TOKEN_TYPES = frozenset([0x14, 0x15, 0x74, 0x79])

  _TRAILER_TOKEN_TYPE = 0x13

  _TRAILER_TOKEN_SIGNATURE = 0xb105

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

    elif token_type == 0x32:
      return {
          'user_id': token_data.user_identifier,
          'group_id': token_data.group_identifier,
          'creator_user_id': token_data.creator_user_identifier,
          'creator_group_id': token_data.creator_group_identifier,
          'access': token_data.access_mode}

    # elif token_type in (0x34, 0x3b):
    #   arguments = []
    #   for _ in range(token):
    #     arguments.append(
    #         self._RawToUTF8(
    #             self.BSM_TOKEN_DATA_INTEGER.parse_stream(file_object)))
    #   return {bsm_type: ','.join(arguments)}

    # elif token_type in (0x3c, 0x3d):
    #   arguments = []
    #   for _ in range(0, token):
    #     sub_token = self.BSM_TOKEN_EXEC_ARGUMENT.parse_stream(file_object)
    #     string = self._CopyUtf8ByteArrayToString(sub_token.text)
    #     arguments.append(string)
    #   return {'arguments': ' '.join(arguments)}

    elif token_type in (0x3e, 0x73):
      return {
          'mode': token_data.file_mode,
          'uid': token_data.user_identifier,
          'gid': token_data.group_identifier,
          'system_id': token_data.file_system_identifier,
          'node_id': token_data.file_identifier,
          'device': token_data.device}

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

    elif token_type == 0x7e:
      protocol = bsmtoken.BSM_PROTOCOLS.get(token_data.net_type, 'UNKNOWN')
      if token_data.net_type == 4:
        ip_address = self._FormatPackedIPv6Address(token_data.ip_address[:4])
      elif token_data.net_type == 16:
        ip_address = self._FormatPackedIPv6Address(token_data.ip_address)
      return {
          'protocols': protocol,
          'net_type': token_data.net_type,
          'address': ip_address}

    elif token_type in (0x80, 0x81):
      protocol = bsmtoken.BSM_PROTOCOLS.get(token_data.socket_family, 'UNKNOWN')
      if token_type == 0x80:
        ip_address = self._FormatPackedIPv4Address(token_data.ip_addresss)
      elif token_type == 0x81:
        ip_address = self._FormatPackedIPv6Address(token_data.ip_addresss)
      return {
          'protocols': protocol,
          'family': token_data.socket_family,
          'port': token_data.port_number,
          'address': ip_address}

    elif token_type == 0x82:
      protocol = bsmtoken.BSM_PROTOCOLS.get(token_data.socket_family, 'UNKNOWN')
      return {
          'protocols': protocol,
          'family': token_data.socket_family,
          'path': token_data.socket_path}

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

    if token_data.format_version != 11:
      raise errors.ParseError('Unsupported format version type: {0:d}'.format(
          token_data.format_version))

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

      token_type_string = self._TOKEN_TYPES.get(token_type, 'UNKNOWN')
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
