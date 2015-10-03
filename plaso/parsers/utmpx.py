# -*- coding: utf-8 -*-
"""Parser for utmpx files."""

# TODO: Add support for other implementations than Mac OS X.
#       The parser should be checked against IOS UTMPX file.

import logging

import construct

from plaso.events import time_events
from plaso.lib import errors
from plaso.lib import eventdata
from plaso.parsers import interface
from plaso.parsers import manager


__author__ = 'Joaquin Moreno Garijo (Joaquin.MorenoGarijo.2013@live.rhul.ac.uk)'


class UtmpxMacOsXEvent(time_events.PosixTimeEvent):
  """Convenience class for an event utmpx."""
  DATA_TYPE = u'mac:utmpx:event'

  def __init__(
      self, posix_time, user, terminal, status, computer_name, micro_seconds=0):
    """Initializes the event object.

    Args:
      posix_time: the POSIX time value, which contains the number of seconds
                  since January 1, 1970 00:00:00 UTC.
      user: active user name
      terminal: name of the terminal
      status: terminal status
      computer_name: name of the host or IP.
      micro_seconds: optional number of micro seconds.
    """
    super(UtmpxMacOsXEvent, self).__init__(
        posix_time, eventdata.EventTimestamp.START_TIME,
        micro_seconds=micro_seconds)
    self.computer_name = computer_name
    self.status = status
    self.terminal = terminal
    self.user = user


class UtmpxParser(interface.SingleFileBaseParser):
  """Parser for UTMPX files."""

  NAME = u'utmpx'
  DESCRIPTION = u'Parser for UTMPX files.'

  # INFO: Type is suppose to be a short (2 bytes),
  # however if we analyze the file it is always
  # byte follow by 3 bytes with \x00 value.
  MAC_UTMPX_ENTRY = construct.Struct(
      u'utmpx_mac',
      construct.String(u'user', 256),
      construct.ULInt32(u'id'),
      construct.String(u'tty_name', 32),
      construct.ULInt32(u'pid'),
      construct.ULInt16(u'status_type'),
      construct.ULInt16(u'unknown'),
      construct.ULInt32(u'timestamp'),
      construct.ULInt32(u'microsecond'),
      construct.String(u'hostname', 256),
      construct.Padding(64))

  MAC_UTMPX_ENTRY_SIZE = MAC_UTMPX_ENTRY.sizeof()

  # 9, 10 and 11 are only for Darwin and IOS.
  MAC_STATUS_TYPE = {
      0: u'EMPTY',
      1: u'RUN_LVL',
      2: u'BOOT_TIME',
      3: u'OLD_TIME',
      4: u'NEW_TIME',
      5: u'INIT_PROCESS',
      6: u'LOGIN_PROCESS',
      7: u'USER_PROCESS',
      8: u'DEAD_PROCESS',
      9: u'ACCOUNTING',
      10: u'SIGNATURE',
      11: u'SHUTDOWN_TIME'}

  def _ReadEntry(self, file_object):
    """Reads an UTMPX entry.

    Args:
      file_object: a file-like object that points to an UTMPX file.

    Returns:
      An event object (instance of UtmpxMacOsXEvent) or None if
      the UTMPX entry cannot be read.
    """
    data = file_object.read(self.MAC_UTMPX_ENTRY_SIZE)
    if len(data) != self.MAC_UTMPX_ENTRY_SIZE:
      return

    try:
      entry = self.MAC_UTMPX_ENTRY.parse(data)
    except (IOError, construct.FieldError) as exception:
      logging.warning(
          u'Unable to parse Mac OS X UTMPX entry with error: {0:s}'.format(
              exception))
      return

    user, _, _ = entry.user.partition(b'\x00')
    if not user:
      user = u'N/A'

    terminal, _, _ = entry.tty_name.partition(b'\x00')
    if not terminal:
      terminal = u'N/A'

    computer_name, _, _ = entry.hostname.partition(b'\x00')
    if not computer_name:
      computer_name = u'localhost'

    value_status = self.MAC_STATUS_TYPE.get(entry.status_type, u'N/A')
    status = u'{0}'.format(value_status)

    return UtmpxMacOsXEvent(
        entry.timestamp, user, terminal, status, computer_name,
        micro_seconds=entry.microsecond)

  def _VerifyStructure(self, file_object):
    """Verify that we are dealing with an UTMPX entry.

    Args:
      file_object: a file-like object that points to an UTMPX file.

    Returns:
      True if it is a UTMPX entry or False otherwise.
    """
    # First entry is a SIGNAL entry of the file ("header").
    try:
      header = self.MAC_UTMPX_ENTRY.parse_stream(file_object)
    except (IOError, construct.FieldError):
      return False
    user, _, _ = header.user.partition(b'\x00')

    # The UTMPX_ENTRY structure will often successfully compile on various
    # structures, such as binary plist files, and thus we need to do some
    # additional validation. The first one is to check if the user name
    # can be converted into a unicode string, otherwise we can assume
    # we are dealing with non UTMPX data.
    try:
      user.decode(u'utf-8')
    except UnicodeDecodeError:
      return False

    if user != b'utmpx-1.00':
      return False
    if self.MAC_STATUS_TYPE[header.status_type] != u'SIGNATURE':
      return False
    if header.timestamp != 0 or header.microsecond != 0 or header.pid != 0:
      return False
    tty_name, _, _ = header.tty_name.partition(b'\x00')
    hostname, _, _ = header.hostname.partition(b'\x00')
    if tty_name or hostname:
      return False

    return True

  def ParseFileObject(self, parser_mediator, file_object, **kwargs):
    """Parses an UTMPX file-like object.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      file_object: The file-like object to extract data from.

    Raises:
      UnableToParseFile: when the file cannot be parsed.
    """
    if not self._VerifyStructure(file_object):
      raise errors.UnableToParseFile(
          u'The file is not an UTMPX file.')

    event_object = self._ReadEntry(file_object)
    while event_object:
      event_object.offset = file_object.tell()
      parser_mediator.ProduceEvent(event_object)

      event_object = self._ReadEntry(file_object)


manager.ParsersManager.RegisterParser(UtmpxParser)
