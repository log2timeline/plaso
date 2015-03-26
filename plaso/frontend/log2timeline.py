# -*- coding: utf-8 -*-
"""The log2timeline front-end."""

import logging
import sys

import plaso

# Registering output modules so that output bypass works.
from plaso import output as _  # pylint: disable=unused-import
from plaso.frontend import extraction_frontend
from plaso.frontend import frontend
from plaso.frontend import utils as frontend_utils
from plaso.hashers import manager as hashers_manager
from plaso.parsers import manager as parsers_manager

import pytz


class LoggingFilter(logging.Filter):
  """Class that implements basic filtering of log events for plaso.

  Some libraries, like binplist, introduce excessive amounts of
  logging that clutters down the debug logs of plaso, making them
  almost non-usable. This class implements a filter designed to make
  the debug logs more clutter-free.
  """

  def filter(self, record):
    """Filter messages sent to the logging infrastructure."""
    if record.module == 'binplist' and record.levelno == logging.DEBUG:
      return False

    return True


class Log2TimelineFrontend(extraction_frontend.ExtractionFrontend):
  """Class that implements the log2timeline front-end."""

  def __init__(self):
    """Initializes the front-end object."""
    input_reader = frontend.StdinFrontendInputReader()
    output_writer = frontend.StdoutFrontendOutputWriter()

    super(Log2TimelineFrontend, self).__init__(input_reader, output_writer)

  def _GetPluginData(self):
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

  def _GetTimeZones(self):
    """Returns a generator of the names of all the supported time zones."""
    yield 'local'
    for zone in pytz.all_timezones:
      yield zone

  def ListPluginInformation(self):
    """Lists all plugin and parser information."""
    plugin_list = self._GetPluginData()
    return_string_pieces = []

    return_string_pieces.append(
        u'{:=^80}'.format(u' log2timeline/plaso information. '))

    for header, data in plugin_list.items():
      # TODO: Using the frontend utils here instead of "self.PrintHeader"
      # since the desired output here is a string that can be sent later
      # to an output writer. Change this entire function so it can utilize
      # PrintHeader or something similar.
      return_string_pieces.append(frontend_utils.FormatHeader(header))
      for entry_header, entry_data in sorted(data):
        return_string_pieces.append(
            frontend_utils.FormatOutputString(entry_header, entry_data))

    return_string_pieces.append(u'')
    self._output_writer.Write(u'\n'.join(return_string_pieces))

  def ListTimeZones(self):
    """Lists the time zones."""
    self._output_writer.Write(u'=' * 40)
    self._output_writer.Write(u'       ZONES')
    self._output_writer.Write(u'-' * 40)
    for timezone in self._GetTimeZones():
      self._output_writer.Write(u'  {0:s}'.format(timezone))
    self._output_writer.Write(u'=' * 40)
