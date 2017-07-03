# -*- coding: utf-8 -*-
"""Basic Security Module Parser."""

import binascii
import logging
import os
import socket

import construct

from dfdatetime import posix_time as dfdatetime_posix_time

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.lib import errors
from plaso.lib import timelib
from plaso.parsers import interface
from plaso.parsers import manager
from plaso.unix import bsmtoken

import pytz  # pylint: disable=wrong-import-order


__author__ = 'Joaquin Moreno Garijo (Joaquin.MorenoGarijo.2013@live.rhul.ac.uk)'


# Note that we're using Array and a helper function here instead of
# PascalString because the latter seems to break pickling on Windows.

def _BSMTokenGetLength(context):
  """Construct context parser helper function to replace lambda."""
  return context.length


# Note that we're using RepeatUntil and a helper function here instead of
# CString because the latter seems to break pickling on Windows.

def _BSMTokenIsEndOfString(value, unused_context):
  """Construct context parser helper function to replace lambda."""
  return value == b'\x00'


# Note that we're using Switch and a helper function here instead of
# IfThenElse because the latter seems to break pickling on Windows.

def _BSMTokenGetNetType(context):
  """Construct context parser helper function to replace lambda."""
  return context.net_type


def _BSMTokenGetSocketDomain(context):
  """Construct context parser helper function to replace lambda."""
  return context.socket_domain


class BSMEventData(events.EventData):
  """Generic BSM event data.

  Attributes:
    event_type (str): text with ID that represents the type of the event.
    extra_tokens (dict): event extra tokens.
    record_length (int): record length in bytes (trailer number).
  """

  DATA_TYPE = u'bsm:event'

  def __init__(self):
    """Initializes event data."""
    super(BSMEventData, self).__init__(data_type=self.DATA_TYPE)
    self.event_type = None
    self.extra_tokens = None
    self.record_length = None


class MacBSMEventData(events.EventData):
  """Mac OS X BSM event data.

  Attributes:
    event_type (str): text with ID that represents the type of the event.
    extra_tokens (dict): event extra tokens.
    record_length (int): record length in bytes (trailer number).
    return_value (str): processed return value and exit status.
  """

  DATA_TYPE = u'mac:bsm:event'

  def __init__(self):
    """Initializes event data."""
    super(MacBSMEventData, self).__init__(data_type=self.DATA_TYPE)
    self.event_type = None
    self.extra_tokens = None
    self.record_length = None
    self.return_value = None


