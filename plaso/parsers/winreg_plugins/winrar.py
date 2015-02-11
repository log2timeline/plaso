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
"""This file contains a parser for WinRAR for Plaso."""

import re

from plaso.events import windows_events
from plaso.parsers import winreg
from plaso.parsers.winreg_plugins import interface


__author__ = 'David Nides (david.nides@gmail.com)'


class WinRarHistoryPlugin(interface.KeyPlugin):
  """Windows Registry plugin for parsing WinRAR History keys."""
  # TODO: Create NTUSER.DAT test file with WinRAR data.

  NAME = 'winreg_winrar'
  DESCRIPTION = u'Parser for WinRAR History Registry data.'

  REG_TYPE = 'NTUSER'
  REG_KEYS = [
      u'\\Software\\WinRAR\\DialogEditHistory\\ExtrPath',
      u'\\Software\\WinRAR\\DialogEditHistory\\ArcName',
      u'\\Software\\WinRAR\\ArcHistory']

  _RE_VALUE_NAME = re.compile(r'^[0-9]+$', re.I)

  def GetEntries(
      self, parser_mediator, key=None, registry_type=None, codepage='cp1252',
      **kwargs):
    """Collect values under WinRAR ArcHistory and return event for each one.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      key: Optional Registry key (instance of winreg.WinRegKey).
           The default is None.
      registry_type: Optional Registry type string. The default is None.
    """
    for value in key.GetValues():
      # Ignore any value not in the form: '[0-9]+'.
      if not value.name or not self._RE_VALUE_NAME.search(value.name):
        continue

      # Ignore any value that is empty or that does not contain a string.
      if not value.data or not value.DataIsString():
        continue

      if value.name == '0':
        timestamp = key.last_written_timestamp
      else:
        timestamp = 0

      text_dict = {}
      text_dict[value.name] = value.data

      # TODO: shouldn't this behavior be, put all the values
      # into a single event object with the last written time of the key?
      event_object = windows_events.WindowsRegistryEvent(
          timestamp, key.path, text_dict, offset=key.offset,
          registry_type=registry_type,
          source_append=': WinRAR History')
      parser_mediator.ProduceEvent(event_object)


winreg.WinRegistryParser.RegisterPlugin(WinRarHistoryPlugin)
