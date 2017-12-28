# -*- coding: utf-8 -*-
"""Parser for utmpx files."""

from __future__ import unicode_literals

# TODO: Add support for other implementations than Mac OS X.
#       The parser should be checked against IOS UTMPX file.

import logging

import construct

from dfdatetime import posix_time as dfdatetime_posix_time

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import errors
from plaso.lib import definitions
from plaso.parsers import interface
from plaso.parsers import manager


class UtmpxMacOsXEventData(events.EventData):
  """Mac OS X utmpx event data.

  Attributes:
    computer_name (str): name of the host or IP address.
    status_type (int): terminal status type.
    terminal (str): name of the terminal.
    user (str): active user name.
  """

  DATA_TYPE = 'mac:utmpx:event'

  def __init__(self):
    """Initializes event data."""
    super(UtmpxMacOsXEventData, self).__init__(data_type=self.DATA_TYPE)
    self.computer_name = None
    self.status_type = None
    self.terminal = None
    self.user = None


class UtmpxParser(interface.FileObjectParser):
  """Parser for UTMPX files."""

  NAME = 'utmpx'
  DESCRIPTION = 'Parser for UTMPX files.'

  # INFO: Type is suppose to be a short (2 bytes),
  # however if we analyze the file it is always
  # byte follow by 3 bytes with \x00 value.
  _UTMPX_ENTRY = construct.Struct(
      'utmpx_mac',
      construct.String('user', 256),
      construct.ULInt32('id'),
      construct.String('tty_name', 32),
      construct.ULInt32('pid'),
      construct.ULInt16('status_type'),
      construct.ULInt16('unknown'),
      construct.ULInt32('timestamp'),
      construct.ULInt32('microseconds'),
      construct.String('hostname', 256),
      construct.Padding(64))

  _UTMPX_ENTRY_SIZE = _UTMPX_ENTRY.sizeof()

  _STATUS_TYPE_SIGNATURE = 10

  def _ReadEntry(self, parser_mediator, file_object):
    """Reads an UTMPX entry.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      file_object (dfvfs.FileIO): a file-like object.

    Returns:
      bool: True if the UTMPX entry was successfully read.
    """
    data = file_object.read(self._UTMPX_ENTRY_SIZE)
    if len(data) != self._UTMPX_ENTRY_SIZE:
      return False

    try:
      entry_struct = self._UTMPX_ENTRY.parse(data)
    except (IOError, construct.FieldError) as exception:
      logging.warning(
          'Unable to parse Mac OS X UTMPX entry with error: {0!s}'.format(
              exception))
      return False

    user, _, _ = entry_struct.user.partition(b'\x00')
    if not user:
      user = 'N/A'

    terminal, _, _ = entry_struct.tty_name.partition(b'\x00')
    if not terminal:
      terminal = 'N/A'

    computer_name, _, _ = entry_struct.hostname.partition(b'\x00')
    if not computer_name:
      computer_name = 'localhost'

    event_data = UtmpxMacOsXEventData()
    event_data.computer_name = computer_name
    event_data.offset = file_object.tell()
    event_data.status_type = entry_struct.status_type
    event_data.terminal = terminal
    event_data.user = user

    timestamp = (entry_struct.timestamp * 1000000) + entry_struct.microseconds
    date_time = dfdatetime_posix_time.PosixTimeInMicroseconds(
        timestamp=timestamp)
    event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_START)
    parser_mediator.ProduceEventWithEventData(event, event_data)

    return True

  def _VerifyStructure(self, file_object):
    """Verify that we are dealing with an UTMPX entry.

    Args:
      file_object (dfvfs.FileIO): a file-like object.

    Returns:
      bool: True if it is a UTMPX entry or False otherwise.
    """
    # First entry is a SIGNAL entry of the file ("header").
    try:
      header_struct = self._UTMPX_ENTRY.parse_stream(file_object)
    except (IOError, construct.FieldError):
      return False
    user, _, _ = header_struct.user.partition(b'\x00')

    # The UTMPX_ENTRY structure will often successfully compile on various
    # structures, such as binary plist files, and thus we need to do some
    # additional validation. The first one is to check if the user name
    # can be converted into a Unicode string, otherwise we can assume
    # we are dealing with non UTMPX data.
    try:
      user.decode('utf-8')
    except UnicodeDecodeError:
      return False

    if user != b'utmpx-1.00':
      return False
    if header_struct.status_type != self._STATUS_TYPE_SIGNATURE:
      return False
    if (header_struct.timestamp != 0 or header_struct.microseconds != 0 or
        header_struct.pid != 0):
      return False
    tty_name, _, _ = header_struct.tty_name.partition(b'\x00')
    hostname, _, _ = header_struct.hostname.partition(b'\x00')
    if tty_name or hostname:
      return False

    return True

  def ParseFileObject(self, parser_mediator, file_object, **kwargs):
    """Parses an UTMPX file-like object.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      file_object (dfvfs.FileIO): a file-like object.

    Raises:
      UnableToParseFile: when the file cannot be parsed.
    """
    if not self._VerifyStructure(file_object):
      raise errors.UnableToParseFile(
          'The file is not an UTMPX file.')

    while self._ReadEntry(parser_mediator, file_object):
      pass


manager.ParsersManager.RegisterParser(UtmpxParser)
