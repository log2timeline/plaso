# -*- coding: utf-8 -*-
"""Windows Registry plugin to parse the Explorer ProgramsCache key."""

import construct

from plaso.events import windows_events
from plaso.parsers import winreg
from plaso.parsers.shared import shell_items
from plaso.parsers.winreg_plugins import interface


class ExplorerProgramsCachePlugin(interface.WindowsRegistryPlugin):
  """Class that parses the Explorer ProgramsCache Registry data."""

  NAME = u'explorer_programscache'
  DESCRIPTION = u'Parser for Explorer ProgramsCache Registry data.'

  REG_TYPE = u'NTUSER'

  REG_KEYS = [
      (u'\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\'
       u'StartPage'),
      (u'\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\'
       u'StartPage2')]

  URLS = [
      (u'https://github.com/libyal/assorted/blob/master/documentation/'
       u'Jump%20lists%20format.asciidoc#4-explorer-programscache-registry-'
       u'values')]

  _HEADER_STRUCT = construct.Struct(
      u'programscache_header',
      construct.ULInt32(u'format_version'))

  _ENTRY_HEADER_STRUCT = construct.Struct(
      u'programscache_entry_header',
      construct.ULInt32(u'data_size'))

  _ENTRY_FOOTER_STRUCT = construct.Struct(
      u'programscache_entry_footer',
      construct.Byte(u'sentinel'))

  def _ParseValueData(self, parser_mediator, registry_key, registry_value):
    """Extracts event objects from a Explorer ProgramsCache value data.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      registry_key: A Windows Registry key (instance of
                    dfwinreg.WinRegistryKey).
      registry_value: A Windows Registry value (instance of
                     dfwinreg.WinRegistryValue).
    """
    value_data = registry_value.data
    if len(value_data) < 4:
      return

    try:
      header_struct = self._HEADER_STRUCT.parse(value_data)
    except construct.FieldError as exception:
      parser_mediator.ProduceParseError(
          u'unable to parse header with error: {0:s}'.format(
              exception))
      return

    format_version = header_struct.get(u'format_version')
    if format_version not in [0x01, 0x09, 0x0c, 0x13]:
      parser_mediator.ProduceParseError(
          u'unsupported format version: 0x{0:08x}'.format(format_version))
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
        parser_mediator.ProduceParseError((
            u'unable to parse sentinel at offset: 0x{0:08x} '
            u'with error: {1:s}').format(value_data_offset, exception))
        return

      value_data_offset += self._ENTRY_FOOTER_STRUCT.sizeof()

      sentinel = entry_footer_struct.get(u'sentinel')

    link_targets = []
    while sentinel in [0x00, 0x01]:
      try:
        entry_header_struct = self._ENTRY_HEADER_STRUCT.parse(
            value_data[value_data_offset:])
      except construct.FieldError as exception:
        parser_mediator.ProduceParseError((
            u'unable to parse entry header at offset: 0x{0:08x} '
            u'with error: {1:s}').format(value_data_offset, exception))
        break

      value_data_offset += self._ENTRY_HEADER_STRUCT.sizeof()

      entry_data_size = entry_header_struct.get(u'data_size')

      display_name = u'{0:s} {1:s}'.format(
          registry_key.path, registry_value.name)

      shell_items_parser = shell_items.ShellItemsParser(display_name)
      shell_items_parser.UpdateChainAndParse(
          parser_mediator, value_data[value_data_offset:], None,
          codepage=parser_mediator.codepage)

      link_target = shell_items_parser.CopyToPath()
      link_targets.append(link_target)

      value_data_offset += entry_data_size

      try:
        entry_footer_struct = self._ENTRY_FOOTER_STRUCT.parse(
            value_data[value_data_offset:])
      except construct.FieldError as exception:
        parser_mediator.ProduceParseError((
            u'unable to parse entry footer at offset: 0x{0:08x} '
            u'with error: {1:s}').format(value_data_offset, exception))
        break

      value_data_offset += self._ENTRY_FOOTER_STRUCT.sizeof()

      sentinel = entry_footer_struct.get(u'sentinel')

    # TODO: recover remaining items.

    list_name = registry_value.name
    list_values = u' '.join([
        u'{0:d}: {1:s}'.format(index, link_target)
        for index, link_target in enumerate(link_targets)])

    event_object = windows_events.WindowsRegistryListEvent(
        registry_key.last_written_time, registry_key.path,
        list_name, list_values, value_name=registry_value.name)

    parser_mediator.ProduceEvent(event_object)

  def GetEntries(self, parser_mediator, registry_key, **kwargs):
    """Extracts event objects from a Explorer ProgramsCache Registry key.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      registry_key: A Windows Registry key (instance of
                    dfwinreg.WinRegistryKey).
    """
    registry_value = registry_key.GetValueByName(u'ProgramsCache')
    if registry_value:
      self._ParseValueData(parser_mediator, registry_key, registry_value)

    registry_value = registry_key.GetValueByName(u'ProgramsCacheSMP')
    if registry_value:
      self._ParseValueData(parser_mediator, registry_key, registry_value)

    registry_value = registry_key.GetValueByName(u'ProgramsCacheTBP')
    if registry_value:
      self._ParseValueData(parser_mediator, registry_key, registry_value)

    values_dict = {}
    for registry_value in registry_key.GetValues():
      # Ignore the default value.
      if not registry_value.name or registry_value.name in [
          u'ProgramsCache', u'ProgramsCacheSMP', u'ProgramsCacheTBP']:
        continue

      # Ignore any value that is empty or that does not contain a string.
      if not registry_value.data or not registry_value.DataIsString():
        continue

      values_dict[registry_value.name] = registry_value.data

    event_object = windows_events.WindowsRegistryEvent(
        registry_key.last_written_time, registry_key.path, values_dict,
        offset=registry_key.offset)

    parser_mediator.ProduceEvent(event_object)


winreg.WinRegistryParser.RegisterPlugin(ExplorerProgramsCachePlugin)
