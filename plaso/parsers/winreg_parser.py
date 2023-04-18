# -*- coding: utf-8 -*-
"""Parser for Windows NT Registry (REGF) files."""

from dfwinreg import errors as dfwinreg_errors
from dfwinreg import regf as dfwinreg_regf
from dfwinreg import registry as dfwinreg_registry
from dfwinreg import registry_searcher as dfwinreg_registry_searcher

from plaso.engine import artifact_filters
from plaso.lib import specification
from plaso.filters import path_filter
from plaso.parsers import interface
from plaso.parsers import logger
from plaso.parsers import manager


class WinRegistryParser(interface.FileObjectParser):
  """Parses Windows NT Registry (REGF) files."""

  NAME = 'winreg'
  DATA_FORMAT = 'Windows NT Registry (REGF) file'

  _plugin_classes = {}

  _ARTIFACTS_FILTER_HELPER = (
      artifact_filters.ArtifactDefinitionsFiltersHelper)

  _AMCACHE_ROOT_KEY_NAMES = frozenset([
      '{11517b7c-e79d-4e20-961b-75a811715add}',
      '{356c48f6-2fee-e7ef-2a64-39f59ec3be22}'])

  _CONTROL_SET_PREFIX = (
      'HKEY_LOCAL_MACHINE\\System\\ControlSet').lower()

  _NORMALIZED_CONTROL_SET_PREFIX = (
      'HKEY_LOCAL_MACHINE\\System\\CurrentControlSet').lower()

  def __init__(self):
    """Initializes a parser."""
    super(WinRegistryParser, self).__init__()
    self._path_filter = None
    self._plugins_per_key_path = {}
    self._plugins_without_key_paths = []

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

  def EnablePlugins(self, plugin_includes):
    """Enables parser plugins.

    Args:
      plugin_includes (set[str]): names of the plugins to enable, where
          set(['*']) represents all plugins. Note the default plugin, if
          it exists, is always enabled and cannot be disabled.
    """
    self._plugins_per_name = {}
    self._plugins_per_key_path = {}
    self._plugins_without_key_paths = []

    if not self._plugin_classes:
      return

    key_paths = []

    for plugin_name, plugin_class in self._plugin_classes.items():
      if plugin_name == self._default_plugin_name:
        self._default_plugin = plugin_class()
        continue

      if (plugin_includes != self.ALL_PLUGINS and
          plugin_name not in plugin_includes):
        continue

      plugin_object = plugin_class()
      self._plugins_per_name[plugin_name] = plugin_object

      for registry_key_filter in plugin_object.FILTERS:
        plugin_key_paths = getattr(registry_key_filter, 'key_paths', [])
        if (not plugin_key_paths and
            plugin_object not in self._plugins_without_key_paths):
          self._plugins_without_key_paths.append(plugin_object)
          continue

        for plugin_key_path in plugin_key_paths:
          plugin_key_path = plugin_key_path.lower()
          if plugin_key_path in self._plugins_per_key_path:
            logger.warning((
                'Windows Registry key path: {0:s} defined by plugin: {1:s} '
                'already set by plugin: {2:s}').format(
                    plugin_key_path, plugin_object.NAME,
                    self._plugins_per_key_path[plugin_key_path].NAME))
            continue

          self._plugins_per_key_path[plugin_key_path] = plugin_object

          key_paths.append(plugin_key_path)

    self._path_filter = path_filter.PathFilterScanTree(
        key_paths, case_sensitive=False, path_segment_separator='\\')

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
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
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
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
    """
    matching_plugin = None

    logger.debug('Parsing Windows Registry key: {0:s}'.format(
        registry_key.path))

    normalized_key_path = self._NormalizeKeyPath(registry_key.path)
    if self._path_filter and self._path_filter.CheckPath(normalized_key_path):
      matching_plugin = self._plugins_per_key_path[normalized_key_path]
    else:
      for plugin in self._plugins_without_key_paths:
        profiling_name = '/'.join([self.NAME, plugin.NAME])

        parser_mediator.SampleFormatCheckStartTiming(profiling_name)

        try:
          if self._CanProcessKeyWithPlugin(registry_key, plugin):
            matching_plugin = plugin
            break

        finally:
          parser_mediator.SampleFormatCheckStopTiming(profiling_name)

    if not matching_plugin:
      matching_plugin = self._default_plugin

    if matching_plugin:
      self._ParseKeyWithPlugin(parser_mediator, registry_key, matching_plugin)

  def _ParseRecurseKeys(self, parser_mediator, registry_key):
    """Parses the Registry keys recursively.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
    """
    # Note that we do not use dfWinReg generators here to be able to catch
    # exceptions raised by corrupt files.

    self._ParseKey(parser_mediator, registry_key)

    for subkey_index in range(registry_key.number_of_subkeys):
      if parser_mediator.abort:
        break

      try:
        subkey = registry_key.GetSubkeyByIndex(subkey_index)
        self._ParseRecurseKeys(parser_mediator, subkey)

      except IOError as exception:
        parser_mediator.ProduceExtractionWarning(
            'in key: {0:s} error: {1!s}'.format(registry_key.path, exception))

  def _ParseKeysFromFindSpecs(self, parser_mediator, win_registry, find_specs):
    """Parses the Registry keys from FindSpecs.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      win_registry (dfwinreg.WinRegistryKey): root Windows Registry key.
      find_specs (dfwinreg.FindSpecs): Keys to search for.
    """
    searcher = dfwinreg_registry_searcher.WinRegistrySearcher(win_registry)
    for registry_key_path in searcher.Find(find_specs=find_specs):
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
    code_page = parser_mediator.GetCodePage()

    registry_file = dfwinreg_regf.REGFWinRegistryFile(
        ascii_codepage=code_page, emulate_virtual_keys=False)

    try:
      registry_file.Open(file_object)
    except IOError as exception:
      parser_mediator.ProduceExtractionWarning(
          'unable to open Windows Registry file with error: {0!s}'.format(
              exception))
      return

    try:
      win_registry = dfwinreg_registry.WinRegistry()

      key_path_prefix = win_registry.GetRegistryFileMapping(registry_file)
      registry_file.SetKeyPathPrefix(key_path_prefix)
      root_key = registry_file.GetRootKey()
      if root_key:
        # For now treat AMCache.hve separately.
        if root_key.name.lower() in self._AMCACHE_ROOT_KEY_NAMES:
          self._ParseRecurseKeys(parser_mediator, root_key)

        elif not parser_mediator.registry_find_specs:
          self._ParseRecurseKeys(parser_mediator, root_key)

        elif not self._ARTIFACTS_FILTER_HELPER.CheckKeyCompatibility(
            key_path_prefix):
          logger.warning((
              'Artifacts filters are not supported for Windows Registry '
              'file with key path prefix: "{0:s}".').format(
                  key_path_prefix))

        else:
          win_registry.MapFile(key_path_prefix, registry_file)
          # Note that win_registry will close the mapped registry_file.
          registry_file = None

          self._ParseKeysFromFindSpecs(
              parser_mediator, win_registry,
              parser_mediator.registry_find_specs)

    except IOError as exception:
      parser_mediator.ProduceExtractionWarning('{0!s}'.format(exception))

    finally:
      if registry_file:
        registry_file.Close()


manager.ParsersManager.RegisterParser(WinRegistryParser)
