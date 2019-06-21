# -*- coding: utf-8 -*-
"""Windows Registry plugin to parse the Explorer ProgramsCache key."""

from __future__ import unicode_literals

import uuid

from plaso.containers import events
from plaso.containers import time_events
from plaso.containers import windows_events
from plaso.lib import definitions
from plaso.lib import errors
from plaso.parsers import winreg
from plaso.parsers.shared import shell_items
from plaso.parsers.winreg_plugins import dtfabric_plugin
from plaso.parsers.winreg_plugins import interface


class ExplorerProgramsCacheEventData(events.EventData):
  """Explorer ProgramsCache event data attribute container.

  Attributes:
    entries (str): entries in the program cache.
    key_path (str): Windows Registry key path.
    known_folder_identifier (str): known folder identifier.
    value_name (str): Windows Registry value name.
  """

  DATA_TYPE = 'windows:registry:explorer:programcache'

  def __init__(self):
    """Initializes event data."""
    super(ExplorerProgramsCacheEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.entries = None
    self.key_path = None
    self.known_folder_identifier = None
    self.value_name = None


class ExplorerProgramsCacheWindowsRegistryPlugin(
    dtfabric_plugin.DtFabricBaseWindowsRegistryPlugin):
  """Class that parses the Explorer ProgramsCache Registry data."""

  NAME = 'explorer_programscache'
  DESCRIPTION = 'Parser for Explorer ProgramsCache Registry data.'

  FILTERS = frozenset([
      interface.WindowsRegistryKeyPathFilter(
          'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\'
          'Explorer\\StartPage'),
      interface.WindowsRegistryKeyPathFilter(
          'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\'
          'Explorer\\StartPage2')])

  _DEFINITION_FILE = 'programscache.yaml'

  def _ParseValueData(self, parser_mediator, registry_key, registry_value):
    """Extracts event objects from a Explorer ProgramsCache value data.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
      registry_value (dfwinreg.WinRegistryValue): Windows Registry value.

    Raises:
      ParseError: if the value data could not be parsed.
    """
    value_data = registry_value.data

    value_data_size = len(value_data)
    if value_data_size < 4:
      return

    header_map = self._GetDataTypeMap('programscache_header')

    try:
      header = self._ReadStructureFromByteStream(
          value_data, 0, header_map)
    except (ValueError, errors.ParseError) as exception:
      parser_mediator.ProduceExtractionWarning(
          'unable to parse header value with error: {0!s}'.format(
              exception))
      return

    if header.format_version not in (1, 9, 12, 19):
      parser_mediator.ProduceExtractionWarning(
          'unsupported format version: {0:d}'.format(header.format_version))
      return

    known_folder_identifier = None
    if header.format_version == 1:
      value_data_offset = 8

    elif header.format_version == 9:
      value_data_offset = 6

    elif header.format_version in (12, 19):
      known_folder_identifier = uuid.UUID(bytes_le=value_data[4:20])
      value_data_offset = 20

    entry_header_map = self._GetDataTypeMap('programscache_entry_header')
    entry_footer_map = self._GetDataTypeMap('programscache_entry_footer')

    sentinel = 0
    if header.format_version != 9:
      try:
        entry_footer = self._ReadStructureFromByteStream(
            value_data[value_data_offset:], value_data_offset, entry_footer_map)
      except (ValueError, errors.ParseError) as exception:
        parser_mediator.ProduceExtractionWarning((
            'unable to parse sentinel at offset: 0x{0:08x} '
            'with error: {1!s}').format(value_data_offset, exception))
        return

      value_data_offset += entry_footer_map.GetByteSize()

      sentinel = entry_footer.sentinel

    link_targets = []
    while sentinel in (0x00, 0x01):
      if value_data_offset >= value_data_size:
        break

      try:
        entry_header = self._ReadStructureFromByteStream(
            value_data[value_data_offset:], value_data_offset, entry_header_map)
      except (ValueError, errors.ParseError) as exception:
        parser_mediator.ProduceExtractionWarning((
            'unable to parse entry header at offset: 0x{0:08x} '
            'with error: {1!s}').format(value_data_offset, exception))
        break

      value_data_offset += entry_header_map.GetByteSize()

      display_name = '{0:s} {1:s}'.format(
          registry_key.path, registry_value.name)

      shell_items_parser = shell_items.ShellItemsParser(display_name)
      shell_items_parser.ParseByteStream(
          parser_mediator, value_data[value_data_offset:],
          codepage=parser_mediator.codepage)

      link_target = shell_items_parser.CopyToPath()
      link_targets.append(link_target)

      value_data_offset += entry_header.data_size

      try:
        entry_footer = self._ReadStructureFromByteStream(
            value_data[value_data_offset:], value_data_offset, entry_footer_map)
      except (ValueError, errors.ParseError) as exception:
        parser_mediator.ProduceExtractionWarning((
            'unable to parse entry footer at offset: 0x{0:08x} '
            'with error: {1!s}').format(value_data_offset, exception))
        return

      value_data_offset += entry_footer_map.GetByteSize()

      sentinel = entry_footer.sentinel

    # TODO: recover remaining items.

    if known_folder_identifier:
      known_folder_identifier = '{0!s}'.format(known_folder_identifier)

    event_data = ExplorerProgramsCacheEventData()
    event_data.entries = ' '.join([
        '{0:d}: {1:s}'.format(index, link_target)
        for index, link_target in enumerate(link_targets)]) or None
    event_data.key_path = registry_key.path
    event_data.known_folder_identifier = known_folder_identifier
    event_data.value_name = registry_value.name

    event = time_events.DateTimeValuesEvent(
        registry_key.last_written_time, definitions.TIME_DESCRIPTION_WRITTEN)
    parser_mediator.ProduceEventWithEventData(event, event_data)

  def ExtractEvents(self, parser_mediator, registry_key, **kwargs):
    """Extracts events from a Windows Registry key.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
    """
    registry_value = registry_key.GetValueByName('ProgramsCache')
    if registry_value:
      self._ParseValueData(parser_mediator, registry_key, registry_value)

    registry_value = registry_key.GetValueByName('ProgramsCacheSMP')
    if registry_value:
      self._ParseValueData(parser_mediator, registry_key, registry_value)

    registry_value = registry_key.GetValueByName('ProgramsCacheTBP')
    if registry_value:
      self._ParseValueData(parser_mediator, registry_key, registry_value)

    values_dict = self._GetValuesFromKey(registry_key)
    for name in list(values_dict.keys()):
      if name.lower() in (
          'programscache', 'programscachesmp', 'programscachetbp'):
        del values_dict[name]

    event_data = windows_events.WindowsRegistryEventData()
    event_data.key_path = registry_key.path
    event_data.values = ' '.join([
        '{0:s}: {1!s}'.format(name, value)
        for name, value in sorted(values_dict.items())]) or None

    event = time_events.DateTimeValuesEvent(
        registry_key.last_written_time, definitions.TIME_DESCRIPTION_WRITTEN)
    parser_mediator.ProduceEventWithEventData(event, event_data)


winreg.WinRegistryParser.RegisterPlugin(
    ExplorerProgramsCacheWindowsRegistryPlugin)
