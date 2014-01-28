#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2014 The Plaso Project Authors.
# Please see the AUTHORS file for details on individual authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Parser for Linux UTMP files."""

import construct
import logging
import os
import socket

from plaso.lib import errors
from plaso.lib import event
from plaso.lib import eventdata
from plaso.lib import parser
from plaso.lib import timelib


__author__ = 'Joaquin Moreno Garijo (Joaquin.MorenoGarijo.2013@live.rhul.ac.uk)'


class UtmpEvent(event.EventObject):
  """Convenience class for an UTMP event."""

  DATA_TYPE = 'linux:utmp:event'

  def __init__(
      self, timestamp, microsecond, user, computer_name,
      terminal, status, ip_address, structure):
    """Initializes the event object.

    Args:
      timestamp: Epoch when the terminal was started.
      microsecond: number of microseconds related with timestamp.
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
    super(UtmpEvent, self).__init__()
    self.timestamp = timelib.Timestamp.FromPosixTimeWithMicrosecond(
        timestamp, microsecond)
    self.timestamp_desc = eventdata.EventTimestamp.START_TIME
    self.user = user
    self.computer_name = computer_name
    self.terminal = terminal
    self.status = status
    self.ip_address = ip_address
    self.exit = structure.exit
    self.pid = structure.pid
    self.terminal_id = structure.terminal_id


class UtmpParser(parser.BaseParser):
  """Parser for Linux UTMP files."""

  NAME = 'utmp'

  LINUX_UTMP_ENTRY = construct.Struct(
      'utmp_linux',
      construct.ULInt32('type'),
      construct.ULInt32('pid'),
      construct.String('terminal', 32),
      construct.ULInt32('terminal_id'),
      construct.String('username', 32),
      construct.String('hostname', 256),
      construct.ULInt16('termination'),
      construct.ULInt16('exit'),
      construct.ULInt32('session'),
      construct.ULInt32('timestamp'),
      construct.ULInt32('microsecond'),
      construct.ULInt32('address_a'),
      construct.ULInt32('address_b'),
      construct.ULInt32('address_c'),
      construct.ULInt32('address_d'),
      construct.Padding(20))

  STATUS_TYPE = {
      0: 'EMPTY',
      1: 'RUN_LVL',
      2: 'BOOT_TIME',
      3: 'NEW_TIME',
      4: 'OLD_TIME',
      5: 'INIT_PROCESS',
      6: 'LOGIN_PROCESS',
      7: 'USER_PROCESS',
      8: 'DEAD_PROCESS',
      9: 'ACCOUNTING'}

  def __init__(self, pre_obj, config=None):
    """Initializes the parser.

    Args:
      pre_obj: pre-parsing object.
      config: configuration object.
    """
    super(UtmpParser, self).__init__(pre_obj, config)
    self._utmp_record_size = self.LINUX_UTMP_ENTRY.sizeof()

  def Parse(self, file_entry):
    """Extract data from an UTMP file.

    Args:
      file_entry: a file entry object.

    Returns:
      An UtmpEvent for each entry.
    """

    file_object = file_entry.Open()
    try:
      structure = self.LINUX_UTMP_ENTRY.parse_stream(file_object)
    except (IOError, construct.FieldError) as exception:
      raise errors.UnableToParseFile((
          u'Not an UTMP Header, unable to parse. '
          u'Reason given: {}').format(exception))
    if structure.type not in self.STATUS_TYPE:
      raise errors.UnableToParseFile((
          u'Not an UTMP file, unknown type '
          u'[{}].').format(structure.type))
    if not self._VerifyTextField(structure.terminal):
      raise errors.UnableToParseFile((
          u'Not an UTMP file, unknown terminal'
          u'[{}].').format(structure.terminal))
    if not self._VerifyTextField(structure.username):
      raise errors.UnableToParseFile((
          u'Not an UTMP file, unknown username'
          u'[{}].').format(structure.username))
    if not self._VerifyTextField(structure.hostname):
      raise errors.UnableToParseFile((
          u'Not an UTMP file, unknown hostname '
          u'[{}].').format(structure.hostname))

    file_object.seek(0, os.SEEK_SET)
    event_object = self._ReadUtmpEvent(file_object)
    while event_object:
      event_object.offset = file_object.tell()
      yield event_object
      event_object = self._ReadUtmpEvent(file_object)

  def _VerifyTextField(self, text):
    """Check if a bytestream is a null terminated string.

    Args:
      event_object: text field from the structure.

    Return:
      True if it is a null terminated string, False otherwise.
    """
    _, _, null_chars = text.partition('\x00')
    if not null_chars:
      return False
    return len(null_chars) == null_chars.count('\x00')

  def _ReadUtmpEvent(self, file_object):
    """Returns an UtmpEvent from a single UTMP entry.

    Args:
      file_object: a file-like object that points to an UTMP file.

    Returns:
      An event object constructed from a single UTMP record or None if we
      have reached the end of the file (or EOF).
    """
    offset = file_object.tell()
    data = file_object.read(self._utmp_record_size)
    if not data or len(data) != self._utmp_record_size:
      return
    try:
      entry = self.LINUX_UTMP_ENTRY.parse(data)
    except (IOError, construct.FieldError):
      logging.warning((
          u'UTMP entry at 0x{:x} couldn\'t be parsed.').format(offset))
      return self.__ReadUtmpEvent(file_object)

    user = self._GetTextFromNullTerminatedString(entry.username)
    terminal = self._GetTextFromNullTerminatedString(entry.terminal)
    if terminal == '~':
      terminal = u'system boot'
    computer_name = self._GetTextFromNullTerminatedString(entry.hostname)
    if computer_name == u'N/A' or computer_name == u':0':
      computer_name = u'localhost'
    status = self.STATUS_TYPE.get(entry.type, u'N/A')

    if not entry.address_b:
      try:
        ip_address = socket.inet_ntoa(
            construct.ULInt32('int').build(entry.address_a))
        if ip_address == '0.0.0.0':
          ip_address = u'localhost'
      except (IOError, construct.FieldError, socket.error):
        ip_address = u'N/A'
    else:
      ip_address = u'.'.join(
          [entry.address_a, entry.address_b,
           entry.address_c, entry.address_d])

    return UtmpEvent(entry.timestamp, entry.microsecond, user,
        computer_name, terminal, status, ip_address, entry)

  def _GetTextFromNullTerminatedString(
      self, null_terminated_string, default_string = u'N/A'):
    """Get a UTF-8 text from a raw null terminated string.

    Args:
      null_terminated_string: Raw string terminated with null character.
      default_string: The default string returned if the parser fails.

    Returns:
      A decoded UTF-8 string or if unable to decode, the supplied default
      string.
    """
    text, _, _ = null_terminated_string.partition('\x00')
    try:
      text = text.decode('utf-8')
    except UnicodeDecodeError:
      logging.warning(
          u'Decode UTF8 failed, the message string may be cut short.')
      text = text.decode('utf-8', 'ignore')
    if not text:
      return default_string
    return text