class BSMParser(interface.FileObjectParser):
  """Parser for BSM files."""

  NAME = u'bsm_log'
  DESCRIPTION = u'Parser for BSM log files.'

  # BSM supported version (0x0b = 11).
  AUDIT_HEADER_VERSION = 11

  # Magic Trail Header.
  BSM_TOKEN_TRAILER_MAGIC = b'b105'

  # IP Version constants.
  AU_IPv4 = 4
  AU_IPv6 = 16

  IPV4_STRUCT = construct.UBInt32(u'ipv4')

  IPV6_STRUCT = construct.Struct(
      u'ipv6',
      construct.UBInt64(u'high'),
      construct.UBInt64(u'low'))

  # Tested structures.
  # INFO: I have ommited the ID in the structures declaration.
  #       I used the BSM_TYPE first to read the ID, and then, the structure.
  # Tokens always start with an ID value that identifies their token
  # type and subsequent structure.
  _BSM_TOKEN = construct.UBInt8(u'token_id')

  # Data type structures.
  BSM_TOKEN_DATA_CHAR = construct.String(u'value', 1)
  BSM_TOKEN_DATA_SHORT = construct.UBInt16(u'value')
  BSM_TOKEN_DATA_INTEGER = construct.UBInt32(u'value')

  # Common structure used by other structures.
  # audit_uid: integer, uid that generates the entry.
  # effective_uid: integer, the permission user used.
  # effective_gid: integer, the permission group used.
  # real_uid: integer, user id of the user that execute the process.
  # real_gid: integer, group id of the group that execute the process.
  # pid: integer, identification number of the process.
  # session_id: unknown, need research.
  BSM_TOKEN_SUBJECT_SHORT = construct.Struct(
      u'subject_data',
      construct.UBInt32(u'audit_uid'),
      construct.UBInt32(u'effective_uid'),
      construct.UBInt32(u'effective_gid'),
      construct.UBInt32(u'real_uid'),
      construct.UBInt32(u'real_gid'),
      construct.UBInt32(u'pid'),
      construct.UBInt32(u'session_id'))

  # Common structure used by other structures.
  # Identify the kind of inet (IPv4 or IPv6)
  # TODO: instead of 16, AU_IPv6 must be used.
  BSM_IP_TYPE_SHORT = construct.Struct(
      u'bsm_ip_type_short',
      construct.UBInt32(u'net_type'),
      construct.Switch(
          u'ip_addr',
          _BSMTokenGetNetType,
          {16: IPV6_STRUCT},
          default=IPV4_STRUCT))

  # Initial fields structure used by header structures.
  # length: integer, the length of the entry, equal to trailer (doc: length).
  # version: integer, version of BSM (AUDIT_HEADER_VERSION).
  # event_type: integer, the type of event (/etc/security/audit_event).
  # modifier: integer, unknown, need research (It is always 0).
  BSM_HEADER = construct.Struct(
      u'bsm_header',
      construct.UBInt32(u'length'),
      construct.UBInt8(u'version'),
      construct.UBInt16(u'event_type'),
      construct.UBInt16(u'modifier'))

  # First token of one entry.
  # timestamp: unsigned integer, number of seconds since
  #            January 1, 1970 00:00:00 UTC.
  # microseconds: unsigned integer, number of micro seconds.
  BSM_HEADER32 = construct.Struct(
      u'bsm_header32',
      BSM_HEADER,
      construct.UBInt32(u'timestamp'),
      construct.UBInt32(u'microseconds'))

  BSM_HEADER64 = construct.Struct(
      u'bsm_header64',
      BSM_HEADER,
      construct.UBInt64(u'timestamp'),
      construct.UBInt64(u'microseconds'))

  BSM_HEADER32_EX = construct.Struct(
      u'bsm_header32_ex',
      BSM_HEADER,
      BSM_IP_TYPE_SHORT,
      construct.UBInt32(u'timestamp'),
      construct.UBInt32(u'microseconds'))

  # Token TEXT, provides extra information.
  BSM_TOKEN_TEXT = construct.Struct(
      u'bsm_token_text',
      construct.UBInt16(u'length'),
      construct.Array(_BSMTokenGetLength, construct.UBInt8(u'text')))

  # Path of the executable.
  BSM_TOKEN_PATH = BSM_TOKEN_TEXT

  # Identified the end of the record (follow by TRAILER).
  # status: integer that identifies the status of the exit (BSM_ERRORS).
  # return: returned value from the operation.
  BSM_TOKEN_RETURN32 = construct.Struct(
      u'bsm_token_return32',
      construct.UBInt8(u'status'),
      construct.UBInt32(u'return_value'))

  BSM_TOKEN_RETURN64 = construct.Struct(
      u'bsm_token_return64',
      construct.UBInt8(u'status'),
      construct.UBInt64(u'return_value'))

  # Identified the number of bytes that was written.
  # magic: 2 bytes that identifies the TRAILER (BSM_TOKEN_TRAILER_MAGIC).
  # length: integer that has the number of bytes from the entry size.
  BSM_TOKEN_TRAILER = construct.Struct(
      u'bsm_token_trailer',
      construct.UBInt16(u'magic'),
      construct.UBInt32(u'record_length'))

  # A 32-bits argument.
  # num_arg: the number of the argument.
  # name_arg: the argument's name.
  # text: the string value of the argument.
  BSM_TOKEN_ARGUMENT32 = construct.Struct(
      u'bsm_token_argument32',
      construct.UBInt8(u'num_arg'),
      construct.UBInt32(u'name_arg'),
      construct.UBInt16(u'length'),
      construct.Array(_BSMTokenGetLength, construct.UBInt8(u'text')))

  # A 64-bits argument.
  # num_arg: integer, the number of the argument.
  # name_arg: text, the argument's name.
  # text: the string value of the argument.
  BSM_TOKEN_ARGUMENT64 = construct.Struct(
      u'bsm_token_argument64',
      construct.UBInt8(u'num_arg'),
      construct.UBInt64(u'name_arg'),
      construct.UBInt16(u'length'),
      construct.Array(_BSMTokenGetLength, construct.UBInt8(u'text')))

  # Identify an user.
  # terminal_id: unknown, research needed.
  # terminal_addr: unknown, research needed.
  BSM_TOKEN_SUBJECT32 = construct.Struct(
      u'bsm_token_subject32',
      BSM_TOKEN_SUBJECT_SHORT,
      construct.UBInt32(u'terminal_port'),
      IPV4_STRUCT)

  # Identify an user using a extended Token.
  # terminal_port: unknown, need research.
  # net_type: unknown, need research.
  BSM_TOKEN_SUBJECT32_EX = construct.Struct(
      u'bsm_token_subject32_ex',
      BSM_TOKEN_SUBJECT_SHORT,
      construct.UBInt32(u'terminal_port'),
      BSM_IP_TYPE_SHORT)

  # au_to_opaque // AUT_OPAQUE
  BSM_TOKEN_OPAQUE = BSM_TOKEN_TEXT

  # au_to_seq // AUT_SEQ
  BSM_TOKEN_SEQUENCE = BSM_TOKEN_DATA_INTEGER

  # Program execution with options.
  # For each argument we are going to have a string+ "\x00".
  # Example: [00 00 00 02][41 42 43 00 42 42 00]
  #          2 Arguments, Arg1: [414243] Arg2: [4242].
  BSM_TOKEN_EXEC_ARGUMENTS = construct.UBInt32(u'number_arguments')

  BSM_TOKEN_EXEC_ARGUMENT = construct.Struct(
      u'bsm_token_exec_argument',
      construct.RepeatUntil(
          _BSMTokenIsEndOfString, construct.StaticField("text", 1)))

  # au_to_in_addr // AUT_IN_ADDR:
  BSM_TOKEN_ADDR = IPV4_STRUCT

  # au_to_in_addr_ext // AUT_IN_ADDR_EX:
  BSM_TOKEN_ADDR_EXT = construct.Struct(
      u'bsm_token_addr_ext',
      construct.UBInt32(u'net_type'),
      IPV6_STRUCT)

  # au_to_ip // AUT_IP:
  # TODO: parse this header in the correct way.
  BSM_TOKEN_IP = construct.String(u'binary_ipv4_add', 20)

  # au_to_ipc // AUT_IPC:
  BSM_TOKEN_IPC = construct.Struct(
      u'bsm_token_ipc',
      construct.UBInt8(u'object_type'),
      construct.UBInt32(u'object_id'))

  # au_to_ipc_perm // au_to_ipc_perm
  BSM_TOKEN_IPC_PERM = construct.Struct(
      u'bsm_token_ipc_perm',
      construct.UBInt32(u'user_id'),
      construct.UBInt32(u'group_id'),
      construct.UBInt32(u'creator_user_id'),
      construct.UBInt32(u'creator_group_id'),
      construct.UBInt32(u'access_mode'),
      construct.UBInt32(u'slot_seq'),
      construct.UBInt32(u'key'))

  # au_to_iport // AUT_IPORT:
  BSM_TOKEN_PORT = construct.UBInt16(u'port_number')

  # au_to_file // AUT_OTHER_FILE32:
  BSM_TOKEN_FILE = construct.Struct(
      u'bsm_token_file',
      construct.UBInt32(u'timestamp'),
      construct.UBInt32(u'microseconds'),
      construct.UBInt16(u'length'),
      construct.Array(_BSMTokenGetLength, construct.UBInt8(u'text')))

  # au_to_subject64 // AUT_SUBJECT64:
  BSM_TOKEN_SUBJECT64 = construct.Struct(
      u'bsm_token_subject64',
      BSM_TOKEN_SUBJECT_SHORT,
      construct.UBInt64(u'terminal_port'),
      IPV4_STRUCT)

  # au_to_subject64_ex // AU_IPv4:
  BSM_TOKEN_SUBJECT64_EX = construct.Struct(
      u'bsm_token_subject64_ex',
      BSM_TOKEN_SUBJECT_SHORT,
      construct.UBInt32(u'terminal_port'),
      construct.UBInt32(u'terminal_type'),
      BSM_IP_TYPE_SHORT)

  # au_to_process32 // AUT_PROCESS32:
  BSM_TOKEN_PROCESS32 = construct.Struct(
      u'bsm_token_process32',
      BSM_TOKEN_SUBJECT_SHORT,
      construct.UBInt32(u'terminal_port'),
      IPV4_STRUCT)

  # au_to_process64 // AUT_PROCESS32:
  BSM_TOKEN_PROCESS64 = construct.Struct(
      u'bsm_token_process64',
      BSM_TOKEN_SUBJECT_SHORT,
      construct.UBInt64(u'terminal_port'),
      IPV4_STRUCT)

  # au_to_process32_ex // AUT_PROCESS32_EX:
  BSM_TOKEN_PROCESS32_EX = construct.Struct(
      u'bsm_token_process32_ex',
      BSM_TOKEN_SUBJECT_SHORT,
      construct.UBInt32(u'terminal_port'),
      BSM_IP_TYPE_SHORT)

  # au_to_process64_ex // AUT_PROCESS64_EX:
  BSM_TOKEN_PROCESS64_EX = construct.Struct(
      u'bsm_token_process64_ex',
      BSM_TOKEN_SUBJECT_SHORT,
      construct.UBInt64(u'terminal_port'),
      BSM_IP_TYPE_SHORT)

  # au_to_sock_inet32 // AUT_SOCKINET32:
  BSM_TOKEN_AUT_SOCKINET32 = construct.Struct(
      u'bsm_token_aut_sockinet32',
      construct.UBInt16(u'net_type'),
      construct.UBInt16(u'port_number'),
      IPV4_STRUCT)

  # Info: checked against the source code of XNU, but not against
  #       real BSM file.
  BSM_TOKEN_AUT_SOCKINET128 = construct.Struct(
      u'bsm_token_aut_sockinet128',
      construct.UBInt16(u'net_type'),
      construct.UBInt16(u'port_number'),
      IPV6_STRUCT)

  INET6_ADDR_TYPE = construct.Struct(
      u'addr_type',
      construct.UBInt16(u'ip_type'),
      construct.UBInt16(u'source_port'),
      construct.UBInt64(u'saddr_high'),
      construct.UBInt64(u'saddr_low'),
      construct.UBInt16(u'destination_port'),
      construct.UBInt64(u'daddr_high'),
      construct.UBInt64(u'daddr_low'))

  INET4_ADDR_TYPE = construct.Struct(
      u'addr_type',
      construct.UBInt16(u'ip_type'),
      construct.UBInt16(u'source_port'),
      construct.UBInt32(u'source_address'),
      construct.UBInt16(u'destination_port'),
      construct.UBInt32(u'destination_address'))

  # au_to_socket_ex // AUT_SOCKET_EX
  # TODO: Change the 26 for unixbsm.BSM_PROTOCOLS.INET6.
  BSM_TOKEN_AUT_SOCKINET32_EX = construct.Struct(
      u'bsm_token_aut_sockinet32_ex',
      construct.UBInt16(u'socket_domain'),
      construct.UBInt16(u'socket_type'),
      construct.Switch(
          u'structure_addr_port',
          _BSMTokenGetSocketDomain,
          {26: INET6_ADDR_TYPE},
          default=INET4_ADDR_TYPE))

  # au_to_sock_unix // AUT_SOCKUNIX
  BSM_TOKEN_SOCKET_UNIX = construct.Struct(
      u'bsm_token_au_to_sock_unix',
      construct.UBInt16(u'family'),
      construct.RepeatUntil(
          _BSMTokenIsEndOfString,
          construct.StaticField("path", 1)))

  # au_to_data // au_to_data
  # how to print: bsmtoken.BSM_TOKEN_DATA_PRINT.
  # type: bsmtoken.BSM_TOKEN_DATA_TYPE.
  # unit_count: number of type values.
  # BSM_TOKEN_DATA has a end field = type * unit_count
  BSM_TOKEN_DATA = construct.Struct(
      u'bsm_token_data',
      construct.UBInt8(u'how_to_print'),
      construct.UBInt8(u'data_type'),
      construct.UBInt8(u'unit_count'))

  # au_to_attr32 // AUT_ATTR32
  BSM_TOKEN_ATTR32 = construct.Struct(
      u'bsm_token_attr32',
      construct.UBInt32(u'file_mode'),
      construct.UBInt32(u'uid'),
      construct.UBInt32(u'gid'),
      construct.UBInt32(u'file_system_id'),
      construct.UBInt64(u'file_system_node_id'),
      construct.UBInt32(u'device'))

  # au_to_attr64 // AUT_ATTR64
  BSM_TOKEN_ATTR64 = construct.Struct(
      u'bsm_token_attr64',
      construct.UBInt32(u'file_mode'),
      construct.UBInt32(u'uid'),
      construct.UBInt32(u'gid'),
      construct.UBInt32(u'file_system_id'),
      construct.UBInt64(u'file_system_node_id'),
      construct.UBInt64(u'device'))

  # au_to_exit // AUT_EXIT
  BSM_TOKEN_EXIT = construct.Struct(
      u'bsm_token_exit',
      construct.UBInt32(u'status'),
      construct.UBInt32(u'return_value'))

  # au_to_newgroups // AUT_NEWGROUPS
  # INFO: we must read BSM_TOKEN_DATA_INTEGER for each group.
  BSM_TOKEN_GROUPS = construct.UBInt16(u'group_number')

  # au_to_exec_env == au_to_exec_args
  BSM_TOKEN_EXEC_ENV = BSM_TOKEN_EXEC_ARGUMENTS

  # au_to_zonename //AUT_ZONENAME
  BSM_TOKEN_ZONENAME = BSM_TOKEN_TEXT

  # Token ID.
  # List of valid Token_ID.
  # Token_ID -> (NAME_STRUCTURE, STRUCTURE)
  # Only the checked structures are been added to the valid structures lists.
  _BSM_TOKEN_TYPES = {
      17: (u'BSM_TOKEN_FILE', BSM_TOKEN_FILE),
      19: (u'BSM_TOKEN_TRAILER', BSM_TOKEN_TRAILER),
      20: (u'BSM_HEADER32', BSM_HEADER32),
      21: (u'BSM_HEADER64', BSM_HEADER64),
      33: (u'BSM_TOKEN_DATA', BSM_TOKEN_DATA),
      34: (u'BSM_TOKEN_IPC', BSM_TOKEN_IPC),
      35: (u'BSM_TOKEN_PATH', BSM_TOKEN_PATH),
      36: (u'BSM_TOKEN_SUBJECT32', BSM_TOKEN_SUBJECT32),
      38: (u'BSM_TOKEN_PROCESS32', BSM_TOKEN_PROCESS32),
      39: (u'BSM_TOKEN_RETURN32', BSM_TOKEN_RETURN32),
      40: (u'BSM_TOKEN_TEXT', BSM_TOKEN_TEXT),
      41: (u'BSM_TOKEN_OPAQUE', BSM_TOKEN_OPAQUE),
      42: (u'BSM_TOKEN_ADDR', BSM_TOKEN_ADDR),
      43: (u'BSM_TOKEN_IP', BSM_TOKEN_IP),
      44: (u'BSM_TOKEN_PORT', BSM_TOKEN_PORT),
      45: (u'BSM_TOKEN_ARGUMENT32', BSM_TOKEN_ARGUMENT32),
      47: (u'BSM_TOKEN_SEQUENCE', BSM_TOKEN_SEQUENCE),
      96: (u'BSM_TOKEN_ZONENAME', BSM_TOKEN_ZONENAME),
      113: (u'BSM_TOKEN_ARGUMENT64', BSM_TOKEN_ARGUMENT64),
      114: (u'BSM_TOKEN_RETURN64', BSM_TOKEN_RETURN64),
      116: (u'BSM_HEADER32_EX', BSM_HEADER32_EX),
      119: (u'BSM_TOKEN_PROCESS64', BSM_TOKEN_PROCESS64),
      122: (u'BSM_TOKEN_SUBJECT32_EX', BSM_TOKEN_SUBJECT32_EX),
      127: (u'BSM_TOKEN_AUT_SOCKINET32_EX', BSM_TOKEN_AUT_SOCKINET32_EX),
      128: (u'BSM_TOKEN_AUT_SOCKINET32', BSM_TOKEN_AUT_SOCKINET32)}

  # Untested structures.
  # When not tested structure is found, we try to parse using also
  # these structures.
  BSM_TYPE_LIST_NOT_TESTED = {
      49: (u'BSM_TOKEN_ATTR', BSM_TOKEN_ATTR32),
      50: (u'BSM_TOKEN_IPC_PERM', BSM_TOKEN_IPC_PERM),
      52: (u'BSM_TOKEN_GROUPS', BSM_TOKEN_GROUPS),
      59: (u'BSM_TOKEN_GROUPS', BSM_TOKEN_GROUPS),
      60: (u'BSM_TOKEN_EXEC_ARGUMENTS', BSM_TOKEN_EXEC_ARGUMENTS),
      61: (u'BSM_TOKEN_EXEC_ENV', BSM_TOKEN_EXEC_ENV),
      62: (u'BSM_TOKEN_ATTR32', BSM_TOKEN_ATTR32),
      82: (u'BSM_TOKEN_EXIT', BSM_TOKEN_EXIT),
      115: (u'BSM_TOKEN_ATTR64', BSM_TOKEN_ATTR64),
      117: (u'BSM_TOKEN_SUBJECT64', BSM_TOKEN_SUBJECT64),
      123: (u'BSM_TOKEN_PROCESS32_EX', BSM_TOKEN_PROCESS32_EX),
      124: (u'BSM_TOKEN_PROCESS64_EX', BSM_TOKEN_PROCESS64_EX),
      125: (u'BSM_TOKEN_SUBJECT64_EX', BSM_TOKEN_SUBJECT64_EX),
      126: (u'BSM_TOKEN_ADDR_EXT', BSM_TOKEN_ADDR_EXT),
      129: (u'BSM_TOKEN_AUT_SOCKINET128', BSM_TOKEN_AUT_SOCKINET128),
      130: (u'BSM_TOKEN_SOCKET_UNIX', BSM_TOKEN_SOCKET_UNIX)}

  MESSAGE_CAN_NOT_SAVE = (
      u'Plaso: some tokens from this entry can not be saved. Entry at 0x{0:X} '
      u'with unknown token id "0x{1:X}".')

  # BSM token types:
  # https://github.com/openbsm/openbsm/blob/master/sys/bsm/audit_record.h
  _BSM_TOKEN_TYPE_ARGUMENT32 = 45
  _BSM_TOKEN_TYPE_ARGUMENT64 = 113
  _BSM_TOKEN_TYPE_ATTR = 49
  _BSM_TOKEN_TYPE_ATTR32 = 62
  _BSM_TOKEN_TYPE_ATTR64 = 115
  _BSM_TOKEN_TYPE_EXEC_ARGUMENTS = 60
  _BSM_TOKEN_TYPE_EXEC_ENV = 61
  _BSM_TOKEN_TYPE_EXIT = 82
  _BSM_TOKEN_TYPE_HEADER32 = 20
  _BSM_TOKEN_TYPE_HEADER32_EX = 116
  _BSM_TOKEN_TYPE_HEADER64 = 21
  _BSM_TOKEN_TYPE_PATH = 35
  _BSM_TOKEN_TYPE_PROCESS32 = 38
  _BSM_TOKEN_TYPE_PROCESS32_EX = 123
  _BSM_TOKEN_TYPE_PROCESS64 = 119
  _BSM_TOKEN_TYPE_PROCESS64_EX = 124
  _BSM_TOKEN_TYPE_RETURN32 = 39
  _BSM_TOKEN_TYPE_RETURN64 = 114
  _BSM_TOKEN_TYPE_SUBJECT32 = 36
  _BSM_TOKEN_TYPE_SUBJECT32_EX = 122
  _BSM_TOKEN_TYPE_SUBJECT64 = 117
  _BSM_TOKEN_TYPE_SUBJECT64_EX = 125
  _BSM_TOKEN_TYPE_TEXT = 40
  _BSM_TOKEN_TYPE_ZONENAME = 96

  _BSM_ARGUMENT_TOKEN_TYPES = (
      _BSM_TOKEN_TYPE_ARGUMENT32,
      _BSM_TOKEN_TYPE_ARGUMENT64)

  _BSM_ATTR_TOKEN_TYPES = (
      _BSM_TOKEN_TYPE_ATTR,
      _BSM_TOKEN_TYPE_ATTR32,
      _BSM_TOKEN_TYPE_ATTR64)

  _BSM_EXEV_TOKEN_TYPES = (
      _BSM_TOKEN_TYPE_EXEC_ARGUMENTS,
      _BSM_TOKEN_TYPE_EXEC_ENV)

  _BSM_HEADER_TOKEN_TYPES = (
      _BSM_TOKEN_TYPE_HEADER32,
      _BSM_TOKEN_TYPE_HEADER32_EX,
      _BSM_TOKEN_TYPE_HEADER64)

  _BSM_PROCESS_TOKEN_TYPES = (
      _BSM_TOKEN_TYPE_PROCESS32,
      _BSM_TOKEN_TYPE_PROCESS64)

  _BSM_PROCESS_EX_TOKEN_TYPES = (
      _BSM_TOKEN_TYPE_PROCESS32_EX,
      _BSM_TOKEN_TYPE_PROCESS64_EX)

  _BSM_RETURN_TOKEN_TYPES = (
      _BSM_TOKEN_TYPE_EXIT,
      _BSM_TOKEN_TYPE_RETURN32,
      _BSM_TOKEN_TYPE_RETURN64)

  _BSM_SUBJECT_TOKEN_TYPES = (
      _BSM_TOKEN_TYPE_SUBJECT32,
      _BSM_TOKEN_TYPE_SUBJECT64)

  _BSM_SUBJECT_EX_TOKEN_TYPES = (
      _BSM_TOKEN_TYPE_SUBJECT32_EX,
      _BSM_TOKEN_TYPE_SUBJECT64_EX)

  _BSM_UTF8_BYTE_ARRAY_TOKEN_TYPES = (
      _BSM_TOKEN_TYPE_PATH,
      _BSM_TOKEN_TYPE_TEXT,
      _BSM_TOKEN_TYPE_ZONENAME)

  def __init__(self):
    """Initializes a parser object."""
    super(BSMParser, self).__init__()
    # Create the dictionary with all token IDs: tested and untested.
    self._bsm_type_list_all = self._BSM_TOKEN_TYPES.copy()
    self._bsm_type_list_all.update(self.BSM_TYPE_LIST_NOT_TESTED)

  def _CopyByteArrayToBase16String(self, byte_array):
    """Copies a byte array into a base-16 encoded Unicode string.

    Args:
      byte_array (bytes): A byte array.

    Returns:
      str: a base-16 encoded Unicode string.
    """
    return u''.join([u'{0:02x}'.format(byte) for byte in byte_array])

  def _CopyUtf8ByteArrayToString(self, byte_array):
    """Copies a UTF-8 encoded byte array into a Unicode string.

    Args:
      byte_array (bytes): A byte array containing an UTF-8 encoded string.

    Returns:
      str: A Unicode string.
    """
    byte_stream = b''.join(map(chr, byte_array))

    try:
      string = byte_stream.decode(u'utf-8')
    except UnicodeDecodeError:
      logging.warning(u'Unable to decode UTF-8 formatted byte array.')
      string = byte_stream.decode(u'utf-8', errors=u'ignore')

    string, _, _ = string.partition(b'\x00')
    return string

  def _IPv4Format(self, address):
    """Formats an IPv4 address as a human readable string.

    Args:
      address (int): IPv4 address.

    Returns:
      str: human readable string of IPv4 address in 4 octet representation:
          "1.2.3.4".
    """
    ipv4_string = self.IPV4_STRUCT.build(address)
    return socket.inet_ntoa(ipv4_string)

  def _IPv6Format(self, high, low):
    """Formats an IPv6 address as a human readable string.

    Args:
      high (int): upper 64-bit part of the IPv6 address.
      low (int): lower 64-bit part of the IPv6 address.

    Returns:
      str: human readable string of IPv6 address.
    """
    ipv6_string = self.IPV6_STRUCT.build(
        construct.Container(high=high, low=low))
    # socket.inet_ntop not supported in Windows.
    if hasattr(socket, u'inet_ntop'):
      return socket.inet_ntop(socket.AF_INET6, ipv6_string)

    # TODO: this approach returns double "::", illegal IPv6 addr.
    str_address = binascii.hexlify(ipv6_string)
    address = []
    blank = False
    for pos in range(0, len(str_address), 4):
      if str_address[pos:pos + 4] == u'0000':
        if not blank:
          address.append(u'')
          blank = True
      else:
        blank = False
        address.append(str_address[pos:pos + 4].lstrip(u'0'))
    return u':'.join(address)

  def _ParseBSMEvent(self, parser_mediator, file_object):
    """Parses a BSM entry (BSMEvent) from the file-like object.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      file_object (dfvfs.FileIO): a file-like object.

    Returns:
      bool: True if the BSM entry was parsed.
    """
    record_start_offset = file_object.tell()

    try:
      token_type = self._BSM_TOKEN.parse_stream(file_object)
    except (IOError, construct.FieldError) as exception:
      parser_mediator.ProduceExtractionError((
          u'unable to parse BSM token type at offset: 0x{0:08x} with error: '
          u'{1:s}.').format(record_start_offset, exception))
      return False

    if token_type not in self._BSM_HEADER_TOKEN_TYPES:
      parser_mediator.ProduceExtractionError(
          u'unsupported token type: {0:d} at offset: 0x{1:08x}.'.format(
              token_type, record_start_offset))
      # TODO: if it is a Mac OS X, search for the trailer magic value
      #       as a end of the entry can be a possibility to continue.
      return False

    _, record_structure = self._BSM_TOKEN_TYPES.get(token_type, (u'', None))

    try:
      token = record_structure.parse_stream(file_object)
    except (IOError, construct.FieldError) as exception:
      parser_mediator.ProduceExtractionError((
          u'unable to parse BSM record at offset: 0x{0:08x} with error: '
          u'{1:s}.').format(record_start_offset, exception))
      return False

    event_type = bsmtoken.BSM_AUDIT_EVENT.get(
        token.bsm_header.event_type, u'UNKNOWN')
    event_type = u'{0:s} ({1:d})'.format(
        event_type, token.bsm_header.event_type)

    timestamp = (token.timestamp * 1000000) + token.microseconds
    date_time = dfdatetime_posix_time.PosixTimeInMicroseconds(
        timestamp=timestamp)

    record_length = token.bsm_header.length
    record_end_offset = record_start_offset + record_length

    # A dict of tokens that has the entry.
    extra_tokens = {}

    # Read until we reach the end of the record.
    while file_object.tell() < record_end_offset:
      # Check if it is a known token.
      try:
        token_type = self._BSM_TOKEN.parse_stream(file_object)
      except (IOError, construct.FieldError):
        logging.warning(
            u'Unable to parse the Token ID at position: {0:d}'.format(
                file_object.tell()))
        return False

      _, record_structure = self._BSM_TOKEN_TYPES.get(token_type, (u'', None))

      if not record_structure:
        pending = record_end_offset - file_object.tell()
        new_extra_tokens = self.TryWithUntestedStructures(
            file_object, token_type, pending)
        extra_tokens.update(new_extra_tokens)
      else:
        token = record_structure.parse_stream(file_object)
        new_extra_tokens = self.FormatToken(token_type, token, file_object)
        extra_tokens.update(new_extra_tokens)

    if file_object.tell() > record_end_offset:
      logging.warning(
          u'Token ID {0:d} not expected at position 0x{1:08x}.'
          u'Jumping for the next entry.'.format(
              token_type, file_object.tell()))
      try:
        file_object.seek(
            record_end_offset - file_object.tell(), os.SEEK_CUR)
      except (IOError, construct.FieldError) as exception:
        logging.warning(
            u'Unable to jump to next entry with error: {0:s}'.format(exception))
        return False

    # BSM can be in more than one OS: BSD, Solaris and Mac OS X.
    if parser_mediator.platform != u'MacOSX':
      event_data = BSMEventData()
    else:
      event_data = MacBSMEventData()

      # In Mac OS X the last two tokens are the return status and the trailer.
      return_value = extra_tokens.get(u'BSM_TOKEN_RETURN32')
      if not return_value:
        return_value = extra_tokens.get(u'BSM_TOKEN_RETURN64')
      if not return_value:
        return_value = 'UNKNOWN'

      event_data.return_value = return_value

    event_data.event_type = event_type
    event_data.extra_tokens = extra_tokens
    event_data.offset = record_start_offset
    event_data.record_length = record_length

    # TODO: check why trailer was passed to event in original while
    # event was expecting record length.
    # if extra_tokens:
    #   trailer = extra_tokens.get(u'BSM_TOKEN_TRAILER', u'unknown')

    event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_CREATION)
    parser_mediator.ProduceEventWithEventData(event, event_data)

    return True

  def _RawToUTF8(self, byte_stream):
    """Copies a UTF-8 byte stream into a Unicode string.

    Args:
      byte_stream (bytes): byte stream containing an UTF-8 encoded string.

    Returns:
      str: A Unicode string.
    """
    try:
      string = byte_stream.decode(u'utf-8')
    except UnicodeDecodeError:
      logging.warning(
          u'Decode UTF8 failed, the message string may be cut short.')
      string = byte_stream.decode(u'utf-8', errors=u'ignore')
    return string.partition(b'\x00')[0]

  def ParseFileObject(self, parser_mediator, file_object, **kwargs):
    """Parses a BSM file-like object.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      file_object (dfvfs.FileIO): a file-like object.

    Raises:
      UnableToParseFile: when the file cannot be parsed.
    """
    try:
      is_bsm = self.VerifyFile(parser_mediator, file_object)
    except (IOError, construct.FieldError) as exception:
      raise errors.UnableToParseFile(
          u'Unable to parse BSM file with error: {0:s}'.format(exception))

    if not is_bsm:
      raise errors.UnableToParseFile(u'Not a BSM File, unable to parse.')

    file_object.seek(0, os.SEEK_SET)

    while self._ParseBSMEvent(parser_mediator, file_object):
      pass

  def VerifyFile(self, parser_mediator, file_object):
    """Check if the file is a BSM file.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      file_object (dfvfs.FileIO): a file-like object.

    Returns:
      bool: True if this is a valid BSM file, False otherwise.
    """
    # First part of the entry is always a Header.
    try:
      token_type = self._BSM_TOKEN.parse_stream(file_object)
    except (IOError, construct.FieldError):
      return False

    if token_type not in self._BSM_HEADER_TOKEN_TYPES:
      return False

    _, record_structure = self._BSM_TOKEN_TYPES.get(token_type, (u'', None))

    try:
      header = record_structure.parse_stream(file_object)
    except (IOError, construct.FieldError):
      return False

    if header.bsm_header.version != self.AUDIT_HEADER_VERSION:
      return False

    try:
      token_identifier = self._BSM_TOKEN.parse_stream(file_object)
    except (IOError, construct.FieldError):
      return False

    # If is Mac OS X BSM file, next entry is a  text token indicating
    # if it is a normal start or it is a recovery track.
    if parser_mediator.platform == u'MacOSX':
      token_type, record_structure = self._BSM_TOKEN_TYPES.get(
          token_identifier, (u'', None))

      if not record_structure:
        return False

      if token_type != u'BSM_TOKEN_TEXT':
        logging.warning(u'It is not a valid first entry for Mac OS X BSM.')
        return False

      try:
        token = record_structure.parse_stream(file_object)
      except (IOError, construct.FieldError):
        return

      text = self._CopyUtf8ByteArrayToString(token.text)
      if (text != u'launchctl::Audit startup' and
          text != u'launchctl::Audit recovery'):
        logging.warning(u'It is not a valid first entry for Mac OS X BSM.')
        return False

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
    extra_tokens = {}

    # Read all the "pending" bytes.
    try:
      if token_id in self._bsm_type_list_all:
        token = self._bsm_type_list_all[token_id][1].parse_stream(file_object)
        new_extra_tokens = self.FormatToken(token_id, token, file_object)
        extra_tokens.update(new_extra_tokens)
        while file_object.tell() < (start_position + pending):
          # Check if it is a known token.
          try:
            token_id = self._BSM_TOKEN.parse_stream(file_object)
          except (IOError, construct.FieldError):
            logging.warning(
                u'Unable to parse the Token ID at position: {0:d}'.format(
                    file_object.tell()))
            return
          if token_id not in self._bsm_type_list_all:
            break
          token = self._bsm_type_list_all[token_id][1].parse_stream(file_object)
          new_extra_tokens = self.FormatToken(token_id, token, file_object)
          extra_tokens.update(new_extra_tokens)
    except (IOError, construct.FieldError):
      token_id = 255

    next_entry = (start_position + pending)
    if file_object.tell() != next_entry:
      # Unknown Structure.
      logging.warning(u'Unknown Token at "0x{0:X}", ID: {1} (0x{2:X})'.format(
          start_position - 1, token_id, token_id))
      # TODO: another way to save this information must be found.
      extra_tokens.update(
          {u'message': self.MESSAGE_CAN_NOT_SAVE.format(
              start_position - 1, start_token_id)})
      # Move to next entry.
      file_object.seek(next_entry - file_object.tell(), os.SEEK_CUR)
      # It returns null list because it doesn't know witch structure was
      # the incorrect structure that makes that it can arrive to the spected
      # end of the entry.
      return {}
    return extra_tokens

  def FormatToken(self, token_id, token, file_object):
    """Parse the Token depending of the type of the structure.

    Args:
      token_id (int): identification of the token_type.
      token (structure): token struct to parse.
      file_object: BSM file.

    Returns:
      (dict): parsed Token values.

    Keys for returned dictionary are token name like BSM_TOKEN_SUBJECT32.
    Values of this dictionary are key-value pairs like terminal_ip:127.0.0.1.
    """
    if token_id not in self._bsm_type_list_all:
      return {}

    bsm_type, _ = self._bsm_type_list_all.get(token_id, [u'', u''])

    if token_id in self._BSM_UTF8_BYTE_ARRAY_TOKEN_TYPES:
      try:
        string = self._CopyUtf8ByteArrayToString(token.text)
      except TypeError:
        string = u'Unknown'
      return {bsm_type: string}

    elif token_id in self._BSM_RETURN_TOKEN_TYPES:
      return {bsm_type: {
          u'error': bsmtoken.BSM_ERRORS.get(token.status, u'Unknown'),
          u'token_status': token.status,
          u'call_status': token.return_value
      }}

    elif token_id in self._BSM_SUBJECT_TOKEN_TYPES:
      return {bsm_type: {
          u'aid': token.subject_data.audit_uid,
          u'euid': token.subject_data.effective_uid,
          u'egid': token.subject_data.effective_gid,
          u'uid': token.subject_data.real_uid,
          u'gid': token.subject_data.real_gid,
          u'pid': token.subject_data.pid,
          u'session_id': token.subject_data.session_id,
          u'terminal_port': token.terminal_port,
          u'terminal_ip': self._IPv4Format(token.ipv4)
      }}

    elif token_id in self._BSM_SUBJECT_EX_TOKEN_TYPES:
      if token.bsm_ip_type_short.net_type == self.AU_IPv6:
        ip = self._IPv6Format(
            token.bsm_ip_type_short.ip_addr.high,
            token.bsm_ip_type_short.ip_addr.low)
      elif token.bsm_ip_type_short.net_type == self.AU_IPv4:
        ip = self._IPv4Format(token.bsm_ip_type_short.ip_addr)
      else:
        ip = u'unknown'
      return {bsm_type: {
          u'aid': token.subject_data.audit_uid,
          u'euid': token.subject_data.effective_uid,
          u'egid': token.subject_data.effective_gid,
          u'uid': token.subject_data.real_uid,
          u'gid': token.subject_data.real_gid,
          u'pid': token.subject_data.pid,
          u'session_id': token.subject_data.session_id,
          u'terminal_port': token.terminal_port,
          u'terminal_ip': ip
      }}

    elif token_id in self._BSM_ARGUMENT_TOKEN_TYPES:
      string = self._CopyUtf8ByteArrayToString(token.text)
      return {bsm_type: {
          u'string': string,
          u'num_arg': token.num_arg,
          u'is': token.name_arg}}

    elif token_id in self._BSM_EXEV_TOKEN_TYPES:
      arguments = []
      for _ in range(0, token):
        sub_token = self.BSM_TOKEN_EXEC_ARGUMENT.parse_stream(file_object)
        string = self._CopyUtf8ByteArrayToString(sub_token.text)
        arguments.append(string)
      return {bsm_type: u' '.join(arguments)}

    elif bsm_type == u'BSM_TOKEN_AUT_SOCKINET32':
      return {bsm_type: {
          u'protocols':
          bsmtoken.BSM_PROTOCOLS.get(token.net_type, u'UNKNOWN'),
          u'net_type': token.net_type,
          u'port': token.port_number,
          u'address': self._IPv4Format(token.ipv4)
      }}

    elif bsm_type == u'BSM_TOKEN_AUT_SOCKINET128':
      return {bsm_type: {
          u'protocols':
          bsmtoken.BSM_PROTOCOLS.get(token.net_type, u'UNKNOWN'),
          u'net_type': token.net_type,
          u'port': token.port_number,
          u'address': self._IPv6Format(token.ipv6.high, token.ipv6.low)
      }}

    elif bsm_type == u'BSM_TOKEN_ADDR':
      return {bsm_type: self._IPv4Format(token)}

    elif bsm_type == u'BSM_TOKEN_IP':
      return {u'IPv4_Header': u'0x{0:s}]'.format(token.encode(u'hex'))}

    elif bsm_type == u'BSM_TOKEN_ADDR_EXT':
      return {bsm_type: {
          u'protocols':
          bsmtoken.BSM_PROTOCOLS.get(token.net_type, u'UNKNOWN'),
          u'net_type': token.net_type,
          u'address': self._IPv6Format(token.ipv6.high, token.ipv6.low)
      }}

    elif bsm_type == u'BSM_TOKEN_PORT':
      return {bsm_type: token}

    elif bsm_type == u'BSM_TOKEN_TRAILER':
      return {bsm_type: token.record_length}

    elif bsm_type == u'BSM_TOKEN_FILE':
      # TODO: if this timestamp is usefull, it must be extracted as a separate
      #       event object.
      timestamp = timelib.Timestamp.FromPosixTimeWithMicrosecond(
          token.timestamp, token.microseconds)
      date_time = timelib.Timestamp.CopyToDatetime(timestamp, pytz.UTC)
      date_time_string = date_time.strftime(u'%Y-%m-%d %H:%M:%S')

      string = self._CopyUtf8ByteArrayToString(token.text)
      return {bsm_type: {u'string': string, u'timestamp': date_time_string}}

    elif bsm_type == u'BSM_TOKEN_IPC':
      return {bsm_type: {
          u'object_type': token.object_type,
          u'object_id': token.object_id
      }}

    elif token_id in self._BSM_PROCESS_TOKEN_TYPES:
      return {bsm_type: {
          u'aid': token.subject_data.audit_uid,
          u'euid': token.subject_data.effective_uid,
          u'egid': token.subject_data.effective_gid,
          u'uid': token.subject_data.real_uid,
          u'gid': token.subject_data.real_gid,
          u'pid': token.subject_data.pid,
          u'session_id': token.subject_data.session_id,
          u'terminal_port': token.terminal_port,
          u'terminal_ip': self._IPv4Format(token.ipv4)
      }}

    elif token_id in self._BSM_PROCESS_EX_TOKEN_TYPES:
      if token.bsm_ip_type_short.net_type == self.AU_IPv6:
        ip = self._IPv6Format(
            token.bsm_ip_type_short.ip_addr.high,
            token.bsm_ip_type_short.ip_addr.low)
      elif token.bsm_ip_type_short.net_type == self.AU_IPv4:
        ip = self._IPv4Format(token.bsm_ip_type_short.ip_addr)
      else:
        ip = u'unknown'
      return {bsm_type: {
          u'aid': token.subject_data.audit_uid,
          u'euid': token.subject_data.effective_uid,
          u'egid': token.subject_data.effective_gid,
          u'uid': token.subject_data.real_uid,
          u'gid': token.subject_data.real_gid,
          u'pid': token.subject_data.pid,
          u'session_id': token.subject_data.session_id,
          u'terminal_port': token.terminal_port,
          u'terminal_ip': ip
      }}

    elif bsm_type == u'BSM_TOKEN_DATA':
      data = []
      data_type = bsmtoken.BSM_TOKEN_DATA_TYPE.get(token.data_type, u'')

      if data_type == u'AUR_CHAR':
        for _ in range(token.unit_count):
          data.append(self.BSM_TOKEN_DATA_CHAR.parse_stream(file_object))

      elif data_type == u'AUR_SHORT':
        for _ in range(token.unit_count):
          data.append(self.BSM_TOKEN_DATA_SHORT.parse_stream(file_object))

      elif data_type == u'AUR_INT32':
        for _ in range(token.unit_count):
          data.append(self.BSM_TOKEN_DATA_INTEGER.parse_stream(file_object))

      else:
        data.append(u'Unknown type data')

      # TODO: the data when it is string ends with ".", HW a space is return
      #       after uses the UTF-8 conversion.
      return {bsm_type: {
          u'format': bsmtoken.BSM_TOKEN_DATA_PRINT[token.how_to_print],
          u'data':
          u'{0}'.format(self._RawToUTF8(''.join(map(str, data))))
      }}

    elif token_id in self._BSM_ATTR_TOKEN_TYPES:
      return {bsm_type: {
          u'mode': token.file_mode,
          u'uid': token.uid,
          u'gid': token.gid,
          u'system_id': token.file_system_id,
          u'node_id': token.file_system_node_id,
          u'device': token.device}}

    elif bsm_type == u'BSM_TOKEN_GROUPS':
      arguments = []
      for _ in range(token):
        arguments.append(
            self._RawToUTF8(
                self.BSM_TOKEN_DATA_INTEGER.parse_stream(file_object)))
      return {bsm_type: u','.join(arguments)}

    elif bsm_type == u'BSM_TOKEN_AUT_SOCKINET32_EX':
      if bsmtoken.BSM_PROTOCOLS.get(token.socket_domain, u'') == u'INET6':
        saddr = self._IPv6Format(
            token.structure_addr_port.saddr_high,
            token.structure_addr_port.saddr_low)
        daddr = self._IPv6Format(
            token.structure_addr_port.daddr_high,
            token.structure_addr_port.daddr_low)
      else:
        saddr = self._IPv4Format(token.structure_addr_port.source_address)
        daddr = self._IPv4Format(token.structure_addr_port.destination_address)

      return {bsm_type:{
          u'from': saddr,
          u'from_port': token.structure_addr_port.source_port,
          u'to': daddr,
          u'to_port': token.structure_addr_port.destination_port}}

    elif bsm_type == u'BSM_TOKEN_IPC_PERM':
      return {bsm_type: {
          u'user_id': token.user_id,
          u'group_id': token.group_id,
          u'creator_user_id': token.creator_user_id,
          u'creator_group_id': token.creator_group_id,
          u'access': token.access_mode}}

    elif bsm_type == u'BSM_TOKEN_SOCKET_UNIX':
      string = self._CopyUtf8ByteArrayToString(token.path)
      return {bsm_type: {u'family': token.family, u'path': string}}

    elif bsm_type == u'BSM_TOKEN_OPAQUE':
      string = self._CopyByteArrayToBase16String(token.text)
      return {bsm_type: string}

    elif bsm_type == u'BSM_TOKEN_SEQUENCE':
      return {bsm_type: token}


manager.ParsersManager.RegisterParser(BSMParser)
