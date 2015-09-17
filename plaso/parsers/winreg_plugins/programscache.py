# -*- coding: utf-8 -*-
"""Windows Registry plugin to parse the Explorer ProgramsCache key."""

import construct

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

  def _ParseValueData(self, parser_mediator, registry_value):
    """Extracts event objects from a Explorer ProgramsCache value data.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      registry_value: A Windows Registry value (instance of
                     dfwinreg.WinRegistryValue).
    """
    value_data = registry_value.data

    header_struct = self._HEADER_STRUCT.parse(value_data)
    # TODO: handle parse error

    format_version = header_struct.get(u'format_version')
    if format_version not in [0x01, 0x09, 0x0c, 0x13]:
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
      entry_footer_struct = self._ENTRY_FOOTER_STRUCT.parse(
          value_data[value_data_offset:])
      value_data_offset += self._ENTRY_FOOTER_STRUCT.sizeof()

      sentinel = entry_footer_struct.get(u'sentinel')

    link_targets = []
    while sentinel in [0x00, 0x01]:
      entry_header_struct = self._ENTRY_HEADER_STRUCT.parse(
          value_data[value_data_offset:])
      value_data_offset += self._ENTRY_HEADER_STRUCT.sizeof()

      entry_data_size = entry_header_struct.get(u'data_size')

      # TODO: should this be a mix of filename, key path and value name?
      display_name = u''
      shell_items_parser = shell_items.ShellItemsParser(display_name)
      shell_items_parser.UpdateChainAndParse(
          parser_mediator, value_data[value_data_offset:], None,
          codepage=parser_mediator.codepage)

      link_target = shell_items_parser.CopyToPath()
      link_targets.append(link_target)

      value_data_offset += entry_data_size

      entry_footer_struct = self._ENTRY_FOOTER_STRUCT.parse(
          value_data[value_data_offset:])
      value_data_offset += self._ENTRY_FOOTER_STRUCT.sizeof()

      sentinel = entry_footer_struct.get(u'sentinel')

  # TODO: generate event with all link targets?

  # TODO: handle recovered items?

  def GetEntries(self, parser_mediator, registry_key, **kwargs):
    """Extracts event objects from a Explorer ProgramsCache Registry key.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      registry_key: A Windows Registry key (instance of
                    dfwinreg.WinRegistryKey).
    """
    # TODO: generate a Registry event for the key.

    registry_value = registry_key.GetValueByName(u'ProgramsCache')
    if registry_value:
      self._ParseValueData(parser_mediator, registry_value)

    registry_value = registry_key.GetValueByName(u'ProgramsCacheSMP')
    if registry_value:
      self._ParseValueData(parser_mediator, registry_value)

    registry_value = registry_key.GetValueByName(u'ProgramsCacheTBP')
    if registry_value:
      self._ParseValueData(parser_mediator, registry_value)


winreg.WinRegistryParser.RegisterPlugin(ExplorerProgramsCachePlugin)
