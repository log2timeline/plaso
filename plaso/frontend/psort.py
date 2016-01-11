# -*- coding: utf-8 -*-
"""The psort front-end."""

from __future__ import print_function
import collections
import multiprocessing
import logging

from plaso import formatters   # pylint: disable=unused-import
from plaso import output   # pylint: disable=unused-import

from plaso.analysis import manager as analysis_manager
from plaso.analysis import mediator as analysis_mediator
from plaso.engine import knowledge_base
from plaso.engine import queue
from plaso.engine import zeromq_queue
from plaso.frontend import analysis_frontend
from plaso.lib import bufferlib
from plaso.lib import event
from plaso.lib import timelib
from plaso.multi_processing import multi_process
from plaso.output import event_buffer as output_event_buffer
from plaso.output import manager as output_manager
from plaso.output import mediator as output_mediator
from plaso.proto import plaso_storage_pb2
from plaso.serializer import protobuf_serializer
from plaso.storage import time_range as storage_time_range

import pytz


class PsortFrontend(analysis_frontend.AnalysisFrontend):
  """Class that implements the psort front-end."""

  # The amount of time to wait for analysis plugins to compile their reports,
  # in seconds.
  MAX_ANALYSIS_PLUGIN_REPORT_WAIT = 60

  def __init__(self):
    """Initializes the front-end object."""
    super(PsortFrontend, self).__init__()

    self._analysis_process_info = []
    self._data_location = None
    self._filter_buffer = None
    self._filter_expression = None
    # Instance of EventObjectFilter.
    self._filter_object = None
    self._output_format = None
    self._preferred_language = u'en-US'
    self._quiet_mode = False
    self._use_zeromq = False

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

  def GetAnalysisPluginInfo(self):
    """Retrieves information about the registered analysis plugins.

    Returns:
      A sorted list of tuples containing the name, docstring and type of each
      analysis plugin.
    """
    return analysis_manager.AnalysisPluginManager.GetAllPluginInformation()

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

  def _ProcessAnalysisPlugins(
      self, analysis_plugins, analysis_report_incoming_queue, storage_file,
      counter, preferred_encoding=u'utf-8'):
    """Runs the analysis plugins.

    Args:
      analysis_plugins: the analysis plugins.
      analysis_report_incoming_queue: the analysis output queue (instance of
                                      Queue).
      storage_file: a storage file object (instance of StorageFile).
      counter: a counter object (instance of collections.Counter).
      preferred_encoding: optional preferred encoding.
    """
    if not analysis_plugins:
      return

    logging.info(u'Processing data from analysis plugins.')

    # Wait for all analysis plugins to complete.
    for analysis_process_info in self._analysis_process_info:
      name = analysis_process_info.plugin.NAME
      if analysis_process_info.plugin.LONG_RUNNING_PLUGIN:
        logging.warning(
            u'{0:s} may take a long time to run. It will not be automatically '
            u'terminated.'.format(name))
        report_wait = None
      else:
        report_wait = self.MAX_ANALYSIS_PLUGIN_REPORT_WAIT
      completion_event = analysis_process_info.completion_event
      logging.info(
          u'Waiting for analysis plugin: {0:s} to complete.'.format(name))
      if completion_event.wait(report_wait):
        logging.info(u'Plugin {0:s} has completed.'.format(name))
      else:
        logging.warning(
            u'Analysis process {0:s} failed to compile its report in a '
            u'reasonable time. No report will be displayed or stored.'.format(
                name))

    logging.info(u'All analysis plugins are now completed.')

    # Go over each output.
    analysis_queue_consumer = PsortAnalysisReportQueueConsumer(
        analysis_report_incoming_queue, storage_file, self._filter_expression,
        preferred_encoding=preferred_encoding)

    analysis_queue_consumer.ConsumeItems()

    if analysis_queue_consumer.tags:
      storage_file.StoreTagging(analysis_queue_consumer.tags)

    # TODO: analysis_queue_consumer.anomalies:

    for item, value in analysis_queue_consumer.counter.iteritems():
      counter[item] = value

  def _StartAnalysisPlugins(
      self, storage_file_path, analysis_plugins, pre_obj,
      analysis_queue_port=None, analysis_report_incoming_queue=None,
      command_line_arguments=None):
    """Start all the analysis plugin.

    Args:
      storage_file_path: string containing the path of the storage file.
      analysis_plugins: list of analysis plugin objects (instance of
                        AnalysisPlugin) that should be started.
      pre_obj: The preprocessor object (instance of PreprocessObject).
      analysis_queue_port: optional TCP port that the ZeroMQ analysis report
                           queues should use.
      analysis_report_incoming_queue: optional queue (instance of Queue) that
                                      reports should to pushed to, when ZeroMQ
                                      is not in use.
      command_line_arguments: optional string of the command line arguments or
                              None if not set.
    """
    logging.info(u'Starting analysis plugins.')
    self._SetAnalysisPluginProcessInformation(
        storage_file_path, analysis_plugins, pre_obj,
        command_line_arguments=command_line_arguments)

    knowledge_base_object = knowledge_base.KnowledgeBase(pre_obj=pre_obj)
    for analysis_plugin in analysis_plugins:
      if self._use_zeromq:
        analysis_plugin_output_queue = zeromq_queue.ZeroMQPushConnectQueue(
            delay_open=True, port=analysis_queue_port)
      else:
        analysis_plugin_output_queue = analysis_report_incoming_queue

      analysis_report_queue_producer = queue.ItemQueueProducer(
          analysis_plugin_output_queue)

      completion_event = multiprocessing.Event()
      analysis_mediator_object = analysis_mediator.AnalysisMediator(
          analysis_report_queue_producer, knowledge_base_object,
          data_location=self._data_location,
          completion_event=completion_event)
      analysis_process = multiprocessing.Process(
          name=u'Analysis {0:s}'.format(analysis_plugin.plugin_name),
          target=analysis_plugin.RunPlugin,
          args=(analysis_mediator_object,))

      process_info = PsortAnalysisProcess(
          completion_event, analysis_plugin, analysis_process)
      self._analysis_process_info.append(process_info)

      analysis_process.start()
      logging.info(
          u'Plugin: [{0:s}] started.'.format(analysis_plugin.plugin_name))

    logging.info(u'Analysis plugins running')

  def _SetAnalysisPluginProcessInformation(
      self, storage_file_path, analysis_plugins, pre_obj,
      command_line_arguments=None):
    """Sets analysis plugin options in a preprocessor object.

    Args:
      storage_file_path: string containing the path of the storage file.
      analysis_plugins: the list of analysis plugins to add.
      pre_obj: the preprocessor object (instance of PreprocessObject).
      command_line_arguments: optional string of the command line arguments or
                              None if not set.
    """
    analysis_plugin_names = [plugin.NAME for plugin in analysis_plugins]
    time_of_run = timelib.Timestamp.GetNow()

    pre_obj.collection_information[u'cmd_line'] = command_line_arguments
    pre_obj.collection_information[u'file_processed'] = storage_file_path
    pre_obj.collection_information[u'method'] = u'Running Analysis Plugins'
    pre_obj.collection_information[u'plugins'] = analysis_plugin_names
    pre_obj.collection_information[u'time_of_run'] = time_of_run
    pre_obj.counter = collections.Counter()

  # TODO: fix docstring, function does not create the pre_obj the call to
  # storage does. Likely refactor this functionality into the storage API.
  def _GetLastGoodPreprocess(self, storage_file):
    """Gets the last stored preprocessing object with time zone information.

    From all preprocessing objects, try to get the last one that has
    time zone information stored in it, the highest chance of it containing
    the information we are seeking (defaulting to the last one). If there are
    no preprocessing objects in the file, we'll make a new one

    Args:
      storage_file: a Plaso storage file object.

    Returns:
      A preprocess object (instance of PreprocessObject), or None if there are
      no preprocess objects in the storage file.
    """
    pre_objs = storage_file.GetStorageInformation()
    if not pre_objs:
      return None
    pre_obj = pre_objs[-1]
    for obj in pre_objs:
      if getattr(obj, u'time_zone_str', u''):
        pre_obj = obj

    return pre_obj

  def GetOutputModule(
      self, storage_file, preferred_encoding=u'utf-8', timezone=pytz.UTC):
    """Return an output module.

    Args:
      storage_file: a storage file object (instance of StorageFile).
      preferred_encoding: optional preferred encoding.
      timezone: optional timezone.

    Returns:
      an output module object (instance of OutputModule) or None if not able to
      open one up.

    Raises:
      RuntimeError: if a non-recoverable situation is encountered.
    """
    formatter_mediator = self.GetFormatterMediator()

    try:
      formatter_mediator.SetPreferredLanguageIdentifier(
          self._preferred_language)
    except (KeyError, TypeError) as exception:
      raise RuntimeError(exception)

    output_mediator_object = output_mediator.OutputMediator(
        formatter_mediator, preferred_encoding=preferred_encoding,
        timezone=timezone)
    output_mediator_object.SetStorageFile(storage_file)

    try:
      output_module = output_manager.OutputManager.NewOutputModule(
          self._output_format, output_mediator_object)

    except IOError as exception:
      raise RuntimeError(
          u'Unable to create output module with error: {0:s}'.format(
              exception))

    if not output_module:
      raise RuntimeError(u'Missing output module.')

    return output_module

  def GetAnalysisPluginsAndEventQueues(self, analysis_plugins_string):
    """Return a list of analysis plugins and event queues.

    Args:
      analysis_plugins_string: comma separated string with names of analysis
                               plugins to load.

    Returns:
      A tuple of two lists, one containing list of analysis plugins
      and the other a list of event queues.
    """
    if not analysis_plugins_string:
      return [], []

    event_producers = []
    # These are the queues analysis plugins will read from.
    analysis_plugin_input_queues = []
    analysis_plugins_list = [
        name.strip() for name in analysis_plugins_string.split(u',')]

    for _ in range(0, len(analysis_plugins_list)):
      if self._use_zeromq:
        output_queue = zeromq_queue.ZeroMQPushBindQueue()
        # Open the queue so it can bind to a random port, and we can get the
        # port number to use in the input queue.
        output_queue.Open()
        queue_port = output_queue.port
        input_queue = zeromq_queue.ZeroMQPullConnectQueue(
            port=queue_port, delay_open=True)
        analysis_plugin_input_queues.append(input_queue)
      else:
        input_queue = multi_process.MultiProcessingQueue(timeout=5)
        analysis_plugin_input_queues.append(input_queue)
        output_queue = input_queue
      event_producers.append(queue.ItemQueueProducer(output_queue))

    analysis_plugins = analysis_manager.AnalysisPluginManager.LoadPlugins(
        analysis_plugins_list, analysis_plugin_input_queues)

    analysis_plugins = list(analysis_plugins)

    return analysis_plugins, event_producers

  def ProcessEventsFromStorage(
      self, storage_file, output_buffer, analysis_queues=None,
      filter_buffer=None, my_filter=None, time_slice=None):
    """Reads event objects from the storage to process and filter them.

    Args:
      storage_file: the storage file object (instance of StorageFile).
      output_buffer: the output buffer object (instance of EventBuffer).
      analysis_queues: optional list of analysis queues.
      filter_buffer: optional filter buffer used to store previously discarded
                     events to store time slice history.
      my_filter: optional filter object (instance of PFilter).
      time_slice: optional time slice object (instance of TimeRange).

    Returns:
      A Counter object (instance of collections.Counter), that tracks the
      number of unique events extracted from storage.
    """
    counter = collections.Counter()
    my_limit = getattr(my_filter, u'limit', 0)
    forward_entries = 0
    if not analysis_queues:
      analysis_queues = []

    # TODO: refactor to use StorageReader.
    for event_object in storage_file.GetSortedEntries(time_range=time_slice):
      # TODO: clean up this function.
      if not my_filter:
        counter[u'Events Included'] += 1
        self._AppendEvent(event_object, output_buffer, analysis_queues)
      else:
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

    for analysis_queue in analysis_queues:
      analysis_queue.Close()

    if output_buffer.duplicate_counter:
      counter[u'Duplicate Removals'] = output_buffer.duplicate_counter

    if my_limit:
      counter[u'Limited By'] = my_limit
    return counter

  def ProcessStorage(
      self, output_module, storage_file, storage_file_path, analysis_plugins,
      event_queue_producers, command_line_arguments=None,
      deduplicate_events=True, preferred_encoding=u'utf-8',
      time_slice=None, use_time_slicer=False):
    """Processes a plaso storage file.

    Args:
      output_module: an output module (instance of OutputModule).
      storage_file: the storage file object (instance of StorageFile).
      storage_file_path: string containing the path of the storage file.
      analysis_plugins: list of analysis plugin objects (instance of
                        AnalysisPlugin).
      event_queue_producers: list of event queue producer objects (instance
                             of ItemQueueProducer).
      command_line_arguments: optional string of the command line arguments or
                              None if not set.
      deduplicate_events: optional boolean value to indicate if the event
                          objects should be deduplicated.
      preferred_encoding: optional preferred encoding.
      time_slice: optional time slice object (instance of TimeSlice).
      use_time_slicer: optional boolean value to indicate the 'time slicer'
                       should be used. The 'time slicer' will provide a
                       context of events around an event of interest.

    Returns:
      A counter (an instance of collections.Counter) that tracks the number of
      events extracted from storage, and the analysis plugin results.

    Raises:
      RuntimeError: if a non-recoverable situation is encountered.
    """
    time_slice = None
    if time_slice:
      if time_slice.event_timestamp is not None:
        time_slice = storage_time_range.TimeRange(
            time_slice.start_timestamp, time_slice.end_timestamp)

      elif use_time_slicer:
        self._filter_buffer = bufferlib.CircularBuffer(time_slice.duration)

    with storage_file:
      # TODO: allow for single processing.
      # TODO: add upper queue limit.
      analysis_queue_port = None
      if self._use_zeromq:
        analysis_report_incoming_queue = zeromq_queue.ZeroMQPullBindQueue(
            delay_open=False, port=None, linger_seconds=5)
        analysis_queue_port = analysis_report_incoming_queue.port
      else:
        analysis_report_incoming_queue = multi_process.MultiProcessingQueue(
            timeout=5)

      pre_obj = self._GetLastGoodPreprocess(storage_file)
      if pre_obj is None:
        pre_obj = event.PreprocessObject()

      if analysis_plugins:
        self._StartAnalysisPlugins(
            storage_file_path, analysis_plugins, pre_obj,
            analysis_queue_port=analysis_queue_port,
            analysis_report_incoming_queue=analysis_report_incoming_queue,
            command_line_arguments=command_line_arguments)

        # Assign the preprocessing object to the storage.
        # This is normally done in the construction of the storage object,
        # however we cannot do that here since the preprocessing object is
        # stored inside the storage file, so we need to open it first to
        # be able to read it in, before we make changes to it. Thus we need
        # to access this protected member of the class.
        # pylint: disable=protected-access
        storage_file._pre_obj = pre_obj
      else:
        event_queue_producers = []

      output_buffer = output_event_buffer.EventBuffer(
          output_module, deduplicate_events)
      with output_buffer:
        counter = self.ProcessEventsFromStorage(
            storage_file, output_buffer, analysis_queues=event_queue_producers,
            filter_buffer=self._filter_buffer, my_filter=self._filter_object,
            time_slice=time_slice)

      for information in storage_file.GetStorageInformation():
        if hasattr(information, u'counter'):
          counter[u'Stored Events'] += information.counter[u'total']

      # Get all reports and tags from analysis plugins.
      self._ProcessAnalysisPlugins(
          analysis_plugins, analysis_report_incoming_queue, storage_file,
          counter, preferred_encoding=preferred_encoding)

    if self._filter_object and not counter[u'Limited By']:
      counter[u'Filter By Date'] = (
          counter[u'Stored Events'] - counter[u'Events Included'] -
          counter[u'Events Filtered Out'])

    return counter

  def SetFilter(self, filter_object, filter_expression):
    """Set the filter information.

    Args:
      filter_object: a filter object (instance of FilterObject).
      filter_expression: the filter expression string.
    """
    self._filter_object = filter_object
    self._filter_expression = filter_expression

  def SetPreferredLanguageIdentifier(self, language_identifier):
    """Sets the preferred language identifier.

    Args:
      language_identifier: the language identifier string e.g. en-US for
                           US English or is-IS for Icelandic.
    """
    self._preferred_language = language_identifier

  def SetOutputFormat(self, output_format):
    """Sets the output format.

    Args:
      output_format: the output format.
    """
    self._output_format = output_format

  def SetQuietMode(self, quiet_mode=False):
    """Sets whether tools is in quiet mode or not.

    Args:
      quiet_mode: boolean, when True the tool is in quiet mode.
    """
    self._quiet_mode = quiet_mode

  def SetUseZeroMQ(self, use_zeromq=False):
    """Sets whether the tool is using ZeroMQ for queueing or not.

    Args:
      use_zeromq: boolean, when True the tool will use ZeroMQ for queuing.
    """
    self._use_zeromq = use_zeromq


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
      preferred_encoding: optional preferred encoding.
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
      # TODO: move this print to the psort tool or equivalent.
      print(report_string.encode(self._preferred_encoding))
    except UnicodeDecodeError:
      logging.error(
          u'Unable to print report due to an unicode decode error. '
          u'The report is stored inside the storage file and can be '
          u'viewed using pinfo [if unable to view please submit a '
          u'bug report https://github.com/log2timeline/plaso/issues')


class PsortAnalysisProcess(object):
  """A class to contain information about a running analysis process.

  Attributes:
    completion_event: an optional Event object (instance of
                      Multiprocessing.Event, Queue.Event or similar) that will
                      be set when the analysis plugin is complete.
    plugin: the plugin running in the process (instance of AnalysisProcess).
    process: the process (instance of Multiprocessing.Process) that
             encapsulates the analysis process.
  """
  def __init__(self, completion_event, plugin, process):
    super(PsortAnalysisProcess, self).__init__()
    self.completion_event = completion_event
    self.plugin = plugin
    self.process = process
