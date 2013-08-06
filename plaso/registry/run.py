#!/usr/bin/python
# -*- coding: utf-8 -*-
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
from plaso.lib import win_registry_interface


class RunBase(win_registry_interface.KeyPlugin):
  """Base class for all Run Key plugins."""

  __abstract = True

  URLS = ['http://msdn.microsoft.com/en-us/library/aa376977(v=vs.85).aspx']
  DESCRIPTION = 'Run Key'

  def GetEntries(self):
    """Collect the Values under the Run Key and return an event for each one."""
    for value in self._key.GetValues():
      # Ignore the default value.
      if not value.name:
        continue

      # Ignore any value that is empty or that does not contain a string.
      if not value.data or not value.DataIsString():
        continue

      text_dict = {}
      text_dict[value.name] = value.data

      yield event.WinRegistryEvent(
          self._key.path, text_dict, timestamp=self._key.last_written_timestamp,
          source_append=': {0:s}'.format(self.DESCRIPTION))


class RunNtuserPlugin(RunBase):
  """Gathers the Run Keys for User hive."""

  REG_KEY = '\\Software\\Microsoft\\Windows\\CurrentVersion\\Run'
  REG_TYPE = 'NTUSER'


class RunOnceNtuserPlugin(RunBase):
  """Gathers the RunOnce key for the User hive."""

  REG_KEY = '\\Software\\Microsoft\\Windows\\CurrentVersion\\RunOnce'
  REG_TYPE = 'NTUSER'
  DESCRIPTION = 'RunOnce Key'


class RunSoftwarePlugin(RunBase):
  """Gathers the Run Key for Software hive."""

  REG_KEY = '\\Microsoft\\Windows\\CurrentVersion\\Run'
  REG_TYPE = 'SOFTWARE'


class RunOnceSoftwarePlugin(RunBase):
  """Gathers the RunOnce key for the Software hive."""

  REG_KEY = '\\Microsoft\\Windows\\CurrentVersion\\RunOnce'
  REG_TYPE = 'SOFTWARE'
  DESCRIPTION = 'RunOnce Key'


class SetupRunOnceSoftwarePlugin(RunBase):
  """Gathers the RunOnce\\Setup key for the Software hive."""

  REG_KEY = '\\Microsoft\\Windows\\CurrentVersion\\RunOnce\\Setup'
  REG_TYPE = 'SOFTWARE'
  DESCRIPTION = 'RunOnce Setup Key'


class RunServicesSoftwarePlugin(RunBase):
  """Gathers the RunServices Key for Software hive."""

  REG_KEY = '\\Microsoft\\Windows\\CurrentVersion\\RunServices'
  REG_TYPE = 'SOFTWARE'
  DESCRIPTION = 'RunServices Key'


class RunServicesOnceSoftwarePlugin(RunBase):
  """Gathers the RunServicesOnce Key for Software hive."""

  REG_KEY = '\\Microsoft\\Windows\\CurrentVersion\\RunServicesOnce'
  REG_TYPE = 'SOFTWARE'
  DESCRIPTION = 'RunServicesOnce Key'
