# -*- coding: utf-8 -*-
"""Helper for parser and plugin filter expressions."""


class ParserFilterExpressionHelper(object):
  """Helper for parser and plugin filter expressions.

  A parser filter expression is a comma separated value string that denotes
  which parsers and plugins should be used. Each element can contain either:

  * The name of a preset (case sensitive), which is a predefined list of parsers
    and/or plugins (see data/presets.yaml for the default presets).
  * The name of a parser (case insensitive), for example 'msiecf'.
  * The name of a plugin, prefixed with the parser name and a '/', for example
    'sqlite/chrome_history'.

  If the element begins with an exclamation mark ('!') the item will be
  excluded from the set of enabled parsers and plugins, otherwise the element
  will be included.
  """

  def _GetParserAndPluginsList(self, parsers_and_plugins):
    """Flattens the parsers and plugins dictionary into a list.

    Args:
      parsers_and_plugins (dict[str, set[str]]): parsers and plugins.

    Returns:
      list[str]: alphabetically sorted list of the parsers and plugins.
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

    Note that exclusion takes precedence over inclusion.

    Args:
      excludes (dict[str, set[str]]): excluded parsers and plugins.
      includes (dict[str, set[str]]): included parsers and plugins.

    Returns:
      str: a parser filter expression.

        A parser filter expression is a comma separated value string that
        denotes which parsers should be used. Each element can contain either:

        * The name of a parser (case insensitive), for example 'msiecf'.
        * The name of a plugin, prefixed with the parser name and a '/', for
          example 'sqlite/chrome_history'.

        If the element begins with an exclamation mark ('!') the item will be
        excluded from the set of enabled parsers and plugins, otherwise the
        element will be included.

    Raises:
      RuntimeError: if a specific plugin is excluded but no corresponding parser
          is included.
    """
    excluded_parsers_and_plugins = self._GetParserAndPluginsList(excludes)
    included_parsers_and_plugins = self._GetParserAndPluginsList(includes)

    # Note that below set comprehension is used to determine the set of
    # excluded and included parsers.
    excluded_parsers = {
        name for name, plugins in excludes.items() if plugins != set(['*'])}
    included_parsers = {name for name, plugins in includes.items() if plugins}
    missing_parser_filters = excluded_parsers.difference(included_parsers)
    if missing_parser_filters:
      missing_parser_filters = self._GetParserAndPluginsList({
          name: excludes[name] for name in missing_parser_filters})
      raise RuntimeError((
          'Parser filters: {0:s} defined to be excluded but no corresponding '
          'include expression').format(','.join(missing_parser_filters)))

    overlapping_parser_filters = set(included_parsers_and_plugins).intersection(
        set(excluded_parsers_and_plugins))
    if overlapping_parser_filters:
      included_parsers_and_plugins = sorted(
          set(included_parsers_and_plugins) - overlapping_parser_filters)

    parser_filters = [
        '!{0:s}'.format(parser_filter)
        for parser_filter in excluded_parsers_and_plugins]
    parser_filters.extend(included_parsers_and_plugins)
    return ','.join(parser_filters)

  def _ExpandPreset(self, presets_manager, preset_name, parsers_and_plugins):
    """Expands a preset in the parsers and plugins.

    This functions replaces the preset in parsers_and_plugins with the parser
    and plugin or preset names defined by the preset.

    Args:
      presets_manager (ParserPresetsManager): a parser preset manager, that
          is used to resolve which parsers and/or plugins are defined by
          presets.
      preset_name (str): name of the preset to expand.
      parsers_and_plugins (dict[str, set[str]]): parsers, plugins and presets.

    Raises:
      RuntimeError: if the plugins list of a preset in parsers_and_plugins,
          contains plugin definitions other than '*'.
    """
    if preset_name not in parsers_and_plugins:
      return

    plugins = parsers_and_plugins.get(preset_name, None)
    if plugins != set(['*']):
      raise RuntimeError((
          '{0:s} cannot be used as a preset name and plugin name at '
          'same time.').format(preset_name))

    del parsers_and_plugins[preset_name]

    for parser_filter in presets_manager.GetParsersByPreset(preset_name):
      parser, _, plugin = parser_filter.partition('/')
      if not plugin:
        plugin = '*'

      parsers_and_plugins.setdefault(parser, set())
      parsers_and_plugins[parser].add(plugin)

  def _ExpandPresets(self, presets_manager, preset_names, parsers_and_plugins):
    """Expands the presets in the parsers and plugins.

    This functions replaces the presets in parsers_and_plugins with the parser
    and plugin or preset names defined by the presets.

    Args:
      presets_manager (ParserPresetsManager): a parser preset manager, that
          is used to resolve which parsers and/or plugins are defined by
          presets.
      preset_names (set[str]): names of the presets defined by the presets
          manager.
      parsers_and_plugins (dict[str, set[str]]): parsers, plugins and presets.
    """
    for preset_name in preset_names:
      self._ExpandPreset(presets_manager, preset_name, parsers_and_plugins)

  def ExpandPresets(self, presets_manager, expression):
    """Expands all presets in a parser filter expression.

    Args:
      presets_manager (ParserPresetsManager): a parser preset manager, that
          is used to resolve which parsers and/or plugins are defined by
          presets.
      expression (str): parser filter expression, where an empty expression
          represents all parsers and plugins.

          A parser filter expression is a comma separated value string that
          denotes which parsers and plugins should be used. Each element can be
          either:

          * The name of a preset (case sensitive), which is a predefined list of
            parsers and/or plugins (see data/presets.yaml for the default
            presets).
          * The name of a parser (case insensitive), for example 'msiecf'.
          * The name of a plugin, prefixed with the parser name and a '/', for
            example 'sqlite/chrome_history'.

          If the element begins with an exclamation mark ('!') the item will
          be excluded from the set of enabled parsers and plugins, otherwise
          the element will be included.

    Returns:
      str: a parser filter expression where presets have been expanded or None
          to represent all parsers and plugins.
    """
    if not expression:
      return None

    preset_names = set(presets_manager.GetNames())

    excludes, includes = self.SplitExpression(expression)

    while set(excludes.keys()).intersection(preset_names):
      self._ExpandPresets(presets_manager, preset_names, excludes)

    while set(includes.keys()).intersection(preset_names):
      self._ExpandPresets(presets_manager, preset_names, includes)

    return self._JoinExpression(excludes, includes)

  def SplitExpression(self, expression):
    """Determines the excluded and included elements in an expression string.

    This method will not expand presets, and preset names are treated like
    parser names.

    Args:
      expression (str): parser filter expression.

          A parser filter expression is a comma separated value string that
          denotes which parsers and plugins should be used. Each element can be
          either:

          * The name of a preset (case sensitive), which is a predefined list of
            parsers and/or plugins (see data/presets.yaml for the default
            presets).
          * The name of a parser (case insensitive), for example 'msiecf'.
          * The name of a plugin, prefixed with the parser name and a '/', for
            example 'sqlite/chrome_history'.

          If the element begins with an exclamation mark ('!') the item will
          be excluded from the set of enabled parsers and plugins, otherwise
          the element will be included.

    Returns:
      tuple: containing:

        excludes (dict[str, set[str]]): excluded presets, plugins and presets.
            Dictionary keys are preset and/or parser names, and values are
            sets containing plugin names to enable for a parser or an asterisk
            character ('*') to represent all plugins, or that no specific
            plugins were specified.
        includes (dict[str, set[str]]): included presets, parsers and plugins.
            Dictionary keys are preset and/or parser names, and values are
            sets containing plugin names to enable for a parser or an asterisk
            character ('*') to represent all plugins, or that no specific
            plugins were specified.
    """
    if not expression:
      return {}, {}

    excludes = {}
    includes = {}

    for expression_element in expression.split(','):
      expression_element = expression_element.strip()
      if not expression_element:
        continue

      expression_element = expression_element.lower()

      if expression_element.startswith('!'):
        expression_element = expression_element[1:]
        parsers_and_plugins = excludes
      else:
        parsers_and_plugins = includes

      parser, _, plugin = expression_element.partition('/')
      if not plugin:
        plugin = '*'

      parsers_and_plugins.setdefault(parser, set())
      parsers_and_plugins[parser].add(plugin)

    return excludes, includes
