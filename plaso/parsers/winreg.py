# -*- coding: utf-8 -*-
"""Parser for Windows NT Registry (REGF) files."""

from __future__ import unicode_literals

from dfwinreg import errors as dfwinreg_errors
from dfwinreg import interface as dfwinreg_interface
from dfwinreg import regf as dfwinreg_regf
from dfwinreg import registry as dfwinreg_registry
from dfwinreg import registry_searcher as dfwinreg_registry_searcher

from plaso.engine import artifact_filters
from plaso.lib import specification
from plaso.filters import path_filter
from plaso.parsers import interface
from plaso.parsers import logger
from plaso.parsers import manager


class FileObjectWinRegistryFileReader(dfwinreg_interface.WinRegistryFileReader):
  """A single file-like object Windows Registry file reader."""

  # pylint: disable=arguments-differ
  def Open(self, file_object, ascii_codepage='cp1252'):
    """Opens a Windows Registry file-like object.

    Args:
      file_object (dfvfs.FileIO): Windows Registry file-like object.
      ascii_codepage (Optional[str]): ASCII string codepage.

    Returns:
      WinRegistryFile: Windows Registry file or None.
    """
    registry_file = dfwinreg_regf.REGFWinRegistryFile(
        ascii_codepage=ascii_codepage)

    # We don't catch any IOErrors here since we want to produce a parse error
    # from the parser if this happens.
    registry_file.Open(file_object)

    return registry_file


