# -*- coding: utf-8 -*-
"""The psort front-end."""

from __future__ import print_function
import collections
import logging
import time

from plaso.engine import plaso_queue
from plaso.engine import zeromq_queue
from plaso.lib import bufferlib
from plaso.lib import py2to3
from plaso.multi_processing import analysis_process
from plaso.multi_processing import engine as multi_process_engine
from plaso.multi_processing import multi_process_queue
from plaso.output import event_buffer as output_event_buffer
from plaso.storage import time_range as storage_time_range


class PsortAnalysisReportQueueConsumer(plaso_queue.ItemQueueConsumer):
  """Class that implements an analysis report queue consumer.

  The consumer subscribes to updates on the queue and writes the analysis
  reports to the storage.
  """

  def __init__(
      self, queue, storage_writer, filter_string, preferred_encoding=u'utf-8'):
    """Initializes the item queue consumer.

    Args:
      queue (Queue): queue.
      storage_writer (StorageWriter): storage writer.
      filter_string (str): string containing the filter expression.
      preferred_encoding (Optional[str]): preferred encoding.
    """
    super(PsortAnalysisReportQueueConsumer, self).__init__(queue)
    self._filter_string = filter_string
    self._preferred_encoding = preferred_encoding
    self._storage_writer = storage_writer

  def _ConsumeItem(self, analysis_report, **unused_kwargs):
    """Consumes an item callback for ConsumeItems.

    Args:
      analysis_report (AnalysisReport): analysis report.
    """
    if self._filter_string:
      analysis_report.filter_string = self._filter_string

    # For now we print the report to disk and then save it.
    # TODO: Have the option of saving to a separate file and
    # do something more here, for instance saving into a HTML
    # file, or something else (including potential images).
    self._storage_writer.AddAnalysisReport(analysis_report)

    report_string = analysis_report.GetString()
    try:
      # TODO: move this print to the psort tool or equivalent.
      print(report_string.encode(self._preferred_encoding))

    except UnicodeDecodeError:
      logging.error(
          u'Unable to print report due to a Unicode decode error. '
          u'The report is stored inside the storage file and can be '
          u'viewed using pinfo [if unable to view please submit a '
          u'bug report https://github.com/log2timeline/plaso/issues')


