# -*- coding: utf-8 -*-
"""The psort front-end."""

import collections
import multiprocessing
import logging
import sys

from plaso import formatters   # pylint: disable=unused-import
from plaso import output   # pylint: disable=unused-import

from plaso.analysis import manager as analysis_manager
from plaso.analysis import mediator as analysis_mediator
from plaso.cli import tools as cli_tools
from plaso.engine import knowledge_base
from plaso.engine import queue
from plaso.frontend import analysis_frontend
from plaso.frontend import frontend
from plaso.lib import bufferlib
from plaso.lib import pfilter
from plaso.lib import timelib
from plaso.multi_processing import multi_process
from plaso.output import interface as output_interface
from plaso.output import manager as output_manager
from plaso.output import mediator as output_mediator
from plaso.proto import plaso_storage_pb2
from plaso.serializer import protobuf_serializer

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
    self._output_file_object = None
    self._output_format = None
    self._preferred_language = u'en-US'

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

  def HasOutputClass(self, name):
    """Determines if a specific output class is registered with the manager.

    Args:
      name: The name of the output module.

    Returns:
      A boolean indicating if the output class is registered.
    """
    return output_manager.OutputManager.HasOutputClass(name)

  def GetAnalysisPlugins(self):
    """Retrieves the available analysis plugins.

    Returns:
      A sorted list of available plugin names and docstrings.
    """
    return analysis_manager.AnalysisPluginManager.ListAllPluginNames()

  def GetOutputClasses(self):
    """Retrieves the available output classes.

    Returns:
      An output module generator which yields tuples of output class names
      and type object.
    """
    return output_manager.OutputManager.GetOutputClasses()

  def GetTimeSlice(self, event_time_string, duration=5, timezone=pytz.UTC):
    """Retrieves a time slice.

    Args:
      event_time_string: event time string of the time slice or None.
      duration: optional duration of the time slize in minutes.
                The default is 5, which represent 2.5 minutes before
                and 2.5 minutes after the event timestamp.
      timezone: optional timezone. The default is UTC.

    Returns:
      A time slice object (instance of TimeSlice).
    """
    if event_time_string:
      event_timestamp = timelib.Timestamp.FromTimeString(
          event_time_string, timezone=timezone)
    else:
      event_timestamp = None

    return frontend.TimeSlice(event_timestamp, duration=duration)

  def _ProcessAnalysisPlugins(
      self, analysis_plugins, event_queue_producers, analysis_output_queue,
      storage_file, counter, preferred_encoding=u'utf-8'):
    """Runs the analysis plugins.

    Args:
      analysis_plugins: the analysis plugins.
      event_queue_producers: a list of event queue producter objects
                             (instances of ItemQueueProducer).
      analysis_output_queue: the analysis output queue (instance of Queue).
      storage_file: a storage file object (instance of StorageFile).
      counter: a counter object (instance of collections.Counter).
      preferred_encoding: optional preferred encoding. The default is "utf-8".
    """
    if not analysis_plugins:
      return

    logging.info(u'Processing data from analysis plugins.')
    for event_queue_producer in event_queue_producers:
      event_queue_producer.SignalEndOfInput()

    # Wait for all analysis plugins to complete.
    for number, analysis_process in enumerate(self._analysis_processes):
      logging.debug(
          u'Waiting for analysis plugin: {0:d} to complete.'.format(number))

      if analysis_process.is_alive():
        analysis_process.join(timeout=10)
      else:
        logging.warning(u'Plugin {0:d} already stopped.'.format(number))
        analysis_process.terminate()

    logging.debug(u'All analysis plugins are now stopped.')

    # Close the output queue.
    analysis_output_queue.SignalAbort()

    # Go over each output.
    analysis_queue_consumer = PsortAnalysisReportQueueConsumer(
        analysis_output_queue, storage_file, self._filter_expression,
        preferred_encoding=preferred_encoding)

    analysis_queue_consumer.ConsumeItems()

    if analysis_queue_consumer.tags:
      storage_file.StoreTagging(analysis_queue_consumer.tags)

    # TODO: analysis_queue_consumer.anomalies:

    for item, value in analysis_queue_consumer.counter.iteritems():
      counter[item] = value

  def ProcessStorage(
      self, options, analysis_plugins, analysis_plugins_output_format,
      deduplicate_events=True, preferred_encoding=u'utf-8', time_slice=None,
      timezone=pytz.UTC, use_time_slicer=False):
    """Processes a plaso storage file.

    Args:
      options: the command line arguments (instance of argparse.Namespace).
      analysis_plugins: the analysis plugins.
      analysis_plugins_output_format: the analysis plugins output format.
      deduplicate_events: optional boolean value to indicate if the event
                          objects should be deduplicated. The default is True.
      preferred_encoding: optional preferred encoding. The default is "utf-8".
      time_slice: optional time slice object (instance of TimeSlice).
                  The default is None.
      timezone: optional timezone. The default is UTC.
      use_time_slicer: optional boolean value to indicate the 'time slicer'
                       should be used. The default is False. The 'time slicer'
                       will provide a context of events around an event of
                       interest.

    Returns:
      A counter (an instance of counter.Counter) that contains the analysis
      plugin results or None.

    Raises:
      RuntimeError: if a non-recoverable situation is encountered.
    """
    # TODO: remove this in psort options refactor.
    self._output_format = getattr(options, u'output_format', None)
    self._output_filename = getattr(options, u'write', None)

    if time_slice:
      if time_slice.event_timestamp:
        pfilter.TimeRangeCache.SetLowerTimestamp(time_slice.start_timestamp)
        pfilter.TimeRangeCache.SetUpperTimestamp(time_slice.end_timestamp)

      elif use_time_slicer:
        self._filter_buffer = bufferlib.CircularBuffer(time_slice.duration)

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

    counter = None
    with storage_file:
      storage_file.SetStoreLimit(self._filter_object)

      formatter_mediator = self.GetFormatterMediator()

      try:
        formatter_mediator.SetPreferredLanguageIdentifier(
            self._preferred_language)
      except (KeyError, TypeError) as exception:
        raise RuntimeError(exception)

      output_mediator_object = output_mediator.OutputMediator(
          formatter_mediator, storage_file, config=options,
          preferred_encoding=preferred_encoding, timezone=timezone)

      kwargs = {}
      # TODO: refactor this to use CLI argument helpers.
      if self._output_format in [u'pstorage', u'sql4n6']:
        kwargs[u'filehandle'] = self._output_filename
      elif self._output_format not in [u'elastic', u'timesketch']:
        if self._output_filename:
          self._output_file_object = open(self._output_filename, 'wb')
          kwargs[u'output_writer'] = cli_tools.FileObjectOutputWriter(
              self._output_file_object)
        else:
          kwargs[u'output_writer'] = self._output_writer

      try:
        output_module = output_manager.OutputManager.NewOutputModule(
            self._output_format, output_mediator_object, **kwargs)

      except IOError as exception:
        raise RuntimeError(
            u'Unable to create output module with error: {0:s}'.format(
                exception))

      if not output_module:
        raise RuntimeError(u'Missing output module.')

      # TODO: allow for single processing.
      # TODO: add upper queue limit.
      analysis_output_queue = multi_process.MultiProcessingQueue()

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
        if preferred_encoding:
          cmd_line = u' '.join(sys.argv)
          try:
            pre_obj.collection_information[u'cmd_line'] = cmd_line.decode(
                preferred_encoding)
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

        analysis_plugins = analysis_manager.AnalysisPluginManager.LoadPlugins(
            analysis_plugins_list, event_queues, options=options)

        # Now we need to start all the plugins.
        for analysis_plugin in analysis_plugins:
          analysis_report_queue_producer = queue.ItemQueueProducer(
              analysis_output_queue)

          analysis_mediator_object = analysis_mediator.AnalysisMediator(
              analysis_report_queue_producer, knowledge_base_object,
              output_format=analysis_plugins_output_format)
          analysis_process = multiprocessing.Process(
              name=u'Analysis {0:s}'.format(analysis_plugin.plugin_name),
              target=analysis_plugin.RunPlugin,
              args=(analysis_mediator_object,))
          self._analysis_processes.append(analysis_process)

          analysis_process.start()
          logging.info(
              u'Plugin: [{0:s}] started.'.format(analysis_plugin.plugin_name))
      else:
        event_queue_producers = []

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

      # TODO: refactor to separate function.
      if not getattr(options, u'quiet', False):
        logging.info(u'Output processing is done.')

      # Get all reports and tags from analysis plugins.
      self._ProcessAnalysisPlugins(
          analysis_plugins, event_queue_producers, analysis_output_queue,
          storage_file, counter, preferred_encoding=preferred_encoding)

    if self._output_file_object:
      self._output_file_object.close()
      self._output_file_object = None

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
      self, queue_object, storage_file, filter_string,
      preferred_encoding=u'utf-8'):
    """Initializes the queue consumer.

    Args:
      queue_object: the queue object (instance of Queue).
      storage_file: the storage file (instance of StorageFile).
      filter_string: the filter string.
      preferred_encoding: optional preferred encoding. The default is "utf-8".
    """
    super(PsortAnalysisReportQueueConsumer, self).__init__(queue_object)
    self._filter_string = filter_string
    self._preferred_encoding = preferred_encoding
    self._storage_file = storage_file
    self.anomalies = []
    self.counter = collections.Counter()
    self.tags = []

  def _ConsumeItem(self, analysis_report, **unused_kwargs):
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
