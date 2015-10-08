# -*- coding: utf-8 -*-
"""Parser for Windows NT Registry (REGF) files."""

from plaso.dfwinreg import registry as dfwinreg_registry
from plaso.lib import specification
from plaso.parsers import interface
from plaso.parsers import manager


# TODO: rename to REGFParser.
class WinRegistryParser(interface.SingleFileBaseParser):
  """Parses Windows NT Registry (REGF) files."""

  NAME = u'winreg'
  DESCRIPTION = u'Parser for Windows NT Registry (REGF) files.'

  _plugin_classes = {}

  def __init__(self):
    """Initializes a parser object."""
    super(WinRegistryParser, self).__init__()
    self._plugins = WinRegistryParser.GetPluginObjects()

    for list_index, plugin_object in enumerate(self._plugins):
      if plugin_object.NAME == u'winreg_default':
        self._default_plugin = self._plugins.pop(list_index)
        break

    # TODO: build a filter tree to optimize lookups.

  def _CanProcessKeyWithPlugin(self, registry_key, plugin_object):
    """Determines if a plugin can process a Windows Registry key or its values.

    Args:
      registry_key: a Windows Registry key (instance of
                    dfwinreg.WinRegistryKey).
      plugin_object: a Windows Registry plugin object (instance of
                     WindowsRegistryPlugin).

    Returns:
      A boolean value that indicates a match.
    """
    for filter_object in plugin_object.FILTERS:
      if filter_object.Match(registry_key):
        return True

    return False

  @classmethod
  def GetFormatSpecification(cls):
    """Retrieves the format specification."""
    format_specification = specification.FormatSpecification(cls.NAME)
    format_specification.AddNewSignature(b'regf', offset=0)
    return format_specification

  def ParseFileObject(self, parser_mediator, file_object, **kwargs):
    """Parses a Windows Registry file-like object.

    Args:
      parser_mediator: a parser mediator object (instance of ParserMediator).
      file_object: a file-like object.
    """
    win_registry_reader = dfwinreg_registry.FileObjectWinRegistryFileReader()
    registry_file = win_registry_reader.Open(file_object)

    win_registry = dfwinreg_registry.WinRegistry()
    key_path_prefix = win_registry.GetRegistryFileMapping(registry_file)
    registry_file.SetKeyPathPrefix(key_path_prefix)
    root_key = registry_file.GetRootKey()
    if not root_key:
      return

    try:
      for registry_key in root_key.RecurseKeys():
        # TODO: use a filter tree to optimize lookups.
        found_matching_plugin = False
        for plugin_object in self._plugins:
          if parser_mediator.abort:
            break

          if self._CanProcessKeyWithPlugin(registry_key, plugin_object):
            found_matching_plugin = True
            plugin_object.UpdateChainAndProcess(parser_mediator, registry_key)

        if not found_matching_plugin:
          self._default_plugin.UpdateChainAndProcess(
              parser_mediator, registry_key)

    except IOError as exception:
      parser_mediator.ProduceParseError(u'{0:s}'.format(exception))


manager.ParsersManager.RegisterParser(WinRegistryParser)
