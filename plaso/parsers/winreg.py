# -*- coding: utf-8 -*-
"""Parser for Windows NT Registry (REGF) files."""

import logging

from plaso.dfwinreg import errors as dfwinreg_errors
from plaso.dfwinreg import interface as dfwinreg_interface
from plaso.dfwinreg import regf as dfwinreg_regf
from plaso.dfwinreg import registry as dfwinreg_registry
from plaso.lib import specification
from plaso.parsers import interface
from plaso.parsers import manager


class FileObjectWinRegistryFileReader(dfwinreg_interface.WinRegistryFileReader):
  """A single file-like object Windows Registry file reader."""

  def Open(self, file_object, ascii_codepage=u'cp1252'):
    """Opens a Windows Registry file-like object.

    Args:
      file_object: the Windows Registry file-like object.
      ascii_codepage: optional ASCII string codepage. The default is cp1252
                      (or windows-1252).

    Returns:
      The Windows Registry file (instance of WinRegistryFile) or None.
    """
    registry_file = dfwinreg_regf.REGFWinRegistryFile(
        ascii_codepage=ascii_codepage)

    try:
      registry_file.Open(file_object)
    except IOError as exception:
      logging.warning(
          u'Unable to open Windows Registry file with error: {0:s}'.format(
              exception))
      return

    return registry_file


# TODO: rename to REGFParser.
class WinRegistryParser(interface.FileObjectParser):
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

  def _ParseKeyWithPlugin(self, parser_mediator, registry_key, plugin_object):
    """Parses the Registry key with a specific plugin.

    Args:
      parser_mediator: a parser mediator object (instance of ParserMediator).
      registry_key: a Registry key object (instance of
                    dfwinreg.WinRegistryKey).
      plugin_object: a Windows Registry plugin object (instance of
                     WindowsRegistryPlugin).
    """
    try:
      plugin_object.UpdateChainAndProcess(parser_mediator, registry_key)
    except (IOError, dfwinreg_errors.WinRegistryValueError) as exception:
      parser_mediator.ProduceParseError(
          u'in key: {0:s} {1:s}'.format(registry_key.path, exception))

  def _ParseRecurseKeys(self, parser_mediator, root_key):
    """Parses the Registry keys recursively.

    Args:
      parser_mediator: a parser mediator object (instance of ParserMediator).
      root_key: a root Registry key object (instance of
                dfwinreg.WinRegistryKey).
    """
    for registry_key in root_key.RecurseKeys():
      # TODO: use a filter tree to optimize lookups.
      found_matching_plugin = False
      for plugin_object in self._plugins:
        if parser_mediator.abort:
          break

        if self._CanProcessKeyWithPlugin(registry_key, plugin_object):
          found_matching_plugin = True
          self._ParseKeyWithPlugin(
              parser_mediator, registry_key, plugin_object)

      if not found_matching_plugin:
        self._ParseKeyWithPlugin(
            parser_mediator, registry_key, self._default_plugin)

  def ParseFileObject(self, parser_mediator, file_object, **kwargs):
    """Parses a Windows Registry file-like object.

    Args:
      parser_mediator: a parser mediator object (instance of ParserMediator).
      file_object: a file-like object.
    """
    win_registry_reader = FileObjectWinRegistryFileReader()
    registry_file = win_registry_reader.Open(file_object)

    win_registry = dfwinreg_registry.WinRegistry()
    key_path_prefix = win_registry.GetRegistryFileMapping(registry_file)
    registry_file.SetKeyPathPrefix(key_path_prefix)
    root_key = registry_file.GetRootKey()
    if not root_key:
      return

    try:
      self._ParseRecurseKeys(parser_mediator, root_key)
    except IOError as exception:
      parser_mediator.ProduceParseError(u'{0:s}'.format(exception))


manager.ParsersManager.RegisterParser(WinRegistryParser)
