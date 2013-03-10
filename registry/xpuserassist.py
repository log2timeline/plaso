#!/usr/bin/python
# -*- coding: utf-8 -*-
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
"""This file contains a simple UserAssist plugin for Plaso."""
import logging
import struct

from plaso.lib import event
from plaso.lib import timelib
from plaso.lib import win_registry_interface


class XPUserAssistPlugin(win_registry_interface.KeyPlugin):
  """A registry plugin that parses XP UserAssist entries."""

  REG_KEY = ('\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer'
             '\\UserAssist\\{{75048700-EF1F-11D0-9888-006097DEACF9}}\\Count')
  REG_TYPE = 'NTUSER'
  URLS = [u'http://blog.didierstevens.com/programs/userassist/']

  def GetEntries(self):
    """Retrieves the values in the UserAssist Registry key."""
    for value in self._key.GetValues():
      data = value.GetRawData()
      name_raw = value.name
      try:
        name = name_raw.decode('rot-13')
      except UnicodeEncodeError as e:
        logging.error(
            u'Unable to properly decode UA string: {} - [{}]'.format(
                name_raw, e))
        characters = []
        for char in name_raw:
          if ord(char) < 128:
            try:
              characters.append(char.decode('rot-13'))
            except UnicodeEncodeError:
              characters.append(char)
          else:
            characters.append(char)

        name = u''.join(characters)

      if len(data) != 16:
        logging.debug('[UserAssist] Value entry is not of correct length.')
        continue
      _, count, filetime = struct.unpack('<LLQ', data)

      if not filetime:
        logging.debug(
            u'[UserAssist] Value entry without a timestamp value: %s (%d)',
            name, count)
        continue

      if count > 5:
        count -= 5

      text_dict = {}
      text_dict[u'{0}'.format(name)] = u'[Count: {0}]'.format(count)
      yield event.WinRegistryEvent(
          u'', text_dict, timelib.Timestamp.FromFiletime(filetime))
