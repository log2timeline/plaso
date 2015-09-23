# -*- coding: utf-8 -*-
"""Parser for Linux UTMP files."""

import construct
import logging
import os
import socket

from plaso.events import time_events
from plaso.lib import errors
from plaso.lib import eventdata
from plaso.parsers import interface
from plaso.parsers import manager


__author__ = 'Joaquin Moreno Garijo (Joaquin.MorenoGarijo.2013@live.rhul.ac.uk)'


class UtmpEvent(time_events.PosixTimeEvent):
  """Convenience class for an UTMP event."""

  DATA_TYPE = u'linux:utmp:event'

  def __init__(
      self, posix_time, microsecond, user, computer_name,
      terminal, status, ip_address, structure):
    """Initializes the event object.

    Args:
      posix_time: the POSIX time value, which contains the number of seconds
                  since January 1, 1970 00:00:00 UTC.
      microsecond: number of micro seconds.
      user: active user name.
      computer_name: name of the computer.
      terminal: type of terminal.
      status: login status.
      ip_address: ip_address from the connection is done.
      structure: entry structure parsed.
        exit: integer that represents the exit status.
        pid: integer with the process ID.
        terminal_id: integer with the Inittab ID.
    """
    super(UtmpEvent, self).__init__(
        posix_time, eventdata.EventTimestamp.START_TIME,
        micro_seconds=microsecond)
    self.computer_name = computer_name
    self.exit = structure.exit
    self.ip_address = ip_address
    self.pid = structure.pid
    self.status = status
    self.terminal_id = structure.terminal_id
    self.terminal = terminal
    self.user = user


class UtmpParser(interface.SingleFileBaseParser):
  """Parser for Linux/Unix UTMP files."""

  _INITIAL_FILE_OFFSET = None

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
      construct.ULInt32(u'microsecond'),
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

  def ParseFileObject(self, parser_mediator, file_object, **kwargs):
    """Parses an UTMP file-like object.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      file_object: The file-like object to extract data from.

    Raises:
      UnableToParseFile: when the file cannot be parsed.
    """
    file_object.seek(0, os.SEEK_SET)
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
    event_object = self._ReadUtmpEvent(file_object)
    while event_object:
      event_object.offset = file_object.tell()
      parser_mediator.ProduceEvent(event_object)
      event_object = self._ReadUtmpEvent(file_object)

  def _VerifyTextField(self, text):
    """Check if a byte stream is a null terminated string.

    Args:
      event_object: text field from the structure.

    Return:
      True if it is a null terminated string, False otherwise.
    """
    _, _, null_chars = text.partition(b'\x00')
    if not null_chars:
      return False
    return len(null_chars) == null_chars.count(b'\x00')

  def _ReadUtmpEvent(self, file_object):
    """Returns an UtmpEvent from a single UTMP entry.

    Args:
      file_object: a file-like object that points to an UTMP file.

    Returns:
      An event object constructed from a single UTMP record or None if we
      have reached the end of the file (or EOF).
    """
    offset = file_object.tell()
    data = file_object.read(self.LINUX_UTMP_ENTRY_SIZE)
    if not data or len(data) != self.LINUX_UTMP_ENTRY_SIZE:
      return
    try:
      entry = self.LINUX_UTMP_ENTRY.parse(data)
    except (IOError, construct.FieldError):
      logging.warning((
          u'UTMP entry at 0x{:x} couldn\'t be parsed.').format(offset))
      return self._ReadUtmpEvent(file_object)

    user = self._GetTextFromNullTerminatedString(entry.username)
    terminal = self._GetTextFromNullTerminatedString(entry.terminal)
    if terminal == u'~':
      terminal = u'system boot'
    computer_name = self._GetTextFromNullTerminatedString(entry.hostname)
    if computer_name == u'N/A' or computer_name == u':0':
      computer_name = u'localhost'
    status = self.STATUS_TYPE.get(entry.type, u'N/A')

    if not entry.address_b:
      try:
        ip_address = socket.inet_ntoa(
            construct.ULInt32(u'int').build(entry.address_a))
        if ip_address == u'0.0.0.0':
          ip_address = u'localhost'
      except (IOError, construct.FieldError, socket.error):
        ip_address = u'N/A'
    else:
      ip_address = u'{0:d}.{1:d}.{2:d}.{3:d}'.format(
          entry.address_a, entry.address_b, entry.address_c, entry.address_d)

    return UtmpEvent(
        entry.timestamp, entry.microsecond, user, computer_name, terminal,
        status, ip_address, entry)

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


manager.ParsersManager.RegisterParser(UtmpParser)
