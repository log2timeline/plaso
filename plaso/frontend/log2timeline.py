# -*- coding: utf-8 -*-
"""The log2timeline front-end."""

import logging
import sys

import plaso
# The following import makes sure the filters are registered.
from plaso import filters
# The following import makes sure the hashers are registered.
from plaso import hashers  # pylint: disable=unused-import
# The following import makes sure the parsers are registered.
from plaso import parsers  # pylint: disable=unused-import
# The following import makes sure the output modules are registered.
from plaso import output  # pylint: disable=unused-import
from plaso.frontend import extraction_frontend
from plaso.frontend import presets
from plaso.hashers import manager as hashers_manager
from plaso.parsers import manager as parsers_manager
from plaso.output import manager as output_manager


class LoggingFilter(logging.Filter):
  """Class that implements basic filtering of log events for plaso.

  Some libraries, like binplist, introduce excessive amounts of
  logging that clutters down the debug logs of plaso, making them
  almost non-usable. This class implements a filter designed to make
  the debug logs more clutter-free.
  """

  def filter(self, record):
    """Filter messages sent to the logging infrastructure."""
    if record.module == u'binplist' and record.levelno == logging.DEBUG:
      return False

    return True


class Log2TimelineFrontend(extraction_frontend.ExtractionFrontend):
  """Class that implements the log2timeline front-end."""

  def _GetFiltersInformation(self):
    """Retrieves the filters information.

    Returns:
      A list of tuples of filter names and docstrings.
    """
    filters_information = []
    for filter_object in sorted(filters.ListFilters()):
      # TODO: refactor to use DESCRIPTION instead of docstring.
      doc_string, _, _ = filter_object.__doc__.partition(u'\n')
      filters_information.append((filter_object.filter_name, doc_string))

    return filters_information

  def _GetHashersInformation(self):
    """Retrieves the hashers information.

    Returns:
      A list of tuples of hasher names and descriptions.
    """
    hashers_information = []
    for _, hasher_class in hashers_manager.HashersManager.GetHashers():
      description = getattr(hasher_class, u'DESCRIPTION', u'')
      hashers_information.append((hasher_class.NAME, description))

    return hashers_information

  def _GetOutputModulesInformation(self):
    """Retrieves the output modules information.

    Returns:
      A list of tuples of output module names and descriptions.
    """
    output_modules_information = []
    for name, description in sorted(output_manager.OutputManager.GetOutputs()):
      output_modules_information.append((name, description))

    return output_modules_information

  def _GetParsersInformation(self):
    """Retrieves the parsers information.

    Returns:
      A list of tuples of parser names and descriptions.
    """
    parsers_information = []
    for _, parser_class in parsers_manager.ParsersManager.GetParsers():
      description = getattr(parser_class, u'DESCRIPTION', u'')
      parsers_information.append((parser_class.NAME, description))

    return parsers_information

  def _GetParserPluginsInformation(self):
    """Retrieves the parser plugins information.

    Returns:
      A list of tuples of parser plugin names and descriptions.
    """
    parser_plugins_information = []
    for _, parser_class in parsers_manager.ParsersManager.GetParsers():
      if parser_class.SupportsPlugins():
        for _, plugin_class in parser_class.GetPlugins():
          description = getattr(plugin_class, u'DESCRIPTION', u'')
          parser_plugins_information.append((plugin_class.NAME, description))

    return parser_plugins_information

  def _GetParserPresetsInformation(self):
    """Retrieves the parser presets information.

    Returns:
      A list of tuples of parser preset names and related parsers names.
    """
    parser_presets_information = []
    for preset_name, parser_names in sorted(presets.categories.items()):
      parser_presets_information.append((preset_name, u', '.join(parser_names)))

    return parser_presets_information

  def GetPluginData(self):
    """Retrieves the version and various plugin information.

    Returns:
      A dictionary object with lists of available parsers and plugins.
    """
    return_dict = {}

    return_dict[u'Versions'] = [
        (u'plaso engine', plaso.GetVersion()),
        (u'python', sys.version)]

    return_dict[u'Hashers'] = self._GetHashersInformation()
    return_dict[u'Parsers'] = self._GetParsersInformation()
    return_dict[u'Parser Plugins'] = self._GetParserPluginsInformation()
    return_dict[u'Parser Presets'] = self._GetParserPresetsInformation()
    return_dict[u'Output Modules'] = self._GetOutputModulesInformation()
    return_dict[u'Filters'] = self._GetFiltersInformation()

    return return_dict
