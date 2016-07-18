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
from plaso.containers import sessions
from plaso.engine import knowledge_base
from plaso.engine import plaso_queue
from plaso.engine import zeromq_queue
from plaso.formatters import mediator as formatters_mediator
from plaso.frontend import analysis_frontend
from plaso.lib import bufferlib
from plaso.lib import errors
from plaso.lib import py2to3
from plaso.multi_processing import multi_process_queue
from plaso.output import event_buffer as output_event_buffer
from plaso.output import manager as output_manager
from plaso.output import mediator as output_mediator
from plaso.storage import time_range as storage_time_range
from plaso.storage import reader
from plaso.storage import zip_file as storage_zip_file


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
    self._knowledge_base = knowledge_base.KnowledgeBase()
    self._output_format = None
    self._preferred_language = u'en-US'
    self._quiet_mode = False
    self._storage_file_path = None
    self._use_zeromq = True

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
    inode = event_object.inode
    if isinstance(inode, py2to3.STRING_TYPES):
      inode_list = inode.split(u';')
      try:
        new_inode = int(inode_list[0], 10)
      except (ValueError, IndexError):
        new_inode = 0

      event_object.inode = new_inode

    for event_queue in event_queues:
      event_queue.ProduceItem(event_object)

  def _CleanUpAfterAbort(self):
    """Signals the front-end to stop running nicely after an abort."""
    # TODO: implement clean up logic.
    return

  def _CreateSession(
      self, command_line_arguments=None, preferred_encoding=u'utf-8'):
    """Creates the session start information.

    Args:
      command_line_arguments (Optional[str]): the command line arguments.
      preferred_encoding (Optional[str]): preferred encoding.

    Returns:
      Session: session attribute container.
    """
    session = sessions.Session()

    session.command_line_arguments = command_line_arguments
    session.preferred_encoding = preferred_encoding

    return session

  def _ProcessAnalysisPlugins(
      self, analysis_plugins, analysis_report_incoming_queue, session,
      storage_file, counter, preferred_encoding=u'utf-8'):
    """Runs the analysis plugins.

    Args:
      analysis_plugins (list[AnalysisPlugin]): analysis plugins.
      analysis_report_incoming_queue (Queue): analysis output queue.
      session (Session): session the storage changes are part of.
      storage_file (BaseStorage): session-based storage file.
      counter (collections.Counter): counter.
      preferred_encoding (Optional[str]): preferred encoding.
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

      logging.info(
          u'Waiting for analysis plugin: {0:s} to complete.'.format(name))

      completion_event = analysis_process_info.completion_event
      if completion_event.wait(report_wait):
        logging.info(u'Plugin {0:s} has completed.'.format(name))
      else:
        logging.warning(
            u'Analysis process {0:s} failed to compile its report in a '
            u'reasonable time. No report will be displayed or stored.'.format(
                name))

    logging.info(u'All analysis plugins are now completed.')

    analysis_report_consumer = PsortAnalysisReportQueueConsumer(
        analysis_report_incoming_queue, session, storage_file,
        self._filter_expression, preferred_encoding=preferred_encoding)

    analysis_report_consumer.ConsumeItems()
    for item, value in iter(analysis_report_consumer.reports_counter.items()):
      counter[item] = value

  def _ProcessStorage(
      self, output_module, storage_file, analysis_plugins,
      event_queue_producers, command_line_arguments=None,
      deduplicate_events=True, preferred_encoding=u'utf-8',
      time_slice=None, use_time_slicer=False):
    """Processes a plaso storage file.

    Args:
      output_module (OutputModule): output module.
      storage_file (StorageFile): storage file.
      analysis_plugins (list[AnalysisPlugin]): analysis plugins that should
          be run.
      event_queue_producers (list[ItemQueueProducer]): event queue producers.
      command_line_arguments (Optional[str]): command line arguments.
      deduplicate_events (Optional[bool]): True if events should be
          deduplicated.
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
    if time_slice:
      if time_slice.event_timestamp is not None:
        time_slice = storage_time_range.TimeRange(
            time_slice.start_timestamp, time_slice.end_timestamp)

      elif use_time_slicer:
        self._filter_buffer = bufferlib.CircularBuffer(time_slice.duration)

    # TODO: allow for single processing.
    # TODO: add upper queue limit.
    analysis_queue_port = None
    if self._use_zeromq:
      analysis_report_incoming_queue = zeromq_queue.ZeroMQPullBindQueue(
          delay_open=False, port=None, linger_seconds=5)
      analysis_queue_port = analysis_report_incoming_queue.port
    else:
      analysis_report_incoming_queue = multi_process_queue.MultiProcessingQueue(
          timeout=5)

    storage_file.ReadPreprocessingInformation(self._knowledge_base)

    session = self._CreateSession(
        command_line_arguments=command_line_arguments,
        preferred_encoding=preferred_encoding)

    if not analysis_plugins:
      event_queue_producers = []
    else:
      self._StartAnalysisPlugins(
          analysis_plugins, analysis_queue_port=analysis_queue_port,
          analysis_report_incoming_queue=analysis_report_incoming_queue)

      # TODO: refactor to use storage writer.
      session_start = session.CreateSessionStart()
      storage_file.WriteSessionStart(session_start)

    # TODO: refactor to first apply the analysis plugins
    # then generate the output.
    output_buffer = output_event_buffer.EventBuffer(
        output_module, deduplicate_events)
    with output_buffer:
      storage_reader = reader.StorageObjectReader(storage_file)
      counter = self.ProcessEventsFromStorage(
          storage_reader, output_buffer, analysis_queues=event_queue_producers,
          filter_buffer=self._filter_buffer, my_filter=self._filter_object,
          time_slice=time_slice)

    # Get all reports and tags from analysis plugins.
    self._ProcessAnalysisPlugins(
        analysis_plugins, analysis_report_incoming_queue, session,
        storage_file, counter, preferred_encoding=preferred_encoding)

    if analysis_plugins:
      session_completion = session.CreateSessionCompletion()
      storage_file.WriteSessionCompletion(session_completion)

    return counter

  def _StartAnalysisPlugins(
      self, analysis_plugins, analysis_queue_port=None,
      analysis_report_incoming_queue=None):
    """Start all the analysis plugin.

    Args:
      analysis_plugins (list[AnalysisPlugin]): analysis plugins that should
          be run.
      analysis_queue_port (Optional[int]): TCP port of the ZeroMQ analysis
          report queues.
      analysis_report_incoming_queue (Optional[Queue]):
          queue that reports should to pushed to, when ZeroMQ is not in use.
    """
    logging.info(u'Starting analysis plugins.')

    for analysis_plugin in analysis_plugins:
      if self._use_zeromq:
        analysis_plugin_output_queue = zeromq_queue.ZeroMQPushConnectQueue(
            delay_open=True, port=analysis_queue_port)
      else:
        analysis_plugin_output_queue = analysis_report_incoming_queue

      analysis_report_queue_producer = plaso_queue.ItemQueueProducer(
          analysis_plugin_output_queue)

      completion_event = multiprocessing.Event()
      analysis_mediator_object = analysis_mediator.AnalysisMediator(
          analysis_report_queue_producer, self._knowledge_base,
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

  def GetAnalysisPluginsAndEventQueues(self, analysis_plugins_string):
    """Return a list of analysis plugins and event queues.

    Args:
      analysis_plugins_string (str): comma separated names of analysis plugins
          to load.

    Returns:
      tuple: consists:

        list[AnalysisPlugin]: analysis plugins
        list[Queue]: event queues
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
        input_queue = multi_process_queue.MultiProcessingQueue(timeout=5)
        analysis_plugin_input_queues.append(input_queue)
        output_queue = input_queue
      event_producers.append(plaso_queue.ItemQueueProducer(output_queue))

    analysis_plugins = analysis_manager.AnalysisPluginManager.LoadPlugins(
        analysis_plugins_list, analysis_plugin_input_queues)

    analysis_plugins = list(analysis_plugins)

    return analysis_plugins, event_producers

  def CreateOutputModule(self, preferred_encoding=u'utf-8', timezone=u'UTC'):
    """Create an output module.

    Args:
      preferred_encoding (Optional[str]): preferred encoding to output.
      timezone (Optional[str]): timezone to use for timestamps in output.

    Returns:
      OutputModule: output module.

    Raises:
      RuntimeError: if a non-recoverable situation is encountered.
    """
    formatter_mediator = formatters_mediator.FormatterMediator(
        data_location=self._data_location)

    try:
      formatter_mediator.SetPreferredLanguageIdentifier(
          self._preferred_language)
    except (KeyError, TypeError) as exception:
      raise RuntimeError(exception)

    output_mediator_object = output_mediator.OutputMediator(
        self._knowledge_base, formatter_mediator,
        preferred_encoding=preferred_encoding)
    output_mediator_object.SetTimezone(timezone)

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

  def HasOutputClass(self, name):
    """Determines if a specific output class is registered with the manager.

    Args:
      name: The name of the output module.

    Returns:
      A boolean indicating if the output class is registered.
    """
    return output_manager.OutputManager.HasOutputClass(name)

  def ProcessEventsFromStorage(
      self, storage_reader, output_buffer, analysis_queues=None,
      filter_buffer=None, my_filter=None, time_slice=None):
    """Reads event objects from the storage to process and filter them.

    Args:
      storage_reader: a storage reader object (instance of StorageReader).
      output_buffer: an output buffer object (instance of EventBuffer).
      analysis_queues: optional list of analysis queues.
      filter_buffer: optional filter buffer used to store previously discarded
                     events to store time slice history.
      my_filter: optional filter object (instance of PFilter).
      time_slice: optional time slice object (instance of TimeRange).

    Returns:
      A counter object (instance of collections.Counter), that tracks the
      number of unique events extracted from storage.
    """
    counter = collections.Counter()
    my_limit = getattr(my_filter, u'limit', 0)
    forward_entries = 0
    if not analysis_queues:
      analysis_queues = []

    for event_object in storage_reader.GetEvents(time_range=time_slice):
      # TODO: clean up this function.
      if not my_filter:
        counter[u'Events Included'] += 1
        self._AppendEvent(event_object, output_buffer, analysis_queues)
      else:
        if my_filter.Match(event_object):
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
      self, output_module, analysis_plugins, event_queue_producers,
      command_line_arguments=None, deduplicate_events=True,
      preferred_encoding=u'utf-8', time_slice=None, use_time_slicer=False):
    """Processes a plaso storage file.

    Args:
      output_module (OutputModule): output module.
      analysis_plugins (list[AnalysisPlugin]): analysis plugins that should
                                               be run.
      event_queue_producers (list[ItemQueueProducer]): event queue producers.
      command_line_arguments (Optional[str]): command line arguments.
      deduplicate_events (Optional[bool]): True if events should be
                                           deduplicated.
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
      UserAbort: if the user initiated an abort.
    """
    # TODO: preprocess object refactor.
    pre_obj = None
    if analysis_plugins:
      pre_obj = getattr(self._knowledge_base, u'_pre_obj', None)

    if analysis_plugins:
      read_only = False
    else:
      read_only = True

    # TODO: we are directly invoking ZIP file storage here. In storage rewrite
    # come up with a more generic solution.
    storage_file = storage_zip_file.ZIPStorageFile()
    try:
      storage_file.Open(path=self._storage_file_path, read_only=read_only)
    except IOError as exception:
      raise RuntimeError(
          u'Unable to open storage file: {0:s} with error: {1:s}.'.format(
              self._storage_file_path, exception))

    try:
      counter = self._ProcessStorage(
          output_module, storage_file, analysis_plugins, event_queue_producers,
          command_line_arguments=command_line_arguments,
          deduplicate_events=deduplicate_events,
          preferred_encoding=preferred_encoding,
          time_slice=time_slice, use_time_slicer=use_time_slicer)

      # TODO: preprocess object refactor.
      if pre_obj:
        storage_file.WritePreprocessObject(pre_obj)
    except KeyboardInterrupt:
      self._CleanUpAfterAbort()
      raise errors.UserAbort

    finally:
      storage_file.Close()

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

  def SetStorageFile(self, storage_file_path):
    """Sets the storage file path.

    Args:
      storage_file_path: The path of the storage file.
    """
    self._storage_file_path = storage_file_path

  def SetUseZeroMQ(self, use_zeromq=True):
    """Sets whether the tool is using ZeroMQ for queueing or not.

    Args:
      use_zeromq: boolean, when True the tool will use ZeroMQ for queuing.
    """
    self._use_zeromq = use_zeromq


class PsortAnalysisReportQueueConsumer(plaso_queue.ItemQueueConsumer):
  """Class that implements an analysis report queue consumer.

  The consumer subscribes to updates on the queue and writes the analysis
  reports to the storage.

  Attributes:
    reports_counter: a counter containing the number of reports (instance of
                     collections.Counter).
  """

  def __init__(
      self, queue, session, storage_file, filter_string,
      preferred_encoding=u'utf-8'):
    """Initializes the item queue consumer.

    Args:
      queue (Queue): queue.
      session (Session): session the storage changes are part of.
      storage_file (BaseStorage): session-based storage file.
      filter_string (str): string containing the filter expression.
      preferred_encoding (Optional[str]): preferred encoding.
    """
    super(PsortAnalysisReportQueueConsumer, self).__init__(queue)
    self._filter_string = filter_string
    self._preferred_encoding = preferred_encoding
    self._session = session
    self._storage_file = storage_file
    self._tags = []

    # Counter containing the number of reports.
    self.reports_counter = collections.Counter()

  def _ConsumeItem(self, analysis_report, **unused_kwargs):
    """Consumes an item callback for ConsumeItems.

    Args:
      analysis_report: an analysis report (instance of AnalysisReport).
    """
    if self._filter_string:
      analysis_report.filter_string = self._filter_string

    # For now we print the report to disk and then save it.
    # TODO: Have the option of saving to a separate file and
    # do something more here, for instance saving into a HTML
    # file, or something else (including potential images).
    self._storage_file.AddAnalysisReport(analysis_report)

    report_identifier = analysis_report.plugin_name
    self._session.analysis_reports_counter[u'total'] += 1
    self._session.analysis_reports_counter[report_identifier] += 1

    # TODO: refactor this as part of psort rewrite.
    event_tags = getattr(analysis_report, u'_event_tags', [])
    for event_tag in event_tags:
      self._storage_file.AddEventTag(event_tag)

      self._session.event_labels_counter[u'total'] += 1
      for label in event_tag.labels:
        self._session.event_labels_counter[label] += 1

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
    """Initializes an analysis process.

    Args:
      completion_event: a completion event (instance of Multiprocessing.Event,
                        Queue.Event or similar) that will be set when the
                        analysis plugin is complete.
      plugin: the plugin running in the process (instance of AnalysisProcess).
      process: the process (instance of Multiprocessing.Process) that
               encapsulates the analysis process.
    """
    super(PsortAnalysisProcess, self).__init__()
    self.completion_event = completion_event
    self.plugin = plugin
    self.process = process
