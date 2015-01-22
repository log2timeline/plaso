#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2012 The Plaso Project Authors.
# Please see the AUTHORS file for details on individual authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Psort (Plaso Síar Og Raðar Þessu) - Makes output from Plaso Storage files.

Sample Usage:
  psort.py /tmp/mystorage.dump "date > '01-06-2012'"

See additional details here: http://plaso.kiddaland.net/usage/psort
"""

import argparse
import collections
import datetime
import time
import multiprocessing
import logging
import pdb
import sys

import plaso
from plaso import analysis
from plaso import filters
from plaso import formatters   # pylint: disable=unused-import
from plaso import output   # pylint: disable=unused-import

from plaso.analysis import context as analysis_context
from plaso.analysis import interface as analysis_interface
from plaso.artifacts import knowledge_base
from plaso.engine import queue
from plaso.frontend import frontend
from plaso.frontend import utils as frontend_utils
from plaso.lib import bufferlib
from plaso.lib import errors
from plaso.lib import pfilter
from plaso.lib import timelib
from plaso.multi_processing import multi_process
from plaso.output import interface as output_interface
from plaso.proto import plaso_storage_pb2
from plaso.serializer import protobuf_serializer

import pytz


class PsortFrontend(frontend.AnalysisFrontend):
  """Class that implements the psort front-end."""

  def __init__(self):
    """Initializes the front-end object."""
    input_reader = frontend.StdinFrontendInputReader()
    output_writer = frontend.StdoutFrontendOutputWriter()

    super(PsortFrontend, self).__init__(input_reader, output_writer)

    self._analysis_processes = []
    self._filter_buffer = None
    self._filter_expression = None
    self._filter_object = None
    self._output_module_class = None
    self._output_stream = None
    self._slice_size = 5

  def AddAnalysisPluginOptions(self, argument_group, plugin_names):
    """Adds the analysis plugin options to the argument group

    Args:
      argument_group: The argparse argument group (instance of
                      argparse._ArgumentGroup).
      plugin_names: a string containing comma separated analysis plugin names.

    Raises:
      BadConfigOption: if non-existing analysis plugin names are specified.
    """
    if plugin_names == 'list':
      return

    plugin_list = set([
        name.strip().lower() for name in plugin_names.split(',')])

    # Get a list of all available plugins.
    analysis_plugins = set([
        name.lower() for name, _, _ in analysis.ListAllPluginNames()])

    # Get a list of the selected plugins (ignoring selections that did not
    # have an actual plugin behind it).
    plugins_to_load = analysis_plugins.intersection(plugin_list)

    # Check to see if we are trying to load plugins that do not exist.
    difference = plugin_list.difference(analysis_plugins)
    if difference:
      raise errors.BadConfigOption(
          u'Non-existing analysis plugins specified: {0:s}'.format(
              u' '.join(difference)))

    plugins = analysis.LoadPlugins(plugins_to_load, None)
    for plugin in plugins:
      if plugin.ARGUMENTS:
        for parameter, config in plugin.ARGUMENTS:
          argument_group.add_argument(parameter, **config)

  def AddOutputModuleOptions(self, argument_group, module_names):
    """Adds the output module options to the argument group

    Args:
      argument_group: The argparse argument group (instance of
                      argparse._ArgumentGroup).
      module_names: a string containing comma separated output module names.
    """
    if module_names == 'list':
      return

    modules_list = set([name.lower() for name in module_names])

    for output_module_string, _ in output_interface.ListOutputFormatters():
      if not output_module_string.lower() in modules_list:
        continue

      output_module = output_interface.GetOutputFormatter(output_module_string)
      if output_module.ARGUMENTS:
        for parameter, config in output_module.ARGUMENTS:
          argument_group.add_argument(parameter, **config)

  def ListAnalysisPlugins(self):
    """Lists the analysis modules."""
    self.PrintHeader('Analysis Modules')
    format_length = 10
    for name, _, _ in analysis.ListAllPluginNames():
      if len(name) > format_length:
        format_length = len(name)

    for name, description, plugin_type in analysis.ListAllPluginNames():
      if plugin_type == analysis_interface.AnalysisPlugin.TYPE_ANNOTATION:
        type_string = 'Annotation/tagging plugin'
      elif plugin_type == analysis_interface.AnalysisPlugin.TYPE_ANOMALY:
        type_string = 'Anomaly plugin'
      elif plugin_type == analysis_interface.AnalysisPlugin.TYPE_REPORT:
        type_string = 'Summary/Report plugin'
      elif plugin_type == analysis_interface.AnalysisPlugin.TYPE_STATISTICS:
        type_string = 'Statistics plugin'
      else:
        type_string = 'Unknown type'

      description = u'{0:s} [{1:s}]'.format(description, type_string)
      self.PrintColumnValue(name, description, format_length)
    self.PrintSeparatorLine()

  def ListOutputModules(self):
    """Lists the output modules."""
    self.PrintHeader('Output Modules')
    for name, description in output_interface.ListOutputFormatters():
      self.PrintColumnValue(name, description, 10)
    self.PrintSeparatorLine()

  def ListTimeZones(self):
    """Lists the timezones."""
    self.PrintHeader('Zones')
    max_length = 0
    for zone in pytz.all_timezones:
      if len(zone) > max_length:
        max_length = len(zone)

    self.PrintColumnValue('Timezone', 'UTC Offset', max_length)
    for zone in pytz.all_timezones:
      zone_obj = pytz.timezone(zone)
      date_str = unicode(zone_obj.localize(datetime.datetime.utcnow()))
      if '+' in date_str:
        _, _, diff = date_str.rpartition('+')
        diff_string = u'+{0:s}'.format(diff)
      else:
        _, _, diff = date_str.rpartition('-')
        diff_string = u'-{0:s}'.format(diff)
      self.PrintColumnValue(zone, diff_string, max_length)
    self.PrintSeparatorLine()

  def ParseOptions(self, options):
    """Parses the options and initializes the front-end.

    Args:
      options: the command line arguments (instance of argparse.Namespace).

    Raises:
      BadConfigOption: if the options are invalid.
    """
    super(PsortFrontend, self).ParseOptions(options)

    output_format = getattr(options, 'output_format', None)
    if not output_format:
      raise errors.BadConfigOption(u'Missing output format.')

    self._output_module_class = output_interface.GetOutputFormatter(
        output_format)
    if not self._output_module_class:
      raise errors.BadConfigOption(
          u'Invalid output format: {0:s}.'.format(output_format))

    self._output_stream = getattr(options, 'write', None)
    if not self._output_stream:
      self._output_stream = sys.stdout

    self._filter_expression = getattr(options, 'filter', None)
    if self._filter_expression:
      self._filter_object = filters.GetFilter(self._filter_expression)
      if not self._filter_object:
        raise errors.BadConfigOption(
            u'Invalid filter expression: {0:s}'.format(self._filter_expression))

      # Check to see if we need to create a circular buffer.
      if getattr(options, 'slicer', None):
        self._slice_size = getattr(options, 'slice_size', 5)
        self._filter_buffer = bufferlib.CircularBuffer(self._slice_size)

  def ParseStorage(self, options):
    """Open a storage file and parse through it.

    Args:
      options: the command line arguments (instance of argparse.Namespace).

    Returns:
      A counter.

    Raises:
      RuntimeError: if a non-recoverable situation is encountered.
    """
    counter = None

    if options.slice:
      if options.timezone == 'UTC':
        zone = pytz.utc
      else:
        zone = pytz.timezone(options.timezone)

      timestamp = timelib.Timestamp.FromTimeString(options.slice, timezone=zone)

      # Convert number of minutes to microseconds.
      range_operator = self._slice_size * 60 * 1000000

      # Set the time range.
      pfilter.TimeRangeCache.SetLowerTimestamp(timestamp - range_operator)
      pfilter.TimeRangeCache.SetUpperTimestamp(timestamp + range_operator)

    if options.analysis_plugins:
      read_only = False
    else:
      read_only = True

    try:
      storage_file = self.OpenStorageFile(read_only=read_only)
    except IOError as exception:
      raise RuntimeError(
          u'Unable to open storage file: {0:s} with error: {1:s}.'.format(
              self._storage_file_path, exception))

    with storage_file:
      storage_file.SetStoreLimit(self._filter_object)

      try:
        output_module = self._output_module_class(
            storage_file, self._output_stream, options, self._filter_object)
      except IOError as exception:
        raise RuntimeError(
            u'Unable to create output module with error: {0:s}'.format(
                exception))

      if not output_module:
        raise RuntimeError(u'Missing output module.')

      if options.analysis_plugins:
        logging.info(u'Starting analysis plugins.')
        # Within all preprocessing objects, try to get the last one that has
        # time zone information stored in it, the highest chance of it
        # containing the information we are seeking (defaulting to the last
        # one).
        pre_objs = storage_file.GetStorageInformation()
        pre_obj = pre_objs[-1]
        for obj in pre_objs:
          if getattr(obj, 'time_zone_str', ''):
            pre_obj = obj

        # Fill in the collection information.
        pre_obj.collection_information = {}
        encoding = getattr(pre_obj, 'preferred_encoding', None)
        if encoding:
          cmd_line = ' '.join(sys.argv)
          try:
            pre_obj.collection_information['cmd_line'] = cmd_line.decode(
                encoding)
          except UnicodeDecodeError:
            pass
        pre_obj.collection_information['file_processed'] = (
            self._storage_file_path)
        pre_obj.collection_information['method'] = 'Running Analysis Plugins'
        pre_obj.collection_information['plugins'] = options.analysis_plugins
        time_of_run = timelib.Timestamp.GetNow()
        pre_obj.collection_information['time_of_run'] = time_of_run

        pre_obj.counter = collections.Counter()

        # Assign the preprocessing object to the storage.
        # This is normally done in the construction of the storage object,
        # however we cannot do that here since the preprocessing object is
        # stored inside the storage file, so we need to open it first to
        # be able to read it in, before we make changes to it. Thus we need
        # to access this protected member of the class.
        # pylint: disable=protected-access
        storage_file._pre_obj = pre_obj

        # Start queues and load up plugins.
        # TODO: add upper queue limit.
        analysis_output_queue = multi_process.MultiProcessingQueue()
        event_queue_producers = []
        event_queues = []
        analysis_plugins_list = [
            x.strip() for x in options.analysis_plugins.split(',')]

        for _ in xrange(0, len(analysis_plugins_list)):
          # TODO: add upper queue limit.
          analysis_plugin_queue = multi_process.MultiProcessingQueue()
          event_queues.append(analysis_plugin_queue)
          event_queue_producers.append(
              queue.ItemQueueProducer(event_queues[-1]))

        knowledge_base_object = knowledge_base.KnowledgeBase()

        analysis_plugins = analysis.LoadPlugins(
            analysis_plugins_list, event_queues, options)

        # Now we need to start all the plugins.
        for analysis_plugin in analysis_plugins:
          analysis_report_queue_producer = queue.ItemQueueProducer(
              analysis_output_queue)
          analysis_context_object = analysis_context.AnalysisContext(
              analysis_report_queue_producer, knowledge_base_object)
          analysis_process = multiprocessing.Process(
              name='Analysis {0:s}'.format(analysis_plugin.plugin_name),
              target=analysis_plugin.RunPlugin, args=(analysis_context_object,))
          self._analysis_processes.append(analysis_process)

          analysis_process.start()
          logging.info(
              u'Plugin: [{0:s}] started.'.format(analysis_plugin.plugin_name))
      else:
        event_queue_producers = []

      output_buffer = output_interface.EventBuffer(output_module, options.dedup)
      with output_buffer:
        counter = ProcessOutput(
            output_buffer, output_module, self._filter_object,
            self._filter_buffer, event_queue_producers)

      for information in storage_file.GetStorageInformation():
        if hasattr(information, 'counter'):
          counter['Stored Events'] += information.counter['total']

      if not options.quiet:
        logging.info(u'Output processing is done.')

      # Get all reports and tags from analysis plugins.
      if options.analysis_plugins:
        logging.info(u'Processing data from analysis plugins.')
        for event_queue_producer in event_queue_producers:
          event_queue_producer.SignalEndOfInput()

        # Wait for all analysis plugins to complete.
        for number, analysis_process in enumerate(self._analysis_processes):
          logging.debug(
              u'Waiting for analysis plugin: {0:d} to complete.'.format(number))
          if analysis_process.is_alive():
            analysis_process.join(10)
          else:
            logging.warning(u'Plugin {0:d} already stopped.'.format(number))
            analysis_process.terminate()
        logging.debug(u'All analysis plugins are now stopped.')

        # Close the output queue.
        analysis_output_queue.SignalEndOfInput()

        # Go over each output.
        analysis_queue_consumer = PsortAnalysisReportQueueConsumer(
            analysis_output_queue, storage_file, self._filter_expression,
            self.preferred_encoding)

        analysis_queue_consumer.ConsumeItems()

        if analysis_queue_consumer.tags:
          storage_file.StoreTagging(analysis_queue_consumer.tags)

        # TODO: analysis_queue_consumer.anomalies:

        for item, value in analysis_queue_consumer.counter.iteritems():
          counter[item] = value

    if self._filter_object and not counter['Limited By']:
      counter['Filter By Date'] = (
          counter['Stored Events'] - counter['Events Included'] -
          counter['Events Filtered Out'])

    return counter


# TODO: Function: _ConsumeItem is not defined, inspect if we need to define it
# or change the interface so that is not an abstract method.
# TODO: Remove this after dfVFS integration.
# pylint: disable=abstract-method
class PsortAnalysisReportQueueConsumer(queue.ItemQueueConsumer):
  """Class that implements an analysis report queue consumer for psort."""

  def __init__(
      self, queue_object, storage_file, filter_string, preferred_encoding):
    """Initializes the queue consumer.

    Args:
      queue_object: the queue object (instance of Queue).
      storage_file: the storage file (instance of StorageFile).
      filter_string: the filter string.
      preferred_encoding: the preferred encoding.
    """
    super(PsortAnalysisReportQueueConsumer, self).__init__(queue_object)
    self._filter_string = filter_string
    self._preferred_encoding = preferred_encoding
    self._storage_file = storage_file
    self.anomalies = []
    self.counter = collections.Counter()
    self.tags = []

  def _ConsumeItem(self, analysis_report):
    """Consumes an item callback for ConsumeItems.

    Args:
      analysis_report: the analysis report (instance of AnalysisReport).
    """
    self.counter['Total Reports'] += 1
    self.counter[u'Report: {0:s}'.format(analysis_report.plugin_name)] += 1

    self.anomalies.extend(analysis_report.GetAnomalies())
    self.tags.extend(analysis_report.GetTags())

    if self._filter_string:
      analysis_report.filter_string = self._filter_string

    # For now we print the report to disk and then save it.
    # TODO: Have the option of saving to a separate file and
    # do something more here, for instance saving into a HTML
    # file, or something else (including potential images).
    self._storage_file.StoreReport(analysis_report)

    report_string = analysis_report.GetString()
    try:
      print report_string.encode(self._preferred_encoding)
    except UnicodeDecodeError:
      logging.error(
          u'Unable to print report due to an unicode decode error. '
          u'The report is stored inside the storage file and can be '
          u'viewed using pinfo [if unable to view please submit a '
          u'bug report https://github.com/log2timeline/plaso/issues')


def _AppendEvent(event_object, output_buffer, event_queues):
  """Appends an event object to an output buffer and queues.

  Args:
    event_object: an event object (instance of EventObject).
    output_buffer: the output buffer.
    event_queues: a list of event queues that serve as input for
                  the analysis plugins.
  """
  output_buffer.Append(event_object)

  # Needed due to duplicate removals, if two events
  # are merged then we'll just pick the first inode value.
  inode = getattr(event_object, 'inode', None)
  if isinstance(inode, basestring):
    inode_list = inode.split(';')
    try:
      new_inode = int(inode_list[0], 10)
    except (ValueError, IndexError):
      new_inode = 0

    event_object.inode = new_inode

  for event_queue in event_queues:
    event_queue.ProduceItem(event_object)


def ProcessOutput(
    output_buffer, output_module, my_filter=None, filter_buffer=None,
    analysis_queues=None):
  """Fetch EventObjects from storage and process and filter them.

  Args:
    output_buffer: output.EventBuffer object.
    output_module: The output module (instance of OutputFormatter).
    my_filter: A filter object.
    filter_buffer: A filter buffer used to store previously discarded
    events to store time slice history.
    analysis_queues: A list of analysis queues.
  """
  counter = collections.Counter()
  my_limit = getattr(my_filter, 'limit', 0)
  forward_entries = 0
  if not analysis_queues:
    analysis_queues = []

  event_object = output_module.FetchEntry()
  while event_object:
    if my_filter:
      event_match = event_object
      if isinstance(event_object, plaso_storage_pb2.EventObject):
        # TODO: move serialization to storage, if low-level filtering is needed
        # storage should provide functions for it.
        serializer = protobuf_serializer.ProtobufEventObjectSerializer
        event_match = serializer.ReadSerialized(event_object)

      if my_filter.Match(event_match):
        counter['Events Included'] += 1
        if filter_buffer:
          # Indicate we want forward buffering.
          forward_entries = 1
          # Empty the buffer.
          for event_in_buffer in filter_buffer.Flush():
            counter['Events Added From Slice'] += 1
            counter['Events Included'] += 1
            counter['Events Filtered Out'] -= 1
            _AppendEvent(event_in_buffer, output_buffer, analysis_queues)
        _AppendEvent(event_object, output_buffer, analysis_queues)
        if my_limit:
          if counter['Events Included'] == my_limit:
            break
      else:
        if filter_buffer and forward_entries:
          if forward_entries <= filter_buffer.size:
            _AppendEvent(event_object, output_buffer, analysis_queues)
            forward_entries += 1
            counter['Events Added From Slice'] += 1
            counter['Events Included'] += 1
          else:
            # Reached the max, don't include other entries.
            forward_entries = 0
            counter['Events Filtered Out'] += 1
        elif filter_buffer:
          filter_buffer.Append(event_object)
          counter['Events Filtered Out'] += 1
        else:
          counter['Events Filtered Out'] += 1
    else:
      counter['Events Included'] += 1
      _AppendEvent(event_object, output_buffer, analysis_queues)

    event_object = output_module.FetchEntry()

  if output_buffer.duplicate_counter:
    counter['Duplicate Removals'] = output_buffer.duplicate_counter

  if my_limit:
    counter['Limited By'] = my_limit
  return counter


def Main(arguments=None):
  """Start the tool."""
  multiprocessing.freeze_support()

  front_end = PsortFrontend()

  arg_parser = argparse.ArgumentParser(
      description=(
          u'PSORT - Application to read, filter and process '
          u'output from a plaso storage file.'), add_help=False)

  tool_group = arg_parser.add_argument_group('Optional Arguments For Psort')
  output_group = arg_parser.add_argument_group(
      'Optional Arguments For Output Modules')
  analysis_group = arg_parser.add_argument_group(
      'Optional Arguments For Analysis Modules')

  tool_group.add_argument(
      '-d', '--debug', action='store_true', dest='debug', default=False,
      help='Fall back to debug shell if psort fails.')

  tool_group.add_argument(
      '-q', '--quiet', action='store_true', dest='quiet', default=False,
      help='Don\'t print out counter information after processing.')

  tool_group.add_argument(
      '-h', '--help', action='help', help='Show this help message and exit.')

  tool_group.add_argument(
      '-a', '--include_all', action='store_false', dest='dedup', default=True,
      help=(
          'By default the tool removes duplicate entries from the output. '
          'This parameter changes that behavior so all events are included.'))

  tool_group.add_argument(
      '-o', '--output_format', '--output-format', metavar='FORMAT',
      dest='output_format', default='dynamic', help=(
          'The output format or "-o list" to see a list of available '
          'output formats.'))

  tool_group.add_argument(
      '--analysis', metavar='PLUGIN_LIST', dest='analysis_plugins',
      default='', action='store', type=unicode, help=(
          'A comma separated list of analysis plugin names to be loaded '
          'or "--analysis list" to see a list of available plugins.'))

  tool_group.add_argument(
      '-z', '--zone', metavar='TIMEZONE', default='UTC', dest='timezone', help=(
          'The timezone of the output or "-z list" to see a list of available '
          'timezones.'))

  tool_group.add_argument(
      '-w', '--write', metavar='OUTPUTFILE', dest='write',
      help='Output filename.  Defaults to stdout.')

  tool_group.add_argument(
      '--slice', metavar='DATE', dest='slice', type=str,
      default='', action='store', help=(
          'Create a time slice around a certain date. This parameter, if '
          'defined will display all events that happened X minutes before and '
          'after the defined date. X is controlled by the parameter '
          '--slice_size but defaults to 5 minutes.'))

  tool_group.add_argument(
      '--slicer', dest='slicer', action='store_true', default=False, help=(
          'Create a time slice around every filter match. This parameter, if '
          'defined will save all X events before and after a filter match has '
          'been made. X is defined by the --slice_size parameter.'))

  tool_group.add_argument(
      '--slice_size', dest='slice_size', type=int, default=5, action='store',
      help=(
          'Defines the slice size. In the case of a regular time slice it '
          'defines the number of minutes the slice size should be. In the '
          'case of the --slicer it determines the number of events before '
          'and after a filter match has been made that will be included in '
          'the result set. The default value is 5]. See --slice or --slicer '
          'for more details about this option.'))

  tool_group.add_argument(
      '-v', '--version', dest='version', action='version',
      version='log2timeline - psort version {0:s}'.format(plaso.GetVersion()),
      help='Show the current version of psort.')

  front_end.AddStorageFileOptions(tool_group)

  tool_group.add_argument(
      'filter', nargs='?', action='store', metavar='FILTER', default=None,
      type=unicode, help=(
          'A filter that can be used to filter the dataset before it '
          'is written into storage. More information about the filters'
          ' and it\'s usage can be found here: http://plaso.kiddaland.'
          'net/usage/filters'))

  if arguments is None:
    arguments = sys.argv[1:]

  # Add the output module options.
  if '-o' in arguments:
    argument_index = arguments.index('-o') + 1
  elif '--output_format' in arguments:
    argument_index = arguments.index('--output_format') + 1
  elif '--output-format' in arguments:
    argument_index = arguments.index('--output-format') + 1
  else:
    argument_index = 0

  if argument_index > 0:
    module_names = arguments[argument_index]
    front_end.AddOutputModuleOptions(output_group, [module_names])

  # Add the analysis plugin options.
  if '--analysis' in arguments:
    argument_index = arguments.index('--analysis') + 1

    # Get the names of the analysis plugins that should be loaded.
    plugin_names = arguments[argument_index]
    try:
      front_end.AddAnalysisPluginOptions(analysis_group, plugin_names)
    except errors.BadConfigOption as exception:
      arg_parser.print_help()
      print u''
      logging.error('{0:s}'.format(exception))
      return False

  options = arg_parser.parse_args(args=arguments)

  format_str = '[%(levelname)s] %(message)s'
  if getattr(options, 'debug', False):
    logging.basicConfig(level=logging.DEBUG, format=format_str)
  else:
    logging.basicConfig(level=logging.INFO, format=format_str)

  if options.timezone == 'list':
    front_end.ListTimeZones()
    return True

  if options.analysis_plugins == 'list':
    front_end.ListAnalysisPlugins()
    return True

  if options.output_format == 'list':
    front_end.ListOutputModules()
    return True

  try:
    front_end.ParseOptions(options)
  except errors.BadConfigOption as exception:
    arg_parser.print_help()
    print u''
    logging.error(u'{0:s}'.format(exception))
    return False

  if front_end.preferred_encoding == 'ascii':
    logging.warning(
        u'The preferred encoding of your system is ASCII, which is not optimal '
        u'for the typically non-ASCII characters that need to be parsed and '
        u'processed. The tool will most likely crash and die, perhaps in a way '
        u'that may not be recoverable. A five second delay is introduced to '
        u'give you time to cancel the runtime and reconfigure your preferred '
        u'encoding, otherwise continue at own risk.')
    time.sleep(5)

  try:
    counter = front_end.ParseStorage(options)

    if not options.quiet:
      logging.info(frontend_utils.FormatHeader('Counter'))
      for element, count in counter.most_common():
        logging.info(frontend_utils.FormatOutputString(element, count))

  except IOError as exception:
    # Piping results to "|head" for instance causes an IOError.
    if u'Broken pipe' not in exception:
      logging.error(u'Processing stopped early: {0:s}.'.format(exception))

  except KeyboardInterrupt:
    pass

  # Catching every remaining exception in case we are debugging.
  except Exception as exception:
    if not options.debug:
      raise
    logging.error(u'{0:s}'.format(exception))
    pdb.post_mortem()

  return True


if __name__ == '__main__':
  if not Main():
    sys.exit(1)
  else:
    sys.exit(0)
