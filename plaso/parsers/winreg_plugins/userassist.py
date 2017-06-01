# -*- coding: utf-8 -*-
"""The UserAssist Windows Registry plugin."""

import logging

import construct

from dfdatetime import filetime as dfdatetime_filetime
from dfdatetime import semantic_time as dfdatetime_semantic_time

from plaso.containers import events
from plaso.containers import time_events
from plaso.engine import path_helper
from plaso.lib import definitions
from plaso.parsers import winreg
from plaso.parsers.winreg_plugins import interface
from plaso.winnt import known_folder_ids


class UserAssistWindowsRegistryEventData(events.EventData):
  """UserAssist Windows Registry event data.

  Attributes:
    application_focus_count (int): application focus count.
    application_focus_duration (int): application focus duration.
    entry_index (int): entry index.
    key_path (str): Windows Registry key path.
    number_of_executions (int): nubmer of executions.
    regvalue (dict[str, str]): UserAssist values.
    value_name (str): name of the Windows Registry value.
  """

  DATA_TYPE = u'windows:registry:userassist'

  def __init__(self):
    """Initializes event data."""
    super(UserAssistWindowsRegistryEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.application_focus_count = None
    self.application_focus_duration = None
    self.entry_index = None
    self.key_path = None
    self.number_of_executions = None
    self.value_name = None


class UserAssistWindowsRegistryKeyPathFilter(
    interface.WindowsRegistryKeyPathFilter):
  """UserAssist Windows Registry key path filter."""

  _KEY_PATH_FORMAT = (
      u'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\'
      u'Explorer\\UserAssist\\{{{0:s}}}')

  def __init__(self, user_assist_guid):
    """Initializes Windows Registry key filter.

    Args:
      user_assist_guid (str): UserAssist GUID.
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
      construct.ULInt32(u'number_of_executions'),
      construct.ULInt64(u'timestamp'))

  # UserAssist format version used in Windows 2008, 7, 8.
  _USERASSIST_V5_STRUCT = construct.Struct(
      u'userassist_entry',
      construct.Padding(4),
      construct.ULInt32(u'number_of_executions'),
      construct.ULInt32(u'application_focus_count'),
      construct.ULInt32(u'application_focus_duration'),
      construct.Padding(44),
      construct.ULInt64(u'timestamp'),
      construct.Padding(4))

  def ExtractEvents(self, parser_mediator, registry_key, **kwargs):
    """Extracts events from a Windows Registry key.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
    """
    version_value = registry_key.GetValueByName(u'Version')
    count_subkey = registry_key.GetSubkeyByName(u'Count')

    if not version_value:
      parser_mediator.ProduceExtractionError(u'missing version value')
      return

    if not version_value.DataIsInteger():
      parser_mediator.ProduceExtractionError(
          u'unsupported version value data type')
      return

    format_version = version_value.GetDataAsObject()
    if format_version not in (3, 5):
      parser_mediator.ProduceExtractionError(
          u'unsupported format version: {0:d}'.format(format_version))
      return

    if not count_subkey:
      parser_mediator.ProduceExtractionError(u'missing count subkey')
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
          # TODO: fix missing self._knowledge_base
          environment_variables = self._knowledge_base.GetEnvironmentVariables()
          value_name = path_helper.PathHelper.ExpandWindowsPath(
              value_name, environment_variables)

      value_data_size = len(registry_value.data)
      if not registry_value.DataIsBinaryData():
        parser_mediator.ProduceExtractionError(
            u'unsupported value data type: {0:s}'.format(
                registry_value.data_type_string))

      elif value_name == u'UEME_CTLSESSION':
        pass

      elif format_version == 3:
        if value_data_size != self._USERASSIST_V3_STRUCT.sizeof():
          parser_mediator.ProduceExtractionError(
              u'unsupported value data size: {0:d}'.format(value_data_size))

        else:
          parsed_data = self._USERASSIST_V3_STRUCT.parse(registry_value.data)
          timestamp = parsed_data.get(u'timestamp', None)

          number_of_executions = parsed_data.get(u'number_of_executions', None)
          if number_of_executions is not None and number_of_executions > 5:
            number_of_executions -= 5

          event_data = UserAssistWindowsRegistryEventData()
          event_data.key_path = count_subkey.path
          event_data.number_of_executions = number_of_executions
          event_data.offset = registry_value.offset
          event_data.value_name = value_name

          if not timestamp:
            date_time = dfdatetime_semantic_time.SemanticTime(u'Not set')
          else:
            date_time = dfdatetime_filetime.Filetime(timestamp=timestamp)

          # TODO: check if last written is correct.
          event = time_events.DateTimeValuesEvent(
              date_time, definitions.TIME_DESCRIPTION_WRITTEN)
          parser_mediator.ProduceEventWithEventData(event, event_data)

      elif format_version == 5:
        if value_data_size != self._USERASSIST_V5_STRUCT.sizeof():
          parser_mediator.ProduceExtractionError(
              u'unsupported value data size: {0:d}'.format(value_data_size))

        parsed_data = self._USERASSIST_V5_STRUCT.parse(registry_value.data)

        userassist_entry_index += 1
        timestamp = parsed_data.get(u'timestamp', None)

        event_data = UserAssistWindowsRegistryEventData()
        event_data.application_focus_count = parsed_data.get(
            u'application_focus_count', None)
        event_data.application_focus_duration = parsed_data.get(
            u'application_focus_duration', None)
        event_data.entry_index = userassist_entry_index
        event_data.key_path = count_subkey.path
        event_data.number_of_executions = parsed_data.get(
            u'number_of_executions', None)
        event_data.offset = count_subkey.offset
        event_data.value_name = value_name

        if not timestamp:
          date_time = dfdatetime_semantic_time.SemanticTime(u'Not set')
        else:
          date_time = dfdatetime_filetime.Filetime(timestamp=timestamp)

        # TODO: check if last written is correct.
        event = time_events.DateTimeValuesEvent(
            date_time, definitions.TIME_DESCRIPTION_WRITTEN)
        parser_mediator.ProduceEventWithEventData(event, event_data)


winreg.WinRegistryParser.RegisterPlugin(UserAssistPlugin)
