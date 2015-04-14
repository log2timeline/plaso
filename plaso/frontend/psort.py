# -*- coding: utf-8 -*-
"""The psort front-end."""

import collections
import datetime
import multiprocessing
import logging
import sys

from plaso import analysis
from plaso import filters
from plaso import formatters   # pylint: disable=unused-import
from plaso import output   # pylint: disable=unused-import

from plaso.analysis import context as analysis_context
from plaso.analysis import interface as analysis_interface
from plaso.artifacts import knowledge_base
from plaso.engine import queue
from plaso.frontend import analysis_frontend
from plaso.frontend import frontend
from plaso.lib import bufferlib
from plaso.lib import errors
from plaso.lib import pfilter
from plaso.lib import timelib
from plaso.multi_processing import multi_process
from plaso.output import interface as output_interface
from plaso.output import manager as output_manager
from plaso.output import mediator as output_mediator
from plaso.proto import plaso_storage_pb2
from plaso.serializer import protobuf_serializer
from plaso.winnt import language_ids

import pytz


class PsortFrontend(analysis_frontend.AnalysisFrontend):
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
    self._output_filename = None
    self._output_format = None
    self._preferred_language = u'en-US'
    self._slice_size = 5

  def _AppendEvent(self, event_object, output_buffer, event_queues):
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
    inode = getattr(event_object, u'inode', None)
    if isinstance(inode, basestring):
      inode_list = inode.split(u';')
      try:
        new_inode = int(inode_list[0], 10)
      except (ValueError, IndexError):
        new_inode = 0

      event_object.inode = new_inode

    for event_queue in event_queues:
      event_queue.ProduceItem(event_object)

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
    if module_names == u'list':
      return

    modules_list = set([name.lower() for name in module_names])

    manager = output_manager.OutputManager
    for output_module_string, _ in manager.GetOutputs():
      if not output_module_string.lower() in modules_list:
        continue

      output_module = manager.GetOutputClass(output_module_string)
      if output_module.ARGUMENTS:
        for parameter, config in output_module.ARGUMENTS:
          argument_group.add_argument(parameter, **config)

  def ListAnalysisPlugins(self):
    """Lists the analysis modules."""
    self.PrintHeader(u'Analysis Modules')
    format_length = 10
    for name, _, _ in analysis.ListAllPluginNames():
      if len(name) > format_length:
        format_length = len(name)

    for name, description, plugin_type in analysis.ListAllPluginNames():
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
    manager = output_manager.OutputManager
    for name, description in manager.GetOutputs():
      self.PrintColumnValue(name, description, 10)
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

  def ParseOptions(self, options):
    """Parses the options and initializes the front-end.

    Args:
      options: the command line arguments (instance of argparse.Namespace).

    Raises:
      BadConfigOption: if the options are invalid.
    """
    super(PsortFrontend, self).ParseOptions(options)

    self._output_format = getattr(options, u'output_format', None)
    if not self._output_format:
      raise errors.BadConfigOption(u'Missing output format.')

    if not output_manager.OutputManager.HasOutputClass(self._output_format):
      raise errors.BadConfigOption(
          u'Unsupported output format: {0:s}.'.format(self._output_format))

    self._output_filename = getattr(options, u'write', None)

    self._filter_expression = getattr(options, u'filter', None)
    if self._filter_expression:
      self._filter_object = filters.GetFilter(self._filter_expression)
      if not self._filter_object:
        raise errors.BadConfigOption(
            u'Invalid filter expression: {0:s}'.format(self._filter_expression))

      # Check to see if we need to create a circular buffer.
      if getattr(options, u'slicer', None):
        self._slice_size = getattr(options, u'slice_size', 5)
        self._filter_buffer = bufferlib.CircularBuffer(self._slice_size)

    self._preferred_language = getattr(options, u'preferred_language', u'en-US')

  def ProcessStorage(self, options):
    """Open a storage file and processes the events within.

    Args:
      options: the command line arguments (instance of argparse.Namespace).

    Returns:
      A counter.

    Raises:
      RuntimeError: if a non-recoverable situation is encountered.
    """
    counter = None

    slice_option = getattr(options, u'slice', None)
    if slice_option:
      timezone = getattr(options, u'timezone', u'UTC')
      if timezone == u'UTC':
        zone = pytz.UTC
      else:
        zone = pytz.timezone(timezone)

      timestamp = timelib.Timestamp.FromTimeString(slice_option, timezone=zone)

      # Convert number of minutes to microseconds.
      range_operator = self._slice_size * 60 * 1000000

      # Set the time range.
      pfilter.TimeRangeCache.SetLowerTimestamp(timestamp - range_operator)
      pfilter.TimeRangeCache.SetUpperTimestamp(timestamp + range_operator)

    analysis_plugins = getattr(options, u'analysis_plugins', u'')
    if analysis_plugins:
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

      if self._output_filename:
        output_stream = self._output_filename
      else:
        output_stream = sys.stdout

      formatter_mediator = self.GetFormatterMediator()

      try:
        formatter_mediator.SetPreferredLanguageIdentifier(
            self._preferred_language)
      except (KeyError, TypeError) as exception:
        raise RuntimeError(exception)

      output_mediator_object = output_mediator.OutputMediator(
          formatter_mediator, storage_file, config=options)

      kwargs = {}
      if self._filter_object:
        kwargs[u'field_filter'] = self._filter_object
      if output_stream:
        kwargs[u'filehandle'] = output_stream

      try:
        output_module = output_manager.OutputManager.NewOutputModule(
            self._output_format, output_mediator_object, **kwargs)

      except IOError as exception:
        raise RuntimeError(
            u'Unable to create output module with error: {0:s}'.format(
                exception))

      if not output_module:
        raise RuntimeError(u'Missing output module.')

      if analysis_plugins:
        logging.info(u'Starting analysis plugins.')
        # Within all preprocessing objects, try to get the last one that has
        # time zone information stored in it, the highest chance of it
        # containing the information we are seeking (defaulting to the last
        # one).
        pre_objs = storage_file.GetStorageInformation()
        pre_obj = pre_objs[-1]
        for obj in pre_objs:
          if getattr(obj, u'time_zone_str', u''):
            pre_obj = obj

        # Fill in the collection information.
        pre_obj.collection_information = {}
        encoding = getattr(pre_obj, u'preferred_encoding', None)
        if encoding:
          cmd_line = u' '.join(sys.argv)
          try:
            pre_obj.collection_information[u'cmd_line'] = cmd_line.decode(
                encoding)
          except UnicodeDecodeError:
            pass
        pre_obj.collection_information[u'file_processed'] = (
            self._storage_file_path)
        pre_obj.collection_information[u'method'] = u'Running Analysis Plugins'
        pre_obj.collection_information[u'plugins'] = analysis_plugins
        time_of_run = timelib.Timestamp.GetNow()
        pre_obj.collection_information[u'time_of_run'] = time_of_run

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
            name.strip() for name in analysis_plugins.split(u',')]

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
              name=u'Analysis {0:s}'.format(analysis_plugin.plugin_name),
              target=analysis_plugin.RunPlugin, args=(analysis_context_object,))
          self._analysis_processes.append(analysis_process)

          analysis_process.start()
          logging.info(
              u'Plugin: [{0:s}] started.'.format(analysis_plugin.plugin_name))
      else:
        event_queue_producers = []

      deduplicate_events = getattr(options, u'dedup', True)
      output_buffer = output_interface.EventBuffer(
          output_module, deduplicate_events)
      with output_buffer:
        counter = self.ProcessOutput(
            storage_file, output_buffer, my_filter=self._filter_object,
            filter_buffer=self._filter_buffer,
            analysis_queues=event_queue_producers)

      for information in storage_file.GetStorageInformation():
        if hasattr(information, u'counter'):
          counter[u'Stored Events'] += information.counter[u'total']

      if not getattr(options, u'quiet', False):
        logging.info(u'Output processing is done.')

      # Get all reports and tags from analysis plugins.
      if analysis_plugins:
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

    if self._filter_object and not counter[u'Limited By']:
      counter[u'Filter By Date'] = (
          counter[u'Stored Events'] - counter[u'Events Included'] -
          counter[u'Events Filtered Out'])

    return counter

  def ProcessOutput(
      self, storage_file, output_buffer, my_filter=None, filter_buffer=None,
      analysis_queues=None):
    """Reads event objects from the storage to process and filter them.

    Args:
      storage_file: The storage file object (instance of StorageFile).
      output_buffer: The output buffer object (instance of EventBuffer).
      my_filter: Optional filter object (instance of PFilter).
                 The default is None.
      filter_buffer: Optional filter buffer used to store previously discarded
                     events to store time slice history. The default is None.
      analysis_queues: Optional list of analysis queues. The default is None.
    """
    counter = collections.Counter()
    my_limit = getattr(my_filter, u'limit', 0)
    forward_entries = 0
    if not analysis_queues:
      analysis_queues = []

    event_object = storage_file.GetSortedEntry()
    while event_object:
      if my_filter:
        event_match = event_object
        if isinstance(event_object, plaso_storage_pb2.EventObject):
          # TODO: move serialization to storage, if low-level filtering is
          # needed storage should provide functions for it.
          serializer = protobuf_serializer.ProtobufEventObjectSerializer
          event_match = serializer.ReadSerialized(event_object)

        if my_filter.Match(event_match):
          counter[u'Events Included'] += 1
          if filter_buffer:
            # Indicate we want forward buffering.
            forward_entries = 1
            # Empty the buffer.
            for event_in_buffer in filter_buffer.Flush():
              counter[u'Events Added From Slice'] += 1
              counter[u'Events Included'] += 1
              counter[u'Events Filtered Out'] -= 1
              self._AppendEvent(event_in_buffer, output_buffer, analysis_queues)
          self._AppendEvent(event_object, output_buffer, analysis_queues)
          if my_limit:
            if counter[u'Events Included'] == my_limit:
              break
        else:
          if filter_buffer and forward_entries:
            if forward_entries <= filter_buffer.size:
              self._AppendEvent(event_object, output_buffer, analysis_queues)
              forward_entries += 1
              counter[u'Events Added From Slice'] += 1
              counter[u'Events Included'] += 1
            else:
              # Reached the max, don't include other entries.
              forward_entries = 0
              counter[u'Events Filtered Out'] += 1
          elif filter_buffer:
            filter_buffer.Append(event_object)
            counter[u'Events Filtered Out'] += 1
          else:
            counter[u'Events Filtered Out'] += 1
      else:
        counter[u'Events Included'] += 1
        self._AppendEvent(event_object, output_buffer, analysis_queues)

      event_object = storage_file.GetSortedEntry()

    if output_buffer.duplicate_counter:
      counter[u'Duplicate Removals'] = output_buffer.duplicate_counter

    if my_limit:
      counter[u'Limited By'] = my_limit
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
    self.counter[u'Total Reports'] += 1
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
