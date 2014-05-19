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
"""This file contains the MountPoints2 plugin."""

from plaso.lib import event
from plaso.parsers.winreg_plugins import interface


class MountPoints2Plugin(interface.KeyPlugin):
  """Windows Registry plugin for parsing the MountPoints2 key."""

  NAME = 'winreg_mountpoints2'

  REG_TYPE = 'NTUSER'

  REG_KEYS = [
      (u'\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\'
       u'MountPoints2')]

  URLS = [u'http://support.microsoft.com/kb/932463']

  def GetEntries(self, key, **unused_kwargs):
    """Retrieves information from the MountPoints2 registry key.

    Args:
      key: A Windows Registry key (instance of WinRegKey).

    Yields:
      An event object of with the extracted data.
    """
    for subkey in key.GetSubkeys():
      name = subkey.name
      if not name:
        continue

      text_dict = {}
      text_dict[u'Volume'] = name

      # Get the label if it exists.
      label_value = subkey.GetValue('_LabelFromReg')
      if label_value:
        text_dict[u'Label'] = label_value.data

      if name.startswith('{'):
        text_dict[u'Type'] = u'Volume'

      elif name.startswith('#'):
        # The format is: ##Server_Name#Share_Name.
        text_dict[u'Type'] = u'Remote Drive'
        server_name, _, share_name = name[2:].partition('#')
        text_dict[u'Remote_Server'] = server_name
        text_dict[u'Share_Name'] = u'\\{0:s}'.format(
            share_name.replace(u'#', u'\\'))

      else:
        text_dict[u'Type'] = u'Drive'

      yield event.WinRegistryEvent(
          key.path, text_dict, timestamp=subkey.last_written_timestamp,
          offset=subkey.offset)
