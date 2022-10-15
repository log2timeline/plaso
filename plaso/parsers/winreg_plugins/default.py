# -*- coding: utf-8 -*-
"""The default Windows Registry plugin."""

from plaso.parsers import winreg_parser
from plaso.parsers.winreg_plugins import interface


class DefaultPlugin(interface.WindowsRegistryPlugin):
  """Default plugin that extracts minimum information from every Registry key.

  The default plugin will parse every Registry key that is passed to it and
  extract minimum information, such as a list of available values and if
  possible content of those values. The timestamp used is the timestamp
  when the Registry key was last modified.
  """

  NAME = 'winreg_default'
  DATA_FORMAT = 'Windows Registry data'

  def ExtractEvents(self, parser_mediator, registry_key, **kwargs):
    """Extracts events from a Windows Registry key.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
    """
    self._ProduceDefaultWindowsRegistryEvent(parser_mediator, registry_key)


winreg_parser.WinRegistryParser.RegisterPlugin(DefaultPlugin)
