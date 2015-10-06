# -*- coding: utf-8 -*-
"""The parsers and plugins manager objects."""

import pysigscan

from plaso.frontend import presets
from plaso.lib import specification


class ParsersManager(object):
  """Class that implements the parsers manager."""

  _parser_classes = {}

  @classmethod
  def DeregisterParser(cls, parser_class):
    """Deregisters a parser class.

    The parser classes are identified based on their lower case name.

    Args:
      parser_class: the class object of the parser.

    Raises:
      KeyError: if parser class is not set for the corresponding name.
    """
    parser_name = parser_class.NAME.lower()
    if parser_name not in cls._parser_classes:
      raise KeyError(u'Parser class not set for name: {0:s}.'.format(
          parser_class.NAME))

    del cls._parser_classes[parser_name]

  @classmethod
  def GetFilterListsFromString(cls, parser_filter_string):
    """Determines an include and exclude list of parser and plugin names.

    Takes a comma separated string and splits it up into two lists,
    of parsers, those to include and exclude from selection.

    If a particular filter is prepended with a minus sign it will
    be included in the exclude section, otherwise it is placed in the include.

    Args:
      parser_filter_string: The parser filter string.

    Returns:
      A tuple of two lists, include and exclude.
    """
    includes = []
    excludes = []

    if not parser_filter_string:
      return includes, excludes

    preset_categories = presets.categories.keys()

    for filter_string in parser_filter_string.split(u','):
      filter_string = filter_string.strip()
      if not filter_string:
        continue

      if filter_string.startswith(u'-'):
        active_list = excludes
        filter_string = filter_string[1:]
      else:
        active_list = includes

      filter_string = filter_string.lower()
      if filter_string in cls._parser_classes:
        parser_class = cls._parser_classes[filter_string]
        active_list.append(filter_string)

        if parser_class.SupportsPlugins():
          active_list.extend(parser_class.GetPluginNames())

      elif filter_string in preset_categories:
        active_list.extend(
            presets.GetParsersFromCategory(filter_string))

      else:
        active_list.append(filter_string)

    return includes, excludes

  @classmethod
  def GetParserFilterListsFromString(cls, parser_filter_string):
    """Determines an include and exclude list of parser names.

    Takes a comma separated string and splits it up into two lists,
    of parsers to include and to exclude from selection. If a particular
    filter is prepended with a minus sign it will be included in the
    exclude section, otherwise in the include.

    Args:
      parser_filter_string: The parser filter string.

    Returns:
      A tuple of two lists, include and exclude.
    """
    if not parser_filter_string:
      return [], []

    # Build the plugin to parser map, which cannot be a class member
    # otherwise the map will become invalid if a parser with plugins
    # is deregistered.
    plugin_to_parser_map = {}
    for parser_name, parser_class in cls._parser_classes.iteritems():
      if parser_class.SupportsPlugins():
        for plugin_name in parser_class.GetPluginNames():
          plugin_to_parser_map[plugin_name] = parser_name

    includes = set()
    excludes = set()

    preset_categories = presets.categories.keys()

    for filter_string in parser_filter_string.split(u','):
      filter_string = filter_string.strip()
      if not filter_string:
        continue

      if filter_string.startswith(u'-'):
        active_list = excludes
        filter_string = filter_string[1:]
      else:
        active_list = includes

      filter_string = filter_string.lower()
      if filter_string in cls._parser_classes:
        active_list.add(filter_string)

      elif filter_string in preset_categories:
        for entry in presets.GetParsersFromCategory(filter_string):
          active_list.add(plugin_to_parser_map.get(entry, entry))

      else:
        active_list.add(plugin_to_parser_map.get(
            filter_string, filter_string))

    return list(includes), list(excludes)

  @classmethod
  def GetParserNames(cls, parser_filter_string=None):
    """Retrieves the parser names.

    Args:
      parser_filter_string: Optional parser filter string, where None
                            represents all parsers and plugins.

    Returns:
      A list of parser names.
    """
    parser_names = []

    for parser_name, _ in cls.GetParsers(
        parser_filter_string=parser_filter_string):
      parser_names.append(parser_name)

    return sorted(parser_names)

  @classmethod
  def GetParserPluginsInformation(cls, parser_filter_string=None):
    """Retrieves the parser plugins information.

    Args:
      parser_filter_string: Optional parser filter string, where None
                            represents all parsers and plugins.

    Returns:
      A list of tuples of parser plugin names and descriptions.
    """
    parser_plugins_information = []
    for _, parser_class in cls.GetParsers(
        parser_filter_string=parser_filter_string):
      if parser_class.SupportsPlugins():
        for plugin_name, plugin_class in parser_class.GetPlugins():
          description = getattr(plugin_class, u'DESCRIPTION', u'')
          parser_plugins_information.append((plugin_name, description))

    return parser_plugins_information

  @classmethod
  def GetParserObjects(cls, parser_filter_string=None):
    """Retrieves the parser objects.

    Args:
      parser_filter_string: Optional parser filter string, where None
                            represents all parsers and plugins.

    Returns:
      A dictionary mapping parser names to parsers objects (instances of
      BaseParser).
    """
    parser_objects = {}

    for parser_name, parser_class in cls.GetParsers(
        parser_filter_string=parser_filter_string):
      parser_objects[parser_name] = parser_class()

    return parser_objects

  @classmethod
  def GetParsers(cls, parser_filter_string=None):
    """Retrieves the registered parsers.

    Retrieves a list of all registered parsers from a parser filter string.
    The filter string can contain direct names of parsers, presets or plugins.
    The filter string can also negate selection if prepended with a minus sign,
    eg: foo,-bar would include parser foo but not include parser bar.

    The three types of entries in the filter string:
     * name of a parser: this would be the exact name of a single parser to
       include (or exclude), eg: foo;
     * name of a preset, eg. win7: the presets are defined in
       plaso.frontend.presets;
     * name of a plugin: if a plugin name is included the parent parser will be
       included in the list of registered parsers;

    Args:
      parser_filter_string: Optional parser filter string, where None
                            represents all parsers and plugins.

    Yields:
      A tuple that contains the uniquely identifying name of the parser
      and the parser class (subclass of BaseParser).
    """
    parsers_to_include, parsers_to_exclude = cls.GetParserFilterListsFromString(
        parser_filter_string)

    # TODO: Add a warning in the case where an exclusion excludes a parser
    # that is also in the inclusion list, eg: user selects chrome_history but
    # excludes sqlite.
    for parser_name, parser_class in cls._parser_classes.iteritems():
      if parsers_to_exclude and parser_name in parsers_to_exclude:
        continue

      if parsers_to_include and parser_name not in parsers_to_include:
        continue

      yield parser_name, parser_class

  @classmethod
  def GetParsersInformation(cls):
    """Retrieves the parsers information.

    Returns:
      A list of tuples of parser names and descriptions.
    """
    parsers_information = []
    for _, parser_class in cls.GetParsers():
      description = getattr(parser_class, u'DESCRIPTION', u'')
      parsers_information.append((parser_class.NAME, description))

    return parsers_information

  @classmethod
  def GetNamesOfParsersWithPlugins(cls):
    """Retrieves the names of all parsers with plugins.

    Returns:
      A list of parser names.
    """
    parser_names = []

    for parser_name, parser_class in cls.GetParsers():
      if parser_class.SupportsPlugins():
        parser_names.append(parser_name)

    return sorted(parser_names)

  @classmethod
  def GetScanner(cls, specification_store):
    """Initializes the scanner object form the specification store.

    Args:
      specification_store: a specification store (instance of
                           FormatSpecificationStore).

    Returns:
      A scanner object (instance of pysigscan.scanner).
    """
    scanner_object = pysigscan.scanner()

    for format_specification in specification_store.specifications:
      for signature in format_specification.signatures:
        pattern_offset = signature.offset

        if pattern_offset is None:
          signature_flags = pysigscan.signature_flags.NO_OFFSET
        elif pattern_offset < 0:
          pattern_offset *= -1
          signature_flags = pysigscan.signature_flags.RELATIVE_FROM_END
        else:
          signature_flags = pysigscan.signature_flags.RELATIVE_FROM_START

        scanner_object.add_signature(
            signature.identifier, pattern_offset, signature.pattern,
            signature_flags)

    return scanner_object

  @classmethod
  def GetSpecificationStore(cls, parser_filter_string=None):
    """Retrieves the specification store for the parsers.

    This method will create a specification store for parsers that define
    a format specification and a list of parser names for those that do not.

    Args:
      parser_filter_string: Optional parser filter string, where None
                            represents all parsers and plugins.

    Returns:
      A tuple of a format specification store (instance of
      FormatSpecificationStore) and the list of remaining parser names
      that do not have a format specification.
    """
    specification_store = specification.FormatSpecificationStore()
    remainder_list = []

    for parser_name, parser_class in cls.GetParsers(
        parser_filter_string=parser_filter_string):
      format_specification = parser_class.GetFormatSpecification()

      if format_specification is not None:
        specification_store.AddSpecification(format_specification)
      else:
        remainder_list.append(parser_name)

    return specification_store, remainder_list

  @classmethod
  def GetWindowsRegistryPlugins(cls):
    """Build a list of all available Windows Registry plugins.

    Returns:
      A plugins list (instance of PluginList).
    """
    parser_class = cls._parser_classes.get(u'winreg', None)
    if not parser_class:
      return

    return parser_class.GetPluginList()

  @classmethod
  def RegisterParser(cls, parser_class):
    """Registers a parser class.

    The parser classes are identified based on their lower case name.

    Args:
      parser_class: the class object of the parser.

    Raises:
      KeyError: if parser class is already set for the corresponding name.
    """
    parser_name = parser_class.NAME.lower()
    if parser_name in cls._parser_classes:
      raise KeyError((u'Parser class already set for name: {0:s}.').format(
          parser_class.NAME))

    cls._parser_classes[parser_name] = parser_class

  @classmethod
  def RegisterParsers(cls, parser_classes):
    """Registers parser classes.

    The parser classes are identified based on their lower case name.

    Args:
      parser_classes: a list of class objects of the parsers.

    Raises:
      KeyError: if parser class is already set for the corresponding name.
    """
    for parser_class in parser_classes:
      cls.RegisterParser(parser_class)
