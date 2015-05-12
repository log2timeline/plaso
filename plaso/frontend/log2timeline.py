# -*- coding: utf-8 -*-
"""The log2timeline front-end."""

import logging
import sys

import plaso

# Registering output modules so that output bypass works.
from plaso import output as _  # pylint: disable=unused-import
from plaso.frontend import extraction_frontend
from plaso.hashers import manager as hashers_manager
from plaso.parsers import manager as parsers_manager


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

  def GetPluginData(self):
    """Return a dict object with a list of all available parsers and plugins."""
    return_dict = {}

    # Import all plugins and parsers to print out the necessary information.
    # This is not import at top since this is only required if this parameter
    # is set, otherwise these libraries get imported in their respected
    # locations.

    # The reason why some of these libraries are imported as '_' is to make sure
    # all appropriate parsers and plugins are registered, yet we don't need to
    # directly call these libraries, it is enough to load them up to get them
    # registered.

    # TODO: remove this hack includes should be a the top if this does not work
    # remove the need for implicit behavior on import.
    from plaso import filters
    from plaso import hashers as _  # pylint: disable=redefined-outer-name
    from plaso import parsers as _   # pylint: disable=redefined-outer-name
    from plaso import output as _  # pylint: disable=redefined-outer-name
    from plaso.frontend import presets
    from plaso.output import manager as output_manager

    return_dict[u'Versions'] = [
        (u'plaso engine', plaso.GetVersion()),
        (u'python', sys.version)]

    return_dict[u'Hashers'] = []
    for _, hasher_class in hashers_manager.HashersManager.GetHashers():
      description = getattr(hasher_class, u'DESCRIPTION', u'')
      return_dict[u'Hashers'].append((hasher_class.NAME, description))

    return_dict[u'Parsers'] = []
    for _, parser_class in parsers_manager.ParsersManager.GetParsers():
      description = getattr(parser_class, u'DESCRIPTION', u'')
      return_dict[u'Parsers'].append((parser_class.NAME, description))

    return_dict[u'Parser Lists'] = []
    for category, parsers in sorted(presets.categories.items()):
      return_dict[u'Parser Lists'].append((category, ', '.join(parsers)))

    return_dict[u'Output Modules'] = []
    for name, description in sorted(
        output_manager.OutputManager.GetOutputs()):
      return_dict[u'Output Modules'].append((name, description))

    return_dict[u'Plugins'] = []
    for _, parser_class in parsers_manager.ParsersManager.GetParsers():
      if parser_class.SupportsPlugins():
        for _, plugin_class in parser_class.GetPlugins():
          description = getattr(plugin_class, u'DESCRIPTION', u'')
          return_dict[u'Plugins'].append((plugin_class.NAME, description))

    return_dict[u'Filters'] = []
    for filter_obj in sorted(filters.ListFilters()):
      doc_string, _, _ = filter_obj.__doc__.partition('\n')
      return_dict[u'Filters'].append((filter_obj.filter_name, doc_string))

    return return_dict
