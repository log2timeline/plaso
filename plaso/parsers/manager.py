# -*- coding: utf-8 -*-
"""The parsers and plugins manager."""

import logging
import pysigscan

from plaso.frontend import presets
from plaso.lib import specification


class ParsersManager(object):
  """Class that implements the parsers and plugins manager."""

  _parser_classes = {}
  parser_filter_string = None

  @classmethod
  def _CheckForIntersection(cls, includes, excludes):
    """Checks for parsers and plugins in both the inclusion and exclusion
    sets. If an intersection is found, the parser or plugin is removed from
    the inclusion set.

    Args:
      includes: the parsers and plugins to include
      excludes: the parsers and plugins to exclude
    """
    if includes and excludes:
      for matching_parser in set(includes) & set(excludes):
        # Check parser and plugin list for exact equivalence
        if includes[matching_parser] == excludes[matching_parser]:
          logging.warning(
              u'Parser {0:s} was in both the inclusion and exclusion lists. '
              u'Ignoring included parser.'.format(matching_parser))
          includes.pop(matching_parser)

        # Check if plugins are in both lists
        else:
          intersection = (
              set(includes[matching_parser]) &set(excludes[matching_parser]))
          if intersection:
            logging.warning(
                u'Plugin {0:s}/{1:s} was in both the inclusion and exclusion '
                u'lists. Ignoring included plugin.'.format(
                    matching_parser, list(intersection)))
            includes[matching_parser] = list(
                set(includes[matching_parser]) - intersection)

      # Check for unnecessary excluded parsers
      parser_to_pop = []
      for parser in excludes:
        if includes and parser not in includes:
          logging.warning(
              u'The excluded parser: {0:s} is not associated with the included '
              u'parsers {1:s}. Ignoring excluded parser.'.format(
                  parser, includes))
          parser_to_pop.append(parser)

      for parser in parser_to_pop:
        excludes.pop(parser)

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
  def GetFilterDicts(cls):
    """Determines an include and exclude dict of parser keys and associated
    plugins.

    Takes a comma separated string and splits it up into two dicts,
    of parsers and plugins to include and to exclude from selection. If a
    particular filter is prepended with an exclamation point it will be
    added to the exclude section, otherwise in the include.

    Returns:
      A tuple of two dicts, include and exclude.
    """
    if not cls.parser_filter_string:
      return {}, {}

    includes = {}
    excludes = {}

    preset_categories = presets.categories.keys()

    for filter_string in cls.parser_filter_string.split(u','):
      filter_string = filter_string.strip()
      if not filter_string:
        continue

      if filter_string.startswith(u'!'):
        active_dict = excludes
        filter_string = filter_string[1:]
      else:
        active_dict = includes

      filter_string = filter_string.lower()
      if filter_string in preset_categories:
        for entry in presets.GetParsersFromCategory(filter_string):
          parser, _, plugin = entry.partition(u'/')
          active_dict.setdefault(parser, [])
          if plugin:
            active_dict[parser].append(plugin)
      else:
        parser, _, plugin = filter_string.partition(u'/')
        active_dict.setdefault(parser, [])
        if plugin:
          active_dict[parser].append(plugin)

    cls._CheckForIntersection(includes, excludes)
    return includes, excludes

  @classmethod
  def GetParserPluginsInformation(cls):
    """Retrieves the parser plugins information.

    Returns:
      A list of tuples of parser plugin names and descriptions.
    """
    parser_plugins_information = []
    for _, parser_class in cls.GetParsers():
      if parser_class.SupportsPlugins():
        for plugin_name, plugin_class in parser_class.GetPlugins():
          description = getattr(plugin_class, u'DESCRIPTION', u'')
          parser_plugins_information.append((plugin_name, description))

    return parser_plugins_information

  @classmethod
  def GetParserObjectByName(cls, parser_name):
    """Retrieves a specific parser object by its name.

    Args:
      parser_name: the name of the parser.

    Returns:
      A parser object (instance of BaseParser) or None.
    """
    parser_class = cls._parser_classes.get(parser_name, None)
    if not parser_class:
      return
    return parser_class()

  @classmethod
  def GetParserObjects(cls):
    """Retrieves the parser objects.

    Returns:
      A dictionary mapping parser names to parsers objects (instances of
      BaseParser).
    """
    parser_objects = {}

    for parser_name, parser_class in cls.GetParsers():
      parser_objects[parser_name] = parser_class()

    return parser_objects

  @classmethod
  def GetParsers(cls, parser_filter_string=None):
    """Retrieves the registered parsers and plugins.

    Retrieves a dict of all registered parsers and associated plugins from a
    parser filter string. The filter string can contain direct names of
    parsers, presets or plugins. The filter string can also negate selection
    if prepended with an exclamation point,
    eg: foo,!foo/bar would include parser foo but not include plugin bar.
    A list of specific included and excluded plugins is also passed to each
    parser's class.

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
    if parser_filter_string:
      cls.SetParserFilterString(parser_filter_string=parser_filter_string)
    includes, excludes = cls.GetFilterDicts()

    for parser_name, parser_class in cls._parser_classes.iteritems():
      if (excludes and parser_name in excludes
          and not includes and not excludes[parser_name]):
        continue

      if includes and parser_name not in includes:
        continue

      parser_class.SetFilterLists(
          includes.get(parser_name, []), excludes.get(parser_name, []))
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

  @classmethod
  def SetParserFilterString(cls, parser_filter_string):
    """Sets the parser_filter_string class variable

    Args:
      parser_filter_string: the string to set as the parser_filter_string
      class variable
    """
    cls.parser_filter_string = parser_filter_string
