# -*- coding: utf-8 -*-
"""The parsers and plugins manager."""

import logging

import pysigscan

from plaso.lib import definitions
from plaso.lib import specification
from plaso.parsers import presets


class ParsersManager(object):
  """Class that implements the parsers and plugins manager."""

  _parser_classes = {}

  @classmethod
  def _GetParserFilters(cls, parser_filter_expression):
    """Retrieves the parsers and plugins to include and exclude.

    Takes a comma separated string and splits it up into two dictionaries,
    of parsers and plugins to include and to exclude from selection. If a
    particular filter is prepended with an exclamation point it will be
    added to the exclude section, otherwise in the include.

    Args:
      parser_filter_expression (str): parser filter expression, where None
          represents all parsers and plugins.

    Returns:
      A tuple containing dictionaries of the names of the included and
      excluded parsers and plugins. Where the keys contain the names of
      the parser and the corresponding value the names of the plugins.
    """
    if not parser_filter_expression:
      return {}, {}

    includes = {}
    excludes = {}

    preset_categories = presets.CATEGORIES.keys()

    for parser_filter in parser_filter_expression.split(u','):
      parser_filter = parser_filter.strip()
      if not parser_filter:
        continue

      if parser_filter.startswith(u'!'):
        parser_filter = parser_filter[1:]
        active_dict = excludes
      else:
        active_dict = includes

      parser_filter = parser_filter.lower()
      if parser_filter in preset_categories:
        for parser_in_category in cls._GetParsersFromPresetCategory(
            parser_filter):
          parser, _, plugin = parser_in_category.partition(u'/')
          active_dict.setdefault(parser, [])
          if plugin:
            active_dict[parser].append(plugin)

      else:
        parser, _, plugin = parser_filter.partition(u'/')
        active_dict.setdefault(parser, [])
        if plugin:
          active_dict[parser].append(plugin)

    cls._ReduceParserFilters(includes, excludes)
    return includes, excludes

  @classmethod
  def _GetParsersFromPresetCategory(cls, category):
    """Retrieves the parser names of specific preset category.

    Args:
      category (str): parser preset categories.

    Returns:
      list[str]: parser names in alphabetical order.
    """
    if category not in presets.CATEGORIES:
      return []

    parser_names = set()
    for element_name in presets.CATEGORIES.get(category):
      if element_name in presets.CATEGORIES:
        category_parser_names = cls._GetParsersFromPresetCategory(element_name)
        parser_names.update(category_parser_names)
      else:
        parser_names.add(element_name)

    return sorted(parser_names)

  @classmethod
  def _ReduceParserFilters(cls, includes, excludes):
    """Reduces the parsers and plugins to include and exclude.

    If an intersection is found, the parser or plugin is removed from
    the inclusion set. If a parser is not in inclusion set there is no need
    to have it in the exclusion set.

    Args:
      includes: a dictionary of the names of the parsers and plugins to include.
      excludes: a dictionary of the names of the parsers and plugins to exclude.
    """
    if not includes or not excludes:
      return

    for parser_name in set(includes).intersection(excludes):
      # Check parser and plugin list for exact equivalence.
      if includes[parser_name] == excludes[parser_name]:
        logging.warning(
            u'Parser {0:s} was in both the inclusion and exclusion lists. '
            u'Ignoring included parser.'.format(parser_name))
        includes.pop(parser_name)
        continue

      # Remove plugins that defined are in both inclusion and exclusion lists.
      plugin_includes = includes[parser_name]
      plugin_excludes = excludes[parser_name]
      intersection = set(plugin_includes).intersection(plugin_excludes)
      if not intersection:
        continue

      logging.warning(
          u'Parser {0:s} plugins: {1:s} in both the inclusion and exclusion '
          u'lists. Ignoring included plugins.'.format(
              parser_name, u', '.join(intersection)))
      plugins_list = list(set(plugin_includes).difference(intersection))
      includes[parser_name] = plugins_list

    # Remove excluded parsers that do not run.
    parsers_to_pop = []
    for parser_name in excludes:
      if parser_name in includes:
        continue

      logging.warning(
          u'The excluded parser: {0:s} is not associated with the included '
          u'parsers: {1:s}. Ignoring excluded parser.'.format(
              parser_name, u', '.join(includes.keys())))
      parsers_to_pop.append(parser_name)

    for parser_name in parsers_to_pop:
      excludes.pop(parser_name)

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
  def GetNamesOfParsersWithPlugins(cls):
    """Retrieves the names of all parsers with plugins.

    Returns:
      list[str]: names of all parsers with plugins.
    """
    parser_names = []

    for parser_name, parser_class in cls.GetParsers():
      if parser_class.SupportsPlugins():
        parser_names.append(parser_name)

    return sorted(parser_names)

  @classmethod
  def GetParserAndPluginNames(cls, parser_filter_expression=None):
    """Retrieves the parser and parser plugin names.

    Args:
      parser_filter_expression (Optional[str]): parser filter expression,
          where None represents all parsers and plugins.

    Returns:
      list[str]: parser and parser plugin names.
    """
    parser_and_plugin_names = []
    for parser_name, parser_class in cls.GetParsers(
        parser_filter_expression=parser_filter_expression):
      parser_and_plugin_names.append(parser_name)

      if parser_class.SupportsPlugins():
        for plugin_name, _ in parser_class.GetPlugins():
          parser_and_plugin_names.append(
              u'{0:s}/{1:s}'.format(parser_name, plugin_name))

    return parser_and_plugin_names

  @classmethod
  def GetParserPluginsInformation(cls, parser_filter_expression=None):
    """Retrieves the parser plugins information.

    Args:
      parser_filter_expression (Optional[str]): parser filter expression,
          where None represents all parsers and plugins.

    Returns:
      list[tuple[str, str]]: pairs of parser plugin names and descriptions.
    """
    parser_plugins_information = []
    for _, parser_class in cls.GetParsers(
        parser_filter_expression=parser_filter_expression):
      if parser_class.SupportsPlugins():
        for plugin_name, plugin_class in parser_class.GetPlugins():
          description = getattr(plugin_class, u'DESCRIPTION', u'')
          parser_plugins_information.append((plugin_name, description))

    return parser_plugins_information

  # Note this method is used by l2tpreg.
  @classmethod
  def GetParserObjectByName(cls, parser_name):
    """Retrieves a specific parser object by its name.

    Args:
      parser_name (str): name of the parser.

    Returns:
      BaseParser: parser object or None.
    """
    parser_class = cls._parser_classes.get(parser_name, None)
    if parser_class:
      return parser_class()

  @classmethod
  def GetParserObjects(cls, parser_filter_expression=None):
    """Retrieves the parser objects.

    Args:
      parser_filter_expression (Optional[str]): parser filter expression,
          where None represents all parsers and plugins.

    Returns:
      dict[str, BaseParser]: parsers per name.
    """
    includes, excludes = cls._GetParserFilters(parser_filter_expression)

    parser_objects = {}
    for parser_name, parser_class in iter(cls._parser_classes.items()):
      # If there are no includes all parsers are included by default.
      if not includes and parser_name in excludes:
        continue

      if includes and parser_name not in includes:
        continue

      parser_object = parser_class()
      if parser_class.SupportsPlugins():
        plugin_includes = None
        if parser_name in includes:
          plugin_includes = includes[parser_name]

        parser_object.EnablePlugins(plugin_includes)

      parser_objects[parser_name] = parser_object

    return parser_objects

  @classmethod
  def GetParsers(cls, parser_filter_expression=None):
    """Retrieves the registered parsers and plugins.

    Retrieves a dictionary of all registered parsers and associated plugins
    from a parser filter string. The filter string can contain direct names of
    parsers, presets or plugins. The filter string can also negate selection
    if prepended with an exclamation point, e.g.: "foo,!foo/bar" would include
    parser foo but not include plugin bar. A list of specific included and
    excluded plugins is also passed to each parser's class.

    The three types of entries in the filter string:
     * name of a parser: this would be the exact name of a single parser to
       include (or exclude), e.g. foo;
     * name of a preset, e.g. win7: the presets are defined in
       plaso.frontend.presets;
     * name of a plugin: if a plugin name is included the parent parser will be
       included in the list of registered parsers;

    Args:
      parser_filter_expression (Optional[str]): parser filter expression,
          where None represents all parsers and plugins.

    Yields:
      A tuple that contains the uniquely identifying name of the parser
      and the parser class (subclass of BaseParser).
    """
    includes, excludes = cls._GetParserFilters(parser_filter_expression)

    for parser_name, parser_class in iter(cls._parser_classes.items()):
      # If there are no includes all parsers are included by default.
      if not includes and parser_name in excludes:
        continue

      if includes and parser_name not in includes:
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
  def GetPresetForOperatingSystem(
      cls, operating_system, operating_system_product,
      operating_system_version):
    """Determines the preset for a specific operating system.

    Args:
      operating_system (str): operating system for example "Windows". This
          should be one of the values in definitions.OPERATING_SYSTEMS.
      operating_system_product (str): operating system product for
          example "Windows XP" as determined by preprocessing.
      operating_system_version (str): operating system version for
          example "5.1" as determined by preprocessing.

    Returns:
      str: parser filter preset, where None represents all parsers and plugins.
    """
    # TODO: Make this more sane. Currently we are only checking against
    # one possible version of Windows, and then making the assumption if
    # that is not correct we default to Windows 7. Same thing with other
    # OS's, no assumption or checks are really made there.
    # Also this is done by default, and no way for the user to turn off
    # this behavior, need to add a parameter to the frontend that takes
    # care of overwriting this behavior.

    if operating_system == definitions.OPERATING_SYSTEM_LINUX:
      return u'linux'

    if operating_system == definitions.OPERATING_SYSTEM_MACOSX:
      return u'macosx'

    if operating_system_product:
      operating_system_product = operating_system_product.lower()
    else:
      operating_system_product = u''

    if operating_system_version:
      operating_system_version = operating_system_version.split(u'.')
    else:
      operating_system_version = [u'0', u'0']

    # Windows NT 5 (2000, XP and 2003).
    if (u'windows' in operating_system_product and
        operating_system_version[0] == u'5'):
      return u'winxp'

    # TODO: Improve this detection, this should be more 'intelligent', since
    # there are quite a lot of versions out there that would benefit from
    # loading up the set of 'winxp' parsers.
    if (u'windows xp' in operating_system_product or
        u'windows server 2000' in operating_system_product or
        u'windows server 2003' in operating_system_product):
      return u'winxp'

    # Fallback for other Windows versions.
    if u'windows' in operating_system_product:
      return u'win7'

    if operating_system == definitions.OPERATING_SYSTEM_WINDOWS:
      return u'win7'

  @classmethod
  def GetScanner(cls, specification_store):
    """Initializes a signature scanner form a specification store.

    Args:
      specification_store (FormatSpecificationStore): specification store.

    Returns:
      pysigscan.scanner: signature scanner.
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
  def GetSpecificationStore(cls, parser_filter_expression=None):
    """Retrieves the specification store for the parsers.

    This method will create a specification store for parsers that define
    a format specification and a list of parser names for those that do not.

    Args:
      parser_filter_expression (Optional[str]): parser filter expression,
          where None represents all parsers and plugins.

    Returns:
      A tuple of a format specification store (instance of
      FormatSpecificationStore) and the list of remaining parser names
      that do not have a format specification.
    """
    specification_store = specification.FormatSpecificationStore()
    remainder_list = []

    for parser_name, parser_class in cls.GetParsers(
        parser_filter_expression=parser_filter_expression):
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
      raise KeyError(u'Parser class already set for name: {0:s}.'.format(
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
