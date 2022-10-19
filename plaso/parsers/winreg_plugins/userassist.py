# -*- coding: utf-8 -*-
"""The UserAssist Windows Registry plugin."""

import codecs
import os

from dfdatetime import filetime as dfdatetime_filetime

from plaso.containers import events
from plaso.helpers.windows import known_folders
from plaso.lib import dtfabric_helper
from plaso.lib import errors
from plaso.parsers import logger
from plaso.parsers import winreg_parser
from plaso.parsers.winreg_plugins import interface


class UserAssistWindowsRegistryEventData(events.EventData):
  """UserAssist Windows Registry event data.

  Attributes:
    application_focus_count (int): application focus count.
    application_focus_duration (int): application focus duration.
    entry_index (int): entry index.
    key_path (str): Windows Registry key path.
    last_execution_time (dfdatetime.DateTimeValues): date and time
        the application was last executed (or run).
    number_of_executions (int): number of executions.
    value_name (str): name of the Windows Registry value.
  """

  DATA_TYPE = 'windows:registry:userassist'

  def __init__(self):
    """Initializes event data."""
    super(UserAssistWindowsRegistryEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.application_focus_count = None
    self.application_focus_duration = None
    self.entry_index = None
    self.key_path = None
    self.last_execution_time = None
    self.number_of_executions = None
    self.value_name = None


class UserAssistWindowsRegistryKeyPathFilter(
    interface.WindowsRegistryKeyPathFilter):
  """UserAssist Windows Registry key path filter."""

  _KEY_PATH_FORMAT = (
      'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\'
      'Explorer\\UserAssist\\{{{0:s}}}')

  def __init__(self, user_assist_guid):
    """Initializes Windows Registry key filter.

    Args:
      user_assist_guid (str): UserAssist GUID.
    """
    key_path = self._KEY_PATH_FORMAT.format(user_assist_guid)
    super(UserAssistWindowsRegistryKeyPathFilter, self).__init__(key_path)


class UserAssistPlugin(
    interface.WindowsRegistryPlugin, dtfabric_helper.DtFabricHelper):
  """Plugin that parses an UserAssist key."""

  NAME = 'userassist'
  DATA_FORMAT = 'User Assist Registry data'

  FILTERS = frozenset([
      UserAssistWindowsRegistryKeyPathFilter(
          'FA99DFC7-6AC2-453A-A5E2-5E2AFF4507BD'),
      UserAssistWindowsRegistryKeyPathFilter(
          'F4E57C4B-2036-45F0-A9AB-443BCFE33D9F'),
      UserAssistWindowsRegistryKeyPathFilter(
          'F2A1CB5A-E3CC-4A2E-AF9D-505A7009D442'),
      UserAssistWindowsRegistryKeyPathFilter(
          'CEBFF5CD-ACE2-4F4F-9178-9926F41749EA'),
      UserAssistWindowsRegistryKeyPathFilter(
          'CAA59E3C-4792-41A5-9909-6A6A8D32490E'),
      UserAssistWindowsRegistryKeyPathFilter(
          'B267E3AD-A825-4A09-82B9-EEC22AA3B847'),
      UserAssistWindowsRegistryKeyPathFilter(
          'A3D53349-6E61-4557-8FC7-0028EDCEEBF6'),
      UserAssistWindowsRegistryKeyPathFilter(
          '9E04CAB2-CC14-11DF-BB8C-A2F1DED72085'),
      UserAssistWindowsRegistryKeyPathFilter(
          '75048700-EF1F-11D0-9888-006097DEACF9'),
      UserAssistWindowsRegistryKeyPathFilter(
          '5E6AB780-7743-11CF-A12B-00AA004AE837'),
      UserAssistWindowsRegistryKeyPathFilter(
          '0D6D4F41-2994-4BA0-8FEF-620E43CD2812'),
      UserAssistWindowsRegistryKeyPathFilter(
          'BCB48336-4DDD-48FF-BB0B-D3190DACB3E2')])

  _DEFINITION_FILE = os.path.join(
      os.path.dirname(__file__), 'userassist.yaml')

  def ExtractEvents(self, parser_mediator, registry_key, **kwargs):
    """Extracts events from a Windows Registry key.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
    """
    version_value = registry_key.GetValueByName('Version')
    count_subkey = registry_key.GetSubkeyByName('Count')

    if not version_value:
      parser_mediator.ProduceExtractionWarning('missing version value')
      return

    if not version_value.DataIsInteger():
      parser_mediator.ProduceExtractionWarning(
          'unsupported version value data type')
      return

    format_version = version_value.GetDataAsObject()
    if format_version not in (3, 5):
      parser_mediator.ProduceExtractionWarning(
          'unsupported format version: {0:d}'.format(format_version))
      return

    if not count_subkey:
      parser_mediator.ProduceExtractionWarning('missing count subkey')
      return

    userassist_entry_index = 0

    for registry_value in count_subkey.GetValues():
      try:
        # Note that Python 2 codecs.decode() does not support keyword arguments
        # such as encodings='rot-13'.
        value_name = codecs.decode(registry_value.name, 'rot-13')
      except UnicodeEncodeError as exception:
        logger.debug((
            'Unable to decode UserAssist string: {0:s} with error: {1!s}.\n'
            'Attempting piecewise decoding.').format(
                registry_value.name, exception))

        characters = []
        for char in registry_value.name:
          if ord(char) < 128:
            try:
              characters.append(char.decode('rot-13'))
            except UnicodeEncodeError:
              characters.append(char)
          else:
            characters.append(char)

        value_name = ''.join(characters)

      if format_version == 5:
        path_segments = value_name.split('\\')

        for segment_index, path_segment in enumerate(path_segments):
          path = known_folders.WindowsKnownFoldersHelper.GetPath(
              path_segment)
          if path:
            path_segments[segment_index] = path

        value_name = '\\'.join(path_segments)
        # Check if we might need to substitute values.
        if '%' in value_name:
          value_name = parser_mediator.ExpandWindowsPath(value_name)

      if value_name == 'UEME_CTLSESSION':
        continue

      if format_version == 3:
        entry_map = self._GetDataTypeMap('user_assist_entry_v3')
        entry_data_size = 16
      elif format_version == 5:
        entry_map = self._GetDataTypeMap('user_assist_entry_v5')
        entry_data_size = 72
      else:
        parser_mediator.ProduceExtractionWarning(
            'unsupported format version: {0:d}'.format(format_version))
        continue

      if not registry_value.DataIsBinaryData():
        parser_mediator.ProduceExtractionWarning(
            'unsupported value data type: {0:s}'.format(
                registry_value.data_type_string))
        continue

      value_data_size = len(registry_value.data)
      if entry_data_size != value_data_size:
        parser_mediator.ProduceExtractionWarning(
            'unsupported value data size: {0:d}'.format(value_data_size))
        continue

      try:
        user_assist_entry = self._ReadStructureFromByteStream(
            registry_value.data, 0, entry_map)
      except (ValueError, errors.ParseError) as exception:
        parser_mediator.ProduceExtractionWarning(
            'unable to parse UserAssist entry value with error: {0!s}'.format(
                exception))
        continue

      event_data = UserAssistWindowsRegistryEventData()
      event_data.key_path = count_subkey.path
      event_data.number_of_executions = user_assist_entry.number_of_executions
      event_data.value_name = value_name

      if format_version == 3:
        if event_data.number_of_executions > 5:
          event_data.number_of_executions -= 5

      elif format_version == 5:
        userassist_entry_index += 1

        event_data.application_focus_count = (
            user_assist_entry.application_focus_count)
        event_data.application_focus_duration = (
            user_assist_entry.application_focus_duration)
        event_data.entry_index = userassist_entry_index

      timestamp = user_assist_entry.last_execution_time
      if timestamp:
        event_data.last_execution_time = dfdatetime_filetime.Filetime(
            timestamp=timestamp)

      parser_mediator.ProduceEventData(event_data)


winreg_parser.WinRegistryParser.RegisterPlugin(UserAssistPlugin)
