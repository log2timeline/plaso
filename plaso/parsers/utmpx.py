#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2013 The Plaso Project Authors.
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
"""Parser for utmpx files."""

# TODO: Add support for other implementations than Mac OS X.

import construct
import logging

from plaso.lib import errors
from plaso.lib import event
from plaso.lib import eventdata
from plaso.lib import parser
from plaso.lib import timelib


__author__ = 'Joaquin Moreno Garijo (bastionado@gmail.com)'


class UtmpxMacOsXBootTimeEvent(event.EventObject):
  """Convenience class for boot time from utmpx file."""
  DATA_TYPE = 'mac:utmpx:boottime'

  def __init__(self, timestamp):
    """Initializes the event of boot time system.

    Args:
      timestamp: when the file register the boot time.
    """
    super(UtmpxMacOsXBootTimeEvent, self).__init__()
    self.timestamp = timestamp
    self.timestamp_desc = eventdata.EventTimestamp.START_TIME


class UtmpxMacOsXEvent(event.EventObject):
  """Convenience class for an event utmpx."""
  DATA_TYPE = 'mac:utmpx:event'

  def __init__(self, user, terminal, status, timestamp):
    """Initializes the event object.

    Args:
      user: active user name
      terminal: name of the terminal
      status: terminal status
      timestamp: when the terminal was started
    """
    super(UtmpxMacOsXEvent, self).__init__()
    self.user = user
    self.terminal = terminal
    self.status = status
    self.timestamp = timestamp
    self.timestamp_desc = eventdata.EventTimestamp.START_TIME


class UtmpxParser(parser.BaseParser):
  """Parser for UTMPX files. """

  NAME = 'utmpx'

  MAC_UTMPX_HEADER = construct.Struct(
      'header',
      construct.Bytes('magic', 10),
      construct.Padding(286),
      construct.ULInt16('id'),
      construct.Padding(622),
      construct.ULInt32('unknown1'),
      construct.ULInt32('unknown2'),
      construct.ULInt32('timestamp'),
      construct.Padding(324))

  # INFO: Type is suppose to be a short (2 bytes),
  # however if we analyze the file it is always
  # byte follow by 3 bytes with \x00 value.
  MAC_UTMPX_STRUCT = construct.Struct(
      'utmpx_mac',
      construct.String('user', 256),
      construct.ULInt32('id'),
      construct.String('tty_name', 32),
      construct.ULInt32('pid'),
      construct.ULInt32('status_type'),
      construct.ULInt32('timestamp'),
      construct.ULInt32('microsecond'),
      construct.String('hostname', 256),
      construct.Padding(64))

  MAC_STATUS_TYPE = {
      0 : 'EMPTY',
      1 : 'RUN_LVL',
      2 : 'BOOT_TIME',
      3 : 'OLD_TIME',
      4 : 'NEW_TIME',
      5 : 'INIT_PROCESS',
      6 : 'LOGIN_PROCESS',
      7 : 'USER_PROCESS',
      8 : 'DEAD_PROCESS'}

  MAC_MAGIC = 'utmpx-1.00'

  def __init__(self, pre_obj, config):
    """Initializes the parser.

    Args:
      pre_obj: pre-parsing object.
      config: configuration object.
    """
    super(UtmpxParser, self).__init__(pre_obj, config)
    self._utmpx_record_size = self.MAC_UTMPX_STRUCT.sizeof()

  def _ReadEntry(self, file_object):
    """Reads an UTMPX entry.

    Args:
      file_object: a file-like object that points to an UTMPX file.

    Returns:
      An event object constructed from the UTMPX entry.
    """
    data = file_object.read(self._utmpx_record_size)
    if len(data) != self._utmpx_record_size:
      return

    try:
      entry = self.MAC_UTMPX_STRUCT.parse(data)
    except (IOError, construct.FieldError) as e:
      logging.warning(
          u'Unable to parse Mac OS X UTMPX entry with error: {0:s}'.format(e))
      return

    user, _, _ = entry.user.partition('\x00')
    if not user:
      user = 'N/A'
    terminal, _, _ = entry.tty_name.partition('\x00')
    if not terminal:
      terminal = 'N/A'

    value_status = self.MAC_STATUS_TYPE.get(entry.status_type, 'N/A')
    status = u'{0} ({1:#04x})'.format(value_status, entry.status_type)

    timestamp = timelib.Timestamp.FromPosixTimeWithMicrosecond(
        entry.timestamp, entry.microsecond)

    return UtmpxMacOsXEvent(user, terminal, status, timestamp)

  def Parse(self, file_entry):
    """Extract data from a UTMPX file.

    Args:
      file_entry: a file entry object.

    Returns:
      An UtmpxMacOsXEvent for each logon/logoff event.
    """
    try:
      file_object = file_entry.Open()
      header = self.MAC_UTMPX_HEADER.parse_stream(file_object)
    except (IOError, construct.FieldError) as e:
      raise errors.UnableToParseFile(
          u'Unable to parse Mac OS X UTMPX header with error: {0:s}'.format(e))

    if header.magic != self.MAC_MAGIC:
      raise errors.UnableToParseFile(u'Invalid Mac OS X UTMPX header.')

    yield UtmpxMacOsXBootTimeEvent(
        timelib.Timestamp.FromPosixTime(header.timestamp))

    event_object = self._ReadEntry(file_object)
    while event_object:
      yield event_object
      event_object = self._ReadEntry(file_object)
