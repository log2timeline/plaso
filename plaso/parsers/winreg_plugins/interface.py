# -*- coding: utf-8 -*-
"""The Windows Registry plugin objects interface."""

import abc

from plaso.parsers import plugins


class BaseWindowsRegistryKeyFilter(object):
  """Class that defines the Windows Registry key filter interface."""

  @property
  def key_paths(self):
    """List of key paths defined by the filter."""
    return []

  @abc.abstractmethod
  def Match(self, registry_key):
    """Determines if a Windows Registry key matches the filter.

    Args:
      registry_key: a Windows Registry key (instance of
                    dfwinreg.WinRegistryKey).

    Returns:
      A boolean value that indicates a match.
    """


class WindowsRegistryKeyPathFilter(BaseWindowsRegistryKeyFilter):
  """Windows Registry key path filter."""

  _CONTROL_SET_PREFIX = (
      u'HKEY_LOCAL_MACHINE\\System\\CurrentControlSet')

  # This list must be ordered with most specific matches first.
  _WOW64_PREFIXES = [
      u'HKEY_CURRENT_USER\\Software\\Classes',
      u'HKEY_CURRENT_USER\\Software',
      u'HKEY_LOCAL_MACHINE\\Software\\Classes',
      u'HKEY_LOCAL_MACHINE\\Software']

  def __init__(self, key_path):
    """Initializes Windows Registry key filter object.

    Args:
      key_path: the key path.
    """
    super(WindowsRegistryKeyPathFilter, self).__init__()
    self._key_path = None
    self._key_path_prefix = None
    self._key_path_suffix = None
    self._key_path_upper = None
    self._wow64_key_path = None
    self._wow64_key_path_upper = None

    key_path.rstrip(u'\\')
    self._key_path = key_path

    key_path = key_path.upper()
    self._key_path_upper = key_path

    if key_path.startswith(self._CONTROL_SET_PREFIX.upper()):
      self._key_path_prefix, _, self._key_path_suffix = key_path.partition(
          u'CurrentControlSet'.upper())

    else:
      # Handle WoW64 Windows Registry key redirection.
      # Also see:
      # https://msdn.microsoft.com/en-us/library/windows/desktop/
      # ms724072%28v=vs.85%29.aspx
      # https://msdn.microsoft.com/en-us/library/windows/desktop/
      # aa384253(v=vs.85).aspx
      wow64_prefix = None
      for key_path_prefix in self._WOW64_PREFIXES:
        if key_path.startswith(key_path_prefix.upper()):
          wow64_prefix = key_path_prefix
          break

      if wow64_prefix:
        key_path_suffix = self._key_path[len(wow64_prefix):]
        self._wow64_key_path = u'\\'.join([
            wow64_prefix, u'Wow6432Node', key_path_suffix])
        self._wow64_key_path_upper = self._wow64_key_path.upper()

  @property
  def key_paths(self):
    """List of key paths defined by the filter."""
    if self._wow64_key_path:
      return [self._key_path, self._wow64_key_path]
    return [self._key_path]

  def Match(self, registry_key):
    """Determines if a Windows Registry key matches the filter.

    Args:
      registry_key: a Windows Registry key (instance of
                    dfwinreg.WinRegistryKey).

    Returns:
      A boolean value that indicates a match.
    """
    key_path = registry_key.path.upper()
    if self._key_path_prefix and self._key_path_suffix:
      if (key_path.startswith(self._key_path_prefix) and
          key_path.endswith(self._key_path_suffix)):

        key_path_segment = key_path[
            len(self._key_path_prefix):-len(self._key_path_suffix)]
        if key_path_segment.startswith(u'ControlSet'.upper()):
          try:
            control_set = int(key_path_segment[10:], 10)
          except ValueError:
            control_set = None

          # TODO: check if control_set is in bounds.
          return control_set is not None

    return (
        key_path == self._key_path_upper or
        key_path == self._wow64_key_path_upper)


class WindowsRegistryKeyPathPrefixFilter(BaseWindowsRegistryKeyFilter):
  """Windows Registry key path prefix filter."""

  def __init__(self, key_path_prefix):
    """Initializes Windows Registry key filter object.

    Args:
      key_path_prefix: the key path prefix.
    """
    super(WindowsRegistryKeyPathPrefixFilter, self).__init__()
    self._key_path_prefix = key_path_prefix

  def Match(self, registry_key):
    """Determines if a Windows Registry key matches the filter.

    Args:
      registry_key: a Windows Registry key (instance of
                    dfwinreg.WinRegistryKey).

    Returns:
      A boolean value that indicates a match.
    """
    return registry_key.path.startsswith(self._key_path_prefix)


