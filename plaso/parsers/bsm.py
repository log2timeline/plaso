# -*- coding: utf-8 -*-
"""Basic Security Module Parser."""

import binascii
import construct
import logging
import os
import socket

from plaso.lib import errors
from plaso.lib import event
from plaso.lib import eventdata
from plaso.lib import timelib
from plaso.unix import bsmtoken
from plaso.parsers import interface
from plaso.parsers import manager

import pytz


__author__ = 'Joaquin Moreno Garijo (Joaquin.MorenoGarijo.2013@live.rhul.ac.uk)'


# Note that we're using Array and a helper function here instead of
# PascalString because the latter seems to break pickling on Windows.

def _BsmTokenGetLength(context):
  """Construct context parser helper function to replace lambda."""
  return context.length


# Note that we're using RepeatUntil and a helper function here instead of
# CString because the latter seems to break pickling on Windows.

def _BsmTokenIsEndOfString(value, unused_context):
  """Construct context parser helper function to replace lambda."""
  return value == '\x00'


# Note that we're using Switch and a helper function here instead of
# IfThenElse because the latter seems to break pickling on Windows.

def _BsmTokenGetNetType(context):
  """Construct context parser helper function to replace lambda."""
  return context.net_type


def _BsmTokenGetSocketDomain(context):
  """Construct context parser helper function to replace lambda."""
  return context.socket_domain


class MacBsmEvent(event.EventObject):
  """Convenience class for a Mac OS X BSM event."""

  DATA_TYPE = 'mac:bsm:event'

  def __init__(
      self, event_type, timestamp, extra_tokens,
      return_value, record_length, offset):
    """Initializes the event object.

    Args:
      event_type: String with the text and ID that represents the event type.
      timestamp: Entry Epoch timestamp in UTC.
      extra_tokens: List of the extra tokens of the entry.
      return_value: String with the process return value and exit status.
      record_length: Record length in bytes (trailer number).
      offset: The offset in bytes to where the record starts in the file.
    """
    super(MacBsmEvent, self).__init__()
    self.timestamp = timestamp
    self.timestamp_desc = eventdata.EventTimestamp.CREATION_TIME
    self.event_type = event_type
    self.extra_tokens = extra_tokens
    self.return_value = return_value
    self.record_length = record_length
    self.offset = offset


class BsmEvent(event.EventObject):
  """Convenience class for a Generic BSM event."""

  DATA_TYPE = 'bsm:event'

  def __init__(
      self, event_type, timestamp, extra_tokens, record_length, offset):
    """Initializes the event object.

    Args:
      event_type: Text and integer ID that represents the type of the event.
      timestamp: Timestamp of the entry.
      extra_tokens: List of the extra tokens of the entry.
      record_length: Record length in bytes (trailer number).
      offset: The offset in bytes to where the record starts in the file.
    """
    super(BsmEvent, self).__init__()
    self.timestamp = timestamp
    self.timestamp_desc = eventdata.EventTimestamp.CREATION_TIME
    self.event_type = event_type
    self.extra_tokens = extra_tokens
    self.record_length = record_length
    self.offset = offset


