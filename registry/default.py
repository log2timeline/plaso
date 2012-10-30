# Copyright 2012 Google Inc. All Rights Reserved.
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
"""This file contains a default registry plugin in Plaso."""
from plaso.lib import event
from plaso.lib import win_registry_interface


class DefaultPlugin(win_registry_interface.KeyPlugin):
  """Basic plugin to extract minimal information from registry keys."""

  REG_TYPE = 'any'
  REG_KEY = '\\'
  # This is a special case, plugins normally never overwrite the priority.
  # However the default plugin should only run when all others plugins have
  # tried and failed.
  WEIGHT = 3

  def Process(self, key):
    self._key = key
    return self.GetEntries()

  def GetEntries(self):
    """Return a single EventObject based on key name and values."""
    text_dict = {}

    for value in self._key.GetValues():
      if not value.name:
        continue

      data_type = value.GetTypeStr()

      if 'SZ' in data_type or 'DWORD' in data_type:
        text_dict[u'%s' % value.name] = u'%s' % value.GetData(unicode)
      else:
        text_dict[u'%s' % value.name] = u'[DATA TYPE %s]' % data_type

    if not text_dict:
      text_dict[u'Value'] = u'No values stored in key.'

    evt = event.RegistryEvent(self._key.path, text_dict, self._key.timestamp)
    evt.offset = self._key.offset
    yield evt

