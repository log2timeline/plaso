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
import os
import multiprocessing
import locale
import logging
import pdb
import sys

import plaso
from plaso import analysis
from plaso import filters
from plaso import formatters   # pylint: disable=unused-import
from plaso import output   # pylint: disable=unused-import

from plaso.analysis import interface as analysis_interface
from plaso.lib import bufferlib
from plaso.lib import output as output_lib
from plaso.lib import pfilter
from plaso.lib import queue
from plaso.lib import storage
from plaso.lib import timelib
from plaso.lib import utils
from plaso.proto import plaso_storage_pb2
from plaso.serializer import protobuf_serializer

import pytz


# TODO: Function: _ConsumeItem is not defined, inspect if we need to define it
# or change the interface so that is not an abstract method.
# TODO: Remove this after dfVFS integration.
# pylint: disable=abstract-method
class PsortAnalysisReportQueueConsumer(queue.AnalysisReportQueueConsumer):
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

  def _ConsumeAnalysisReport(self, analysis_report):
    """Consumes an analysis report callback for ConsumeAnalysisReports."""
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
          u'bug report https://code.google.com/p/plaso/issues/list')


def _AppendEvent(event_object, output_buffer, analysis_queues):
  """Appends an event object to an output buffer and queues."""
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

  for analysis_queue in analysis_queues:
    analysis_queue.ProduceEventObject(event_object)


def SetupStorage(input_file_path, read_only=True):
  """Sets up the storage object.

  Attempts to initialize the storage object from the StorageFile library.  If
  we fail on a IO Error (common case for typos) log a warning and gracefully
  exit.

  Args:
    input_file_path: Filesystem path to the plaso storage container.
    read_only: A boolean indicating whether we need read or write support to the
               storage file.

  Returns:
    A storage.StorageFile object.
  """
  try:
    return storage.StorageFile(input_file_path, read_only=read_only)
  except IOError as exception:
    logging.error(u'IO ERROR: {0:s}'.format(exception))
  else:
    logging.error(u'Other Critical Failure Reading Files')
  sys.exit(1)