class BsmParser(interface.SingleFileBaseParser):
  """Parser for BSM files."""

  _INITIAL_FILE_OFFSET = None

  NAME = 'bsm_log'
  DESCRIPTION = u'Parser for BSM log files.'

  # BSM supported version (0x0b = 11).
  AUDIT_HEADER_VERSION = 11

  # Magic Trail Header.
  BSM_TOKEN_TRAILER_MAGIC = 'b105'

  # IP Version constants.
  AU_IPv4 = 4
  AU_IPv6 = 16

  IPV4_STRUCT = construct.UBInt32('ipv4')

  IPV6_STRUCT = construct.Struct(
      'ipv6', construct.UBInt64('high'), construct.UBInt64('low'))

  # Tested structures.
  # INFO: I have ommited the ID in the structures declaration.
  #       I used the BSM_TYPE first to read the ID, and then, the structure.
  # Tokens always start with an ID value that identifies their token
  # type and subsequent structure.
  BSM_TYPE = construct.UBInt8('token_id')

  # Data type structures.
  BSM_TOKEN_DATA_CHAR = construct.String('value', 1)
  BSM_TOKEN_DATA_SHORT = construct.UBInt16('value')
  BSM_TOKEN_DATA_INTEGER = construct.UBInt32('value')

  # Common structure used by other structures.
  # audit_uid: integer, uid that generates the entry.
  # effective_uid: integer, the permission user used.
  # effective_gid: integer, the permission group used.
  # real_uid: integer, user id of the user that execute the process.
  # real_gid: integer, group id of the group that execute the process.
  # pid: integer, identification number of the process.
  # session_id: unknown, need research.
  BSM_TOKEN_SUBJECT_SHORT = construct.Struct(
      'subject_data',
      construct.UBInt32('audit_uid'),
      construct.UBInt32('effective_uid'),
      construct.UBInt32('effective_gid'),
      construct.UBInt32('real_uid'),
      construct.UBInt32('real_gid'),
      construct.UBInt32('pid'),
      construct.UBInt32('session_id'))

  # Common structure used by other structures.
  # Identify the kind of inet (IPv4 or IPv6)
  # TODO: instead of 16, AU_IPv6 must be used.
  BSM_IP_TYPE_SHORT = construct.Struct(
      'bsm_ip_type_short',
      construct.UBInt32('net_type'),
      construct.Switch(
          'ip_addr',
          _BsmTokenGetNetType,
          {16: IPV6_STRUCT},
          default=IPV4_STRUCT))

  # Initial fields structure used by header structures.
  # length: integer, the length of the entry, equal to trailer (doc: length).
  # version: integer, version of BSM (AUDIT_HEADER_VERSION).
  # event_type: integer, the type of event (/etc/security/audit_event).
  # modifier: integer, unknown, need research (It is always 0).
  BSM_HEADER = construct.Struct(
      'bsm_header',
      construct.UBInt32('length'),
      construct.UBInt8('version'),
      construct.UBInt16('event_type'),
      construct.UBInt16('modifier'))

  # First token of one entry.
  # timestamp: integer, Epoch timestamp of the entry.
  # microsecond: integer, the microsecond of the entry.
  BSM_HEADER32 = construct.Struct(
      'bsm_header32',
      BSM_HEADER,
      construct.UBInt32('timestamp'),
      construct.UBInt32('microsecond'))

  BSM_HEADER64 = construct.Struct(
      'bsm_header64',
      BSM_HEADER,
      construct.UBInt64('timestamp'),
      construct.UBInt64('microsecond'))

  BSM_HEADER32_EX = construct.Struct(
      'bsm_header32_ex',
      BSM_HEADER,
      BSM_IP_TYPE_SHORT,
      construct.UBInt32('timestamp'),
      construct.UBInt32('microsecond'))

  # Token TEXT, provides extra information.
  BSM_TOKEN_TEXT = construct.Struct(
      'bsm_token_text',
      construct.UBInt16('length'),
      construct.Array(
          _BsmTokenGetLength,
          construct.UBInt8('text')))

  # Path of the executable.
  BSM_TOKEN_PATH = BSM_TOKEN_TEXT

  # Identified the end of the record (follow by TRAILER).
  # status: integer that identifies the status of the exit (BSM_ERRORS).
  # return: returned value from the operation.
  BSM_TOKEN_RETURN32 = construct.Struct(
      'bsm_token_return32',
      construct.UBInt8('status'),
      construct.UBInt32('return_value'))

  BSM_TOKEN_RETURN64 = construct.Struct(
      'bsm_token_return64',
      construct.UBInt8('status'),
      construct.UBInt64('return_value'))

  # Identified the number of bytes that was written.
  # magic: 2 bytes that identifies the TRAILER (BSM_TOKEN_TRAILER_MAGIC).
  # length: integer that has the number of bytes from the entry size.
  BSM_TOKEN_TRAILER = construct.Struct(
      'bsm_token_trailer',
      construct.UBInt16('magic'),
      construct.UBInt32('record_length'))

  # A 32-bits argument.
  # num_arg: the number of the argument.
  # name_arg: the argument's name.
  # text: the string value of the argument.
  BSM_TOKEN_ARGUMENT32 = construct.Struct(
      'bsm_token_argument32',
      construct.UBInt8('num_arg'),
      construct.UBInt32('name_arg'),
      construct.UBInt16('length'),
      construct.Array(
          _BsmTokenGetLength,
          construct.UBInt8('text')))

  # A 64-bits argument.
  # num_arg: integer, the number of the argument.
  # name_arg: text, the argument's name.
  # text: the string value of the argument.
  BSM_TOKEN_ARGUMENT64 = construct.Struct(
      'bsm_token_argument64',
      construct.UBInt8('num_arg'),
      construct.UBInt64('name_arg'),
      construct.UBInt16('length'),
      construct.Array(
          _BsmTokenGetLength,
          construct.UBInt8('text')))

  # Identify an user.
  # terminal_id: unknown, research needed.
  # terminal_addr: unknown, research needed.
  BSM_TOKEN_SUBJECT32 = construct.Struct(
      'bsm_token_subject32',
      BSM_TOKEN_SUBJECT_SHORT,
      construct.UBInt32('terminal_port'),
      IPV4_STRUCT)

  # Identify an user using a extended Token.
  # terminal_port: unknown, need research.
  # net_type: unknown, need research.
  BSM_TOKEN_SUBJECT32_EX = construct.Struct(
      'bsm_token_subject32_ex',
      BSM_TOKEN_SUBJECT_SHORT,
      construct.UBInt32('terminal_port'),
      BSM_IP_TYPE_SHORT)

  # au_to_opaque // AUT_OPAQUE
  BSM_TOKEN_OPAQUE = BSM_TOKEN_TEXT

  # au_to_seq // AUT_SEQ
  BSM_TOKEN_SEQUENCE = BSM_TOKEN_DATA_INTEGER

  # Program execution with options.
  # For each argument we are going to have a string+ "\x00".
  # Example: [00 00 00 02][41 42 43 00 42 42 00]
  #          2 Arguments, Arg1: [414243] Arg2: [4242].
  BSM_TOKEN_EXEC_ARGUMENTS = construct.UBInt32('number_arguments')

  BSM_TOKEN_EXEC_ARGUMENT = construct.Struct(
      'bsm_token_exec_argument',
      construct.RepeatUntil(
          _BsmTokenIsEndOfString,
          construct.StaticField("text", 1)))

  # au_to_in_addr // AUT_IN_ADDR:
  BSM_TOKEN_ADDR = IPV4_STRUCT

  # au_to_in_addr_ext // AUT_IN_ADDR_EX:
  BSM_TOKEN_ADDR_EXT = construct.Struct(
      'bsm_token_addr_ext',
      construct.UBInt32('net_type'),
      IPV6_STRUCT)

  # au_to_ip // AUT_IP:
  # TODO: parse this header in the correct way.
  BSM_TOKEN_IP = construct.String('binary_ipv4_add', 20)

  # au_to_ipc // AUT_IPC:
  BSM_TOKEN_IPC = construct.Struct(
      'bsm_token_ipc',
      construct.UBInt8('object_type'),
      construct.UBInt32('object_id'))

  # au_to_ipc_perm // au_to_ipc_perm
  BSM_TOKEN_IPC_PERM = construct.Struct(
      'bsm_token_ipc_perm',
      construct.UBInt32('user_id'),
      construct.UBInt32('group_id'),
      construct.UBInt32('creator_user_id'),
      construct.UBInt32('creator_group_id'),
      construct.UBInt32('access_mode'),
      construct.UBInt32('slot_seq'),
      construct.UBInt32('key'))

  # au_to_iport // AUT_IPORT:
  BSM_TOKEN_PORT = construct.UBInt16('port_number')

  # au_to_file // AUT_OTHER_FILE32:
  BSM_TOKEN_FILE = construct.Struct(
      'bsm_token_file',
      construct.UBInt32('timestamp'),
      construct.UBInt32('microsecond'),
      construct.UBInt16('length'),
      construct.Array(
          _BsmTokenGetLength,
          construct.UBInt8('text')))

  # au_to_subject64 // AUT_SUBJECT64:
  BSM_TOKEN_SUBJECT64 = construct.Struct(
      'bsm_token_subject64',
      BSM_TOKEN_SUBJECT_SHORT,
      construct.UBInt64('terminal_port'),
      IPV4_STRUCT)

  # au_to_subject64_ex // AU_IPv4:
  BSM_TOKEN_SUBJECT64_EX = construct.Struct(
      'bsm_token_subject64_ex',
      BSM_TOKEN_SUBJECT_SHORT,
      construct.UBInt32('terminal_port'),
      construct.UBInt32('terminal_type'),
      BSM_IP_TYPE_SHORT)

  # au_to_process32 // AUT_PROCESS32:
  BSM_TOKEN_PROCESS32 = construct.Struct(
      'bsm_token_process32',
      BSM_TOKEN_SUBJECT_SHORT,
      construct.UBInt32('terminal_port'),
      IPV4_STRUCT)

  # au_to_process64 // AUT_PROCESS32:
  BSM_TOKEN_PROCESS64 = construct.Struct(
      'bsm_token_process64',
      BSM_TOKEN_SUBJECT_SHORT,
      construct.UBInt64('terminal_port'),
      IPV4_STRUCT)

  # au_to_process32_ex // AUT_PROCESS32_EX:
  BSM_TOKEN_PROCESS32_EX = construct.Struct(
      'bsm_token_process32_ex',
      BSM_TOKEN_SUBJECT_SHORT,
      construct.UBInt32('terminal_port'),
      BSM_IP_TYPE_SHORT)

  # au_to_process64_ex // AUT_PROCESS64_EX:
  BSM_TOKEN_PROCESS64_EX = construct.Struct(
      'bsm_token_process64_ex',
      BSM_TOKEN_SUBJECT_SHORT,
      construct.UBInt64('terminal_port'),
      BSM_IP_TYPE_SHORT)

  # au_to_sock_inet32 // AUT_SOCKINET32:
  BSM_TOKEN_AUT_SOCKINET32 = construct.Struct(
      'bsm_token_aut_sockinet32',
      construct.UBInt16('net_type'),
      construct.UBInt16('port_number'),
      IPV4_STRUCT)

  # Info: checked against the source code of XNU, but not against
  #       real BSM file.
  BSM_TOKEN_AUT_SOCKINET128 = construct.Struct(
      'bsm_token_aut_sockinet128',
      construct.UBInt16('net_type'),
      construct.UBInt16('port_number'),
      IPV6_STRUCT)

  INET6_ADDR_TYPE = construct.Struct(
      'addr_type',
      construct.UBInt16('ip_type'),
      construct.UBInt16('source_port'),
      construct.UBInt64('saddr_high'),
      construct.UBInt64('saddr_low'),
      construct.UBInt16('destination_port'),
      construct.UBInt64('daddr_high'),
      construct.UBInt64('daddr_low'))

  INET4_ADDR_TYPE = construct.Struct(
      'addr_type',
      construct.UBInt16('ip_type'),
      construct.UBInt16('source_port'),
      construct.UBInt32('source_address'),
      construct.UBInt16('destination_port'),
      construct.UBInt32('destination_address'))

  # au_to_socket_ex // AUT_SOCKET_EX
  # TODO: Change the 26 for unixbsm.BSM_PROTOCOLS.INET6.
  BSM_TOKEN_AUT_SOCKINET32_EX = construct.Struct(
      'bsm_token_aut_sockinet32_ex',
      construct.UBInt16('socket_domain'),
      construct.UBInt16('socket_type'),
      construct.Switch(
          'structure_addr_port',
          _BsmTokenGetSocketDomain,
          {26: INET6_ADDR_TYPE},
          default=INET4_ADDR_TYPE))

  # au_to_sock_unix // AUT_SOCKUNIX
  BSM_TOKEN_SOCKET_UNIX = construct.Struct(
      'bsm_token_au_to_sock_unix',
      construct.UBInt16('family'),
      construct.RepeatUntil(
          _BsmTokenIsEndOfString,
          construct.StaticField("path", 1)))

  # au_to_data // au_to_data
  # how to print: bsmtoken.BSM_TOKEN_DATA_PRINT.
  # type: bsmtoken.BSM_TOKEN_DATA_TYPE.
  # unit_count: number of type values.
  # BSM_TOKEN_DATA has a end field = type * unit_count
  BSM_TOKEN_DATA = construct.Struct(
      'bsm_token_data',
      construct.UBInt8('how_to_print'),
      construct.UBInt8('data_type'),
      construct.UBInt8('unit_count'))

  # au_to_attr32 // AUT_ATTR32
  BSM_TOKEN_ATTR32 = construct.Struct(
      'bsm_token_attr32',
      construct.UBInt32('file_mode'),
      construct.UBInt32('uid'),
      construct.UBInt32('gid'),
      construct.UBInt32('file_system_id'),
      construct.UBInt64('file_system_node_id'),
      construct.UBInt32('device'))

  # au_to_attr64 // AUT_ATTR64
  BSM_TOKEN_ATTR64 = construct.Struct(
      'bsm_token_attr64',
      construct.UBInt32('file_mode'),
      construct.UBInt32('uid'),
      construct.UBInt32('gid'),
      construct.UBInt32('file_system_id'),
      construct.UBInt64('file_system_node_id'),
      construct.UBInt64('device'))

  # au_to_exit // AUT_EXIT
  BSM_TOKEN_EXIT = construct.Struct(
      'bsm_token_exit',
      construct.UBInt32('status'),
      construct.UBInt32('return_value'))

  # au_to_newgroups // AUT_NEWGROUPS
  # INFO: we must read BSM_TOKEN_DATA_INTEGER for each group.
  BSM_TOKEN_GROUPS = construct.UBInt16('group_number')

  # au_to_exec_env == au_to_exec_args
  BSM_TOKEN_EXEC_ENV = BSM_TOKEN_EXEC_ARGUMENTS

  # au_to_zonename //AUT_ZONENAME
  BSM_TOKEN_ZONENAME = BSM_TOKEN_TEXT

  # Token ID.
  # List of valid Token_ID.
  # Token_ID -> [NAME_STRUCTURE, STRUCTURE]
  # Only the checked structures are been added to the valid structures lists.
  BSM_TYPE_LIST = {
      17: ['BSM_TOKEN_FILE', BSM_TOKEN_FILE],
      19: ['BSM_TOKEN_TRAILER', BSM_TOKEN_TRAILER],
      20: ['BSM_HEADER32', BSM_HEADER32],
      21: ['BSM_HEADER64', BSM_HEADER64],
      33: ['BSM_TOKEN_DATA', BSM_TOKEN_DATA],
      34: ['BSM_TOKEN_IPC', BSM_TOKEN_IPC],
      35: ['BSM_TOKEN_PATH', BSM_TOKEN_PATH],
      36: ['BSM_TOKEN_SUBJECT32', BSM_TOKEN_SUBJECT32],
      38: ['BSM_TOKEN_PROCESS32', BSM_TOKEN_PROCESS32],
      39: ['BSM_TOKEN_RETURN32', BSM_TOKEN_RETURN32],
      40: ['BSM_TOKEN_TEXT', BSM_TOKEN_TEXT],
      41: ['BSM_TOKEN_OPAQUE', BSM_TOKEN_OPAQUE],
      42: ['BSM_TOKEN_ADDR', BSM_TOKEN_ADDR],
      43: ['BSM_TOKEN_IP', BSM_TOKEN_IP],
      44: ['BSM_TOKEN_PORT', BSM_TOKEN_PORT],
      45: ['BSM_TOKEN_ARGUMENT32', BSM_TOKEN_ARGUMENT32],
      47: ['BSM_TOKEN_SEQUENCE', BSM_TOKEN_SEQUENCE],
      96: ['BSM_TOKEN_ZONENAME', BSM_TOKEN_ZONENAME],
      113: ['BSM_TOKEN_ARGUMENT64', BSM_TOKEN_ARGUMENT64],
      114: ['BSM_TOKEN_RETURN64', BSM_TOKEN_RETURN64],
      116: ['BSM_HEADER32_EX', BSM_HEADER32_EX],
      119: ['BSM_TOKEN_PROCESS64', BSM_TOKEN_PROCESS64],
      122: ['BSM_TOKEN_SUBJECT32_EX', BSM_TOKEN_SUBJECT32_EX],
      127: ['BSM_TOKEN_AUT_SOCKINET32_EX', BSM_TOKEN_AUT_SOCKINET32_EX],
      128: ['BSM_TOKEN_AUT_SOCKINET32', BSM_TOKEN_AUT_SOCKINET32]}

  # Untested structures.
  # When not tested structure is found, we try to parse using also
  # these structures.
  BSM_TYPE_LIST_NOT_TESTED = {
      49: ['BSM_TOKEN_ATTR32', BSM_TOKEN_ATTR32],
      50: ['BSM_TOKEN_IPC_PERM', BSM_TOKEN_IPC_PERM],
      52: ['BSM_TOKEN_GROUPS', BSM_TOKEN_GROUPS],
      59: ['BSM_TOKEN_GROUPS', BSM_TOKEN_GROUPS],
      60: ['BSM_TOKEN_EXEC_ARGUMENTS', BSM_TOKEN_EXEC_ARGUMENTS],
      61: ['BSM_TOKEN_EXEC_ENV', BSM_TOKEN_EXEC_ENV],
      62: ['BSM_TOKEN_ATTR32', BSM_TOKEN_ATTR32],
      82: ['BSM_TOKEN_EXIT', BSM_TOKEN_EXIT],
      115: ['BSM_TOKEN_ATTR64', BSM_TOKEN_ATTR64],
      117: ['BSM_TOKEN_SUBJECT64', BSM_TOKEN_SUBJECT64],
      123: ['BSM_TOKEN_PROCESS32_EX', BSM_TOKEN_PROCESS32_EX],
      124: ['BSM_TOKEN_PROCESS64_EX', BSM_TOKEN_PROCESS64_EX],
      125: ['BSM_TOKEN_SUBJECT64_EX', BSM_TOKEN_SUBJECT64_EX],
      126: ['BSM_TOKEN_ADDR_EXT', BSM_TOKEN_ADDR_EXT],
      129: ['BSM_TOKEN_AUT_SOCKINET128', BSM_TOKEN_AUT_SOCKINET128],
      130: ['BSM_TOKEN_SOCKET_UNIX', BSM_TOKEN_SOCKET_UNIX]}

  def __init__(self):
    """Initializes a parser object."""
    super(BsmParser, self).__init__()
    # Create the dictionary with all token IDs: tested and untested.
    self.bsm_type_list_all = self.BSM_TYPE_LIST.copy()
    self.bsm_type_list_all.update(self.BSM_TYPE_LIST_NOT_TESTED)

  def ParseFileObject(self, parser_mediator, file_object, **kwargs):
    """Parses a BSM file-like object.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      file_object: A file-like object.

    Raises:
      UnableToParseFile: when the file cannot be parsed.
    """
    file_object.seek(0, os.SEEK_SET)

    try:
      is_bsm = self.VerifyFile(parser_mediator, file_object)
    except (IOError, construct.FieldError) as exception:
      raise errors.UnableToParseFile(
          u'Unable to parse BSM file with error: {0:s}'.format(exception))

    if not is_bsm:
      raise errors.UnableToParseFile(u'Not a BSM File, unable to parse.')

    event_object = self.ReadBSMEvent(parser_mediator, file_object)
    while event_object:
      parser_mediator.ProduceEvent(event_object)

      event_object = self.ReadBSMEvent(parser_mediator, file_object)

  def ReadBSMEvent(self, parser_mediator, file_object):
    """Returns a BsmEvent from a single BSM entry.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      file_object: A file-like object.

    Returns:
      An event object.
    """
    # A list of tokens that has the entry.
    extra_tokens = []

    offset = file_object.tell()

    # Token header, first token for each entry.
    try:
      token_id = self.BSM_TYPE.parse_stream(file_object)
    except (IOError, construct.FieldError):
      return

    bsm_type, structure = self.BSM_TYPE_LIST.get(token_id, ['', ''])
    if bsm_type == 'BSM_HEADER32':
      token = structure.parse_stream(file_object)
    elif bsm_type == 'BSM_HEADER64':
      token = structure.parse_stream(file_object)
    elif bsm_type == 'BSM_HEADER32_EX':
      token = structure.parse_stream(file_object)
    else:
      logging.warning(
          u'Token ID Header {0} not expected at position 0x{1:X}.'
          u'The parsing of the file cannot be continued'.format(
              token_id, file_object.tell()))
      # TODO: if it is a Mac OS X, search for the trailer magic value
      #       as a end of the entry can be a possibility to continue.
      return

    length = token.bsm_header.length
    event_type = u'{0} ({1})'.format(
        bsmtoken.BSM_AUDIT_EVENT.get(token.bsm_header.event_type, 'UNKNOWN'),
        token.bsm_header.event_type)
    timestamp = timelib.Timestamp.FromPosixTimeWithMicrosecond(
        token.timestamp, token.microsecond)

    # Read until we reach the end of the record.
    while file_object.tell() < (offset + length):
      # Check if it is a known token.
      try:
        token_id = self.BSM_TYPE.parse_stream(file_object)
      except (IOError, construct.FieldError):
        logging.warning(
            u'Unable to parse the Token ID at position: {0:d}'.format(
                file_object.tell()))
        return
      if not token_id in self.BSM_TYPE_LIST:
        pending = (offset + length) - file_object.tell()
        extra_tokens.extend(self.TryWithUntestedStructures(
            file_object, token_id, pending))
      else:
        token = self.BSM_TYPE_LIST[token_id][1].parse_stream(file_object)
        extra_tokens.append(self.FormatToken(token_id, token, file_object))

    if file_object.tell() > (offset + length):
      logging.warning(
          u'Token ID {0} not expected at position 0x{1:X}.'
          u'Jumping for the next entry.'.format(
              token_id, file_object.tell()))
      try:
        file_object.seek(
            (offset + length) - file_object.tell(), os.SEEK_CUR)
      except (IOError, construct.FieldError) as exception:
        logging.warning(
            u'Unable to jump to next entry with error: {0:s}'.format(exception))
        return

    # BSM can be in more than one OS: BSD, Solaris and Mac OS X.
    if parser_mediator.platform == 'MacOSX':
      # In Mac OS X the last two tokens are the return status and the trailer.
      if len(extra_tokens) >= 2:
        return_value = extra_tokens[-2:-1][0]
        if (return_value.startswith('[BSM_TOKEN_RETURN32') or
            return_value.startswith('[BSM_TOKEN_RETURN64')):
          _ = extra_tokens.pop(len(extra_tokens)-2)
        else:
          return_value = 'Return unknown'
      else:
        return_value = 'Return unknown'
      if extra_tokens:
        trailer = extra_tokens[-1]
        if trailer.startswith('[BSM_TOKEN_TRAILER'):
          _ = extra_tokens.pop(len(extra_tokens)-1)
        else:
          trailer = 'Trailer unknown'
      else:
        trailer = 'Trailer unknown'
      return MacBsmEvent(
          event_type, timestamp, u'. '.join(extra_tokens),
          return_value, trailer, offset)
    else:
      # Generic BSM format.
      if extra_tokens:
        trailer = extra_tokens[-1]
        if trailer.startswith('[BSM_TOKEN_TRAILER'):
          _ = extra_tokens.pop(len(extra_tokens)-1)
        else:
          trailer = 'Trailer unknown'
      else:
        trailer = 'Trailer unknown'
      return BsmEvent(
          event_type, timestamp, u'. '.join(extra_tokens), trailer, offset)

  def VerifyFile(self, parser_mediator, file_object):
    """Check if the file is a BSM file.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      file_event: file that we want to check.

    Returns:
      True if this is a valid BSM file, otherwise False.
    """
    if file_object.tell() != 0:
      file_object.seek(0)

    # First part of the entry is always a Header.
    try:
      token_id = self.BSM_TYPE.parse_stream(file_object)
    except (IOError, construct.FieldError):
      return False
    if token_id not in self.BSM_TYPE_LIST:
      return False

    bsm_type, structure = self.BSM_TYPE_LIST.get(token_id, ['', ''])
    try:
      if bsm_type == 'BSM_HEADER32':
        header = structure.parse_stream(file_object)
      elif bsm_type == 'BSM_HEADER64':
        header = structure.parse_stream(file_object)
      elif bsm_type == 'BSM_HEADER32_EX':
        header = structure.parse_stream(file_object)
      else:
        return False
    except (IOError, construct.FieldError):
      return False
    if header.bsm_header.version != self.AUDIT_HEADER_VERSION:
      return False

    try:
      token_id = self.BSM_TYPE.parse_stream(file_object)
    except (IOError, construct.FieldError):
      return False

    # If is Mac OS X BSM file, next entry is a  text token indicating
    # if it is a normal start or it is a recovery track.
    if parser_mediator.platform == 'MacOSX':
      bsm_type_list = self.BSM_TYPE_LIST.get(token_id)
      if not bsm_type_list:
        return False

      if bsm_type_list[0] != 'BSM_TOKEN_TEXT':
        logging.warning(u'It is not a valid first entry for Mac OS X BSM.')
        return False
      try:
        token = self.BSM_TOKEN_TEXT.parse_stream(file_object)
      except (IOError, construct.FieldError):
        return

      text = self._CopyUtf8ByteArrayToString(token.text)
      if (text != 'launchctl::Audit startup' and
          text != 'launchctl::Audit recovery'):
        logging.warning(u'It is not a valid first entry for Mac OS X BSM.')
        return False

    file_object.seek(0)
    return True

  def TryWithUntestedStructures(self, file_object, token_id, pending):
    """Try to parse the pending part of the entry using untested structures.

    Args:
      file_object: BSM file.
      token_id: integer with the id that comes from the unknown token.
      pending: pending length of the entry.

    Returns:
      A list of extra tokens data that can be parsed using non-tested
      structures. A message indicating that a structure cannot be parsed
      is added for unparsed structures.
    """
    # Data from the unknown structure.
    start_position = file_object.tell()
    start_token_id = token_id
    extra_tokens = []

    # Read all the "pending" bytes.
    try:
      if token_id in self.bsm_type_list_all:
        token = self.bsm_type_list_all[token_id][1].parse_stream(file_object)
        extra_tokens.append(self.FormatToken(token_id, token, file_object))
        while file_object.tell() < (start_position + pending):
          # Check if it is a known token.
          try:
            token_id = self.BSM_TYPE.parse_stream(file_object)
          except (IOError, construct.FieldError):
            logging.warning(
                u'Unable to parse the Token ID at position: {0:d}'.format(
                    file_object.tell()))
            return
          if token_id not in self.bsm_type_list_all:
            break
          token = self.bsm_type_list_all[token_id][1].parse_stream(
              file_object)
          extra_tokens.append(self.FormatToken(token_id, token, file_object))
    except (IOError, construct.FieldError):
      token_id = 255

    next_entry = (start_position + pending)
    if file_object.tell() != next_entry:
      # Unknown Structure.
      logging.warning(u'Unknown Token at "0x{0:X}", ID: {1} (0x{2:X})'.format(
          start_position-1, token_id, token_id))
      # TODO: another way to save this information must be found.
      extra_tokens.append(
          u'Plaso: some tokens from this entry can '
          u'not be saved. Entry at 0x{0:X} with unknown '
          u'token id "0x{1:X}".'.format(
              start_position-1, start_token_id))
      # Move to next entry.
      file_object.seek(next_entry - file_object.tell(), os.SEEK_CUR)
      # It returns null list because it doesn't know witch structure was
      # the incorrect structure that makes that it can arrive to the spected
      # end of the entry.
      return []
    return extra_tokens

  # TODO: instead of compare the text to know what structure was parsed
  #       is better to compare directly the numeric number (token_id),
  #       less readable, but better performance.
  def FormatToken(self, token_id, token, file_object):
    """Parse the Token depending of the type of the structure.

    Args:
      token_id: Identification integer of the token_type.
      token: Token struct to parse.
      file_object: BSM file.

    Returns:
      String with the parsed Token values.
    """
    if token_id not in self.bsm_type_list_all:
      return u'Type Unknown: {0:d} (0x{0:X})'.format(token_id)

    bsm_type, _ = self.bsm_type_list_all.get(token_id, ['', ''])

    if bsm_type in [
        'BSM_TOKEN_TEXT', 'BSM_TOKEN_PATH', 'BSM_TOKEN_ZONENAME']:
      try:
        string = self._CopyUtf8ByteArrayToString(token.text)
      except TypeError:
        string = u'Unknown'
      return u'[{0}: {1:s}]'.format(bsm_type, string)

    elif bsm_type in [
        'BSM_TOKEN_RETURN32', 'BSM_TOKEN_RETURN64', 'BSM_TOKEN_EXIT']:
      return u'[{0}: {1} ({2}), System call status: {3}]'.format(
          bsm_type, bsmtoken.BSM_ERRORS.get(token.status, 'Unknown'),
          token.status, token.return_value)

    elif bsm_type in ['BSM_TOKEN_SUBJECT32', 'BSM_TOKEN_SUBJECT64']:
      return (
          u'[{0}: aid({1}), euid({2}), egid({3}), uid({4}), gid({5}), '
          u'pid({6}), session_id({7}), terminal_port({8}), '
          u'terminal_ip({9})]').format(
              bsm_type, token.subject_data.audit_uid,
              token.subject_data.effective_uid,
              token.subject_data.effective_gid,
              token.subject_data.real_uid, token.subject_data.real_gid,
              token.subject_data.pid, token.subject_data.session_id,
              token.terminal_port, self._IPv4Format(token.ipv4))

    elif bsm_type in ['BSM_TOKEN_SUBJECT32_EX', 'BSM_TOKEN_SUBJECT64_EX']:
      if token.bsm_ip_type_short.net_type == self.AU_IPv6:
        ip = self._IPv6Format(
            token.bsm_ip_type_short.ip_addr.high,
            token.bsm_ip_type_short.ip_addr.low)
      elif token.bsm_ip_type_short.net_type == self.AU_IPv4:
        ip = self._IPv4Format(token.bsm_ip_type_short.ip_addr)
      else:
        ip = 'unknown'
      return (
          u'[{0}: aid({1}), euid({2}), egid({3}), uid({4}), gid({5}), '
          u'pid({6}), session_id({7}), terminal_port({8}), '
          u'terminal_ip({9})]').format(
              bsm_type, token.subject_data.audit_uid,
              token.subject_data.effective_uid,
              token.subject_data.effective_gid,
              token.subject_data.real_uid, token.subject_data.real_gid,
              token.subject_data.pid, token.subject_data.session_id,
              token.terminal_port, ip)

    elif bsm_type in ['BSM_TOKEN_ARGUMENT32', 'BSM_TOKEN_ARGUMENT64']:
      string = self._CopyUtf8ByteArrayToString(token.text)
      return u'[{0}: {1:s}({2}) is 0x{3:X}]'.format(
          bsm_type, string, token.num_arg, token.name_arg)

    elif bsm_type in ['BSM_TOKEN_EXEC_ARGUMENTS', 'BSM_TOKEN_EXEC_ENV']:
      arguments = []
      for _ in range(0, token):
        sub_token = self.BSM_TOKEN_EXEC_ARGUMENT.parse_stream(file_object)
        string = self._CopyUtf8ByteArrayToString(sub_token.text)
        arguments.append(string)
      return u'[{0}: {1:s}]'.format(bsm_type, u' '.join(arguments))

    elif bsm_type == 'BSM_TOKEN_AUT_SOCKINET32':
      return (u'[{0}: {1} ({2}) open in port {3}. Address {4}]'.format(
          bsm_type, bsmtoken.BSM_PROTOCOLS.get(token.net_type, 'UNKNOWN'),
          token.net_type, token.port_number, self._IPv4Format(token.ipv4)))

    elif bsm_type == 'BSM_TOKEN_AUT_SOCKINET128':
      return u'[{0}: {1} ({2}) open in port {3}. Address {4}]'.format(
          bsm_type, bsmtoken.BSM_PROTOCOLS.get(token.net_type, 'UNKNOWN'),
          token.net_type, token.port_number,
          self._IPv6Format(token.ipv6.high, token.ipv6.low))

    elif bsm_type == 'BSM_TOKEN_ADDR':
      return u'[{0}: {1}]'.format(bsm_type, self._IPv4Format(token))

    elif bsm_type == 'BSM_TOKEN_IP':
      return u'[IPv4_Header: 0x{0:s}]'.format(token.encode('hex'))

    elif bsm_type == 'BSM_TOKEN_ADDR_EXT':
      return u'[{0}: {1} ({2}). Address {3}]'.format(
          bsm_type,
          bsmtoken.BSM_PROTOCOLS.get(token.net_type, 'UNKNOWN'),
          token.net_type, self._IPv6Format(token.ipv6.high, token.ipv6.low))

    elif bsm_type == 'BSM_TOKEN_PORT':
      return u'[{0}: {1}]'.format(bsm_type, token)

    elif bsm_type == 'BSM_TOKEN_TRAILER':
      return u'[{0}: {1}]'.format(bsm_type, token.record_length)

    elif bsm_type == 'BSM_TOKEN_FILE':
      # TODO: if this timestamp is usefull, it must be extracted as a separate
      #       event object.
      timestamp = timelib.Timestamp.FromPosixTimeWithMicrosecond(
          token.timestamp, token.microsecond)
      date_time = timelib.Timestamp.CopyToDatetime(timestamp, pytz.UTC)
      date_time_string = date_time.strftime(u'%Y-%m-%d %H:%M:%S')

      string = self._CopyUtf8ByteArrayToString(token.text)
      return u'[{0}: {1:s}, timestamp: {2:s}]'.format(
          bsm_type, string, date_time_string)

    elif bsm_type == 'BSM_TOKEN_IPC':
      return u'[{0}: object type {1}, object id {2}]'.format(
          bsm_type, token.object_type, token.object_id)

    elif bsm_type in ['BSM_TOKEN_PROCESS32', 'BSM_TOKEN_PROCESS64']:
      return (
          u'[{0}: aid({1}), euid({2}), egid({3}), uid({4}), gid({5}), '
          u'pid({6}), session_id({7}), terminal_port({8}), '
          u'terminal_ip({9})]').format(
              bsm_type, token.subject_data.audit_uid,
              token.subject_data.effective_uid,
              token.subject_data.effective_gid,
              token.subject_data.real_uid, token.subject_data.real_gid,
              token.subject_data.pid, token.subject_data.session_id,
              token.terminal_port, self._IPv4Format(token.ipv4))

    elif bsm_type in ['BSM_TOKEN_PROCESS32_EX', 'BSM_TOKEN_PROCESS64_EX']:
      if token.bsm_ip_type_short.net_type == self.AU_IPv6:
        ip = self._IPv6Format(
            token.bsm_ip_type_short.ip_addr.high,
            token.bsm_ip_type_short.ip_addr.low)
      elif token.bsm_ip_type_short.net_type == self.AU_IPv4:
        ip = self._IPv4Format(token.bsm_ip_type_short.ip_addr)
      else:
        ip = 'unknown'
      return (
          u'[{0}: aid({1}), euid({2}), egid({3}), uid({4}), gid({5}), '
          u'pid({6}), session_id({7}), terminal_port({8}), '
          u'terminal_ip({9})]').format(
              bsm_type, token.subject_data.audit_uid,
              token.subject_data.effective_uid,
              token.subject_data.effective_gid,
              token.subject_data.real_uid, token.subject_data.real_gid,
              token.subject_data.pid, token.subject_data.session_id,
              token.terminal_port, ip)

    elif bsm_type == 'BSM_TOKEN_DATA':
      data = []
      data_type = bsmtoken.BSM_TOKEN_DATA_TYPE.get(token.data_type, '')
      if data_type == 'AUR_CHAR':
        for _ in range(token.unit_count):
          data.append(self.BSM_TOKEN_DATA_CHAR.parse_stream(file_object))
      elif data_type == 'AUR_SHORT':
        for _ in range(token.unit_count):
          data.append(self.BSM_TOKEN_DAT_SHORT.parse_stream(file_object))
      elif data_type == 'AUR_INT32':
        for _ in range(token.unit_count):
          data.append(self.BSM_TOKEN_DATA_INTEGER.parse_stream(file_object))
      else:
        data.append(u'Unknown type data')
      # TODO: the data when it is string ends with ".", HW a space is return
      #       after uses the UTF-8 conversion.
      return u'[{0}: Format data: {1}, Data: {2}]'.format(
          bsm_type, bsmtoken.BSM_TOKEN_DATA_PRINT[token.how_to_print],
          self._RawToUTF8(u''.join(data)))

    elif bsm_type in ['BSM_TOKEN_ATTR32', 'BSM_TOKEN_ATTR64']:
      return (
          u'[{0}: Mode: {1}, UID: {2}, GID: {3}, '
          u'File system ID: {4}, Node ID: {5}, Device: {6}]').format(
              bsm_type, token.file_mode, token.uid, token.gid,
              token.file_system_id, token.file_system_node_id, token.device)

    elif bsm_type == 'BSM_TOKEN_GROUPS':
      arguments = []
      for _ in range(token):
        arguments.append(self._RawToUTF8(
            self.BSM_TOKEN_DATA_INTEGER.parse_stream(file_object)))
      return u'[{0}: {1:s}]'.format(bsm_type, u','.join(arguments))

    elif bsm_type == 'BSM_TOKEN_AUT_SOCKINET32_EX':
      if bsmtoken.BSM_PROTOCOLS.get(token.socket_domain, '') == 'INET6':
        saddr = self._IPv6Format(
            token.structure_addr_port.saddr_high,
            token.structure_addr_port.saddr_low)
        daddr = self._IPv6Format(
            token.structure_addr_port.daddr_high,
            token.structure_addr_port.daddr_low)
      else:
        saddr = self._IPv4Format(token.structure_addr_port.source_address)
        daddr = self._IPv4Format(token.structure_addr_port.destination_address)

      return u'[{0}: from {1} port {2} to {3} port {4}]'.format(
          bsm_type, saddr, token.structure_addr_port.source_port,
          daddr, token.structure_addr_port.destination_port)

    elif bsm_type == 'BSM_TOKEN_IPC_PERM':
      return (
          u'[{0}: user id {1}, group id {2}, create user id {3}, '
          u'create group id {4}, access {5}]').format(
              bsm_type, token.user_id, token.group_id,
              token.creator_user_id, token.creator_group_id, token.access_mode)

    elif bsm_type == 'BSM_TOKEN_SOCKET_UNIX':
      string = self._CopyUtf8ByteArrayToString(token.path)
      return u'[{0}: Family {1}, Path {2:s}]'.format(
          bsm_type, token.family, string)

    elif bsm_type == 'BSM_TOKEN_OPAQUE':
      string = self._CopyByteArrayToBase16String(token.text)
      return u'[{0}: {1:s}]'.format(bsm_type, string)

    elif bsm_type == 'BSM_TOKEN_SEQUENCE':
      return u'[{0}: {1}]'.format(bsm_type, token)

  def _IPv6Format(self, high, low):
    """Provide a readable IPv6 IP having the high and low part in 2 integers.

    Args:
      high: 64 bits integers number with the high part of the IPv6.
      low: 64 bits integers number with the low part of the IPv6.

    Returns:
      String with a well represented IPv6.
    """
    ipv6_string = self.IPV6_STRUCT.build(
        construct.Container(high=high, low=low))
    # socket.inet_ntop not supported in Windows.
    if hasattr(socket, 'inet_ntop'):
      return socket.inet_ntop(socket.AF_INET6, ipv6_string)
    else:
      # TODO: this approach returns double "::", illegal IPv6 addr.
      str_address = binascii.hexlify(ipv6_string)
      address = []
      blank = False
      for pos in range(0, len(str_address), 4):
        if str_address[pos:pos + 4] == '0000':
          if not blank:
            address.append('')
            blank = True
        else:
          blank = False
          address.append(str_address[pos:pos + 4].lstrip('0'))
      return u':'.join(address)

  def _IPv4Format(self, address):
    """Change an integer IPv4 address value for its 4 octets representation.

    Args:
      address: integer with the IPv4 address.

    Returns:
      IPv4 address in 4 octect representation (class A, B, C, D).
    """
    ipv4_string = self.IPV4_STRUCT.build(address)
    return socket.inet_ntoa(ipv4_string)

  def _RawToUTF8(self, byte_stream):
    """Copies a UTF-8 byte stream into a Unicode string.

    Args:
      byte_stream: A byte stream containing an UTF-8 encoded string.

    Returns:
      A Unicode string.
    """
    try:
      string = byte_stream.decode('utf-8')
    except UnicodeDecodeError:
      logging.warning(
          u'Decode UTF8 failed, the message string may be cut short.')
      string = byte_stream.decode('utf-8', errors='ignore')
    return string.partition('\x00')[0]

  def _CopyByteArrayToBase16String(self, byte_array):
    """Copies a byte array into a base-16 encoded Unicode string.

    Args:
      byte_array: A byte array.

    Returns:
      A base-16 encoded Unicode string.
    """
    return u''.join(['{0:02x}'.format(byte) for byte in byte_array])

  def _CopyUtf8ByteArrayToString(self, byte_array):
    """Copies a UTF-8 encoded byte array into a Unicode string.

    Args:
      byte_array: A byte array containing an UTF-8 encoded string.

    Returns:
      A Unicode string.
    """
    byte_stream = ''.join(map(chr, byte_array))

    try:
      string = byte_stream.decode('utf-8')
    except UnicodeDecodeError:
      logging.warning(u'Unable to decode UTF-8 formatted byte array.')
      string = byte_stream.decode('utf-8', errors='ignore')

    string, _, _ = string.partition('\x00')
    return string


manager.ParsersManager.RegisterParser(BsmParser)
