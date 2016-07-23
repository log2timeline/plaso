# -*- coding: utf-8 -*-
"""The psort front-end."""

from __future__ import print_function
import collections
import logging

from plaso import formatters   # pylint: disable=unused-import
from plaso import output   # pylint: disable=unused-import

from plaso.analysis import manager as analysis_manager
from plaso.containers import sessions
from plaso.engine import knowledge_base
from plaso.engine import plaso_queue
from plaso.engine import zeromq_queue
from plaso.formatters import mediator as formatters_mediator
from plaso.frontend import analysis_frontend
from plaso.lib import bufferlib
from plaso.lib import errors
from plaso.lib import py2to3
from plaso.multi_processing import analysis_process
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
    self._data_location = None
    self._event_queues = []
    self._filter_buffer = None
    self._filter_expression = None
    # Instance of EventObjectFilter.
    self._filter_object = None
    self._knowledge_base = knowledge_base.KnowledgeBase()
    self._output_format = None
    self._preferred_language = u'en-US'
    self._processes_per_pid = {}
    self._quiet_mode = False
    self._use_zeromq = True

  def _AppendEvent(self, event, output_buffer):
    """Appends an event object to an event output buffer and analysis queues.

    Args:
      event (EventObject): event.
      output_buffer (EventBuffer): output event buffer.
    """
    output_buffer.Append(event)

    # Needed due to duplicate removals, if two events
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
    for pid, process in iter(self._processes_per_pid.items()):
      name = process.plugin.NAME
      if process.plugin.LONG_RUNNING_PLUGIN:
        logging.warning((
            u'{0:s} PID: {1:d} may take a long time to run. It will not '
            u'be automatically terminated.').format(name, pid))
        report_wait = None
      else:
        report_wait = self.MAX_ANALYSIS_PLUGIN_REPORT_WAIT

      logging.info(
          u'Waiting for analysis plugin: {0:s} to complete.'.format(name))

      completion_event = process.completion_event
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

  def _ProcessEventsFromStorage(
      self, storage_reader, output_buffer, filter_buffer=None, my_filter=None,
      time_slice=None):
    """Reads event objects from the storage to process and filter them.

    Args:
      storage_reader (StorageReader): storage reader.
      output_buffer (EventBuffer): output event buffer.
      filter_buffer (Optional[CircularBuffer]): filter buffer used to store
          previously discarded events to store time slice history.
      my_filter (Optional[FilterObject]): event filter.
      time_slice (Optional[TimeRange]): time range that defines a time slice
          to filter events.

    Returns:
      collections.Counter: counter that tracks the number of unique events
          extracted from storage.
    """
    counter = collections.Counter()
    my_limit = getattr(my_filter, u'limit', 0)
    forward_entries = 0

    for event in storage_reader.GetEvents(time_range=time_slice):
      # TODO: clean up this function.
      if not my_filter:
        counter[u'Events Included'] += 1
        self._AppendEvent(event, output_buffer)
      else:
        if my_filter.Match(event):
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
      self, storage_file, output_module, analysis_plugins,
      command_line_arguments=None, deduplicate_events=True,
      preferred_encoding=u'utf-8', time_slice=None, use_time_slicer=False):
    """Processes a plaso storage file.

    Args:
      storage_file (StorageFile): storage file.
      output_module (OutputModule): output module.
      analysis_plugins (list[AnalysisPlugin]): analysis plugins that should
          be run.
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

    if analysis_plugins:
      self._StartAnalysisProcesses(
          analysis_plugins, analysis_queue_port, analysis_report_incoming_queue)

      # TODO: refactor to use storage writer.
      session_start = session.CreateSessionStart()
      storage_file.WriteSessionStart(session_start)

    # TODO: refactor to first apply the analysis plugins
    # then generate the output.
    output_buffer = output_event_buffer.EventBuffer(
        output_module, deduplicate_events)
    with output_buffer:
      storage_reader = reader.StorageObjectReader(storage_file)
      counter = self._ProcessEventsFromStorage(
          storage_reader, output_buffer, filter_buffer=self._filter_buffer,
          my_filter=self._filter_object, time_slice=time_slice)

    # Get all reports and tags from analysis plugins.
    self._ProcessAnalysisPlugins(
        analysis_plugins, analysis_report_incoming_queue, session,
        storage_file, counter, preferred_encoding=preferred_encoding)

    if analysis_plugins:
      session_completion = session.CreateSessionCompletion()
      storage_file.WriteSessionCompletion(session_completion)

    return counter

  def _RegisterProcess(self, process):
    """Registers a process with the front-end.

    Args:
      process (MultiProcessBaseProcess): process.

    Raises:
      KeyError: if the process is already registered with the front-end.
      ValueError: if the process object is missing.
    """
    if process is None:
      raise ValueError(u'Missing process object.')

    if process.pid in self._processes_per_pid:
      raise KeyError(
          u'Already managing process: {0!s} (PID: {1:d})'.format(
              process.name, process.pid))

    self._processes_per_pid[process.pid] = process

  def _StartAnalysisProcesses(
      self, analysis_plugins, analysis_queue_port,
      analysis_report_incoming_queue):
    """Starts the analysis processes.

    Args:
      analysis_plugins (list[AnalysisPlugin]): analysis plugins that should
          be run.
      analysis_queue_port (int): TCP port of the ZeroMQ analysis report queues.
      analysis_report_incoming_queue (multiprocessing.Queue): queue where
          reports should be pushed to, when ZeroMQ is not used.
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
            delay_open=True, port=analysis_queue_port)

      else:
        input_event_queue = output_event_queue

        analysis_report_queue = analysis_report_incoming_queue

      process_name = u'Analysis {0:s}'.format(analysis_plugin.plugin_name)
      process = analysis_process.AnalysisProcess(
          input_event_queue, analysis_report_queue, self._knowledge_base,
          analysis_plugin, data_location=self._data_location,
          name=process_name)

      self._RegisterProcess(process)

      process.start()

      logging.info(u'Started analysis plugin: {0:s} (PID: {1:d}).'.format(
          analysis_plugin.plugin_name, process.pid))

    logging.info(u'Analysis plugins running')

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
      list[tuple]: contains:

        str: name of analysis plugin.
        str: docstring of analysis plugin.
        type: type of analysis plugin.
    """
    return analysis_manager.AnalysisPluginManager.GetAllPluginInformation()

  def GetAnalysisPlugins(self, analysis_plugins_string):
    """Retrieves analysis plugins.

    Args:
      analysis_plugins_string (str): comma separated names of analysis plugins
          to enable.

    Returns:
      list[AnalysisPlugin]: analysis plugins.
    """
    if not analysis_plugins_string:
      return []

    analysis_plugins_list = [
        name.strip() for name in analysis_plugins_string.split(u',')]

    analysis_plugins = analysis_manager.AnalysisPluginManager.GetPluginObjects(
        analysis_plugins_list)
    return analysis_plugins.values()

  def GetDisabledOutputClasses(self):
    """Retrieves the disabled output classes.

    Returns:
      generator(tuple): contains:

        str: output class names
        type: output class types.
    """
    return output_manager.OutputManager.GetDisabledOutputClasses()

  def GetOutputClasses(self):
    """Retrieves the available output classes.

    Returns:
      generator(tuple): contains:

        str: output class names
        type: output class types.
    """
    return output_manager.OutputManager.GetOutputClasses()

  def HasOutputClass(self, name):
    """Determines if a specific output class is registered with the manager.

    Args:
      name (str): name of the output module.

    Returns:
      bool: True if the output class is registered.
    """
    return output_manager.OutputManager.HasOutputClass(name)

  def ProcessStorage(
      self, storage_file_path, output_module, analysis_plugins,
      command_line_arguments=None, deduplicate_events=True,
      preferred_encoding=u'utf-8', time_slice=None, use_time_slicer=False):
    """Processes a plaso storage file.

    Args:
      storage_file_path (str): path of the storage file.
      output_module (OutputModule): output module.
      analysis_plugins (list[AnalysisPlugin]): analysis plugins that should
          be run.
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
    if analysis_plugins:
      read_only = False
    else:
      read_only = True

    # TODO: we are directly invoking ZIP file storage here. In storage rewrite
    # come up with a more generic solution.
    storage_file = storage_zip_file.ZIPStorageFile()
    try:
      storage_file.Open(path=storage_file_path, read_only=read_only)
    except IOError as exception:
      raise RuntimeError(
          u'Unable to open storage file: {0:s} with error: {1:s}.'.format(
              storage_file_path, exception))

    try:
      counter = self._ProcessStorage(
          storage_file, output_module, analysis_plugins,
          command_line_arguments=command_line_arguments,
          deduplicate_events=deduplicate_events,
          preferred_encoding=preferred_encoding,
          time_slice=time_slice, use_time_slicer=use_time_slicer)

    except KeyboardInterrupt:
      self._CleanUpAfterAbort()
      raise errors.UserAbort

    finally:
      storage_file.Close()

    return counter

  def SetFilter(self, filter_object, filter_expression):
    """Set the filter information.

    Args:
      filter_object (FilterObject): event filter.
      filter_expression (str): filter expression.
    """
    self._filter_object = filter_object
    self._filter_expression = filter_expression

  def SetPreferredLanguageIdentifier(self, language_identifier):
    """Sets the preferred language identifier.

    Args:
      language_identifier (str): language identifier string, for example
          'en-US' for US English or 'is-IS' for Icelandic.
    """
    self._preferred_language = language_identifier

  def SetOutputFormat(self, output_format):
    """Sets the output format.

    Args:
      output_format (str): output format.
    """
    self._output_format = output_format

  def SetQuietMode(self, quiet_mode=False):
    """Sets whether quiet mode should be enabled or not.

    Args:
      quiet_mode (Optional[bool]): True when quiet mode should be enabled.
    """
    self._quiet_mode = quiet_mode

  def SetUseZeroMQ(self, use_zeromq=True):
    """Sets whether ZeroMQ should be used for queueing or not.

    Args:
      use_zeromq (Optional[bool]): True if ZeroMQ should be used for queuing.
    """
    self._use_zeromq = use_zeromq


class PsortAnalysisReportQueueConsumer(plaso_queue.ItemQueueConsumer):
  """Class that implements an analysis report queue consumer.

  The consumer subscribes to updates on the queue and writes the analysis
  reports to the storage.

  Attributes:
    reports_counter (collections.Counter): counter containing the number
        of reports.
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
      analysis_report (AnalysisReport): analysis report.
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
