# -*- coding: utf-8 -*-
"""This file contains a class to provide a parsing framework to plaso.

This class contains a base framework class for parsing fileobjects, and
also some implementations that extend it to provide a more comprehensive
parser.
"""

import abc
import os

from plaso.lib import errors
from plaso.parsers import manager


class BaseFileEntryFilter(object):
  """Class that defines the file entry filter interface."""

  @abc.abstractmethod
  def Match(self, file_entry):
    """Determines if a file entry matches the filter.

    Args:
      file_entry: a file entry object (instance of dfvfs.FileEntry).

    Returns:
      A boolean value that indicates a match.
    """


class FileNameFileEntryFilter(BaseFileEntryFilter):
  """Class that defines a file name file entry filter."""

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
  """Class that defines the parser object interface."""

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

  # TOOD: move this to a filter.
  @classmethod
  def GetFormatSpecification(cls):
    """Retrieves the format specification.

    Returns:
      The format specification (instance of FormatSpecification) or
      None if not available."""
    return

  @classmethod
  def GetPluginNames(cls, parser_filter_string=None):
    """Retrieves the plugin names.

    Args:
      parser_filter_string: optional parser filter string.

    Returns:
      A list of plugin names.
    """
    plugin_names = []

    for plugin_name, _ in cls.GetPlugins(
        parser_filter_string=parser_filter_string):
      plugin_names.append(plugin_name)

    return sorted(plugin_names)

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
  def GetPluginObjects(cls, parser_filter_string=None):
    """Retrieves the plugin objects.

    Args:
      parser_filter_string: optional parser filter string.

    Returns:
      A list of plugin objects (instances of BasePlugin).
    """
    plugin_objects = []

    for _, plugin_class in cls.GetPlugins(
        parser_filter_string=parser_filter_string):
      plugin_object = plugin_class()
      plugin_objects.append(plugin_object)

    return plugin_objects

  @classmethod
  def GetPlugins(cls, parser_filter_string=None):
    """Retrieves the registered plugins.

    Args:
      parser_filter_string: optional parser filter string.

    Yields:
      A tuple that contains the uniquely identifying name of the plugin
      and the plugin class (subclass of BasePlugin).
    """
    if parser_filter_string:
      includes, excludes = manager.ParsersManager.GetFilterListsFromString(
          parser_filter_string)
    else:
      includes = None
      excludes = None

    for plugin_name, plugin_class in cls._plugin_classes.iteritems():
      if excludes and plugin_name in excludes:
        continue

      if includes and plugin_name not in includes:
        continue

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
  """Class that defines the file entry parser interface."""

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
  """Class that defines the file-like object parser interface."""

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
