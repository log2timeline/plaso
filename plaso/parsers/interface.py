# -*- coding: utf-8 -*-
"""The parsers and plugins interface classes."""

import abc
import os

from plaso.lib import errors


class BaseFileEntryFilter(object):
  """File entry filter interface."""

  # pylint: disable=redundant-returns-doc
  @abc.abstractmethod
  def Match(self, file_entry):
    """Determines if a file entry matches the filter.

    Args:
      file_entry (dfvfs.FileEntry): a file entry.

    Returns:
      bool: True if the file entry matches the filter.
    """


class FileNameFileEntryFilter(BaseFileEntryFilter):
  """File name file entry filter."""

  def __init__(self, filename):
    """Initializes a file entry filter.

    Args:
      filename (str): name of the file.
    """
    super(FileNameFileEntryFilter, self).__init__()
    self._filename = filename.lower()

  def Match(self, file_entry):
    """Determines if a file entry matches the filter.

    Args:
      file_entry (dfvfs.FileEntry): a file entry.

    Returns:
      bool: True if the file entry matches the filter.
    """
    if not file_entry:
      return False

    filename = file_entry.name.lower()
    return filename == self._filename


class BaseParser(object):
  """The parser interface."""

  # The name of the parser. This is the name that is used in the registration
  # and used for parser/plugin selection, so this needs to be concise and unique
  # for all plugins/parsers, such as 'Chrome', 'Safari' or 'UserAssist'.
  NAME = 'base_parser'

  # Data format supported by the parser plugin. This information is used by
  # the parser manager to generate parser and plugin information.
  DATA_FORMAT = ''

  # List of filters that should match for the parser to be applied.
  FILTERS = frozenset()

  ALL_PLUGINS = set(['*'])

  # Every derived parser class that implements plugins should define
  # its own _plugin_classes dict:
  # _plugin_classes = {}

  # We deliberately don't define it here to make sure the plugins of
  # different parser classes don't end up in the same dict.
  _plugin_classes = None

  def __init__(self):
    """Initializes a parser.

    By default all plugins will be enabled. To only enable specific plugins
    use the EnablePlugins method and pass it a list of strings containing
    the names of the plugins to enable.

    The default plugin, named "{self.NAME:s}_default", if it exists,
    is always enabled and cannot be disabled.
    """
    super(BaseParser, self).__init__()
    self._default_plugin = None
    self._default_plugin_name = '{0:s}_default'.format(self.NAME)
    self._plugins_per_name = None
    self.EnablePlugins(self.ALL_PLUGINS)

  @classmethod
  def DeregisterPlugin(cls, plugin_class):
    """Deregisters a plugin class.

    The plugin classes are identified based on their lower case name.

    Args:
      plugin_class (type): class of the plugin.

    Raises:
      KeyError: if plugin class is not set for the corresponding name.
    """
    plugin_name = plugin_class.NAME.lower()
    if plugin_name not in cls._plugin_classes:
      raise KeyError(
          'Plugin class not set for name: {0:s}.'.format(
              plugin_class.NAME))

    del cls._plugin_classes[plugin_name]

  def EnablePlugins(self, plugin_includes):
    """Enables parser plugins.

    Args:
      plugin_includes (set[str]): names of the plugins to enable, where
          set(['*']) represents all plugins. Note the default plugin, if
          it exists, is always enabled and cannot be disabled.
    """
    self._plugins_per_name = {}
    if not self._plugin_classes:
      return

    for plugin_name, plugin_class in self._plugin_classes.items():
      if plugin_name == self._default_plugin_name:
        self._default_plugin = plugin_class()
        continue

      if (plugin_includes != self.ALL_PLUGINS and
          plugin_name not in plugin_includes):
        continue

      plugin_object = plugin_class()
      self._plugins_per_name[plugin_name] = plugin_object

  # TODO: move this to a filter.
  # pylint: disable=redundant-returns-doc
  @classmethod
  def GetFormatSpecification(cls):
    """Retrieves the format specification.

    Returns:
      FormatSpecification: a format specification or None if not available.
    """
    return None

  @classmethod
  def GetPluginNames(cls):
    """Retrieves the names of registered plugins.

    Returns:
      list[str]: names of the plugins.
    """
    return list(cls._plugin_classes.keys())

  @classmethod
  def GetPluginObjectByName(cls, plugin_name):
    """Retrieves a specific plugin object by its name.

    Args:
      plugin_name (str): name of the plugin.

    Returns:
      BasePlugin: a plugin object or None if not available.
    """
    plugin_class = cls._plugin_classes.get(plugin_name, None)
    if plugin_class:
      return plugin_class()

    return None

  @classmethod
  def GetPlugins(cls):
    """Retrieves the registered plugins.

    Yields:
      tuple[str, type]: name and class of the plugin.
    """
    for plugin_name, plugin_class in cls._plugin_classes.items():
      yield plugin_name, plugin_class

  @classmethod
  def RegisterPlugin(cls, plugin_class):
    """Registers a plugin class.

    The plugin classes are identified based on their lower case name.

    Args:
      plugin_class (type): class of the plugin.

    Raises:
      KeyError: if plugin class is already set for the corresponding name.
    """
    plugin_name = plugin_class.NAME.lower()
    if plugin_name in cls._plugin_classes:
      raise KeyError((
          'Plugin class already set for name: {0:s}.').format(
              plugin_class.NAME))

    cls._plugin_classes[plugin_name] = plugin_class

  @classmethod
  def RegisterPlugins(cls, plugin_classes):
    """Registers plugin classes.

    Args:
      plugin_classes (list[type]): classes of plugins.

    Raises:
      KeyError: if plugin class is already set for the corresponding name.
    """
    for plugin_class in plugin_classes:
      cls.RegisterPlugin(plugin_class)

  @classmethod
  def SupportsPlugins(cls):
    """Determines if a parser supports plugins.

    Returns:
      bool: True if the parser supports plugins.
    """
    return cls._plugin_classes is not None


