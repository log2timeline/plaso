# -*- coding: utf-8 -*-
"""Helper for parser and plugin filter expressions."""

from __future__ import unicode_literals


class ParserFilterExpressionHelper(object):
  """Helper for parser and plugin filter expressions.

  A parser filter expression is a comma separated value string that denotes
  a list of parser names to include and/or exclude. Each entry can have
  the value of:

  * An exact match of a preset, which is a predefined list of parsers
    (see data/presets.yaml for the list of predefined presets).
  * A name of a single parser (case insensitive), e.g. msiecf.
  * A glob name for a single parser, e.g. '*msie*' (case insensitive).
  """

  def __init__(self, presets_manager):
    """Initializes a helper for parser and plugin filter expressions.

    Args:
      presets_manager (ParserPresetsManager): a parser preset manager.
    """
    super(ParserFilterExpressionHelper, self).__init__()
    self._presets_manager = presets_manager

  def _GetParserAndPluginsList(self, parsers_and_plugins):
    """Flattens the parsers and plugins dictionary into a list.

    Args:
      parsers_and_plugins (dict[str, set[str]]): parsers and plugins.

    Returns:
      list[str]: alphabetically sorted list of the parser and plugins.
    """
    parser_filters = []
    for parser_name, plugins in sorted(parsers_and_plugins.items()):
      for plugin_name in sorted(plugins):
        if plugin_name == '*':
          parser_filters.append(parser_name)
        else:
          parser_filters.append('/'.join([parser_name, plugin_name]))

    return parser_filters

  def _JoinExpression(self, excludes, includes):
    """Creates an expression string of the excluded and included parsers.

    Args:
      excludes (dict[str, set[str]]): excluded parsers and plugins.
      includes (dict[str, set[str]]): included parsers and plugins.

    Returns:
      str: a parser filter expression or None to represent all parsers and
           plugins.

    Raises:
      RuntimeError: if a specific plugin is excluded but no corresponding parser
          is included or if exclude and include parser filters overlap.
    """
    excluded_parser_filters = self._GetParserAndPluginsList(excludes)
    included_parser_filters = self._GetParserAndPluginsList(includes)

    # Note that below set comprehension is used to determine the set of
    # excluded and included parsers.
    excluded_parsers = {
        name for name, plugins in excludes.items() if plugins != set(['*'])}
    included_parsers = {
        name for name, plugins in includes.items() if '*' in plugins}
    missing_parser_filters = excluded_parsers.difference(included_parsers)
    if missing_parser_filters:
      missing_parser_filters = self._GetParserAndPluginsList({
          name:  excludes[name] for name in missing_parser_filters})
      raise RuntimeError((
          'Parser filters: {0:s} defined to be excluded but no corresponding '
          'include expression').format(','.join(missing_parser_filters)))

    overlapping_parser_filters = set(included_parser_filters).intersection(
        set(excluded_parser_filters))
    if overlapping_parser_filters:
      raise RuntimeError((
          'Parser filters: {0:s} defined to be both included and '
          'excludes').format(','.join(overlapping_parser_filters)))

    parser_filters = [
        '!{0:s}'.format(parser_filter)
        for parser_filter in excluded_parser_filters]
    parser_filters.extend(included_parser_filters)
    return ','.join(parser_filters)

  def _ExpandPreset(self, preset_name, parsers_and_plugins):
    """Expands a preset in the parsers and plugins.

    This functions replaces the preset in parsers_and_plugins with the parser
    and plugin or preset names defined by the preset.

    Args:
      preset_name (str): name of the peset to expand.
      parsers_and_plugins (dict[str, set[str]]): parsers and plugins.

    Raises:
      RuntimeError: if the preset in parsers_and_plugins has plugins.
    """
    if preset_name not in parsers_and_plugins:
      return

    plugins = parsers_and_plugins.get(preset_name, None)
    if plugins != set(['*']):
      print(plugins)
      raise RuntimeError('Unsupported preset: {0:s} with plugins.'.format(
          preset_name))

    del parsers_and_plugins[preset_name]

    for parser_filter in self._presets_manager.GetParsersByPreset(preset_name):
      parser, _, plugin = parser_filter.partition('/')
      if not plugin:
        plugin = '*'

      parsers_and_plugins.setdefault(parser, set())
      parsers_and_plugins[parser].add(plugin)

  def _ExpandPresets(self, preset_names, parsers_and_plugins):
    """Expands the presets in the parsers and plugins.

    This functions replaces the presets in parsers_and_plugins with the parser
    and plugin or preset names defined by the presets.

    Args:
      preset_names (set[str]): names of the presets defined by the presets
          manager.
      parsers_and_plugins (dict[str, set[str]]): parsers and plugins.
    """
    for preset_name in preset_names:
      self._ExpandPreset(preset_name, parsers_and_plugins)

  def ExpandPresets(self, expression):
    """Expands all presets in a parser filter expression.

    Args:
      expression (str): the parser filter expression, where None
          represents all parsers and plugins.

    Returns:
      str: a parser filter expression where presets have been expanded or None
          to represent all parsers and plugins.
    """
    preset_names = set(self._presets_manager.GetNames())

    excludes, includes = self.SplitExpression(expression)

    while set(excludes.keys()).intersection(preset_names):
      self._ExpandPresets(preset_names, excludes)

    while set(includes.keys()).intersection(preset_names):
      self._ExpandPresets(preset_names, includes)

    return self._JoinExpression(excludes, includes)

  def SplitExpression(self, expression):
    """Determines the excluded and included parsers form an expression string.

    Args:
      expression (str): the parser filter expression, where None
          represents all parsers and plugins.

    Returns:
      tuple: contains:

        excludes (dict[str, set[str]]): excluded parsers and plugins.
        includes (dict[str, set[str]]): included parsers and plugins.
    """
    if not expression:
      return {}, {}

    excludes = {}
    includes = {}

    for parser_filter in expression.split(','):
      parser_filter = parser_filter.strip()
      if not parser_filter:
        continue

      parser_filter = parser_filter.lower()

      if parser_filter.startswith('!'):
        parser_filter = parser_filter[1:]
        parsers_and_plugins = excludes
      else:
        parsers_and_plugins = includes

      parser, _, plugin = parser_filter.partition('/')
      if not plugin:
        plugin = '*'

      parsers_and_plugins.setdefault(parser, set())
      parsers_and_plugins[parser].add(plugin)

    return excludes, includes
