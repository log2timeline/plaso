#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2012 The Plaso Project Authors.
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
"""This file contains the UserAssist plugins."""

import construct
import logging

from plaso.lib import event
from plaso.lib import timelib
from plaso.parsers.winreg_plugins import interface
from plaso.winnt import environ_expand
from plaso.winnt import knownfolderid


class UserAssistPlugin(interface.KeyPlugin):
  """Plugin that parses an UserAssist key."""

  NAME = 'winreg_userassist'

  DESCRIPTION = 'UserAssistPlugin'

  REG_TYPE = 'NTUSER'
  REG_KEYS = [
      (u'\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer'
       u'\\UserAssist\\{{FA99DFC7-6AC2-453A-A5E2-5E2AFF4507BD}}'),
      (u'\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer'
       u'\\UserAssist\\{{F4E57C4B-2036-45F0-A9AB-443BCFE33D9F}}'),
      (u'\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer'
       u'\\UserAssist\\{{F2A1CB5A-E3CC-4A2E-AF9D-505A7009D442}}'),
      (u'\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer'
       u'\\UserAssist\\{{CEBFF5CD-ACE2-4F4F-9178-9926F41749EA}}'),
      (u'\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer'
       u'\\UserAssist\\{{CAA59E3C-4792-41A5-9909-6A6A8D32490E}}'),
      (u'\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer'
       u'\\UserAssist\\{{B267E3AD-A825-4A09-82B9-EEC22AA3B847}}'),
      (u'\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer'
       u'\\UserAssist\\{{A3D53349-6E61-4557-8FC7-0028EDCEEBF6}}'),
      (u'\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer'
       u'\\UserAssist\\{{9E04CAB2-CC14-11DF-BB8C-A2F1DED72085}}'),
      (u'\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer'
       u'\\UserAssist\\{{75048700-EF1F-11D0-9888-006097DEACF9}}'),
      (u'\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer'
       u'\\UserAssist\\{{5E6AB780-7743-11CF-A12B-00AA004AE837}}'),
      (u'\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer'
       u'\\UserAssist\\{{0D6D4F41-2994-4BA0-8FEF-620E43CD2812}}')]

  URL = [
      u'http://blog.didierstevens.com/programs/userassist/',
      u'https://code.google.com/p/winreg-kb/wiki/UserAssistKeys',
      u'http://intotheboxes.files.wordpress.com/2010/04'
      u'/intotheboxes_2010_q1.pdf']

  # UserAssist format version used in Windows 2000, XP, 2003, Vista.
  USERASSIST_V3_STRUCT = construct.Struct(
      'userassist_entry',
      construct.Padding(4),
      construct.ULInt32('count'),
      construct.ULInt64('timestamp'))

  # UserAssist format version used in Windows 2008, 7, 8.
  USERASSIST_V5_STRUCT = construct.Struct(
      'userassist_entry',
      construct.Padding(4),
      construct.ULInt32('count'),
      construct.ULInt32('app_focus_count'),
      construct.ULInt32('focus_duration'),
      construct.Padding(44),
      construct.ULInt64('timestamp'),
      construct.Padding(4))

  def GetEntries(self, key, **unused_kwargs):
    """Parses a UserAssist Registry key.

    Args:
      key: A Windows Registry key (instance of WinRegKey).

    Yields:
      An event object for every entry in the UserAssist key.
    """
    version_value = key.GetValue('Version')
    count_subkey = key.GetSubkey('Count')
    regalert_string = ''

    if not version_value:
      regalert_string = 'missing version value'
    elif not version_value.DataIsInteger():
      regalert_string = 'unsupported version value data type'
    elif version_value.data not in [3, 5]:
      regalert_string = 'unsupported version: {0:d}'.format(
          version_value.data)
    elif not count_subkey:
      regalert_string = 'missing count subkey'

    if regalert_string:
      text_dict = {}
      text_dict['Version'] = 'REGALERT {0:s}.'.format(regalert_string)
      regalert_string = ''
      yield event.WinRegistryEvent(
          key.path, text_dict, timestamp=key.last_written_timestamp)

    else:
      for value in count_subkey.GetValues():
        try:
          value_name = value.name.decode('rot-13')
        except UnicodeEncodeError as exception:
          logging.debug((
              u'Unable to decode UserAssist string: {0:s} with error: {1:s}.\n'
              u'Attempting piecewise decoding.').format(
                  value.name, exception))

          characters = []
          for char in value.name:
            if ord(char) < 128:
              try:
                characters.append(char.decode('rot-13'))
              except UnicodeEncodeError:
                characters.append(char)
            else:
              characters.append(char)

          value_name = u''.join(characters)

        if version_value.data == 5:
          path_segments = value_name.split('\\')

          for segment_index in range(0, len(path_segments)):
            path_segments[segment_index] = knownfolderid.IDENTIFIERS.get(
                path_segments[segment_index], path_segments[segment_index])

          value_name = u'\\'.join(path_segments)
          # Check if we might need to substitute values.
          if '%' in value_name:
            value_name = environ_expand.ExpandWindowsEnvironmentVariables(
                value_name, self._config)

        if not value.DataIsBinaryData():
          regalert_string = 'unsupported value data type: {0:s}'.format(
              value.data_type_string)

        elif version_value.data == 3:
          if len(value.data) != self.USERASSIST_V3_STRUCT.sizeof():
            regalert_string = 'unsupported value data size: {0:d}'.format(
                len(value.data))
          else:
            parsed_data = self.USERASSIST_V3_STRUCT.parse(value.data)
            filetime = parsed_data.get('timestamp', 0)
            count = parsed_data.get('count', 0)

            if count > 5:
              count -= 5

            text_dict = {}
            text_dict[value_name] = u'[Count: {0}]'.format(count)
            yield event.WinRegistryEvent(
                count_subkey.path, text_dict,
                timestamp=timelib.Timestamp.FromFiletime(filetime),
                offset=value.offset)

        elif version_value.data == 5:
          if len(value.data) != self.USERASSIST_V5_STRUCT.sizeof():
            regalert_string = 'unsupported value data size: {0:d}'.format(
                len(value.data))

          parsed_data = self.USERASSIST_V5_STRUCT.parse(value.data)

          userassist_entry = parsed_data.get('userassist_entry', None)
          count = parsed_data.get('count', None)
          app_focus_count = parsed_data.get('app_focus_count', None)
          focus_duration = parsed_data.get('focus_duration', None)
          timestamp = parsed_data.get('timestamp', 0)

          text_dict = {}
          text_dict[value_name] = (
              u'[userassist_entry: {0}, Count: {1}, app_focus_count: {2}, '
              u'focus_duration: {3}]').format(
              userassist_entry, count, app_focus_count, focus_duration)

          yield event.WinRegistryEvent(
              count_subkey.path, text_dict,
              timestamp=timelib.Timestamp.FromFiletime(timestamp))

    if regalert_string:
      text_dict = {}
      text_dict[value_name] = 'REGALERT {0:s}.'.format(regalert_string)
      regalert_string = ''
      yield event.WinRegistryEvent(
          key.path, text_dict, timestamp=key.last_written_timestamp)
