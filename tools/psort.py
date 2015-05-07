#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Psort (Plaso Síar Og Raðar Þessu) - Makes output from Plaso Storage files.

Sample Usage:
  psort.py /tmp/mystorage.dump "date > '01-06-2012'"

See additional details here: http://plaso.kiddaland.net/usage/psort
"""

import argparse
import datetime
import multiprocessing
import logging
import pdb
import sys
import time

from plaso import filters
# TODO: remove after psort options refactor.
from plaso.analysis import interface as analysis_interface
from plaso.cli import analysis_tool
from plaso.cli.helpers import manager as helpers_manager
from plaso.frontend import psort
from plaso.frontend import utils as frontend_utils
from plaso.lib import errors
from plaso.winnt import language_ids

import pytz


class PsortTool(analysis_tool.AnalysisTool):
  """Class that implements the psort CLI tool."""

  _URL = u'http://plaso.kiddaland.net/usage/filters'

  NAME = u'psort'
  DESCRIPTION = (
      u'Application to read, filter and process output from a plaso storage '
      u'file.')

  def __init__(self, input_reader=None, output_writer=None):
    """Initializes the CLI tool object.

    Args:
      input_reader: the input reader (instance of InputReader).
                    The default is None which indicates the use of the stdin
                    input reader.
      output_writer: the output writer (instance of OutputWriter).
                     The default is None which indicates the use of the stdout
                     output writer.
    """
    super(PsortTool, self).__init__(
        input_reader=input_reader, output_writer=output_writer)
    self._analysis_plugins = None
    self._analysis_plugins_output_format = None
    self._deduplicate_events = True
    self._filter_expression = None
    self._filter_object = None
    self._front_end = psort.PsortFrontend()
    # TODO: remove after psort options refactor.
    self._options = None
    self._output_format = None
    self._quiet_mode = False
    self._time_slice_event_time_string = None
    self._time_slice_duration = 5
    self._use_time_slicer = False

    self.list_analysis_plugins = False
    self.list_language_identifiers = False
    self.list_output_modules = False

  def _ParseAnalysisPluginOptions(self, options):
    """Parses the analysis plugin options.

    Args:
      options: the command line arguments (instance of argparse.Namespace).
    """
    self._analysis_plugins = getattr(options, u'analysis_plugins', u'')
    self._analysis_plugins_output_format = getattr(
        options, u'windows-services-output', u'text')

  def _ParseFilterOptions(self, options):
    """Parses the filter options.

    Args:
      options: the command line arguments (instance of argparse.Namespace).

    Raises:
      BadConfigOption: if the options are invalid.
    """
    self._filter_expression = getattr(options, u'filter', None)
    if self._filter_expression:
      self._filter_object = filters.GetFilter(self._filter_expression)
      if not self._filter_object:
        raise errors.BadConfigOption(
            u'Invalid filter expression: {0:s}'.format(self._filter_expression))

    self._time_slice_event_time_string = getattr(options, u'slice', None)
    self._time_slice_duration = getattr(options, u'slice_size', 5)
    self._use_time_slicer = getattr(options, u'slicer', False)

    # The slice and slicer cannot be set at the same time.
    if self._time_slice_event_time_string and self._use_time_slicer:
      raise errors.BadConfigOption(
          u'Time slice and slicer cannot be used at the same time.')

  def _ParseInformationalOptions(self, options):
    """Parses the informational options.

    Args:
      options: the command line arguments (instance of argparse.Namespace).

    Raises:
      BadConfigOption: if the options are invalid.
    """
    super(PsortTool, self)._ParseInformationalOptions(options)

    self._quiet_mode = getattr(options, u'quiet', False)

  def _ParseLanguageOptions(self, options):
    """Parses the language options.

    Args:
      options: the command line arguments (instance of argparse.Namespace).
    """
    preferred_language = getattr(options, u'preferred_language', u'en-US')
    if preferred_language == u'list':
      self.list_language_identifiers = True
    else:
      self._preferred_language = preferred_language

  def _ProcessStorage(self):
    """Processes a plaso storage file.

    Raises:
      RuntimeError: if a non-recoverable situation is encountered.
    """
    time_slice = None
    if self._time_slice_event_time_string is not None or self._use_time_slicer:
      time_slice = self._front_end.GetTimeSlice(
          self._time_slice_event_time_string,
          duration=self._time_slice_duration, timezone=self._timezone)

    counter = self._front_end.ProcessStorage(
        self._options, self._analysis_plugins,
        self._analysis_plugins_output_format,
        deduplicate_events=self._deduplicate_events,
        preferred_encoding=self.preferred_encoding,
        time_slice=time_slice, timezone=self._timezone,
        use_time_slicer=self._use_time_slicer)

    if not self._quiet_mode:
      logging.info(frontend_utils.FormatHeader(u'Counter'))
      for element, count in counter.most_common():
        # TODO: replace by self._output_writer.Write().
        logging.info(frontend_utils.FormatOutputString(element, count))

  def AddAnalysisPluginOptions(self, argument_group, plugin_names):
    """Adds the analysis plugin options to the argument group

    Args:
      argument_group: The argparse argument group (instance of
                      argparse._ArgumentGroup).
      plugin_names: a string containing comma separated analysis plugin names.

    Raises:
      BadConfigOption: if non-existing analysis plugin names are specified.
    """
    if plugin_names == u'list':
      return

    plugin_list = set([
        name.strip().lower() for name in plugin_names.split(u',')])

    # Get a list of all available plugins.
    analysis_plugins = self._front_end.GetAnalysisPlugins()
    analysis_plugins = set([name.lower() for name, _, _ in analysis_plugins])

    # Get a list of the selected plugins (ignoring selections that did not
    # have an actual plugin behind it).
    plugins_to_load = analysis_plugins.intersection(plugin_list)

    # Check to see if we are trying to load plugins that do not exist.
    difference = plugin_list.difference(analysis_plugins)
    if difference:
      raise errors.BadConfigOption(
          u'Non-existing analysis plugins specified: {0:s}'.format(
              u' '.join(difference)))

    plugins = self._front_end.LoadPlugins(plugins_to_load, None)
    for plugin in plugins:
      if plugin.ARGUMENTS:
        for parameter, config in plugin.ARGUMENTS:
          argument_group.add_argument(parameter, **config)

  def AddFilterOptions(self, argument_group):
    """Adds the filter options to the argument group.

    Args:
      argument_group: The argparse argument group (instance of
                      argparse._ArgumentGroup).
    """
    argument_group.add_argument(
        u'--slice', metavar=u'DATE', dest=u'slice', type=str,
        default=u'', action=u'store', help=(
            u'Create a time slice around a certain date. This parameter, if '
            u'defined will display all events that happened X minutes before '
            u'and after the defined date. X is controlled by the parameter '
            u'--slice_size but defaults to 5 minutes.'))

    argument_group.add_argument(
        u'--slice_size', dest=u'slice_size', type=int, default=5,
        action=u'store', help=(
            u'Defines the slice size. In the case of a regular time slice it '
            u'defines the number of minutes the slice size should be. In the '
            u'case of the --slicer it determines the number of events before '
            u'and after a filter match has been made that will be included in '
            u'the result set. The default value is 5]. See --slice or --slicer '
            u'for more details about this option.'))

    argument_group.add_argument(
        u'--slicer', dest=u'slicer', action=u'store_true', default=False, help=(
            u'Create a time slice around every filter match. This parameter, '
            u'if defined will save all X events before and after a filter '
            u'match has been made. X is defined by the --slice_size '
            u'parameter.'))

    argument_group.add_argument(
        u'filter', nargs=u'?', action=u'store', metavar=u'FILTER', default=None,
        type=unicode, help=(
            u'A filter that can be used to filter the dataset before it '
            u'is written into storage. More information about the filters '
            u'and how to use them can be found here: {0:s}').format(self._URL))

  def AddInformationalOptions(self, argument_group):
    """Adds the informational options to the argument group.

    Args:
      argument_group: The argparse argument group (instance of
                      argparse._ArgumentGroup).
    """
    super(PsortTool, self).AddInformationalOptions(argument_group)

    argument_group.add_argument(
        u'-q', u'--quiet', action=u'store_true', dest=u'quiet', default=False,
        help=u'Do not print a summary after processing.')

  def AddLanguageOptions(self, argument_group):
    """Adds the language options to the argument group.

    Args:
      argument_group: The argparse argument group (instance of
                      argparse._ArgumentGroup).
    """
    argument_group.add_argument(
        u'--language', metavar=u'LANGUAGE', dest=u'preferred_language',
        default=u'en-US', type=unicode, help=(
            u'The preferred language identifier for Windows Event Log message '
            u'strings. Use "--language list" to see a list of available '
            u'language identifiers. Note that formatting will fall back on '
            u'en-US (LCID 0x0409) if the preferred language is not available '
            u'in the database of message string templates.'))

  # TODO: improve the description of module_names.
  def AddOutputModuleOptions(self, argument_group, module_names):
    """Adds the output module options to the argument group

    Args:
      argument_group: The argparse argument group (instance of
                      argparse._ArgumentGroup).
      module_names: a string containing comma separated output module names.
    """
    if module_names == u'list':
      return

    helpers_manager.ArgumentHelperManager.AddCommandLineArguments(
        argument_group, u'output')

    # TODO: Remove this once all output modules have been transitioned
    # into the CLI argument helpers.
    modules_list = set([name.lower() for name in module_names])

    for name, output_class in self._front_end.GetOutputClasses():
      if not name.lower() in modules_list:
        continue

      if output_class.ARGUMENTS:
        for parameter, config in output_class.ARGUMENTS:
          argument_group.add_argument(parameter, **config)

  def ListAnalysisPlugins(self):
    """Lists the analysis modules."""
    self.PrintHeader(u'Analysis Plugins')
    format_length = 10
    analysis_plugins = self._front_end.GetAnalysisPlugins()

    for name, _, _ in analysis_plugins:
      if len(name) > format_length:
        format_length = len(name)

    # TODO: refactor to use type object (class) and add GetTypeString method.
    for name, description, plugin_type in analysis_plugins:
      if plugin_type == analysis_interface.AnalysisPlugin.TYPE_ANNOTATION:
        type_string = u'Annotation/tagging plugin'
      elif plugin_type == analysis_interface.AnalysisPlugin.TYPE_ANOMALY:
        type_string = u'Anomaly plugin'
      elif plugin_type == analysis_interface.AnalysisPlugin.TYPE_REPORT:
        type_string = u'Summary/Report plugin'
      elif plugin_type == analysis_interface.AnalysisPlugin.TYPE_STATISTICS:
        type_string = u'Statistics plugin'
      else:
        type_string = u'Unknown type'

      description = u'{0:s} [{1:s}]'.format(description, type_string)
      self.PrintColumnValue(name, description, format_length)
    self.PrintSeparatorLine()

  def ListLanguageIdentifiers(self):
    """Lists the language identifiers."""
    self.PrintHeader(u'Language identifiers')
    self.PrintColumnValue(u'Identifier', u'Language')
    for language_id, value_list in sorted(
        language_ids.LANGUAGE_IDENTIFIERS.items()):
      self.PrintColumnValue(language_id, value_list[1])

  def ListOutputModules(self):
    """Lists the output modules."""
    self.PrintHeader(u'Output Modules')
    for name, output_class in self._front_end.GetOutputClasses():
      self.PrintColumnValue(name, output_class.DESCRIPTION, 10)
    self.PrintSeparatorLine()

  def ListTimeZones(self):
    """Lists the timezones."""
    self.PrintHeader(u'Zones')
    max_length = 0
    for zone in pytz.all_timezones:
      if len(zone) > max_length:
        max_length = len(zone)

    self.PrintColumnValue(u'Timezone', u'UTC Offset', max_length)
    for zone in pytz.all_timezones:
      zone_obj = pytz.timezone(zone)
      date_str = unicode(zone_obj.localize(datetime.datetime.utcnow()))
      if u'+' in date_str:
        _, _, diff = date_str.rpartition(u'+')
        diff_string = u'+{0:s}'.format(diff)
      else:
        _, _, diff = date_str.rpartition(u'-')
        diff_string = u'-{0:s}'.format(diff)
      self.PrintColumnValue(zone, diff_string, max_length)
    self.PrintSeparatorLine()

  def ParseArguments(self):
    """Parses the command line arguments.

    Returns:
      A boolean value indicating the arguments were successfully parsed.
    """
    logging.basicConfig(
        level=logging.INFO, format=u'[%(levelname)s] %(message)s')

    argument_parser = argparse.ArgumentParser(
        description=self.DESCRIPTION, add_help=False)

    self.AddBasicOptions(argument_parser)
    self.AddStorageFileOptions(argument_parser)

    analysis_group = argument_parser.add_argument_group(u'Analysis Arguments')

    analysis_group.add_argument(
        u'--analysis', metavar=u'PLUGIN_LIST', dest=u'analysis_plugins',
        default=u'', action=u'store', type=unicode, help=(
            u'A comma separated list of analysis plugin names to be loaded '
            u'or "--analysis list" to see a list of available plugins.'))

    info_group = argument_parser.add_argument_group(u'Informational Arguments')

    self.AddInformationalOptions(info_group)

    filter_group = argument_parser.add_argument_group(u'Filter Arguments')

    self.AddFilterOptions(filter_group)

    input_group = argument_parser.add_argument_group(u'Input Arguments')

    self.AddDataLocationOption(input_group)

    output_group = argument_parser.add_argument_group(u'Output Arguments')

    output_group.add_argument(
        u'-a', u'--include_all', action=u'store_false', dest=u'dedup',
        default=True, help=(
            u'By default the psort removes duplicate entries from the '
            u'output. This parameter changes that behavior so all events '
            u'are included.'))

    self.AddLanguageOptions(output_group)

    output_group.add_argument(
        u'-o', u'--output_format', u'--output-format', metavar=u'FORMAT',
        dest=u'output_format', default=u'dynamic', help=(
            u'The output format. Use "-o list" to see a list of available '
            u'output formats.'))

    output_group.add_argument(
        u'-w', u'--write', metavar=u'OUTPUTFILE', dest=u'write',
        help=u'Output filename, defaults to stdout.')

    output_group.add_argument(
        u'-z', u'--zone', metavar=u'TIMEZONE', dest=u'timezone', default=u'UTC',
        type=unicode, help=(
            u'The timezone in which to represent the date and time values. '
            u'Use "-z list" to see a list of available timezones.'))

    # TODO: refactor how arguments is used in a more argparse way.
    arguments = sys.argv[1:]

    # Add the output module options.
    if u'-o' in arguments:
      argument_index = arguments.index(u'-o') + 1
    elif u'--output_format' in arguments:
      argument_index = arguments.index(u'--output_format') + 1
    elif u'--output-format' in arguments:
      argument_index = arguments.index(u'--output-format') + 1
    else:
      argument_index = 0

    if argument_index > 0:
      module_names = arguments[argument_index]
      if module_names == u'list':
        self.list_output_modules = True
      else:
        self.AddOutputModuleOptions(output_group, [module_names])

    # Add the analysis plugin options.
    if u'--analysis' in arguments:
      argument_index = arguments.index(u'--analysis') + 1

      # Get the names of the analysis plugins that should be loaded.
      plugin_names = arguments[argument_index]
      if plugin_names == u'list':
        self.list_analysis_plugins = True
      else:
        try:
          self.AddAnalysisPluginOptions(analysis_group, plugin_names)
        except errors.BadConfigOption as exception:
          self._output_writer.Write(u'\n')
          self._output_writer.Write(argument_parser.format_help())
          return False

    try:
      # TODO: refactor how arguments is used in a more argparse way.
      options = argument_parser.parse_args(args=arguments)
    except UnicodeEncodeError:
      # If we get here we are attempting to print help in a non-Unicode
      # terminal.
      self._output_writer.Write(u'\n')
      self._output_writer.Write(argument_parser.format_help())
      return False

    # Properly prepare the attributes according to local encoding.
    if self.preferred_encoding == u'ascii':
      logging.warning(
          u'The preferred encoding of your system is ASCII, which is not '
          u'optimal for the typically non-ASCII characters that need to be '
          u'parsed and processed. The tool will most likely crash and die, '
          u'perhaps in a way that may not be recoverable. A five second delay '
          u'is introduced to give you time to cancel the runtime and '
          u'reconfigure your preferred encoding, otherwise continue at own '
          u'risk.')
      time.sleep(5)

    try:
      self.ParseOptions(options)
    except errors.BadConfigOption as exception:
      logging.error(u'{0:s}'.format(exception))

      self._output_writer.Write(u'\n')
      self._output_writer.Write(argument_parser.format_help())

      return False

    return True

  def ParseOptions(self, options):
    """Parses the options.

    Args:
      options: the command line arguments (instance of argparse.Namespace).

    Raises:
      BadConfigOption: if the options are invalid.
    """
    # Check the list options first otherwise required options will raise.
    self._ParseLanguageOptions(options)
    self._ParseTimezoneOption(options)

    if (self.list_analysis_plugins or self.list_language_identifiers or
        self.list_output_modules or self.list_timezones):
      return

    super(PsortTool, self).ParseOptions(options)

    self._ParseAnalysisPluginOptions(options)
    self._ParseFilterOptions(options)

    debug = getattr(options, u'debug', False)
    if debug:
      logging_level = logging.DEBUG
    else:
      logging_level = logging.INFO

    logging.basicConfig(
        level=logging_level, format=u'[%(levelname)s] %(message)s')

    self._output_format = getattr(options, u'output_format', None)
    if not self._output_format:
      raise errors.BadConfigOption(u'Missing output format.')

    if not self._front_end.HasOutputClass(self._output_format):
      raise errors.BadConfigOption(
          u'Unsupported output format: {0:s}.'.format(self._output_format))

    self._deduplicate_events = getattr(options, u'dedup', True)

    self._output_filename = getattr(options, u'write', None)

    self._preferred_language = getattr(options, u'preferred_language', u'en-US')

    if not self._data_location:
      logging.warning(u'Unable to automatically determine data location.')

    # TODO: refactor this.
    self._options = options

  def ProcessStorage(self):
    """Processes a plaso storage."""
    try:
      self._ProcessStorage()

    except IOError as exception:
      # Piping results to "|head" for instance causes an IOError.
      if u'Broken pipe' not in exception:
        logging.error(u'Processing stopped early: {0:s}.'.format(exception))

    except KeyboardInterrupt:
      pass

    # Catching every remaining exception in case we are debugging.
    except Exception as exception:
      if not self._debug_mode:
        raise
      logging.error(u'{0:s}'.format(exception))
      pdb.post_mortem()


def Main():
  """The main function."""
  multiprocessing.freeze_support()

  tool = PsortTool()

  if not tool.ParseArguments():
    return False

  have_list_option = False
  if tool.list_analysis_plugins:
    tool.ListAnalysisPlugins()
    have_list_option = True

  if tool.list_output_modules:
    tool.ListOutputModules()
    have_list_option = True

  if tool.list_language_identifiers:
    tool.ListLanguageIdentifiers()
    have_list_option = True

  if tool.list_timezones:
    tool.ListTimeZones()
    have_list_option = True

  if have_list_option:
    return True

  tool.ProcessStorage()
  return True


if __name__ == '__main__':
  if not Main():
    sys.exit(1)
  else:
    sys.exit(0)