class WinRegistryParser(interface.FileObjectParser):
  """Parses Windows NT Registry (REGF) files."""

  NAME = 'winreg'
  DESCRIPTION = 'Parser for Windows NT Registry (REGF) files.'

  _plugin_classes = {}

  _CONTROL_SET_PREFIX = (
      'HKEY_LOCAL_MACHINE\\System\\ControlSet').lower()

  _NORMALIZED_CONTROL_SET_PREFIX = (
      'HKEY_LOCAL_MACHINE\\System\\CurrentControlSet').lower()

  def __init__(self):
    """Initializes a parser object."""
    super(WinRegistryParser, self).__init__()
    self._plugin_per_key_path = {}
    self._plugins_without_key_paths = []

    default_plugin_list_index = None
    key_paths = []

    for list_index, plugin in enumerate(self._plugins):
      if plugin.NAME == 'winreg_default':
        default_plugin_list_index = list_index
        continue

      for registry_key_filter in plugin.FILTERS:
        plugin_key_paths = getattr(registry_key_filter, 'key_paths', [])
        if (not plugin_key_paths and
            plugin not in self._plugins_without_key_paths):
          self._plugins_without_key_paths.append(plugin)
          continue

        for plugin_key_path in plugin_key_paths:
          plugin_key_path = plugin_key_path.lower()
          if plugin_key_path in self._plugin_per_key_path:
            logger.warning((
                'Windows Registry key path: {0:s} defined by plugin: {1:s} '
                'already set by plugin: {2:s}').format(
                    plugin_key_path, plugin.NAME,
                    self._plugin_per_key_path[plugin_key_path].NAME))
            continue

          self._plugin_per_key_path[plugin_key_path] = plugin

          key_paths.append(plugin_key_path)

    if default_plugin_list_index is not None:
      self._default_plugin = self._plugins.pop(default_plugin_list_index)

    self._path_filter = path_filter.PathFilterScanTree(
        key_paths, case_sensitive=False, path_segment_separator='\\')

  def _CanProcessKeyWithPlugin(self, registry_key, plugin):
    """Determines if a plugin can process a Windows Registry key or its values.

    Args:
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
      plugin (WindowsRegistryPlugin): Windows Registry plugin.

    Returns:
      bool: True if the Registry key can be processed with the plugin.
    """
    for registry_key_filter in plugin.FILTERS:
      # Skip filters that define key paths since they are already
      # checked by the path filter.
      if getattr(registry_key_filter, 'key_paths', []):
        continue

      if registry_key_filter.Match(registry_key):
        return True

    return False

  @classmethod
  def GetFormatSpecification(cls):
    """Retrieves the format specification."""
    format_specification = specification.FormatSpecification(cls.NAME)
    format_specification.AddNewSignature(b'regf', offset=0)
    return format_specification

  def _ParseKeyWithPlugin(self, parser_mediator, registry_key, plugin):
    """Parses the Registry key with a specific plugin.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      registry_key (dfwinreg.WinRegistryKey): Windwos Registry key.
      plugin (WindowsRegistryPlugin): Windows Registry plugin.
    """
    try:
      plugin.UpdateChainAndProcess(parser_mediator, registry_key)
    except (IOError, dfwinreg_errors.WinRegistryValueError) as exception:
      parser_mediator.ProduceExtractionWarning(
          'in key: {0:s} error: {1!s}'.format(registry_key.path, exception))

  def _NormalizeKeyPath(self, key_path):
    """Normalizes a Windows Registry key path.

    Args:
      key_path (str): Windows Registry key path.

    Returns:
      str: normalized Windows Registry key path.
    """
    normalized_key_path = key_path.lower()
    # The Registry key path should start with:
    # HKEY_LOCAL_MACHINE\System\ControlSet followed by 3 digits
    # which makes 39 characters.
    if (len(normalized_key_path) < 39 or
        not normalized_key_path.startswith(self._CONTROL_SET_PREFIX)):
      return normalized_key_path

    # Key paths that contain ControlSet### must be normalized to
    # CurrentControlSet.
    return ''.join([
        self._NORMALIZED_CONTROL_SET_PREFIX, normalized_key_path[39:]])

  def _ParseKey(self, parser_mediator, registry_key):
    """Parses the Registry key with a specific plugin.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      registry_key (dfwinreg.WinRegistryKey): Windwos Registry key.
    """
    matching_plugin = None

    normalized_key_path = self._NormalizeKeyPath(registry_key.path)
    if self._path_filter.CheckPath(normalized_key_path):
      matching_plugin = self._plugin_per_key_path[normalized_key_path]
    else:
      for plugin in self._plugins_without_key_paths:
        if self._CanProcessKeyWithPlugin(registry_key, plugin):
          matching_plugin = plugin
          break

    if not matching_plugin:
      matching_plugin = self._default_plugin

    if matching_plugin:
      self._ParseKeyWithPlugin(parser_mediator, registry_key, matching_plugin)

  def _ParseRecurseKeys(self, parser_mediator, root_key):
    """Parses the Registry keys recursively.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      root_key (dfwinreg.WinRegistryKey): root Windows Registry key.
    """
    for registry_key in root_key.RecurseKeys():
      if parser_mediator.abort:
        break

      self._ParseKey(parser_mediator, registry_key)

  def _ParseKeysFromFindSpecs(self, parser_mediator, win_registry, find_specs):
    """Parses the Registry keys from FindSpecs.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      win_registry (dfwinreg.WinRegistryKey): root Windows Registry key.
      find_specs (dfwinreg.FindSpecs): Keys to search for.
    """
    searcher = dfwinreg_registry_searcher.WinRegistrySearcher(win_registry)
    for registry_key_path in iter(searcher.Find(find_specs=find_specs)):
      if parser_mediator.abort:
        break

      registry_key = searcher.GetKeyByPath(registry_key_path)
      self._ParseKey(parser_mediator, registry_key)

  def ParseFileObject(self, parser_mediator, file_object):
    """Parses a Windows Registry file-like object.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      file_object (dfvfs.FileIO): a file-like object.
    """
    win_registry_reader = FileObjectWinRegistryFileReader()

    try:
      registry_file = win_registry_reader.Open(file_object)
    except IOError as exception:
      parser_mediator.ProduceExtractionWarning(
          'unable to open Windows Registry file with error: {0!s}'.format(
              exception))
      return

    win_registry = dfwinreg_registry.WinRegistry()

    key_path_prefix = win_registry.GetRegistryFileMapping(registry_file)
    registry_file.SetKeyPathPrefix(key_path_prefix)
    root_key = registry_file.GetRootKey()
    if not root_key:
      return

    registry_find_specs = getattr(
        parser_mediator.collection_filters_helper, 'registry_find_specs', None)

    if not registry_find_specs:
      try:
        self._ParseRecurseKeys(parser_mediator, root_key)
      except IOError as exception:
        parser_mediator.ProduceExtractionWarning('{0!s}'.format(exception))

    else:
      artifacts_filters_helper = (
          artifact_filters.ArtifactDefinitionsFiltersHelper)
      if not artifacts_filters_helper.CheckKeyCompatibility(key_path_prefix):
        logger.warning((
            'Artifacts filters are not supported for Windows Registry file '
            'with key path prefix: "{0:s}".').format(key_path_prefix))

      else:
        try:
          win_registry.MapFile(key_path_prefix, registry_file)
          self._ParseKeysFromFindSpecs(
              parser_mediator, win_registry, registry_find_specs)
        except IOError as exception:
          parser_mediator.ProduceExtractionWarning('{0!s}'.format(exception))


manager.ParsersManager.RegisterParser(WinRegistryParser)
