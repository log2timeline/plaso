# -*- coding: utf-8 -*-
"""Parser for Linux UTMP files."""

import logging
import os
import socket

import construct

from dfdatetime import posix_time as dfdatetime_posix_time

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import errors
from plaso.lib import definitions
from plaso.parsers import interface
from plaso.parsers import manager


__author__ = 'Joaquin Moreno Garijo (Joaquin.MorenoGarijo.2013@live.rhul.ac.uk)'


class UtmpEventData(events.EventData):
  """UTMP event data.

  Attributes:
    computer_name (str): name of the computer.
    exit (int): exit status.
    ip_address (str): IP address from the connection.
    pid (int): process identifier (PID).
    status (str): login status.
    terminal_id (int): inittab identifier.
    terminal (str): type of terminal.
    user (str): active user name.
  """

  DATA_TYPE = u'linux:utmp:event'

  def __init__(self):
    """Initializes event data."""
    super(UtmpEventData, self).__init__(data_type=self.DATA_TYPE)
    self.computer_name = None
    self.exit = None
    self.ip_address = None
    self.pid = None
    self.status = None
    self.terminal_id = None
    self.terminal = None
    self.user = None


class UtmpParser(interface.FileObjectParser):
  """Parser for Linux/Unix UTMP files."""

  NAME = u'utmp'
  DESCRIPTION = u'Parser for Linux/Unix UTMP files.'

  LINUX_UTMP_ENTRY = construct.Struct(
      u'utmp_linux',
      construct.ULInt32(u'type'),
      construct.ULInt32(u'pid'),
      construct.String(u'terminal', 32),
      construct.ULInt32(u'terminal_id'),
      construct.String(u'username', 32),
      construct.String(u'hostname', 256),
      construct.ULInt16(u'termination'),
      construct.ULInt16(u'exit'),
      construct.ULInt32(u'session'),
      construct.ULInt32(u'timestamp'),
      construct.ULInt32(u'microseconds'),
      construct.ULInt32(u'address_a'),
      construct.ULInt32(u'address_b'),
      construct.ULInt32(u'address_c'),
      construct.ULInt32(u'address_d'),
      construct.Padding(20))

  LINUX_UTMP_ENTRY_SIZE = LINUX_UTMP_ENTRY.sizeof()

  STATUS_TYPE = {
      0: u'EMPTY',
      1: u'RUN_LVL',
      2: u'BOOT_TIME',
      3: u'NEW_TIME',
      4: u'OLD_TIME',
      5: u'INIT_PROCESS',
      6: u'LOGIN_PROCESS',
      7: u'USER_PROCESS',
      8: u'DEAD_PROCESS',
      9: u'ACCOUNTING'}

  # Set a default test value for few fields, this is supposed to be a text
  # that is highly unlikely to be seen in a terminal field, or a username field.
  # It is important that this value does show up in such fields, but otherwise
  # it can be a free flowing text field.
  _DEFAULT_TEST_VALUE = u'Ekki Fraedilegur Moguleiki, thetta er bull ! = + _<>'

  def _GetTextFromNullTerminatedString(
      self, null_terminated_string, default_string=u'N/A'):
    """Get a UTF-8 text from a raw null terminated string.

    Args:
      null_terminated_string: Raw string terminated with null character.
      default_string: The default string returned if the parser fails.

    Returns:
      A decoded UTF-8 string or if unable to decode, the supplied default
      string.
    """
    text, _, _ = null_terminated_string.partition(b'\x00')
    try:
      text = text.decode(u'utf-8')
    except UnicodeDecodeError:
      logging.warning(
          u'[UTMP] Decode UTF8 failed, the message string may be cut short.')
      text = text.decode(u'utf-8', u'ignore')
    if not text:
      return default_string
    return text

  def _ReadEntry(self, parser_mediator, file_object):
    """Reads an UTMP entry.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      file_object (dfvfs.FileIO): a file-like object.

    Returns:
      bool: True if the UTMP entry was successfully read.
    """
    offset = file_object.tell()
    data = file_object.read(self.LINUX_UTMP_ENTRY_SIZE)
    if not data or len(data) != self.LINUX_UTMP_ENTRY_SIZE:
      return False

    try:
      entry = self.LINUX_UTMP_ENTRY.parse(data)
    except (IOError, construct.FieldError):
      logging.warning((
          u'UTMP entry at 0x{0:x} couldn\'t be parsed.').format(offset))
      return False

    user = self._GetTextFromNullTerminatedString(entry.username)
    terminal = self._GetTextFromNullTerminatedString(entry.terminal)
    if terminal == u'~':
      terminal = u'system boot'
    computer_name = self._GetTextFromNullTerminatedString(entry.hostname)
    if computer_name == u'N/A' or computer_name == u':0':
      computer_name = u'localhost'
    status = self.STATUS_TYPE.get(entry.type, u'N/A')

    if entry.address_b:
      ip_address = u'{0:d}.{1:d}.{2:d}.{3:d}'.format(
          entry.address_a, entry.address_b, entry.address_c, entry.address_d)
    else:
      try:
        ip_address = socket.inet_ntoa(
            construct.ULInt32(u'int').build(entry.address_a))
        if ip_address == u'0.0.0.0':
          ip_address = u'localhost'
      except (IOError, construct.FieldError, socket.error):
        ip_address = u'N/A'

    event_data = UtmpEventData()
    event_data.computer_name = computer_name
    event_data.exit = entry.exit
    event_data.ip_address = ip_address
    event_data.pid = entry.pid
    event_data.status = status
    event_data.terminal_id = entry.terminal_id
    event_data.terminal = terminal
    event_data.user = user

    timestamp = (entry.timestamp * 1000000) + entry.microseconds
    date_time = dfdatetime_posix_time.PosixTimeInMicroseconds(
        timestamp=timestamp)
    event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_START)
    parser_mediator.ProduceEventWithEventData(event, event_data)

    return True

  def _VerifyTextField(self, text):
    """Check if a byte stream is a null terminated string.

    Args:
      event_object: text field from the structure.

    Returns:
      bool: True if it is a null terminated string, False otherwise.
    """
    _, _, null_chars = text.partition(b'\x00')
    if not null_chars:
      return False
    return len(null_chars) == null_chars.count(b'\x00')

  def ParseFileObject(self, parser_mediator, file_object, **kwargs):
    """Parses an UTMP file-like object.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      file_object (dfvfs.FileIO): a file-like object.

    Raises:
      UnableToParseFile: when the file cannot be parsed.
    """
    try:
      structure = self.LINUX_UTMP_ENTRY.parse_stream(file_object)
    except (IOError, construct.FieldError) as exception:
      raise errors.UnableToParseFile(
          u'Unable to parse UTMP Header with error: {0:s}'.format(exception))

    if structure.type not in self.STATUS_TYPE:
      raise errors.UnableToParseFile((
          u'Not an UTMP file, unknown type '
          u'[{0:d}].').format(structure.type))

    if not self._VerifyTextField(structure.terminal):
      raise errors.UnableToParseFile(
          u'Not an UTMP file, unknown terminal.')

    if not self._VerifyTextField(structure.username):
      raise errors.UnableToParseFile(
          u'Not an UTMP file, unknown username.')

    if not self._VerifyTextField(structure.hostname):
      raise errors.UnableToParseFile(
          u'Not an UTMP file, unknown hostname.')

    # Check few values.
    terminal = self._GetTextFromNullTerminatedString(
        structure.terminal, self._DEFAULT_TEST_VALUE)
    if terminal == self._DEFAULT_TEST_VALUE:
      raise errors.UnableToParseFile(
          u'Not an UTMP file, no terminal set.')

    username = self._GetTextFromNullTerminatedString(
        structure.username, self._DEFAULT_TEST_VALUE)

    if username == self._DEFAULT_TEST_VALUE:
      raise errors.UnableToParseFile(
          u'Not an UTMP file, no username set.')

    if not structure.timestamp:
      raise errors.UnableToParseFile(
          u'Not an UTMP file, no timestamp set in the first record.')

    file_object.seek(0, os.SEEK_SET)
    while self._ReadEntry(parser_mediator, file_object):
      pass


manager.ParsersManager.RegisterParser(UtmpParser)
