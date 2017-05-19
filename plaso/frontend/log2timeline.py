# -*- coding: utf-8 -*-
"""The log2timeline front-end."""

import logging
import sys

import plaso
# The following import makes sure the filters are registered.
from plaso import filters  # pylint: disable=unused-import
# The following import makes sure the analyzers are registered.
from plaso import analyzers  # pylint: disable=unused-import
# The following import makes sure the parsers are registered.
from plaso import parsers  # pylint: disable=unused-import
# The following import makes sure the output modules are registered.
from plaso import output  # pylint: disable=unused-import
from plaso.filters import manager as filters_manager
from plaso.frontend import extraction_frontend
from plaso.output import manager as output_manager


class LoggingFilter(logging.Filter):
  """Class that implements basic filtering of log events for plaso.

  Some libraries, like binplist, introduce excessive amounts of
  logging that clutters the debug logs of plaso, making them
  almost unusable. This class implements a filter designed to make
  the debug logs more clutter-free.
  """

  def filter(self, record):
    """Filter messages sent to the logging infrastructure."""
    if record.module == u'binplist' and record.levelno < logging.ERROR:
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
    for filter_object in sorted(
        filters_manager.FiltersManager.GetFilterObjects()):
      # TODO: refactor to use DESCRIPTION instead of docstring.
      doc_string, _, _ = filter_object.__doc__.partition(u'\n')
      filters_information.append((filter_object.filter_name, doc_string))

    return filters_information

  def _GetOutputModulesInformation(self):
    """Retrieves the output modules information.

    Returns:
      A list of tuples of output module names and descriptions.
    """
    output_modules_information = []
    for name, output_class in output_manager.OutputManager.GetOutputClasses():
      output_modules_information.append((name, output_class.DESCRIPTION))

    return output_modules_information

  def GetDisabledOutputClasses(self):
    """Retrieves the disabled output classes.

    Returns:
      An output module generator which yields tuples of output class names
      and type object.
    """
    return output_manager.OutputManager.GetDisabledOutputClasses()

  def GetOutputClasses(self):
    """Retrieves the available output classes.

    Returns:
      An output module generator which yields tuples of output class names
      and type object.
    """
    return output_manager.OutputManager.GetOutputClasses()

  def GetPluginData(self):
    """Retrieves the version and various plugin information.

    Returns:
      A dictionary object with lists of available parsers and plugins.
    """
    return_dict = {}

    return_dict[u'Versions'] = [
        (u'plaso engine', plaso.__version__),
        (u'python', sys.version)]

    return_dict[u'Hashers'] = self.GetHashersInformation()
    return_dict[u'Parsers'] = self.GetParsersInformation()
    return_dict[u'Parser Plugins'] = self.GetParserPluginsInformation()
    return_dict[u'Parser Presets'] = self.GetParserPresetsInformation()
    return_dict[u'Output Modules'] = self._GetOutputModulesInformation()
    return_dict[u'Filters'] = self._GetFiltersInformation()

    return return_dict
