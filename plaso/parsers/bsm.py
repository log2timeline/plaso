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
    event_type (int): identifier that represents the type of the event.
    extra_tokens (list[dict[str, dict[str, str]]]): event extra tokens, which
        is a list of dictionaries that contain: {token type: {token values}}
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

  _TOKEN_TYPE_AUT_TRAILER = 0x13
  _TOKEN_TYPE_AUT_HEADER32 = 0x14
  _TOKEN_TYPE_AUT_HEADER32_EX = 0x15
  _TOKEN_TYPE_AUT_RETURN32 = 0x27
  _TOKEN_TYPE_AUT_RETURN64 = 0x72
  _TOKEN_TYPE_AUT_HEADER64 = 0x74
  _TOKEN_TYPE_AUT_HEADER64_EX = 0x79

  _HEADER_TOKEN_TYPES = frozenset([
      _TOKEN_TYPE_AUT_HEADER32,
      _TOKEN_TYPE_AUT_HEADER32_EX,
      _TOKEN_TYPE_AUT_HEADER64,
      _TOKEN_TYPE_AUT_HEADER64_EX])

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
      0x34: 'bsm_token_data_groups',
      0x3b: 'bsm_token_data_groups',
      0x3c: 'bsm_token_data_exec_args',
      0x3d: 'bsm_token_data_exec_args',
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

  _TRAILER_TOKEN_SIGNATURE = 0xb105

  _TOKEN_DATA_FORMAT_FUNCTIONS = {
      0x11: '_FormatOtherFileToken',
      0x21: '_FormatDataToken',
      0x22: '_FormatIPCToken',
      0x23: '_FormatPathToken',
      0x24: '_FormatSubjectOrProcessToken',
      0x26: '_FormatSubjectOrProcessToken',
      0x27: '_FormatReturnOrExitToken',
      0x28: '_FormatTextToken',
      0x29: '_FormatOpaqueToken',
      0x2a: '_FormatInAddrToken',
      0x2b: '_FormatIPToken',
      0x2c: '_FormatIPortToken',
      0x2d: '_FormatArgToken',
      0x2f: '_FormatSeqToken',
      0x32: '_FormatIPCPermToken',
      0x34: '_FormatGroupsToken',
      0x3b: '_FormatGroupsToken',
      0x3c: '_FormatExecArgsToken',
      0x3d: '_FormatExecArgsToken',
      0x3e: '_FormatAttrToken',
      0x52: '_FormatReturnOrExitToken',
      0x60: '_FormatZonenameToken',
      0x71: '_FormatArgToken',
      0x72: '_FormatReturnOrExitToken',
      0x73: '_FormatAttrToken',
      0x75: '_FormatSubjectOrProcessToken',
      0x77: '_FormatSubjectOrProcessToken',
      0x7a: '_FormatSubjectExOrProcessExToken',
      0x7b: '_FormatSubjectExOrProcessExToken',
      0x7c: '_FormatSubjectExOrProcessExToken',
      0x7d: '_FormatSubjectExOrProcessExToken',
      0x7e: '_FormatInAddrExToken',
      0x7f: '_FormatSocketExToken',
      0x80: '_FormatSocketInet32Token',
      0x81: '_FormatSocketInet128Token',
      0x82: '_FormatSocketUnixToken'}

  def _FormatArgToken(self, token_data):
    """Formats an argument token as a dictionary of values.

    Args:
      token_data (bsm_token_data_arg32|bsm_token_data_arg64): AUT_ARG32 or
          AUT_ARG64 token data.

    Returns:
      dict[str, str]: token values.
    """
    return {
        'string': token_data.argument_value.rstrip('\x00'),
        'num_arg': token_data.argument_index,
        'is': token_data.argument_name}

  def _FormatAttrToken(self, token_data):
    """Formats an attribute token as a dictionary of values.

    Args:
      token_data (bsm_token_data_attr32|bsm_token_data_attr64): AUT_ATTR32 or
          AUT_ATTR64 token data.

    Returns:
      dict[str, str]: token values.
    """
    return {
        'mode': token_data.file_mode,
        'uid': token_data.user_identifier,
        'gid': token_data.group_identifier,
        'system_id': token_data.file_system_identifier,
        'node_id': token_data.file_identifier,
        'device': token_data.device}

  def _FormatDataToken(self, token_data):
    """Formats a data token as a dictionary of values.

    Args:
      token_data (bsm_token_data_data): AUT_DATA token data.

    Returns:
      dict[str, str]: token values.
    """
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

  def _FormatInAddrExToken(self, token_data):
    """Formats an extended IPv4 address token as a dictionary of values.

    Args:
      token_data (bsm_token_data_in_addr_ex): AUT_IN_ADDR_EX token data.

    Returns:
      dict[str, str]: token values.
    """
    protocol = bsmtoken.BSM_PROTOCOLS.get(token_data.net_type, 'UNKNOWN')
    if token_data.net_type == 4:
      ip_address = self._FormatPackedIPv6Address(token_data.ip_address[:4])
    elif token_data.net_type == 16:
      ip_address = self._FormatPackedIPv6Address(token_data.ip_address)
    return {
        'protocols': protocol,
        'net_type': token_data.net_type,
        'address': ip_address}

  def _FormatInAddrToken(self, token_data):
    """Formats an IPv4 address token as a dictionary of values.

    Args:
      token_data (bsm_token_data_in_addr): AUT_IN_ADDR token data.

    Returns:
      dict[str, str]: token values.
    """
    ip_address = self._FormatPackedIPv4Address(token_data.ip_address)
    return {'ip': ip_address}

  def _FormatIPCPermToken(self, token_data):
    """Formats an IPC permissions token as a dictionary of values.

    Args:
      token_data (bsm_token_data_ipc_perm): AUT_IPC_PERM token data.

    Returns:
      dict[str, str]: token values.
    """
    return {
        'user_id': token_data.user_identifier,
        'group_id': token_data.group_identifier,
        'creator_user_id': token_data.creator_user_identifier,
        'creator_group_id': token_data.creator_group_identifier,
        'access': token_data.access_mode}

  def _FormatIPCToken(self, token_data):
    """Formats an IPC token as a dictionary of values.

    Args:
      token_data (bsm_token_data_ipc): AUT_IPC token data.

    Returns:
      dict[str, str]: token values.
    """
    return {
        'object_type': token_data.object_type,
        'object_id': token_data.object_identifier}

  def _FormatGroupsToken(self, token_data):
    """Formats a groups token as a dictionary of values.

    Args:
      token_data (bsm_token_data_groups): AUT_GROUPS or AUT_NEWGROUPS token
          data.

    Returns:
      dict[str, str]: token values.
    """
    return {
        'number_of_groups': token_data.number_of_groups,
        'groups': ', '.join(token_data.groups)}

  def _FormatExecArgsToken(self, token_data):
    """Formats an execution arguments token as a dictionary of values.

    Args:
      token_data (bsm_token_data_exec_args): AUT_EXEC_ARGS or AUT_EXEC_ENV
          token data.

    Returns:
      dict[str, str]: token values.
    """
    return {
        'number_of_strings': token_data.number_of_strings,
        'strings': ', '.join(token_data.strings)}

  def _FormatIPortToken(self, token_data):
    """Formats an IP port token as a dictionary of values.

    Args:
      token_data (bsm_token_data_iport): AUT_IPORT token data.

    Returns:
      dict[str, str]: token values.
    """
    return {'port_number': token_data.port_number}

  def _FormatIPToken(self, token_data):
    """Formats an IPv4 packet header token as a dictionary of values.

    Args:
      token_data (bsm_token_data_ip): AUT_IP token data.

    Returns:
      dict[str, str]: token values.
    """
    data = ''.join(['{0:02x}'.format(byte) for byte in token_data.data])
    return {'IPv4_Header': data}

  def _FormatOpaqueToken(self, token_data):
    """Formats an opaque token as a dictionary of values.

    Args:
      token_data (bsm_token_data_opaque): AUT_OPAQUE token data.

    Returns:
      dict[str, str]: token values.
    """
    data = ''.join(['{0:02x}'.format(byte) for byte in token_data.data])
    return {'data': data}

  def _FormatOtherFileToken(self, token_data):
    """Formats an other file token as a dictionary of values.

    Args:
      token_data (bsm_token_data_other_file32): AUT_OTHER_FILE32 token data.

    Returns:
      dict[str, str]: token values.
    """
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

  def _FormatPathToken(self, token_data):
    """Formats a path token as a dictionary of values.

    Args:
      token_data (bsm_token_data_path): AUT_PATH token data.

    Returns:
      dict[str, str]: token values.
    """
    return {'path': token_data.path.rstrip('\x00')}

  def _FormatReturnOrExitToken(self, token_data):
    """Formats a return or exit token as a dictionary of values.

    Args:
      token_data (bsm_token_data_exit|bsm_token_data_return32|
                  bsm_token_data_return64): AUT_EXIT, AUT_RETURN32 or
          AUT_RETURN64 token data.

    Returns:
      dict[str, str]: token values.
    """
    error_string = bsmtoken.BSM_ERRORS.get(token_data.status, 'UNKNOWN')
    return {
        'error': error_string,
        'token_status': token_data.status,
        'call_status': token_data.return_value}

  def _FormatSeqToken(self, token_data):
    """Formats a sequence token as a dictionary of values.

    Args:
      token_data (bsm_token_data_seq): AUT_SEQ token data.

    Returns:
      dict[str, str]: token values.
    """
    return {'sequence_number': token_data.sequence_number}

  def _FormatSocketExToken(self, token_data):
    """Formats an extended socket token as a dictionary of values.

    Args:
      token_data (bsm_token_data_socket_ex): AUT_SOCKET_EX token data.

    Returns:
      dict[str, str]: token values.
    """
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

  def _FormatSocketInet32Token(self, token_data):
    """Formats an Internet socket token as a dictionary of values.

    Args:
      token_data (bsm_token_data_sockinet32): AUT_SOCKINET32 token data.

    Returns:
      dict[str, str]: token values.
    """
    protocol = bsmtoken.BSM_PROTOCOLS.get(token_data.socket_family, 'UNKNOWN')
    ip_address = self._FormatPackedIPv4Address(token_data.ip_addresss)
    return {
        'protocols': protocol,
        'family': token_data.socket_family,
        'port': token_data.port_number,
        'address': ip_address}

  def _FormatSocketInet128Token(self, token_data):
    """Formats an Internet socket token as a dictionary of values.

    Args:
      token_data (bsm_token_data_sockinet64): AUT_SOCKINET128 token data.

    Returns:
      dict[str, str]: token values.
    """
    protocol = bsmtoken.BSM_PROTOCOLS.get(token_data.socket_family, 'UNKNOWN')
    ip_address = self._FormatPackedIPv6Address(token_data.ip_addresss)
    return {
        'protocols': protocol,
        'family': token_data.socket_family,
        'port': token_data.port_number,
        'address': ip_address}

  def _FormatSocketUnixToken(self, token_data):
    """Formats an Unix socket token as a dictionary of values.

    Args:
      token_data (bsm_token_data_sockunix): AUT_SOCKUNIX token data.

    Returns:
      dict[str, str]: token values.
    """
    protocol = bsmtoken.BSM_PROTOCOLS.get(token_data.socket_family, 'UNKNOWN')
    return {
        'protocols': protocol,
        'family': token_data.socket_family,
        'path': token_data.socket_path}

  def _FormatSubjectOrProcessToken(self, token_data):
    """Formats a subject or process token as a dictionary of values.

    Args:
      token_data (bsm_token_data_subject32|bsm_token_data_subject64):
          AUT_SUBJECT32, AUT_PROCESS32, AUT_SUBJECT64 or AUT_PROCESS64 token
          data.

    Returns:
      dict[str, str]: token values.
    """
    ip_address = self._FormatPackedIPv4Address(token_data.ip_address)
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

  def _FormatSubjectExOrProcessExToken(self, token_data):
    """Formats a subject or process token as a dictionary of values.

    Args:
      token_data (bsm_token_data_subject32_ex|bsm_token_data_subject64_ex):
          AUT_SUBJECT32_EX, AUT_PROCESS32_EX, AUT_SUBJECT64_EX or
          AUT_PROCESS64_EX token data.

    Returns:
      dict[str, str]: token values.
    """
    if token_data.net_type == 4:
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

  def _FormatTextToken(self, token_data):
    """Formats a text token as a dictionary of values.

    Args:
      token_data (bsm_token_data_text): AUT_TEXT token data.

    Returns:
      dict[str, str]: token values.
    """
    return {'text': token_data.text.rstrip('\x00')}

  def _FormatTokenData(self, token_type, token_data):
    """Formats the token data as a dictionary of values.

    Args:
      token_type (int): token type.
      token_data (object): token data.

    Returns:
      dict[str, str]: formatted token values or an empty dictionary if no
          formatted token values could be determined.
    """
    token_data_format_function = self._TOKEN_DATA_FORMAT_FUNCTIONS.get(
        token_type)
    if token_data_format_function:
      token_data_format_function = getattr(
          self, token_data_format_function, None)

    if not token_data_format_function:
      return {}

    return token_data_format_function(token_data)

  def _FormatZonenameToken(self, token_data):
    """Formats a time zone name token as a dictionary of values.

    Args:
      token_data (bsm_token_data_zonename): AUT_ZONENAME token data.

    Returns:
      dict[str, str]: token values.
    """
    return {'name': token_data.name.rstrip('\x00')}

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

    # Check the header token type before reading the token data to prevent
    # variable size tokens to consume a large amount of memory.
    token_type = self._ParseTokenType(file_object, header_record_offset)
    if token_type not in self._HEADER_TOKEN_TYPES:
      raise errors.ParseError(
          'Unsupported header token type: 0x{0:02x}'.format(token_type))

    token_type, token_data = self._ParseToken(file_object, header_record_offset)

    if token_data.format_version != 11:
      raise errors.ParseError('Unsupported format version type: {0:d}'.format(
          token_data.format_version))

    timestamp = token_data.microseconds + (
        token_data.timestamp * definitions.MICROSECONDS_PER_SECOND)

    event_type = token_data.event_type
    header_record_size = token_data.record_size
    record_end_offset = header_record_offset + header_record_size

    event_tokens = []
    return_token_values = None

    file_offset = file_object.tell()
    while file_offset < record_end_offset:
      token_type, token_data = self._ParseToken(file_object, file_offset)
      if not token_data:
        raise errors.ParseError('Unsupported token type: 0x{0:02x}'.format(
            token_type))

      file_offset = file_object.tell()

      if token_type == self._TOKEN_TYPE_AUT_TRAILER:
        break

      token_type_string = self._TOKEN_TYPES.get(token_type, 'UNKNOWN')
      token_values = self._FormatTokenData(token_type, token_data)
      event_tokens.append({token_type_string: token_values})

      if token_type in (
          self._TOKEN_TYPE_AUT_RETURN32, self._TOKEN_TYPE_AUT_RETURN64):
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
      tuple: containing:
        int: token type
        object: token data or None if the token type is not supported.
    """
    token_type = self._ParseTokenType(file_object, file_offset)
    token_data = None

    token_data_map_name = self._DATA_TYPE_MAP_PER_TOKEN_TYPE.get(
        token_type, None)
    if token_data_map_name:
      token_data_map = self._GetDataTypeMap(token_data_map_name)

      token_data, _ = self._ReadStructureFromFileObject(
          file_object, file_offset + 1, token_data_map)

    return token_type, token_data

  def _ParseTokenType(self, file_object, file_offset):
    """Parses a token type.

    Args:
      file_object (dfvfs.FileIO): file-like object.
      file_offset (int): offset of the token relative to the start of
          the file-like object.

    Returns:
      int: token type
    """
    token_type_map = self._GetDataTypeMap('uint8')

    token_type, _ = self._ReadStructureFromFileObject(
        file_object, file_offset, token_type_map)

    return token_type

  def ParseFileObject(self, parser_mediator, file_object):
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
