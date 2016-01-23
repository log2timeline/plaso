# -*- coding: utf-8 -*-
"""This file contains the UserAssist Windows Registry plugin."""

import logging

import construct

from plaso.events import windows_events
from plaso.parsers import winreg
from plaso.parsers.winreg_plugins import interface
from plaso.winnt import environ_expand
from plaso.winnt import known_folder_ids


class UserAssistWindowsRegistryKeyPathFilter(
    interface.WindowsRegistryKeyPathFilter):
  """UserAssist Windows Registry key path filter."""

  _KEY_PATH_FORMAT = (
      u'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\'
      u'Explorer\\UserAssist\\{{{0:s}}}')

  def __init__(self, user_assist_guid):
    """Initializes Windows Registry key filter object.

    Args:
      user_assist_guid: string containing the User Assist GUID.
    """
    key_path = self._KEY_PATH_FORMAT.format(user_assist_guid)
    super(UserAssistWindowsRegistryKeyPathFilter, self).__init__(key_path)


class UserAssistPlugin(interface.WindowsRegistryPlugin):
  """Plugin that parses an UserAssist key."""

  NAME = u'userassist'
  DESCRIPTION = u'Parser for User Assist Registry data.'

  FILTERS = frozenset([
      UserAssistWindowsRegistryKeyPathFilter(
          u'FA99DFC7-6AC2-453A-A5E2-5E2AFF4507BD'),
      UserAssistWindowsRegistryKeyPathFilter(
          u'F4E57C4B-2036-45F0-A9AB-443BCFE33D9F'),
      UserAssistWindowsRegistryKeyPathFilter(
          u'F2A1CB5A-E3CC-4A2E-AF9D-505A7009D442'),
      UserAssistWindowsRegistryKeyPathFilter(
          u'CEBFF5CD-ACE2-4F4F-9178-9926F41749EA'),
      UserAssistWindowsRegistryKeyPathFilter(
          u'CAA59E3C-4792-41A5-9909-6A6A8D32490E'),
      UserAssistWindowsRegistryKeyPathFilter(
          u'B267E3AD-A825-4A09-82B9-EEC22AA3B847'),
      UserAssistWindowsRegistryKeyPathFilter(
          u'A3D53349-6E61-4557-8FC7-0028EDCEEBF6'),
      UserAssistWindowsRegistryKeyPathFilter(
          u'9E04CAB2-CC14-11DF-BB8C-A2F1DED72085'),
      UserAssistWindowsRegistryKeyPathFilter(
          u'75048700-EF1F-11D0-9888-006097DEACF9'),
      UserAssistWindowsRegistryKeyPathFilter(
          u'5E6AB780-7743-11CF-A12B-00AA004AE837'),
      UserAssistWindowsRegistryKeyPathFilter(
          u'0D6D4F41-2994-4BA0-8FEF-620E43CD2812'),
      UserAssistWindowsRegistryKeyPathFilter(
          u'BCB48336-4DDD-48FF-BB0B-D3190DACB3E2')])

  URLS = [
      u'http://blog.didierstevens.com/programs/userassist/',
      u'https://code.google.com/p/winreg-kb/wiki/UserAssistKeys',
      u'http://intotheboxes.files.wordpress.com/2010/04'
      u'/intotheboxes_2010_q1.pdf']

  # UserAssist format version used in Windows 2000, XP, 2003, Vista.
  _USERASSIST_V3_STRUCT = construct.Struct(
      u'userassist_entry',
      construct.Padding(4),
      construct.ULInt32(u'count'),
      construct.ULInt64(u'timestamp'))

  # UserAssist format version used in Windows 2008, 7, 8.
  _USERASSIST_V5_STRUCT = construct.Struct(
      u'userassist_entry',
      construct.Padding(4),
      construct.ULInt32(u'count'),
      construct.ULInt32(u'app_focus_count'),
      construct.ULInt32(u'focus_duration'),
      construct.Padding(44),
      construct.ULInt64(u'timestamp'),
      construct.Padding(4))

  def GetEntries(self, parser_mediator, registry_key, **kwargs):
    """Parses a UserAssist Registry key.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      registry_key: A Windows Registry key (instance of
                    dfwinreg.WinRegistryKey).
    """
    version_value = registry_key.GetValueByName(u'Version')
    count_subkey = registry_key.GetSubkeyByName(u'Count')

    if not version_value:
      parser_mediator.ProduceParseError(u'Missing version value')
      return

    if not version_value.DataIsInteger():
      parser_mediator.ProduceParseError(u'Unsupported version value data type')
      return

    format_version = version_value.GetDataAsObject()
    if format_version not in (3, 5):
      parser_mediator.ProduceParseError(
          u'Unsupported format version: {0:d}'.format(format_version))
      return

    if not count_subkey:
      parser_mediator.ProduceParseError(u'Missing count subkey')
      return

    userassist_entry_index = 0

    for registry_value in count_subkey.GetValues():
      try:
        value_name = registry_value.name.decode(u'rot-13')
      except UnicodeEncodeError as exception:
        logging.debug((
            u'Unable to decode UserAssist string: {0:s} with error: {1:s}.\n'
            u'Attempting piecewise decoding.').format(
                registry_value.name, exception))

        characters = []
        for char in registry_value.name:
          if ord(char) < 128:
            try:
              characters.append(char.decode(u'rot-13'))
            except UnicodeEncodeError:
              characters.append(char)
          else:
            characters.append(char)

        value_name = u''.join(characters)

      if format_version == 5:
        path_segments = value_name.split(u'\\')

        for segment_index in range(0, len(path_segments)):
          # Remove the { } from the path segment to get the GUID.
          guid = path_segments[segment_index][1:-1]
          path_segments[segment_index] = known_folder_ids.PATHS.get(
              guid, path_segments[segment_index])

        value_name = u'\\'.join(path_segments)
        # Check if we might need to substitute values.
        if u'%' in value_name:
          # TODO: deprecate direct use of pre_obj.
          value_name = environ_expand.ExpandWindowsEnvironmentVariables(
              value_name, parser_mediator.knowledge_base.pre_obj)

      value_data_size = len(registry_value.data)
      if not registry_value.DataIsBinaryData():
        parser_mediator.ProduceParseError(
            u'Unsupported value data type: {0:s}'.format(
                registry_value.data_type_string))

      elif value_name == u'UEME_CTLSESSION':
        pass

      elif format_version == 3:
        if value_data_size != self._USERASSIST_V3_STRUCT.sizeof():
          parser_mediator.ProduceParseError(
              u'Unsupported value data size: {0:d}'.format(value_data_size))

        else:
          parsed_data = self._USERASSIST_V3_STRUCT.parse(registry_value.data)
          filetime = parsed_data.get(u'timestamp', 0)
          count = parsed_data.get(u'count', 0)

          if count > 5:
            count -= 5

          values_dict = {}
          values_dict[value_name] = u'[Count: {0:d}]'.format(count)
          event_object = windows_events.WindowsRegistryEvent(
              filetime, count_subkey.path, values_dict,
              offset=registry_value.offset)
          parser_mediator.ProduceEvent(event_object)

      elif format_version == 5:
        if value_data_size != self._USERASSIST_V5_STRUCT.sizeof():
          parser_mediator.ProduceParseError(
              u'Unsupported value data size: {0:d}'.format(value_data_size))

        parsed_data = self._USERASSIST_V5_STRUCT.parse(registry_value.data)

        userassist_entry_index += 1
        count = parsed_data.get(u'count', None)
        app_focus_count = parsed_data.get(u'app_focus_count', None)
        focus_duration = parsed_data.get(u'focus_duration', None)
        filetime = parsed_data.get(u'timestamp', 0)

        values_dict = {}
        values_dict[value_name] = (
            u'[UserAssist entry: {0:d}, Count: {1:d}, '
            u'Application focus count: {2:d}, Focus duration: {3:d}]').format(
                userassist_entry_index, count, app_focus_count,
                focus_duration)

        event_object = windows_events.WindowsRegistryEvent(
            filetime, count_subkey.path, values_dict,
            offset=count_subkey.offset)
        parser_mediator.ProduceEvent(event_object)


winreg.WinRegistryParser.RegisterPlugin(UserAssistPlugin)
