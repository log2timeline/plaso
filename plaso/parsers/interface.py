# -*- coding: utf-8 -*-
"""The parsers and plugins interface classes."""

import abc
import os

from plaso.lib import errors


class BaseFileEntryFilter(object):
  """The file entry filter interface."""

  @abc.abstractmethod
  def Match(self, file_entry):
    """Determines if a file entry matches the filter.

    Args:
      file_entry: a file entry object (instance of dfvfs.FileEntry).

    Returns:
      A boolean value that indicates a match.
    """


class FileNameFileEntryFilter(BaseFileEntryFilter):
  """A file name file entry filter."""

  def __init__(self, filename):
    """Initializes a file entry filter object.

    Args:
      filename: string containing the name of the file.
    """
    super(FileNameFileEntryFilter, self).__init__()
    self._filename = filename.lower()

  def Match(self, file_entry):
    """Determines if a file entry matches the filter.

    Args:
      file_entry: a file entry object (instance of dfvfs.FileEntry).

    Returns:
      A boolean value that indicates a match.
    """
    if not file_entry:
      return False

    filename = file_entry.name.lower()
    return filename == self._filename


class BaseParser(object):
  """The parser interface."""

  NAME = u'base_parser'
  DESCRIPTION = u''

  # List of filters that should match for the parser to be applied.
  FILTERS = frozenset()

  # Every derived parser class that implements plugins should define
  # its own _plugin_classes dict:
  # _plugin_classes = {}

  # We deliberately don't define it here to make sure the plugins of
  # different parser classes don't end up in the same dict.
  _plugin_classes = None

  def __init__(self):
    """Initializes a parser object.

    By default all plugins will be enabled. To only enable specific plugins
    use the EnablePlugins method and pass it a list of strings containing
    the names of the plugins to enable.

    The default plugin, named "{self.NAME:s}_default", if it exists,
    is always enabled and cannot be disabled.
    """
    super(BaseParser, self).__init__()
    self._default_plugin = None
    self._plugin_objects = None
    self.EnablePlugins([])

  @classmethod
  def DeregisterPlugin(cls, plugin_class):
    """Deregisters a plugin class.

    The plugin classes are identified based on their lower case name.

    Args:
      plugin_class: the class object of the plugin.

    Raises:
      KeyError: if plugin class is not set for the corresponding name.
    """
    plugin_name = plugin_class.NAME.lower()
    if plugin_name not in cls._plugin_classes:
      raise KeyError(
          u'Plugin class not set for name: {0:s}.'.format(
              plugin_class.NAME))

    del cls._plugin_classes[plugin_name]

  def EnablePlugins(self, plugin_includes):
    """Enables parser plugins.

    Args:
      plugin_includes: a list of strings containing the names of the plugins
                       to enable, where None or an empty list represents all
                       plugins. Note the default plugin, if it exists, is
                       always enabled and cannot be disabled.
    """
    self._plugin_objects = []
    if not self._plugin_classes:
      return

    default_plugin_name = u'{0:s}_default'.format(self.NAME)
    for plugin_name, plugin_class in iter(self._plugin_classes.items()):
      if plugin_name == default_plugin_name:
        self._default_plugin = plugin_class()
        continue

      if plugin_includes and plugin_name not in plugin_includes:
        continue

      plugin_object = plugin_class()
      self._plugin_objects.append(plugin_object)

  # TODO: move this to a filter.
  @classmethod
  def GetFormatSpecification(cls):
    """Retrieves the format specification.

    Returns:
      The format specification (instance of FormatSpecification) or
      None if not available."""
    return

  @classmethod
  def GetPluginObjectByName(cls, plugin_name):
    """Retrieves a specific plugin object by its name.

    Args:
      plugin_name: the name of the plugin.

    Returns:
      A plugin object (instance of BasePlugin) or None.
    """
    plugin_class = cls._plugin_classes.get(plugin_name, None)
    if not plugin_class:
      return
    return plugin_class()

  @classmethod
  def GetPlugins(cls):
    """Retrieves the registered plugins.

    Yields:
      A tuple that contains the uniquely identifying name of the plugin
      and the plugin class (subclass of BasePlugin).
    """
    for plugin_name, plugin_class in iter(cls._plugin_classes.items()):
      yield plugin_name, plugin_class

  @classmethod
  def RegisterPlugin(cls, plugin_class):
    """Registers a plugin class.

    The plugin classes are identified based on their lower case name.

    Args:
      plugin_class: the class object of the plugin.

    Raises:
      KeyError: if plugin class is already set for the corresponding name.
    """
    plugin_name = plugin_class.NAME.lower()
    if plugin_name in cls._plugin_classes:
      raise KeyError((
          u'Plugin class already set for name: {0:s}.').format(
              plugin_class.NAME))

    cls._plugin_classes[plugin_name] = plugin_class

  @classmethod
  def RegisterPlugins(cls, plugin_classes):
    """Registers plugin classes.

    Args:
      plugin_classes: a list of class objects of the plugins.

    Raises:
      KeyError: if plugin class is already set for the corresponding name.
    """
    for plugin_class in plugin_classes:
      cls.RegisterPlugin(plugin_class)

  @classmethod
  def SupportsPlugins(cls):
    """Determines if a parser supports plugins.

    Returns:
      A boolean value indicating whether the parser supports plugins.
    """
    return cls._plugin_classes is not None


class FileEntryParser(BaseParser):
  """The file entry parser interface."""

  def Parse(self, parser_mediator, **kwargs):
    """Parsers the file entry and extracts event objects.

    Args:
      parser_mediator: a parser mediator object (instance of ParserMediator).

    Raises:
      UnableToParseFile: when the file cannot be parsed.
    """
    file_entry = parser_mediator.GetFileEntry()
    if not file_entry:
      raise errors.UnableToParseFile(u'Invalid file entry')

    parser_mediator.AppendToParserChain(self)
    try:
      self.ParseFileEntry(parser_mediator, file_entry, **kwargs)
    finally:
      parser_mediator.PopFromParserChain()

  @abc.abstractmethod
  def ParseFileEntry(self, parser_mediator, file_entry, **kwargs):
    """Parses a file entry.

    Args:
      parser_mediator: a parser mediator object (instance of ParserMediator).
      file_entry: a file entry object (instance of dfvfs.FileEntry).

    Raises:
      UnableToParseFile: when the file cannot be parsed.
    """


class FileObjectParser(BaseParser):
  """The file-like object parser interface."""

  # The initial file offset. Set this value to None if no initial
  # file offset seek needs to be performed.
  _INITIAL_FILE_OFFSET = 0

  def Parse(self, parser_mediator, file_object, **kwargs):
    """Parses a single file-like object.

    Args:
      parser_mediator: a parser mediator object (instance of ParserMediator).
      file_object: a file-like object to parse.

    Raises:
      UnableToParseFile: when the file cannot be parsed.
    """
    if not file_object:
      raise errors.UnableToParseFile(u'Invalid file object')

    if self._INITIAL_FILE_OFFSET is not None:
      file_object.seek(self._INITIAL_FILE_OFFSET, os.SEEK_SET)

    parser_mediator.AppendToParserChain(self)
    try:
      self.ParseFileObject(parser_mediator, file_object, **kwargs)
    finally:
      parser_mediator.PopFromParserChain()

  @abc.abstractmethod
  def ParseFileObject(self, parser_mediator, file_object, **kwargs):
    """Parses a file-like object.

    Args:
      parser_mediator: a parser mediator object (instance of ParserMediator).
      file_object: a file-like object.

    Raises:
      UnableToParseFile: when the file cannot be parsed.
    """
