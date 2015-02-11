#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2014 The Plaso Project Authors.
# Please see the AUTHORS file for details on individual authors.#
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
"""This file contains the LastShutdown value plugin."""

import construct
import logging
from plaso.events import windows_events
from plaso.lib import eventdata
from plaso.lib import timelib
from plaso.parsers import winreg
from plaso.parsers.winreg_plugins import interface


__author__ = 'Preston Miller, dpmforensics.com, github.com/prmiller91'


class ShutdownPlugin(interface.KeyPlugin):
  """Windows Registry plugin for parsing the last shutdown time of a system."""

  NAME = 'winreg_shutdown'
  DESCRIPTION = u'Parser for ShutdownTime Registry value.'

  REG_KEYS = [u'\\{current_control_set}\\Control\\Windows']
  REG_TYPE = 'SYSTEM'
  FILETIME_STRUCT = construct.ULInt64('filetime_timestamp')

  def GetEntries(
      self, parser_mediator, key=None, registry_type=None, codepage='cp1252',
      **unused_kwargs):
    """Collect ShutdownTime value under Windows and produce an event object.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      key: Optional Registry key (instance of winreg.WinRegKey).
          The default is None.
      registry_type: Optional Registry type string. The default is None.
    """
    shutdown_value = key.GetValue('ShutdownTime')
    if not shutdown_value:
      return
    text_dict = {}
    text_dict['Description'] = shutdown_value.name
    try:
      filetime = self.FILETIME_STRUCT.parse(shutdown_value.data)
    except construct.FieldError as exception:
      logging.error(
          u'Unable to extract shutdown timestamp: {0:s}'.format(exception))
      return
    timestamp = timelib.Timestamp.FromFiletime(filetime)

    event_object = windows_events.WindowsRegistryEvent(
        timestamp, key.path, text_dict,
        usage=eventdata.EventTimestamp.LAST_SHUTDOWN, offset=key.offset,
        registry_type=registry_type,
        source_append=u'Shutdown Entry')
    parser_mediator.ProduceEvent(event_object)


winreg.WinRegistryParser.RegisterPlugin(ShutdownPlugin)
