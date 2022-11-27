# -*- coding: utf-8 -*-
"""The parsers and plugins manager."""

import pysigscan

from plaso.filters import parser_filter
from plaso.lib import specification


class ParsersManager(object):
  """The parsers and plugins manager."""

  ALL_PLUGINS = set(['*'])

  _parser_classes = {}

  @classmethod
  def _GetParsers(cls, parser_filter_expression=None):
    """Retrieves the registered parsers and plugins.

    Args:
      parser_filter_expression (Optional[str]): parser filter expression,
          where None represents all parsers and plugins.

          A parser filter expression is a comma separated value string that
          denotes which parsers and plugins should be used. See
          filters/parser_filter.py for details of the expression syntax.

          This function does not support presets, and requires a parser
          filter expression where presets have been expanded.

    Yields:
      tuple: containing:

      * str: name of the parser:
      * type: parser class (subclass of BaseParser).
    """
    parser_filter_helper = parser_filter.ParserFilterExpressionHelper()
    excludes, includes = parser_filter_helper.SplitExpression(
        parser_filter_expression)

    for parser_name, parser_class in cls._parser_classes.items():
      # If there are no includes all parsers are included by default.
      if not includes and parser_name in excludes:
        continue

      if includes and parser_name not in includes:
        continue

      yield parser_name, parser_class

  @classmethod
  def CreateSignatureScanner(cls, specification_store):
    """Creates a signature scanner for format specifications with signatures.

    Args:
      specification_store (FormatSpecificationStore): format specifications
          with signatures.

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
  def CheckFilterExpression(cls, parser_filter_expression):
    """Checks parser and plugin names in a parser filter expression.

    Args:
      parser_filter_expression (str): parser filter expression,
          where None represents all parsers and plugins.

          A parser filter expression is a comma separated value string that
          denotes which parsers and plugins should be used. See
          filters/parser_filter.py for details of the expression syntax.

          This function does not support presets, and requires a parser filter
          expression where presets have been expanded.

    Returns:
      tuple: containing:

      * set(str): parser filter expression elements that contain known parser
          and/or plugin names.
      * set(str): parser filter expression elements that contain unknown parser
          and/or plugin names.
    """
    known_parser_elements = set()
    unknown_parser_elements = set()

    if not parser_filter_expression:
      for parser_name, parser_class in cls._parser_classes.items():
        known_parser_elements.add(parser_name)
        if parser_class.SupportsPlugins():
          for plugin_name in parser_class.GetPluginNames():
            known_parser_elements.add('/'.join([parser_name, plugin_name]))

    else:
      for element in parser_filter_expression.split(','):
        parser_expression = element
        if element.startswith('!'):
          parser_expression = element[1:]

        parser_name, _, plugin_name = parser_expression.partition('/')
        parser_class = cls._parser_classes.get(parser_name, None)
        if not parser_class:
          unknown_parser_elements.add(element)
          continue

        if parser_class.SupportsPlugins():
          plugins = dict(parser_class.GetPlugins())
          if not plugin_name:
            for plugin in plugins:
              known_parser_elements.add('/'.join([parser_name, plugin]))
          elif plugin_name in plugins:
            known_parser_elements.add(element)
          else:
            unknown_parser_elements.add(element)

        elif not plugin_name:
          known_parser_elements.add(element)

    return known_parser_elements, unknown_parser_elements

  @classmethod
  def DeregisterParser(cls, parser_class):
    """Deregisters a parser class.

    The parser classes are identified based on their lower case name.

    Args:
      parser_class (type): parser class (subclass of BaseParser).

    Raises:
      KeyError: if parser class is not set for the corresponding name.
    """
    parser_name = parser_class.NAME.lower()
    if parser_name not in cls._parser_classes:
      raise KeyError('Parser class not set for name: {0:s}.'.format(
          parser_class.NAME))

    del cls._parser_classes[parser_name]

  @classmethod
  def GetFormatsWithSignatures(cls, parser_filter_expression=None):
    """Retrieves the format specifications that have signatures.

    This method will create a specification store for parsers that define
    a format specification with signatures and a list of parser names for
    those that do not.

    Args:
      parser_filter_expression (Optional[str]): parser filter expression,
          where None represents all parsers and plugins.

          A parser filter expression is a comma separated value string that
          denotes which parsers and plugins should be used. See
          filters/parser_filter.py for details of the expression syntax.

          This function does not support presets, and requires a parser filter
          expression where presets have been expanded.

    Returns:
      tuple: containing:

      * FormatSpecificationStore: format specifications with signatures.
      * list[str]: names of parsers that do not have format specifications with
          signatures, or have signatures but also need to be applied 'brute
          force'.
    """
    specification_store = specification.FormatSpecificationStore()
    remainder_list = []

    for parser_name, parser_class in cls._GetParsers(
        parser_filter_expression=parser_filter_expression):
      format_specification = parser_class.GetFormatSpecification()

      if format_specification and format_specification.signatures:
        specification_store.AddSpecification(format_specification)
        # The plist parser is a special case, where it both defines a signature
        # and also needs to be applied 'brute-force' to non-matching files,
        # as the signature matches binary plists, but not XML or JSON plists.
        if parser_name == 'plist':
          remainder_list.append(parser_name)
      else:
        remainder_list.append(parser_name)

    return specification_store, remainder_list

  @classmethod
  def GetNamesOfParsersWithPlugins(cls):
    """Retrieves the names of all parsers with plugins.

    Returns:
      list[str]: names of all parsers with plugins.
    """
    parser_names = []

    for parser_name, parser_class in cls._GetParsers():
      if parser_class.SupportsPlugins():
        parser_names.append(parser_name)

    return sorted(parser_names)

  @classmethod
  def GetParserPluginsInformation(cls, parser_filter_expression=None):
    """Retrieves the parser plugins information.

    Args:
      parser_filter_expression (Optional[str]): parser filter expression,
          where None represents all parsers and plugins.

          A parser filter expression is a comma separated value string that
          denotes which parsers and plugins should be used. See
          filters/parser_filter.py for details of the expression syntax.

          This function does not support presets, and requires a parser
          filter expression where presets have been expanded.

    Returns:
      list[tuple[str, str]]: pairs of parser plugin names and descriptions.
    """
    parser_plugins_information = []
    for _, parser_class in cls._GetParsers(
        parser_filter_expression=parser_filter_expression):
      if parser_class.SupportsPlugins():
        for plugin_name, plugin_class in parser_class.GetPlugins():
          description = ''

          data_format = getattr(plugin_class, 'DATA_FORMAT', '')
          if data_format:
            if data_format.endswith(' file'):
              description = 'Parser for {0:s}s.'.format(data_format)
            else:
              description = 'Parser for {0:s}.'.format(data_format)

          parser_plugins_information.append((plugin_name, description))

    return parser_plugins_information

  @classmethod
  def GetParserObjects(cls, parser_filter_expression=None):
    """Retrieves the parser objects.

    Args:
      parser_filter_expression (Optional[str]): parser filter expression,
          where None represents all parsers and plugins.

          A parser filter expression is a comma separated value string that
          denotes which parsers and plugins should be used. See
          filters/parser_filter.py for details of the expression syntax.

          This function does not support presets, and requires a parser
          filter expression where presets have been expanded.

    Returns:
      dict[str, BaseParser]: parsers per name.
    """
    parser_filter_helper = parser_filter.ParserFilterExpressionHelper()
    excludes, includes = parser_filter_helper.SplitExpression(
        parser_filter_expression)

    parser_objects = {}
    for parser_name, parser_class in cls._parser_classes.items():
      # If there are no includes all parsers are included by default.
      if not includes and parser_name in excludes:
        continue

      if includes and parser_name not in includes:
        continue

      parser_object = parser_class()
      if parser_class.SupportsPlugins():
        plugin_includes = includes.get(parser_name, cls.ALL_PLUGINS)
        parser_object.EnablePlugins(plugin_includes)

      parser_objects[parser_name] = parser_object

    return parser_objects

  @classmethod
  def GetParsersInformation(cls):
    """Retrieves the parsers information.

    Returns:
      list[tuple[str, str]]: parser names and descriptions.
    """
    parsers_information = []
    for _, parser_class in cls._GetParsers():
      description = ''

      data_format = getattr(parser_class, 'DATA_FORMAT', '')
      if data_format:
        if data_format.endswith(' file'):
          description = 'Parser for {0:s}s.'.format(data_format)
        else:
          description = 'Parser for {0:s}.'.format(data_format)

      parsers_information.append((parser_class.NAME, description))

    return parsers_information

  @classmethod
  def RegisterParser(cls, parser_class):
    """Registers a parser class.

    The parser classes are identified based on their lower case name.

    Args:
      parser_class (type): parser class (subclass of BaseParser).

    Raises:
      KeyError: if parser class is already set for the corresponding name.
    """
    parser_name = parser_class.NAME.lower()
    if parser_name in cls._parser_classes:
      raise KeyError('Parser class already set for name: {0:s}.'.format(
          parser_class.NAME))

    cls._parser_classes[parser_name] = parser_class

  @classmethod
  def RegisterParsers(cls, parser_classes):
    """Registers parser classes.

    The parser classes are identified based on their lower case name.

    Args:
      parser_classes (list[type]): parsers classes (subclasses of BaseParser).

    Raises:
      KeyError: if parser class is already set for the corresponding name.
    """
    for parser_class in parser_classes:
      cls.RegisterParser(parser_class)
