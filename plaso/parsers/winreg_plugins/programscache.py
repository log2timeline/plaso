# -*- coding: utf-8 -*-
"""Windows Registry plugin to parse the Explorer ProgramsCache key."""

from plaso.events import windows_events
from plaso.parsers import winreg
from plaso.parsers.winreg_plugins import interface


class ExplorerProgramCache(interface.WindowsRegistryPlugin):
  """Class that parses the Explorer ProgramsCache Registry data."""

  NAME = u'explorer_programcache'
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
       u'values'])

  def GetEntries(
      self, parser_mediator, registry_key, registry_file_type=None, **kwargs):
    """Extracts event objects from a Explorer ProgramsCache Registry key.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      registry_key: A Windows Registry key (instance of
                    dfwinreg.WinRegistryKey).
      registry_file_type: Optional string containing the Windows Registry file
                          type, e.g. NTUSER, SOFTWARE. The default is None.
    """
    # TODO: generate a Registry event for the key.

    program_cache_value = key.GetValue(u'ProgramsCache')
    if program_cache_value:
      # TODO: parse value data.
      pass

    program_cache_value = key.GetValue(u'ProgramsCacheSMP')
    if program_cache_value:
      # TODO: parse value data.
      pass

    program_cache_value = key.GetValue(u'ProgramsCacheTBP')
    if program_cache_value:
      # TODO: parse value data.
      pass


winreg.WinRegistryParser.RegisterPlugin(ExplorerProgramCache)
