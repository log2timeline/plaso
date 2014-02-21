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

from plaso.lib import event
from plaso.parsers.winreg_plugins import interface


class RunUserPlugin(interface.KeyPlugin):
  """Windows Registry plugin for parsing user specific auto runs."""

  NAME = 'winreg_run'

  REG_TYPE = 'NTUSER'

  REG_KEYS = [
      u'\\Software\\Microsoft\\Windows\\CurrentVersion\\Run',
      u'\\Software\\Microsoft\\Windows\\CurrentVersion\\RunOnce']

  URLS = ['http://msdn.microsoft.com/en-us/library/aa376977(v=vs.85).aspx']
  DESCRIPTION = 'Run Key'

  def GetEntries(self, key, **unused_kwargs):
    """Collect the Values under the Run Key and return an event for each one."""
    for value in key.GetValues():
      # Ignore the default value.
      if not value.name:
        continue

      # Ignore any value that is empty or that does not contain a string.
      if not value.data or not value.DataIsString():
        continue

      text_dict = {}
      text_dict[value.name] = value.data

      yield event.WinRegistryEvent(
          key.path, text_dict, timestamp=key.last_written_timestamp,
          source_append=': {0:s}'.format(self.DESCRIPTION))


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