def ProcessOutput(
    output_buffer, formatter, my_filter=None, filter_buffer=None,
    analysis_queues=None):
  """Fetch EventObjects from storage and process and filter them.

  Args:
    output_buffer: output.EventBuffer object.
    formatter: An OutputFormatter.
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

  event_object = formatter.FetchEntry()
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

    event_object = formatter.FetchEntry()

  if output_buffer.duplicate_counter:
    counter['Duplicate Removals'] = output_buffer.duplicate_counter

  if my_limit:
    counter['Limited By'] = my_limit
  return counter


def ParseStorage(my_args):
  """Open a storage file and parse through it."""
  filter_use = None
  filter_buffer = None
  counter = None
  analysis_processes = []

  if my_args.filter:
    filter_use = filters.GetFilter(my_args.filter)
    if not filter_use:
      logging.error(
          u'No filter found for the filter expression: {0:s}'.format(
              my_args.filter))
      sys.exit(1)

    if my_args.slicer:
      # Check to see if we need to create a circular buffer.
      filter_buffer = bufferlib.CircularBuffer(my_args.slice_size)

  if my_args.slice:
    if my_args.timezone == 'UTC':
      zone = pytz.utc
    else:
      zone = pytz.timezone(my_args.timezone)

    timestamp = timelib.Timestamp.FromTimeString(my_args.slice, timezone=zone)

    # Convert number of minutes to microseconds.
    range_operator = my_args.slice_size * int(1e6) * 60
    # Set the time range.
    pfilter.TimeRangeCache.SetLowerTimestamp(timestamp - range_operator)
    pfilter.TimeRangeCache.SetUpperTimestamp(timestamp + range_operator)

    # Check if the filter has a date filter built in and warn if so.
    if my_args.filter:
      if 'date' in my_args.filter or 'timestamp' in my_args.filter:
        logging.warning(
            u'You are trying to use both a "slice" and a date filter, the '
            u'end results might not be what you want it to be... a small delay '
            u'is introduced to allow you to read this message')
        time.sleep(5)

  if my_args.analysis_plugins:
    read_only = False
  else:
    read_only = True

  with SetupStorage(my_args.storagefile, read_only) as store:
    # Identify which stores to use.
    store.SetStoreLimit(filter_use)

    try:
      formatter_cls = output_lib.GetOutputFormatter(my_args.output_format)
      if not formatter_cls:
        logging.error((
            u'Wrong output module choosen, module: {0:s} does not exist. '
            u'Please use {1:s} -o list to see all available modules.').format(
                my_args.output_format, sys.argv[0]))
        sys.exit(1)
      formatter = formatter_cls(
              store, my_args.write, my_args, filter_use)
    except IOError as exception:
      logging.error(u'Error occured during output processing: {0:s}'.format(
          exception))

    if not formatter:
      logging.error(u'Unable to proceed, output buffer not available.')
      sys.exit(1)

    if my_args.analysis_plugins:
      logging.info('Starting analysis plugins.')
      # Within all pre processing objects, try to get the last one that has
      # time zone information stored in it, the highest chance of it containing
      # the information we are seeking (defaulting to the last one).
      pre_objs = store.GetStorageInformation()
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
          pre_obj.collection_information['cmd_line'] = cmd_line.decode(encoding)
        except UnicodeDecodeError:
          pass
      pre_obj.collection_information['file_processed'] = my_args.storagefile
      pre_obj.collection_information['method'] = 'Running Analysis Plugins'
      pre_obj.collection_information['plugins'] = my_args.analysis_plugins
      pre_obj.collection_information['time_of_run'] = timelib.Timestamp.GetNow()

      pre_obj.counter = collections.Counter()

      # Assign the preprocessing object to the storage.
      # This is normally done in the construction of the storage object,
      # however we cannot do that here since the pre processing object is
      # stored inside the storage file, so we need to open it first to
      # be able to read it in, before we make changes to it. Thus we need
      # to access this protected member of the class.
      # pylint: disable=protected-access
      store._pre_obj = pre_obj

      # Start queues and load up plugins.
      analysis_output_queue = queue.MultiThreadedQueue()
      analysis_producers = []
      analysis_queues = []
      analysis_plugins_list = [
          x.strip() for x in my_args.analysis_plugins.split(',')]
      for _ in xrange(0, len(analysis_plugins_list)):
        analysis_queues.append(queue.MultiThreadedQueue())
        analysis_producers.append(
            queue.AnalysisPluginProducer(analysis_queues[-1]))

      analysis_plugins = analysis.LoadPlugins(
          analysis_plugins_list, pre_obj, analysis_queues,
          analysis_output_queue)

      # Now we need to start all the plugins.
      for analysis_plugin in analysis_plugins:
        analysis_processes.append(multiprocessing.Process(
            name='Analysis {0:s}'.format(analysis_plugin.plugin_name),
            target=analysis_plugin.RunPlugin))
        analysis_processes[-1].start()
        logging.info(
            u'Plugin: [{0:s}] started.'.format(analysis_plugin.plugin_name))
    else:
      analysis_producers = []

    with output_lib.EventBuffer(formatter, my_args.dedup) as output_buffer:
      counter = ProcessOutput(
          output_buffer, formatter, filter_use, filter_buffer,
          analysis_producers)

    for information in store.GetStorageInformation():
      if hasattr(information, 'counter'):
        counter['Stored Events'] += information.counter['total']

    if not my_args.quiet:
      logging.info('Output processing is done.')

    # Get all reports and tags from analysis plugins.
    if my_args.analysis_plugins:
      logging.info('Processing data from analysis plugins.')
      for analysis_producer in analysis_producers:
        analysis_producer.SignalEndOfInput()

      # Wait for all analysis plugins to complete.
      for number, analysis_process in enumerate(analysis_processes):
        logging.debug(
            u'Waiting for analysis plugin: {0:s} to complete.'.format(number))
        if analysis_process.is_alive():
          analysis_process.join(10)
        else:
          logging.warning(u'Plugin {0:s} already stopped.'.format(number))
          analysis_process.terminate()
      logging.debug(u'All analysis plugins are now stopped.')

      # Close the output queue.
      analysis_output_queue.SignalEndOfInput()

      # Go over each output.
      analysis_queue_consumer = PsortAnalysisReportQueueConsumer(
          analysis_output_queue, store, my_args.filter,
          my_args.preferred_encoding)

      analysis_queue_consumer.ConsumeAnalysisReports()

      if analysis_queue_consumer.tags:
        store.StoreTagging(analysis_queue_consumer.tags)

      # TODO: analysis_queue_consumer.anomalies:

      for item, value in analysis_queue_consumer.counter.iteritems():
        counter[item] = value

  if filter_use and not counter['Limited By']:
    counter['Filter By Date'] = counter['Stored Events'] - counter[
        'Events Included'] - counter['Events Filtered Out']

  return counter


def ProcessArguments(arguments):
  """Process command line arguments."""
  parser = argparse.ArgumentParser(
      description=(
          u'PSORT - Application to read, filter and process '
          'output from a plaso storage file.'), add_help=False)

  tool_group = parser.add_argument_group('Optional Arguments For Psort')
  output_group = parser.add_argument_group(
      'Optional Arguments For Output Modules')
  analysis_group = parser.add_argument_group(
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
      '-o', '--output_format', metavar='FORMAT', dest='output_format',
      default='dynamic', help='Output format.  -o list to see loaded modules.')

  tool_group.add_argument(
      '--analysis', metavar='PLUGIN_LIST', dest='analysis_plugins',
      default='', action='store', type=unicode, help=(
          'A comma separated list of analysis plugin names to be loaded.'))

  tool_group.add_argument(
      '-z', '--zone', metavar='TIMEZONE', default='UTC', dest='timezone',
      help='Timezone of output. list: "-z list"')

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

  tool_group.add_argument(
      'storagefile', metavar='PLASOFILE', default=None, nargs='?',
      type=unicode, help='Path to the Plaso storage file')

  tool_group.add_argument(
      'filter', nargs='?', action='store', metavar='FILTER', default=None,
      type=unicode, help=(
          'A filter that can be used to filter the dataset before it '
          'is written into storage. More information about the filters'
          ' and it\'s usage can be found here: http://plaso.kiddaland.'
          'net/usage/filters'))

  # Build output module parameters (but only if they are included).
  for output_module_string, _ in output_lib.ListOutputFormatters():
    if not output_module_string.lower() in [x.lower() for x in arguments]:
      continue
    output_module = output_lib.GetOutputFormatter(output_module_string)
    if output_module.ARGUMENTS:
      for parameter, config in output_module.ARGUMENTS:
        output_group.add_argument(parameter, **config)

  # Build the analysis output module parameters (if included).
  if '--analysis' in arguments:
    analysis_index = arguments.index('--analysis')
    # Get the list of plugins that should be loaded.
    plugin_string = arguments[analysis_index + 1]
    if plugin_string != 'list':
      plugin_list = set([x.strip().lower() for x in plugin_string.split(',')])

      # Get a list of all available plugins.
      analysis_plugins = set(
          [x.lower() for x, _, _ in analysis.ListAllPluginNames()])

      # Get a list of the selected plugins (ignoring selections that did not
      # have an actual plugin behind it).
      plugins_to_load = analysis_plugins.intersection(plugin_list)

      # Check to see if we are trying to load plugins that do not exist.
      difference = plugin_list.difference(analysis_plugins)
      if difference:
        parser.print_help()
        print u''
        print u'Trying to load plugins that do not exist: {0:s}'.format(
            u' '.join(difference))
        sys.exit(1)

      plugins = analysis.LoadPlugins(plugins_to_load, None, None, None)
      for plugin in plugins:
        if plugin.ARGUMENTS:
          for parameter, config in plugin.ARGUMENTS:
            analysis_group.add_argument(parameter, **config)

  my_args = parser.parse_args(args=arguments)

  format_str = '[%(levelname)s] %(message)s'
  if my_args.debug:
    logging.basicConfig(level=logging.DEBUG, format=format_str)
  else:
    logging.basicConfig(level=logging.INFO, format=format_str)

  if my_args.timezone == 'list':
    print utils.FormatHeader('Zones')
    max_length = 0
    for zone in pytz.all_timezones:
      if len(zone) > max_length:
        max_length = len(zone)

    print utils.FormatOutputString('Timezone', 'UTC Offset', max_length)
    for zone in pytz.all_timezones:
      zone_obj = pytz.timezone(zone)
      date_str = str(zone_obj.localize(datetime.datetime.utcnow()))
      if '+' in date_str:
        _, _, diff = date_str.rpartition('+')
        diff_string = u'+{0:s}'.format(diff)
      else:
        _, _, diff = date_str.rpartition('-')
        diff_string = u'-{0:s}'.format(diff)
      print utils.FormatOutputString(zone, diff_string, max_length)
    print u'-' * 80
    sys.exit(0)

  if my_args.analysis_plugins == 'list':
    print utils.FormatHeader('Analysis Modules')
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

      text = u'{0:s} [{1:s}]'.format(description, type_string)
      print utils.FormatOutputString(name, text, format_length)
    print u'-' * 80
    sys.exit(0)

  if my_args.output_format == 'list':
    print utils.FormatHeader('Output Modules')
    for name, description in output_lib.ListOutputFormatters():
      print utils.FormatOutputString(name, description, 10)
    print u'-' * 80
    sys.exit(0)

  if not my_args.storagefile:
    parser.print_help()
    print u''
    parser.print_usage()
    print u''
    logging.error('STORAGEFILE required! or -h for HELP')
    sys.exit(0)

  if not os.path.isfile(my_args.storagefile):
    parser.print_help()
    print u''
    parser.print_usage()
    print u''
    logging.error(u'Storage file {0:s} does not exist.'.format(
        my_args.storagefile))
    sys.exit(0)

  if not my_args.write:
    my_args.write = sys.stdout

  # Add local encoding settings.
  my_args.preferred_encoding = locale.getpreferredencoding()
  if my_args.preferred_encoding.lower() == 'ascii':
    logging.warning(
        u'The preferred encoding of your system is ASCII, which is not optimal '
        u'for the typically non-ASCII characters that need to be parsed and '
        u'processed. The tool will most likely crash and die, perhaps in a way '
        u'that may not be recoverable. A five second delay is introduced to '
        u'give you time to cancel the runtime and reconfigure your preferred '
        u'encoding, otherwise continue at own risk.')
    time.sleep(5)

  return my_args


def Main(my_args):
  """Start the tool."""
  try:
    counter = ParseStorage(my_args)

    if not my_args.quiet:
      logging.info(utils.FormatHeader('Counter'))
      for element, count in counter.most_common():
        logging.info(utils.FormatOutputString(element, count))
  except IOError as exception:
    # Piping results to "|head" for instance causes an IOError.
    if 'Broken pipe' not in str(exception):
      logging.error('Processing stopped early: {0:s}.'.format(exception))
  except KeyboardInterrupt:
    pass
  # Catching a very generic error in case we would like to debug
  # a potential crash in the tool.
  except Exception:
    if not my_args.debug:
      raise
    pdb.post_mortem()


if __name__ == '__main__':
  multiprocessing.freeze_support()
  my_options = ProcessArguments(sys.argv[1:])
  Main(my_options)