class FileEntryParser(BaseParser):
  """The file entry parser interface."""

  def Parse(self, parser_mediator):
    """Parses a file entry.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.

    Raises:
      WrongParser: when the file cannot be parsed.
    """
    file_entry = parser_mediator.GetFileEntry()
    if not file_entry:
      raise errors.WrongParser('Invalid file entry')

    parser_mediator.AppendToParserChain(self.NAME)

    parser_chain = parser_mediator.GetParserChain()
    parser_mediator.SampleStartTiming(parser_chain)

    try:
      self.ParseFileEntry(parser_mediator, file_entry)

    finally:
      parser_mediator.SampleStopTiming(parser_chain)

      parser_mediator.PopFromParserChain()

  @abc.abstractmethod
  def ParseFileEntry(self, parser_mediator, file_entry):
    """Parses a file entry.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      file_entry (dfvfs.FileEntry): a file entry to parse.

    Raises:
      WrongParser: when the file cannot be parsed.
    """


class FileObjectParser(BaseParser):
  """The file-like object parser interface."""

  # The initial file offset. Set this value to None if no initial file offset
  # seek needs to be performed.
  _INITIAL_FILE_OFFSET = 0

  # The maximum file size supported by the parser. Set this value to None if no
  # file size check needs to be performed.
  _MAXIMUM_FILE_SIZE = None

  # The minimum file size supported by the parser. Set this value to None if no
  # file size check needs to be performed.
  _MINIMUM_FILE_SIZE = None

  def Parse(self, parser_mediator, file_object):
    """Parses a single file-like object.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      file_object (dfvfs.FileIO): a file-like object to parse.

    Raises:
      WrongParser: when the file cannot be parsed.
    """
    if not file_object:
      raise errors.WrongParser('Invalid file object')

    file_size = file_object.get_size()
    if file_size == 0:
      return

    if (self._MINIMUM_FILE_SIZE is not None and
        file_size < self._MINIMUM_FILE_SIZE):
      raise errors.WrongParser(
          'File size: {0:d} too small, minimum: {1:d}.'.format(
              file_size, self._MINIMUM_FILE_SIZE))

    if (self._MAXIMUM_FILE_SIZE is not None and
        file_size > self._MAXIMUM_FILE_SIZE):
      raise errors.WrongParser(
          'File size: {0:d} too large, maximum: {1:d}.'.format(
              file_size, self._MAXIMUM_FILE_SIZE))

    if self._INITIAL_FILE_OFFSET is not None:
      file_object.seek(self._INITIAL_FILE_OFFSET, os.SEEK_SET)

    parser_mediator.AppendToParserChain(self.NAME)

    parser_chain = parser_mediator.GetParserChain()
    parser_mediator.SampleStartTiming(parser_chain)

    try:
      self.ParseFileObject(parser_mediator, file_object)

    finally:
      parser_mediator.SampleStopTiming(parser_chain)

      parser_mediator.PopFromParserChain()

  @abc.abstractmethod
  def ParseFileObject(self, parser_mediator, file_object):
    """Parses a file-like object.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      file_object (dfvfs.FileIO): a file-like object to parse.

    Raises:
      WrongParser: when the file cannot be parsed.
    """
