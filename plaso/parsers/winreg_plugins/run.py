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
"""This file contains the Run/RunOnce Key plugins for Plaso."""

from plaso.events import windows_events
from plaso.parsers import winreg
from plaso.parsers.winreg_plugins import interface


class RunUserPlugin(interface.KeyPlugin):
  """Windows Registry plugin for parsing user specific auto runs."""

  NAME = 'winreg_run'
  DESCRIPTION = u'Parser for run and run once Registry data.'

  REG_TYPE = 'NTUSER'

  REG_KEYS = [
      u'\\Software\\Microsoft\\Windows\\CurrentVersion\\Run',
      u'\\Software\\Microsoft\\Windows\\CurrentVersion\\RunOnce']

  URLS = ['http://msdn.microsoft.com/en-us/library/aa376977(v=vs.85).aspx']

  def GetEntries(
      self, parser_mediator, key=None, registry_type=None, codepage='cp1252',
      **unused_kwargs):
    """Collect the Values under the Run Key and return an event for each one.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      key: Optional Registry key (instance of winreg.WinRegKey).
           The default is None.
      registry_type: Optional Registry type string. The default is None.
    """
    for value in key.GetValues():
      # Ignore the default value.
      if not value.name:
        continue

      # Ignore any value that is empty or that does not contain a string.
      if not value.data or not value.DataIsString():
        continue

      text_dict = {}
      text_dict[value.name] = value.data

      event_object = windows_events.WindowsRegistryEvent(
          key.last_written_timestamp, key.path, text_dict, offset=key.offset,
          urls=self.URLS, registry_type=registry_type,
          source_append=': Run Key')
      parser_mediator.ProduceEvent(event_object)


class RunSoftwarePlugin(RunUserPlugin):
  """Windows Registry plugin for parsing system wide auto runs."""

  NAME = 'winreg_run_software'

  REG_TYPE = 'SOFTWARE'

  REG_KEYS = [
      u'\\Microsoft\\Windows\\CurrentVersion\\Run',
      u'\\Microsoft\\Windows\\CurrentVersion\\RunOnce',
      u'\\Microsoft\\Windows\\CurrentVersion\\RunOnce\\Setup',
      u'\\Microsoft\\Windows\\CurrentVersion\\RunServices',
      u'\\Microsoft\\Windows\\CurrentVersion\\RunServicesOnce']


winreg.WinRegistryParser.RegisterPlugins([RunUserPlugin, RunSoftwarePlugin])
