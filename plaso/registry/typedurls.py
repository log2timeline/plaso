#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2013 The Plaso Project Authors.
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
"""This file contains the Typed IE URLS plugins for Plaso."""


from plaso.lib import event
from plaso.lib import win_registry_interface


__author__ = 'David Nides (david.nides@gmail.com)'


class IETypedURLS(win_registry_interface.KeyPlugin):
  """Base class for all Typed IE URLS plugins."""

  __abstract = True

  DESCRIPTION = 'Typed IE URLS'

  def GetEntries(self):
    """Collect Values under IE Typed URLS & return event for each one."""
    for value in self._key.GetValues():
      if not value.name:
        continue
      text_dict = {}
      text_dict[value.name] = value.GetStringData()
      if not text_dict[value.name]:
        continue

      if value.name == 'url1':
        reg_evt = event.WinRegistryEvent(
            self._key.path, text_dict, self._key.timestamp)
      else:
        reg_evt = event.WinRegistryEvent(
            self._key.path, text_dict, 0)

      reg_evt.source_append = ': {}'.format(self.DESCRIPTION)
      yield reg_evt


class IETypedURLSPlugin(IETypedURLS):
  """Gathers the Typed IE URLS key for the NTUSER hive."""

  REG_KEY = ('\\Software\\Microsoft\\Internet Explorer\\TypedURLs')
  REG_TYPE = 'NTUSER'
  DESCRIPTION = "Typed IE URLS"