# TODO: used for refactoring.
class PsortMultiProcessEngine(multi_process_engine.MultiProcessEngine):
  """Class that defines the psort multi-processing engine."""

  # The number of seconds to wait for analysis plugins to compile their reports.
  _ANALYSIS_PLUGIN_TIMEOUT = 60

  def __init__(
      self, debug_output=False, enable_profiling=False,
      profiling_directory=None, profiling_sample_rate=1000,
      profiling_type=u'all', use_zeromq=True):
    """Initializes an engine object.

    Args:
      debug_output (Optional[bool]): True if debug output should be enabled.
      enable_profiling (Optional[bool]): True if profiling should be enabled.
      profiling_directory (Optional[str]): path to the directory where
          the profiling sample files should be stored.
      profiling_sample_rate (Optional[int]): the profiling sample rate.
          Contains the number of event sources processed.
      profiling_type (Optional[str]): type of profiling.
          Supported types are:

          * 'memory' to profile memory usage;
          * 'parsers' to profile CPU time consumed by individual parsers;
          * 'processing' to profile CPU time consumed by different parts of
            the processing;
          * 'serializers' to profile CPU time consumed by individual
            serializers.
      use_zeromq (Optional[bool]): True if ZeroMQ should be used for queuing
          instead of Python's multiprocessing queue.
    """
    super(PsortMultiProcessEngine, self).__init__(
        debug_output=debug_output, enable_profiling=enable_profiling,
        profiling_directory=profiling_directory,
        profiling_sample_rate=profiling_sample_rate,
        profiling_type=profiling_type)
    self._analysis_report_queue = None
    self._analysis_report_queue_port = None
    self._event_queues = []
    self._use_zeromq = use_zeromq

  def _AppendEvent(self, event, event_buffer):
    """Appends an event object to an event output buffer and analysis queues.

    Args:
      event (EventObject): event.
      event_buffer (EventBuffer): output event buffer.
    """
    event_buffer.Append(event)

    # TODO: refactor.
    # Needed for duplicate removals, if two events
    # are merged then we'll just pick the first inode value.
    inode = event.inode
    if isinstance(inode, py2to3.STRING_TYPES):
      inode_list = inode.split(u';')
      try:
        new_inode = int(inode_list[0], 10)
      except (IndexError, ValueError):
        new_inode = 0

      event.inode = new_inode

    for event_queue in self._event_queues:
      event_queue.PushItem(event)

  def _ProcessAnalysisPlugins(
      self, storage_writer, filter_expression=None,
      preferred_encoding=u'utf-8'):
    """Runs the analysis plugins.

    Args:
      storage_writer (StorageWriter): storage writer.
      filter_expression (Optional[str]): filter expression.
      preferred_encoding (Optional[str]): preferred encoding.
    """
    logging.info(u'Processing data from analysis plugins.')

    # Wait for all analysis plugins to complete.
    for pid, process in iter(self._processes_per_pid.items()):
      name = process.plugin.NAME
      if process.plugin.LONG_RUNNING_PLUGIN:
        logging.warning((
            u'{0:s} PID: {1:d} may take a long time to run. It will not '
            u'be automatically terminated.').format(name, pid))
        report_wait = None
      else:
        report_wait = self._ANALYSIS_PLUGIN_TIMEOUT

      logging.info(
          u'Waiting for analysis plugin: {0:s} to complete.'.format(name))

      if process.completion_event.wait(report_wait):
        logging.info(u'Plugin {0:s} has completed.'.format(name))
      else:
        logging.warning(
            u'Analysis process {0:s} failed to compile its report in a '
            u'reasonable time. No report will be displayed or stored.'.format(
                name))

    logging.info(u'All analysis plugins are now completed.')

    analysis_report_consumer = PsortAnalysisReportQueueConsumer(
        self._analysis_report_queue, storage_writer,
        filter_expression, preferred_encoding=preferred_encoding)

    analysis_report_consumer.ConsumeItems()

  def _ProcessEventsFromStorage(
      self, storage_reader, output_buffer, filter_buffer=None,
      filter_object=None, time_slice=None):
    """Reads event objects from the storage to process and filter them.

    Args:
      storage_reader (StorageReader): storage reader.
      output_buffer (EventBuffer): output event buffer.
      filter_buffer (Optional[CircularBuffer]): filter buffer used to store
          previously discarded events to store time slice history.
      filter_object (Optional[FilterObject]): event filter.
      time_slice (Optional[TimeRange]): time range that defines a time slice
          to filter events.

    Returns:
      collections.Counter: counter that tracks the number of unique events
          extracted from storage.
    """
    counter = collections.Counter()
    my_limit = getattr(filter_object, u'limit', 0)
    forward_entries = 0

    for event in storage_reader.GetEvents(time_range=time_slice):
      # TODO: clean up this function.
      if not filter_object:
        counter[u'Events Included'] += 1
        self._AppendEvent(event, output_buffer)
      else:
        if filter_object.Match(event):
          counter[u'Events Included'] += 1
          if filter_buffer:
            # Indicate we want forward buffering.
            forward_entries = 1
            # Empty the buffer.
            for event_in_buffer in filter_buffer.Flush():
              counter[u'Events Added From Slice'] += 1
              counter[u'Events Included'] += 1
              counter[u'Events Filtered Out'] -= 1
              self._AppendEvent(event_in_buffer, output_buffer)
          self._AppendEvent(event, output_buffer)
          if my_limit:
            if counter[u'Events Included'] == my_limit:
              break
        else:
          if filter_buffer and forward_entries:
            if forward_entries <= filter_buffer.size:
              self._AppendEvent(event, output_buffer)
              forward_entries += 1
              counter[u'Events Added From Slice'] += 1
              counter[u'Events Included'] += 1
            else:
              # Reached the max, don't include other entries.
              forward_entries = 0
              counter[u'Events Filtered Out'] += 1
          elif filter_buffer:
            filter_buffer.Append(event)
            counter[u'Events Filtered Out'] += 1
          else:
            counter[u'Events Filtered Out'] += 1

    for event_queue in self._event_queues:
      event_queue.Close()

    if output_buffer.duplicate_counter:
      counter[u'Duplicate Removals'] = output_buffer.duplicate_counter

    if my_limit:
      counter[u'Limited By'] = my_limit
    return counter

  def _ProcessStorage(
      self, knowledge_base_object, storage_writer, output_module, data_location,
      analysis_plugins, deduplicate_events=True, filter_expression=None,
      filter_object=None, preferred_encoding=u'utf-8', time_slice=None,
      use_time_slicer=False):
    """Processes a plaso storage file.

    Args:
      knowledge_base_object (KnowledgeBase): contains information from
          the source data needed for processing.
      storage_writer (StorageWriter): storage writer.
      output_module (OutputModule): output module.
      data_location (str): path to the location that data files should
          be loaded from.
      analysis_plugins (list[AnalysisPlugin]): analysis plugins that should
          be run.
      deduplicate_events (Optional[bool]): True if events should be
          deduplicated.
      filter_expression (Optional[str]): filter expression.
      filter_object (Optional[FilterObject]): event filter.
      preferred_encoding (Optional[str]): preferred encoding.
      time_slice (Optional[TimeSlice]): slice of time to output.
      use_time_slicer (Optional[bool]): True if the 'time slicer' should be
          used. The 'time slicer' will provide a context of events around
          an event of interest.

    Returns:
      collections.Counter: counter that tracks the number of events extracted
          from storage and the analysis plugin results.

    Raises:
      RuntimeError: if a non-recoverable situation is encountered.
    """
    filter_buffer = None
    if time_slice:
      if time_slice.event_timestamp is not None:
        time_slice = storage_time_range.TimeRange(
            time_slice.start_timestamp, time_slice.end_timestamp)

      elif use_time_slicer:
        filter_buffer = bufferlib.CircularBuffer(time_slice.duration)

    # TODO: allow for single processing.
    # TODO: add upper queue limit.
    if self._use_zeromq:
      self._analysis_report_queue = zeromq_queue.ZeroMQPullBindQueue(
          delay_open=False, port=None, linger_seconds=5)
      self._analysis_report_queue_port = self._analysis_report_queue.port
    else:
      self._analysis_report_queue = multi_process_queue.MultiProcessingQueue(
          timeout=5)
      self._analysis_report_queue_port = None

    self._StartAnalysisProcesses(
        knowledge_base_object, analysis_plugins, data_location)

    # TODO: refactor to first apply the analysis plugins
    # then generate the output.
    output_buffer = output_event_buffer.EventBuffer(
        output_module, deduplicate_events)
    with output_buffer:
      counter = self._ProcessEventsFromStorage(
          storage_writer, output_buffer, filter_buffer=filter_buffer,
          filter_object=filter_object, time_slice=time_slice)

    self._ProcessAnalysisPlugins(
        storage_writer, filter_expression=filter_expression,
        preferred_encoding=preferred_encoding)

    return counter

  def _StartAnalysisProcesses(
      self, knowledge_base_object, analysis_plugins, data_location):
    """Starts the analysis processes.

    Args:
      knowledge_base_object (KnowledgeBase): contains information from
          the source data needed for processing.
      analysis_plugins (list[AnalysisPlugin]): analysis plugins that should
          be run.
      data_location (str): path to the location that data files should
          be loaded from.
    """
    logging.info(u'Starting analysis plugins.')

    for analysis_plugin in analysis_plugins:
      if self._use_zeromq:
        output_event_queue = zeromq_queue.ZeroMQPushBindQueue()
        # Open the queue so it can bind to a random port, and we can get the
        # port number to use in the input queue.
        output_event_queue.Open()

      else:
        output_event_queue = multi_process_queue.MultiProcessingQueue(timeout=5)

      self._event_queues.append(output_event_queue)

      if self._use_zeromq:
        input_event_queue = zeromq_queue.ZeroMQPullConnectQueue(
            delay_open=True, port=output_event_queue.port)

        analysis_report_queue = zeromq_queue.ZeroMQPushConnectQueue(
            delay_open=True, port=self._analysis_report_queue_port)

      else:
        input_event_queue = output_event_queue
        analysis_report_queue = self._analysis_report_queue

      process_name = u'Analysis {0:s}'.format(analysis_plugin.plugin_name)
      process = analysis_process.AnalysisProcess(
          input_event_queue, analysis_report_queue, knowledge_base_object,
          analysis_plugin, data_location=data_location,
          name=process_name)

      self._RegisterProcess(process)

      process.start()

      logging.info(u'Started analysis plugin: {0:s} (PID: {1:d}).'.format(
          analysis_plugin.plugin_name, process.pid))

    logging.info(u'Analysis plugins running')

  def _StatusUpdateThreadMain(self):
    """Main function of the status update thread."""
    while self._status_update_active:
      # Make a local copy of the PIDs in case the dict is changed by
      # the main thread.
      for pid in list(self._process_information_per_pid.keys()):
        # TODO: implement
        _ = pid

      if self._status_update_callback:
        # pylint: disable=not-callable
        self._status_update_callback(self._processing_status)

      time.sleep(self._STATUS_UPDATE_INTERVAL)

  def ExportEventsWithOutputModule(
      self, knowledge_base_object, storage_reader, output_module,
      deduplicate_events=True, filter_object=None, time_slice=None,
      use_time_slicer=False):
    """Exports events using an output module.

    Args:
      knowledge_base_object (KnowledgeBase): contains information from
          the source data needed for processing.
      storage_reader (StorageReader): storage reader.
      output_module (OutputModule): output module.
      deduplicate_events (Optional[bool]): True if events should be
          deduplicated.
      filter_object (Optional[FilterObject]): event filter.
      time_slice (Optional[TimeSlice]): slice of time to output.
      use_time_slicer (Optional[bool]): True if the 'time slicer' should be
          used. The 'time slicer' will provide a context of events around
          an event of interest.

    Returns:
      collections.Counter: counter that tracks the number of events extracted
          from storage and the analysis plugin results.
    """
    filter_buffer = None
    if time_slice:
      if time_slice.event_timestamp is not None:
        time_slice = storage_time_range.TimeRange(
            time_slice.start_timestamp, time_slice.end_timestamp)

      elif use_time_slicer:
        filter_buffer = bufferlib.CircularBuffer(time_slice.duration)

    storage_reader.ReadPreprocessingInformation(knowledge_base_object)

    event_buffer = output_event_buffer.EventBuffer(
        output_module, deduplicate_events)
    with event_buffer:
      counter = self._ProcessEventsFromStorage(
          storage_reader, event_buffer, filter_buffer=filter_buffer,
          filter_object=filter_object, time_slice=time_slice)

    return counter

  def ProcessStorage(
      self, knowledge_base_object, storage_writer, output_module, data_location,
      analysis_plugins, deduplicate_events=True, filter_expression=None,
      filter_object=None, preferred_encoding=u'utf-8', time_slice=None,
      use_time_slicer=False):
    """Processes a plaso storage file.

    Args:
      knowledge_base_object (KnowledgeBase): contains information from
          the source data needed for processing.
      storage_writer (StorageWriter): storage writer.
      output_module (OutputModule): output module.
      data_location (str): path to the location that data files should
          be loaded from.
      analysis_plugins (list[AnalysisPlugin]): analysis plugins that should
          be run.
      deduplicate_events (Optional[bool]): True if events should be
          deduplicated.
      filter_expression (Optional[str]): filter expression.
      filter_object (Optional[FilterObject]): event filter.
      preferred_encoding (Optional[str]): preferred encoding.
      time_slice (Optional[TimeSlice]): slice of time to output.
      use_time_slicer (Optional[bool]): True if the 'time slicer' should be
          used. The 'time slicer' will provide a context of events around
          an event of interest.

    Returns:
      collections.Counter: counter that tracks the number of events extracted
          from storage and the analysis plugin results.
    """
    if not analysis_plugins:
      return

    self._StartStatusUpdateThread()

    storage_writer.Open()
    storage_writer.WriteSessionStart()

    try:
      counter = self._ProcessStorage(
          knowledge_base_object, storage_writer, output_module, data_location,
          analysis_plugins, deduplicate_events=deduplicate_events,
          filter_expression=filter_expression, filter_object=filter_object,
          preferred_encoding=preferred_encoding,
          time_slice=time_slice, use_time_slicer=use_time_slicer)

    except KeyboardInterrupt:
      self._abort = True

    finally:
      storage_writer.WriteSessionCompletion(aborted=self._abort)

      storage_writer.Close()

      self._StopStatusUpdateThread()

    return counter
