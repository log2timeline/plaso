# -*- coding: utf-8 -*-
"""The Windows Registry plugin interface."""

import abc

from dfwinreg import errors as dfwinreg_errors

from plaso.containers import windows_events
from plaso.parsers import plugins


class BaseWindowsRegistryKeyFilter(object):
  """The Windows Registry key filter interface."""

  @property
  def key_paths(self):
    """List[str]: key paths defined by the filter."""
    return []

  # pylint: disable=redundant-returns-doc
  @abc.abstractmethod
  def Match(self, registry_key):
    """Determines if a Windows Registry key matches the filter.

    Args:
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.

    Returns:
      bool: True if the keys match.
    """


class WindowsRegistryKeyPathFilter(BaseWindowsRegistryKeyFilter):
  """Windows Registry key path filter."""

  _CONTROL_SET_PREFIX = (
      'HKEY_LOCAL_MACHINE\\System\\CurrentControlSet')

  # This list must be ordered with most specific matches first.
  _WOW64_PREFIXES = [
      'HKEY_CURRENT_USER\\Software\\Classes',
      'HKEY_CURRENT_USER\\Software',
      'HKEY_LOCAL_MACHINE\\Software\\Classes',
      'HKEY_LOCAL_MACHINE\\Software']

  def __init__(self, key_path):
    """Initializes a Windows Registry key filter.

    Args:
      key_path (str): key path.
    """
    super(WindowsRegistryKeyPathFilter, self).__init__()

    key_path.rstrip('\\')
    self._key_path = key_path

    key_path = key_path.upper()
    self._key_path_upper = key_path

    self._wow64_key_path = None
    self._wow64_key_path_upper = None

    if key_path.startswith(self._CONTROL_SET_PREFIX.upper()):
      self._key_path_prefix, _, self._key_path_suffix = key_path.partition(
          'CurrentControlSet'.upper())

    else:
      self._key_path_prefix = None
      self._key_path_suffix = None

      # Handle WoW64 Windows Registry key redirection. Also see:
      # https://msdn.microsoft.com/en-us/library/windows/desktop/ms724072%28v=vs.85%29.aspx
      # https://msdn.microsoft.com/en-us/library/windows/desktop/aa384253(v=vs.85).aspx
      wow64_prefix = None
      for key_path_prefix in self._WOW64_PREFIXES:
        if key_path.startswith(key_path_prefix.upper()):
          wow64_prefix = key_path_prefix
          break

      if wow64_prefix:
        key_path_suffix = self._key_path[len(wow64_prefix):]
        self._wow64_key_path = '\\'.join([wow64_prefix, 'Wow6432Node'])

        if key_path_suffix.startswith('\\'):
          key_path_suffix = key_path_suffix[1:]
        if key_path_suffix:
          self._wow64_key_path = '\\'.join([
              self._wow64_key_path, key_path_suffix])
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
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.

    Returns:
      bool: True if the keys match.
    """
    key_path = registry_key.path.upper()
    if self._key_path_prefix and self._key_path_suffix:
      if (key_path.startswith(self._key_path_prefix) and
          key_path.endswith(self._key_path_suffix)):

        key_path_segment = key_path[
            len(self._key_path_prefix):-len(self._key_path_suffix)]
        if key_path_segment.startswith('ControlSet'.upper()):
          try:
            control_set = int(key_path_segment[10:], 10)
          except ValueError:
            control_set = None

          # TODO: check if control_set is in bounds.
          return control_set is not None

    return key_path in (self._key_path_upper, self._wow64_key_path_upper)


class WindowsRegistryKeyPathPrefixFilter(BaseWindowsRegistryKeyFilter):
  """Windows Registry key path prefix filter."""

  def __init__(self, key_path_prefix):
    """Initializes a Windows Registry key filter.

    Args:
      key_path_prefix (str): the key path prefix.
    """
    super(WindowsRegistryKeyPathPrefixFilter, self).__init__()
    self._key_path_prefix = key_path_prefix

  def Match(self, registry_key):
    """Determines if a Windows Registry key matches the filter.

    Args:
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.

    Returns:
      bool: True if the keys match.
    """
    return registry_key.path.startswith(self._key_path_prefix)


class WindowsRegistryKeyPathSuffixFilter(BaseWindowsRegistryKeyFilter):
  """Windows Registry key path suffix filter."""

  def __init__(self, key_path_suffix):
    """Initializes a Windows Registry key filter.

    Args:
      key_path_suffix (str): the key path suffix.
    """
    super(WindowsRegistryKeyPathSuffixFilter, self).__init__()
    self._key_path_suffix = key_path_suffix

  def Match(self, registry_key):
    """Determines if a Windows Registry key matches the filter.

    Args:
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.

    Returns:
      bool: True if the keys match.
    """
    return registry_key.path.endswith(self._key_path_suffix)


class WindowsRegistryKeyWithValuesFilter(BaseWindowsRegistryKeyFilter):
  """Windows Registry key with values filter."""

  _EMPTY_SET = frozenset()

  def __init__(self, value_names):
    """Initializes a Windows Registry key filter.

    Args:
      value_names (list[str]): name of values that should be present in the key.
    """
    super(WindowsRegistryKeyWithValuesFilter, self).__init__()
    self._value_names = frozenset(value_names)

  def Match(self, registry_key):
    """Determines if a Windows Registry key matches the filter.

    Args:
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.

    Returns:
      bool: True if the keys match.
    """
    value_names = frozenset([
        registry_value.name for registry_value in registry_key.GetValues()])

    return self._value_names.issubset(value_names)


class WindowsRegistryPlugin(plugins.BasePlugin):
  """The Windows Registry plugin interface."""

  NAME = 'winreg_plugin'
  DATA_FORMAT = 'Windows Registry data'

  # List of Windows Registry key filters (instances of
  # BaseWindowsRegistryKeyFilter) that should match for the plugin to
  # parse the Windows Registry key or its values.
  FILTERS = frozenset()

  def _GetValueDataFromKey(self, registry_key, value_name):
    """Retrieves the value data from a Registry value.

    Args:
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
      value_name (str): name of the value.

    Returns:
      bytes: value data or None if not available.
    """
    registry_value = registry_key.GetValueByName(value_name)
    if not registry_value:
      return None

    return registry_value.data

  def _GetValueFromKey(self, registry_key, value_name):
    """Retrieves a value from the Windows Registry key.

    Args:
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
      value_name (str): name of the value to retrieve.

    Returns:
      object: value data or None if no corresponding Windows Registry value
          is available.
    """
    registry_value = registry_key.GetValueByName(value_name)
    if not registry_value:
      return None

    return registry_value.GetDataAsObject()

  def _GetValuesFromKey(
      self, parser_mediator, registry_key, names_to_skip=None):
    """Retrieves the values from a Windows Registry key.

    Where:
    * the name of the default value is represented as an empty string;
    * binary data values are represented as "(# bytes)", where # contains
          the number of bytes of the data;
    * empty values are represented as None;
    * empty multi value string values are represented as "[]".

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
      names_to_skip (Optional[list[str]]): names of values that should
          be skipped.

    Returns:
      list[tuple[str, str, str]]: name, data type and data pais of the values
          in the key.
    """
    names_to_skip = [name.lower() for name in names_to_skip or []]

    value_tuples = []
    for registry_value in registry_key.GetValues():
      value_name = registry_value.name or ''
      if value_name.lower() in names_to_skip:
        continue

      data_type_string = registry_value.data_type_string

      if registry_value.data is None:
        value_string = None
      else:
        try:
          value_object = registry_value.GetDataAsObject()

          if registry_value.DataIsMultiString():
            value_string = ', '.join(value_object or [])
            value_string = f'[{value_string:s}]'

          elif (registry_value.DataIsInteger() or
                registry_value.DataIsString()):
            value_string = str(value_object)

          elif parser_mediator.extract_winreg_binary_values:
            value_string = registry_value.data

          else:
            # Add a place holder for remaining types such as REG_BINARY and
            # REG_RESOURCE_REQUIREMENT_LIST.
            value_data_size = len(value_object)
            value_string = f'({value_data_size:d} bytes)'

        except dfwinreg_errors.WinRegistryValueError as exception:
          parser_mediator.ProduceRecoveryWarning((
              f'Unable to retrieve value data of type: {data_type_string:s} '
              f'as object from value: {value_name:s} in key: '
              f'{registry_key.path:s} with error: {exception!s}'))
          value_data_size = len(registry_value.data)
          value_string = f'({value_data_size:d} bytes)'

      value_tuples.append((value_name, data_type_string, value_string))

    return value_tuples or None

  def _ProduceDefaultWindowsRegistryEvent(
      self, parser_mediator, registry_key, names_to_skip=None):
    """Produces a default Windows Registry event.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
      names_to_skip (Optional[list[str]]): names of values that should
          be skipped.
    """
    event_data = windows_events.WindowsRegistryEventData()
    event_data.key_path = registry_key.path
    event_data.last_written_time = registry_key.last_written_time
    event_data.values = self._GetValuesFromKey(
        parser_mediator, registry_key, names_to_skip=names_to_skip)

    parser_mediator.ProduceEventData(event_data)

  # pylint: disable=arguments-differ
  @abc.abstractmethod
  def ExtractEvents(self, parser_mediator, registry_key, **kwargs):
    """Extracts events from a Windows Registry key.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
    """

  # TODO: merge with UpdateChainAndProcess, also requires changes to tests.
  def Process(self, parser_mediator, registry_key, **kwargs):
    """Processes a Windows Registry key or value.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.

    Raises:
      ValueError: If the Windows Registry key is not set.
    """
    if registry_key is None:
      raise ValueError('Windows Registry key is not set.')

    # This will raise if unhandled keyword arguments are passed.
    super(WindowsRegistryPlugin, self).Process(parser_mediator, **kwargs)

    self.ExtractEvents(parser_mediator, registry_key, **kwargs)

  # pylint: disable=arguments-differ
  def UpdateChainAndProcess(self, parser_mediator, registry_key, **kwargs):
    """Updates the parser chain and processes a Windows Registry key or value.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.

    Raises:
      ValueError: If the Windows Registry key is not set.
    """
    parser_mediator.AppendToParserChain(self.NAME)
    try:
      self.Process(parser_mediator, registry_key, **kwargs)
    finally:
      parser_mediator.PopFromParserChain()