class WindowsRegistryKeyPathSuffixFilter(BaseWindowsRegistryKeyFilter):
  """Windows Registry key path suffix filter."""

  def __init__(self, key_path_suffix):
    """Initializes Windows Registry key filter object.

    Args:
      key_path_suffix: the key path suffix.
    """
    super(WindowsRegistryKeyPathSuffixFilter, self).__init__()
    self._key_path_suffix = key_path_suffix

  def Match(self, registry_key):
    """Determines if a Windows Registry key matches the filter.

    Args:
      registry_key: a Windows Registry key (instance of
                    dfwinreg.WinRegistryKey).

    Returns:
      A boolean value that indicates a match.
    """
    return registry_key.path.endswith(self._key_path_suffix)


class WindowsRegistryKeyWithValuesFilter(BaseWindowsRegistryKeyFilter):
  """Windows Registry key with values filter."""

  _EMPTY_SET = frozenset()

  def __init__(self, value_names):
    """Initializes Windows Registry key filter object.

    Args:
      value_names: list of value names that should be present in the key.
    """
    super(WindowsRegistryKeyWithValuesFilter, self).__init__()
    self._value_names = frozenset(value_names)

  def Match(self, registry_key):
    """Determines if a Windows Registry key matches the filter.

    Args:
      registry_key: a Windows Registry key (instance of
                    dfwinreg.WinRegistryKey).

    Returns:
      A boolean value that indicates a match.
    """
    value_names = frozenset([
        registry_value.name for registry_value in registry_key.GetValues()])

    return self._value_names.issubset(value_names)


class WindowsRegistryPlugin(plugins.BasePlugin):
  """Class that defines the Windows Registry plugin object interface."""
  NAME = u'winreg_plugin'
  DESCRIPTION = u'Parser for Windows Registry value data.'

  # List of Windows Registry key filters (instances of
  # BaseWindowsRegistryKeyFilter) that should match for the plugin to
  # parse the Windows Registry or its values.
  FILTERS = frozenset()

  # URLS should contain a list of URLs with additional information about this
  # key or value.
  URLS = []

  @abc.abstractmethod
  def GetEntries(self, parser_mediator, registry_key, **kwargs):
    """Extracts event objects from the Windows Registry key.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      registry_key: A Windows Registry key (instance of
                    dfwinreg.WinRegistryKey).
    """

  # TODO: remove after preg refactor.
  @classmethod
  def GetKeyPaths(cls):
    """Retrieves a list of Windows Registry key paths.

    Returns:
      A list of Windows Registry key paths.
    """
    key_paths = []
    for registry_key_filter in cls.FILTERS:
      plugin_key_paths = getattr(registry_key_filter, u'key_paths', [])
      for plugin_key_path in plugin_key_paths:
        if plugin_key_path not in key_paths:
          key_paths.append(plugin_key_path)

    return sorted(key_paths)

  # TODO: merge with UpdateChainAndProcess, also requires changes to tests.
  def Process(self, parser_mediator, registry_key, **kwargs):
    """Processes a Windows Registry key or value.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      registry_key: A Windows Registry key (instance of
                    dfwinreg.WinRegistryKey).

    Raises:
      ValueError: If the Windows Registry key is not set.
    """
    if registry_key is None:
      raise ValueError(u'Windows Registry key is not set.')

    # This will raise if unhandled keyword arguments are passed.
    super(WindowsRegistryPlugin, self).Process(parser_mediator, **kwargs)

    self.GetEntries(parser_mediator, registry_key, **kwargs)

  def UpdateChainAndProcess(self, parser_mediator, registry_key, **kwargs):
    """Updates the parser chain and processes a Windows Registry key or value.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      registry_key: A Windows Registry key (instance of
                    dfwinreg.WinRegistryKey).

    Raises:
      ValueError: If the Windows Registry key is not set.
    """
    parser_mediator.AppendToParserChain(self)
    try:
      self.Process(parser_mediator, registry_key, **kwargs)
    finally:
      parser_mediator.PopFromParserChain()
