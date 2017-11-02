# -*- coding: utf-8 -*-
"""Windows Registry plugin to parse the Explorer ProgramsCache key."""

from __future__ import unicode_literals

import construct

from plaso.containers import time_events
from plaso.containers import windows_events
from plaso.lib import definitions
from plaso.parsers import winreg
from plaso.parsers.shared import shell_items
from plaso.parsers.winreg_plugins import interface


class ExplorerProgramsCachePlugin(interface.WindowsRegistryPlugin):
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

  URLS = [
      ('https://github.com/libyal/winreg-kb/blob/master/documentation/'
       'Programs%20Cache%20values.asciidoc')]

  _HEADER_STRUCT = construct.Struct(
      'programscache_header',
      construct.ULInt32('format_version'))

  _ENTRY_HEADER_STRUCT = construct.Struct(
      'programscache_entry_header',
      construct.ULInt32('data_size'))

  _ENTRY_FOOTER_STRUCT = construct.Struct(
      'programscache_entry_footer',
      construct.Byte('sentinel'))

  def _ParseValueData(self, parser_mediator, registry_key, registry_value):
    """Extracts event objects from a Explorer ProgramsCache value data.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
      registry_value (dfwinreg.WinRegistryValue): Windows Registry value.
    """
    value_data = registry_value.data
    if len(value_data) < 4:
      return

    try:
      header_struct = self._HEADER_STRUCT.parse(value_data)
    except construct.FieldError as exception:
      parser_mediator.ProduceExtractionError(
          'unable to parse header with error: {0:s}'.format(
              exception))
      return

    format_version = header_struct.get('format_version')
    if format_version not in (0x01, 0x09, 0x0c, 0x13):
      parser_mediator.ProduceExtractionError(
          'unsupported format version: 0x{0:08x}'.format(format_version))
      return

    if format_version == 0x01:
      value_data_offset = 8

    elif format_version == 0x09:
      value_data_offset = 6

    else:
      # TODO: get known folder identifier?
      value_data_offset = 20

    if format_version == 0x09:
      sentinel = 0
    else:
      try:
        entry_footer_struct = self._ENTRY_FOOTER_STRUCT.parse(
            value_data[value_data_offset:])
      except construct.FieldError as exception:
        parser_mediator.ProduceExtractionError((
            'unable to parse sentinel at offset: 0x{0:08x} '
            'with error: {1:s}').format(value_data_offset, exception))
        return

      value_data_offset += self._ENTRY_FOOTER_STRUCT.sizeof()

      sentinel = entry_footer_struct.get('sentinel')

    link_targets = []
    while sentinel in (0x00, 0x01):
      try:
        entry_header_struct = self._ENTRY_HEADER_STRUCT.parse(
            value_data[value_data_offset:])
      except construct.FieldError as exception:
        parser_mediator.ProduceExtractionError((
            'unable to parse entry header at offset: 0x{0:08x} '
            'with error: {1:s}').format(value_data_offset, exception))
        break

      value_data_offset += self._ENTRY_HEADER_STRUCT.sizeof()

      entry_data_size = entry_header_struct.get('data_size')

      display_name = '{0:s} {1:s}'.format(
          registry_key.path, registry_value.name)

      shell_items_parser = shell_items.ShellItemsParser(display_name)
      shell_items_parser.ParseByteStream(
          parser_mediator, value_data[value_data_offset:],
          codepage=parser_mediator.codepage)

      link_target = shell_items_parser.CopyToPath()
      link_targets.append(link_target)

      value_data_offset += entry_data_size

      try:
        entry_footer_struct = self._ENTRY_FOOTER_STRUCT.parse(
            value_data[value_data_offset:])
      except construct.FieldError as exception:
        parser_mediator.ProduceExtractionError((
            'unable to parse entry footer at offset: 0x{0:08x} '
            'with error: {1:s}').format(value_data_offset, exception))
        break

      value_data_offset += self._ENTRY_FOOTER_STRUCT.sizeof()

      sentinel = entry_footer_struct.get('sentinel')

    # TODO: recover remaining items.

    event_data = windows_events.WindowsRegistryListEventData()
    event_data.key_path = registry_key.path
    event_data.list_name = registry_value.name
    event_data.list_values = ' '.join([
        '{0:d}: {1:s}'.format(index, link_target)
        for index, link_target in enumerate(link_targets)])
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

    values_dict = {}
    for registry_value in registry_key.GetValues():
      # Ignore the default value.
      if not registry_value.name or registry_value.name in (
          'ProgramsCache', 'ProgramsCacheSMP', 'ProgramsCacheTBP'):
        continue

      # Ignore any value that is empty or that does not contain a string.
      if not registry_value.data or not registry_value.DataIsString():
        continue

      values_dict[registry_value.name] = registry_value.GetDataAsObject()

    event_data = windows_events.WindowsRegistryEventData()
    event_data.key_path = registry_key.path
    event_data.offset = registry_key.offset
    event_data.regvalue = values_dict

    event = time_events.DateTimeValuesEvent(
        registry_key.last_written_time, definitions.TIME_DESCRIPTION_WRITTEN)
    parser_mediator.ProduceEventWithEventData(event, event_data)


winreg.WinRegistryParser.RegisterPlugin(ExplorerProgramsCachePlugin)
