# -*- coding: utf-8 -*-
"""Processing status classes."""

from __future__ import unicode_literals

import time


class ProcessStatus(object):
  """The status of an individual process.

  Attributes:
    display_name (str): human readable of the file entry currently being
        processed by the process.
    identifier (str): process identifier.
    last_running_time (int): timestamp of the last update when the process had
        a running process status.
    number_of_consumed_event_tags (int): total number of event tags consumed by
        the process.
    number_of_consumed_event_tags_delta (int): number of event tags consumed by
        the process since the last status update.
    number_of_consumed_events (int): total number of events consumed by
        the process.
    number_of_consumed_events_delta (int): number of events consumed by
        the process since the last status update.
    number_of_consumed_reports (int): total number of event reports consumed
        by the process.
    number_of_consumed_reports_delta (int): number of event reports consumed
        by the process since the last status update.
    number_of_consumed_sources (int): total number of event sources consumed
        by the process.
    number_of_consumed_sources_delta (int): number of event sources consumed
        by the process since the last status update.
    number_of_consumed_warnings (int): total number of warnings consumed by
        the process.
    number_of_consumed_warnings_delta (int): number of warnings consumed by
        the process since the last status update.
    number_of_produced_event_tags (int): total number of event tags produced by
        the process.
    number_of_produced_event_tags_delta (int): number of event tags produced by
        the process since the last status update.
    number_of_produced_events (int): total number of events produced by
        the process.
    number_of_produced_events_delta (int): number of events produced by
        the process since the last status update.
    number_of_produced_reports (int): total number of event reports
        produced by the process.
    number_of_produced_reports_delta (int): number of event reports produced
        by the process since the last status update.
    number_of_produced_sources (int): total number of event sources
        produced by the process.
    number_of_produced_sources_delta (int): number of event sources produced
        by the process since the last status update.
    number_of_produced_warnings (int): total number of warnings produced by
        the process.
    number_of_produced_warnings_delta (int): number of warnings produced by
        the process since the last status update.
    pid (int): process identifier (PID).
    status (str): human readable status indication such as "Hashing" or "Idle".
    used_memory (int): size of used memory in bytes.
  """

  def __init__(self):
    """Initializes a process status."""
    super(ProcessStatus, self).__init__()
    self.display_name = None
    self.identifier = None
    self.last_running_time = 0
    self.number_of_consumed_event_tags = 0
    self.number_of_consumed_event_tags_delta = 0
    self.number_of_consumed_events = 0
    self.number_of_consumed_events_delta = 0
    self.number_of_consumed_reports = 0
    self.number_of_consumed_reports_delta = 0
    self.number_of_consumed_sources = 0
    self.number_of_consumed_sources_delta = 0
    self.number_of_consumed_warnings = 0
    self.number_of_consumed_warnings_delta = 0
    self.number_of_produced_event_tags = 0
    self.number_of_produced_event_tags_delta = 0
    self.number_of_produced_events = 0
    self.number_of_produced_events_delta = 0
    self.number_of_produced_reports = 0
    self.number_of_produced_reports_delta = 0
    self.number_of_produced_sources = 0
    self.number_of_produced_sources_delta = 0
    self.number_of_produced_warnings = 0
    self.number_of_produced_warnings_delta = 0
    self.pid = None
    self.status = None
    self.used_memory = 0

  def UpdateNumberOfEventReports(
      self, number_of_consumed_reports, number_of_produced_reports):
    """Updates the number of event reports.

    Args:
      number_of_consumed_reports (int): total number of event reports consumed
          by the process.
      number_of_produced_reports (int): total number of event reports produced
          by the process.

    Returns:
      bool: True if either number of event reports has increased.

    Raises:
      ValueError: if the consumed or produced number of event reports is
          smaller than the value of the previous update.
    """
    consumed_reports_delta = 0
    if number_of_consumed_reports is not None:
      if number_of_consumed_reports < self.number_of_consumed_reports:
        raise ValueError(
            'Number of consumed reports smaller than previous update.')

      consumed_reports_delta = (
          number_of_consumed_reports - self.number_of_consumed_reports)

      self.number_of_consumed_reports = number_of_consumed_reports
      self.number_of_consumed_reports_delta = consumed_reports_delta

    produced_reports_delta = 0
    if number_of_produced_reports is not None:
      if number_of_produced_reports < self.number_of_produced_reports:
        raise ValueError(
            'Number of produced reports smaller than previous update.')

      produced_reports_delta = (
          number_of_produced_reports - self.number_of_produced_reports)

      self.number_of_produced_reports = number_of_produced_reports
      self.number_of_produced_reports_delta = produced_reports_delta

    return consumed_reports_delta > 0 or produced_reports_delta > 0

  def UpdateNumberOfEvents(
      self, number_of_consumed_events, number_of_produced_events):
    """Updates the number of events.

    Args:
      number_of_consumed_events (int): total number of events consumed by
          the process.
      number_of_produced_events (int): total number of events produced by
          the process.

    Returns:
      bool: True if either number of events has increased.

    Raises:
      ValueError: if the consumed or produced number of events is smaller
          than the value of the previous update.
    """
    consumed_events_delta = 0
    if number_of_consumed_events is not None:
      if number_of_consumed_events < self.number_of_consumed_events:
        raise ValueError(
            'Number of consumed events smaller than previous update.')

      consumed_events_delta = (
          number_of_consumed_events - self.number_of_consumed_events)

      self.number_of_consumed_events = number_of_consumed_events
      self.number_of_consumed_events_delta = consumed_events_delta

    produced_events_delta = 0
    if number_of_produced_events is not None:
      if number_of_produced_events < self.number_of_produced_events:
        raise ValueError(
            'Number of produced events smaller than previous update.')

      produced_events_delta = (
          number_of_produced_events - self.number_of_produced_events)

      self.number_of_produced_events = number_of_produced_events
      self.number_of_produced_events_delta = produced_events_delta

    return consumed_events_delta > 0 or produced_events_delta > 0

  def UpdateNumberOfEventSources(
      self, number_of_consumed_sources, number_of_produced_sources):
    """Updates the number of event sources.

    Args:
      number_of_consumed_sources (int): total number of event sources consumed
          by the process.
      number_of_produced_sources (int): total number of event sources produced
          by the process.

    Returns:
      bool: True if either number of event sources has increased.

    Raises:
      ValueError: if the consumed or produced number of event sources is
          smaller than the value of the previous update.
    """
    consumed_sources_delta = 0
    if number_of_consumed_sources is not None:
      if number_of_consumed_sources < self.number_of_consumed_sources:
        raise ValueError(
            'Number of consumed sources smaller than previous update.')

      consumed_sources_delta = (
          number_of_consumed_sources - self.number_of_consumed_sources)

      self.number_of_consumed_sources = number_of_consumed_sources
      self.number_of_consumed_sources_delta = consumed_sources_delta

    produced_sources_delta = 0
    if number_of_produced_sources is not None:
      if number_of_produced_sources < self.number_of_produced_sources:
        raise ValueError(
            'Number of produced sources smaller than previous update.')

      produced_sources_delta = (
          number_of_produced_sources - self.number_of_produced_sources)

      self.number_of_produced_sources = number_of_produced_sources
      self.number_of_produced_sources_delta = produced_sources_delta

    return consumed_sources_delta > 0 or produced_sources_delta > 0

  def UpdateNumberOfEventTags(
      self, number_of_consumed_event_tags, number_of_produced_event_tags):
    """Updates the number of event tags.

    Args:
      number_of_consumed_event_tags (int): total number of event tags consumed
          by the process.
      number_of_produced_event_tags (int): total number of event tags produced
          by the process.

    Returns:
      bool: True if either number of event tags has increased.

    Raises:
      ValueError: if the consumed or produced number of event tags is smaller
          than the value of the previous update.
    """
    consumed_event_tags_delta = 0
    if number_of_consumed_event_tags is not None:
      if number_of_consumed_event_tags < self.number_of_consumed_event_tags:
        raise ValueError(
            'Number of consumed event tags smaller than previous update.')

      consumed_event_tags_delta = (
          number_of_consumed_event_tags - self.number_of_consumed_event_tags)

      self.number_of_consumed_event_tags = number_of_consumed_event_tags
      self.number_of_consumed_event_tags_delta = consumed_event_tags_delta

    produced_event_tags_delta = 0
    if number_of_produced_event_tags is not None:
      if number_of_produced_event_tags < self.number_of_produced_event_tags:
        raise ValueError(
            'Number of produced event tags smaller than previous update.')

      produced_event_tags_delta = (
          number_of_produced_event_tags - self.number_of_produced_event_tags)

      self.number_of_produced_event_tags = number_of_produced_event_tags
      self.number_of_produced_event_tags_delta = produced_event_tags_delta

    return consumed_event_tags_delta > 0 or produced_event_tags_delta > 0

  def UpdateNumberOfWarnings(
      self, number_of_consumed_warnings, number_of_produced_warnings):
    """Updates the number of warnings.

    Args:
      number_of_consumed_warnings (int): total number of warnings consumed by
          the process.
      number_of_produced_warnings (int): total number of warnings produced by
          the process.

    Returns:
      bool: True if either number of warnings has increased.

    Raises:
      ValueError: if the consumed or produced number of warnings is smaller
          than the value of the previous update.
    """
    consumed_warnings_delta = 0
    if number_of_consumed_warnings is not None:
      if number_of_consumed_warnings < self.number_of_consumed_warnings:
        raise ValueError(
            'Number of consumed warnings smaller than previous update.')

      consumed_warnings_delta = (
          number_of_consumed_warnings - self.number_of_consumed_warnings)

      self.number_of_consumed_warnings = number_of_consumed_warnings
      self.number_of_consumed_warnings_delta = consumed_warnings_delta

    produced_warnings_delta = 0
    if number_of_produced_warnings is not None:
      if number_of_produced_warnings < self.number_of_produced_warnings:
        raise ValueError(
            'Number of produced warnings smaller than previous update.')

      produced_warnings_delta = (
          number_of_produced_warnings - self.number_of_produced_warnings)

      self.number_of_produced_warnings = number_of_produced_warnings
      self.number_of_produced_warnings_delta = produced_warnings_delta

    return consumed_warnings_delta > 0 or produced_warnings_delta > 0


class ProcessingStatus(object):
  """The status of the overall extraction process (processing).

  Attributes:
    aborted (bool): True if processing was aborted.
    error_path_specs (list[dfvfs.PathSpec]): path specifications that
        caused critical errors during processing.
    events_status (EventsStatus): status information about events.
    foreman_status (ProcessingStatus): foreman processing status.
    start_time (float): time that the processing was started. Contains the
        number of micro seconds since January 1, 1970, 00:00:00 UTC.
    tasks_status (TasksStatus): status information about tasks.
  """

  def __init__(self):
    """Initializes a processing status."""
    super(ProcessingStatus, self).__init__()
    self._workers_status = {}

    self.aborted = False
    self.error_path_specs = []
    self.events_status = None
    self.foreman_status = None
    self.start_time = time.time()
    self.tasks_status = None

  @property
  def workers_status(self):
    """The worker status objects sorted by identifier."""
    return [self._workers_status[identifier]
            for identifier in sorted(self._workers_status.keys())]

  # pylint: disable=too-many-arguments
  def _UpdateProcessStatus(
      self, process_status, identifier, status, pid, used_memory, display_name,
      number_of_consumed_sources, number_of_produced_sources,
      number_of_consumed_events, number_of_produced_events,
      number_of_consumed_event_tags, number_of_produced_event_tags,
      number_of_consumed_reports, number_of_produced_reports,
      number_of_consumed_warnings, number_of_produced_warnings):
    """Updates a process status.

    Args:
      process_status (ProcessStatus): process status.
      identifier (str): process identifier.
      status (str): human readable status indication such as "Hashing" or
          "Idle".
      pid (int): process identifier (PID).
      used_memory (int): size of used memory in bytes.
      display_name (str): human readable of the file entry currently being
          processed by the process.
      number_of_consumed_sources (int): total number of event sources consumed
          by the process.
      number_of_produced_sources (int): total number of event sources produced
          by the process.
      number_of_consumed_events (int): total number of events consumed by
          the process.
      number_of_produced_events (int): total number of events produced by
          the process.
      number_of_consumed_event_tags (int): total number of event tags consumed
          by the process.
      number_of_produced_event_tags (int): total number of event tags produced
          by the process.
      number_of_consumed_reports (int): total number of event reports consumed
          by the process.
      number_of_produced_reports (int): total number of event reports produced
          by the process.
      number_of_consumed_warnings (int): total number of warnings consumed by
          the process.
      number_of_produced_warnings (int): total number of warnings produced by
          the process.
    """
    new_sources = process_status.UpdateNumberOfEventSources(
        number_of_consumed_sources, number_of_produced_sources)

    new_events = process_status.UpdateNumberOfEvents(
        number_of_consumed_events, number_of_produced_events)

    new_event_tags = process_status.UpdateNumberOfEventTags(
        number_of_consumed_event_tags, number_of_produced_event_tags)

    new_warnings = process_status.UpdateNumberOfWarnings(
        number_of_consumed_warnings, number_of_produced_warnings)

    new_reports = process_status.UpdateNumberOfEventReports(
        number_of_consumed_reports, number_of_produced_reports)

    process_status.display_name = display_name
    process_status.identifier = identifier
    process_status.pid = pid
    process_status.status = status
    process_status.used_memory = used_memory

    if (new_sources or new_events or new_event_tags or new_warnings or
        new_reports):
      process_status.last_running_time = time.time()

  # pylint: disable=too-many-arguments
  def UpdateForemanStatus(
      self, identifier, status, pid, used_memory, display_name,
      number_of_consumed_sources, number_of_produced_sources,
      number_of_consumed_events, number_of_produced_events,
      number_of_consumed_event_tags, number_of_produced_event_tags,
      number_of_consumed_reports, number_of_produced_reports,
      number_of_consumed_warnings, number_of_produced_warnings):
    """Updates the status of the foreman.

    Args:
      identifier (str): foreman identifier.
      status (str): human readable status indication such as "Hashing" or
          "Idle".
      pid (int): process identifier (PID).
      used_memory (int): size of used memory in bytes.
      display_name (str): human readable of the file entry currently being
          processed by the foreman.
      number_of_consumed_sources (int): total number of event sources consumed
          by the foreman.
      number_of_produced_sources (int): total number of event sources produced
          by the foreman.
      number_of_consumed_events (int): total number of events consumed by
          the foreman.
      number_of_produced_events (int): total number of events produced by
          the foreman.
      number_of_consumed_event_tags (int): total number of event tags consumed
          by the foreman.
      number_of_produced_event_tags (int): total number of event tags produced
          by the foreman.
      number_of_consumed_warnings (int): total number of warnings consumed by
          the foreman.
      number_of_produced_warnings (int): total number of warnings produced by
          the foreman.
      number_of_consumed_reports (int): total number of event reports consumed
          by the process.
      number_of_produced_reports (int): total number of event reports produced
          by the process.
    """
    if not self.foreman_status:
      self.foreman_status = ProcessStatus()

    self._UpdateProcessStatus(
        self.foreman_status, identifier, status, pid, used_memory, display_name,
        number_of_consumed_sources, number_of_produced_sources,
        number_of_consumed_events, number_of_produced_events,
        number_of_consumed_event_tags, number_of_produced_event_tags,
        number_of_consumed_reports, number_of_produced_reports,
        number_of_consumed_warnings, number_of_produced_warnings)

  def UpdateEventsStatus(self, events_status):
    """Updates the events status.

    Args:
      events_status (EventsStatus): status information about events.
    """
    self.events_status = events_status

  def UpdateTasksStatus(self, tasks_status):
    """Updates the tasks status.

    Args:
      tasks_status (TasksStatus): status information about tasks.
    """
    self.tasks_status = tasks_status

  # pylint: disable=too-many-arguments
  def UpdateWorkerStatus(
      self, identifier, status, pid, used_memory, display_name,
      number_of_consumed_sources, number_of_produced_sources,
      number_of_consumed_events, number_of_produced_events,
      number_of_consumed_event_tags, number_of_produced_event_tags,
      number_of_consumed_reports, number_of_produced_reports,
      number_of_consumed_warnings, number_of_produced_warnings):
    """Updates the status of a worker.

    Args:
      identifier (str): worker identifier.
      status (str): human readable status indication such as "Hashing" or
          "Idle".
      pid (int): process identifier (PID).
      used_memory (int): size of used memory in bytes.
      display_name (str): human readable of the file entry currently being
          processed by the worker.
      number_of_consumed_sources (int): total number of event sources consumed
          by the worker.
      number_of_produced_sources (int): total number of event sources produced
          by the worker.
      number_of_consumed_events (int): total number of events consumed by
          the worker.
      number_of_produced_events (int): total number of events produced by
          the worker.
      number_of_consumed_event_tags (int): total number of event tags consumed
          by the worker.
      number_of_produced_event_tags (int): total number of event tags produced
          by the worker.
      number_of_consumed_reports (int): total number of event reports consumed
          by the process.
      number_of_produced_reports (int): total number of event reports produced
          by the process.
      number_of_consumed_warnings (int): total number of warnings consumed by
          the worker.
      number_of_produced_warnings (int): total number of warnings produced by
          the worker.
    """
    if identifier not in self._workers_status:
      self._workers_status[identifier] = ProcessStatus()

    process_status = self._workers_status[identifier]
    self._UpdateProcessStatus(
        process_status, identifier, status, pid, used_memory, display_name,
        number_of_consumed_sources, number_of_produced_sources,
        number_of_consumed_events, number_of_produced_events,
        number_of_consumed_event_tags, number_of_produced_event_tags,
        number_of_consumed_reports, number_of_produced_reports,
        number_of_consumed_warnings, number_of_produced_warnings)


class EventsStatus(object):
  """The status of the events.

  Attributes:
    number_of_duplicate_events (int): number of duplicate events, not including
        the original.
    number_of_events_from_time_slice (int): number of events from time slice.
    number_of_filtered_events (int): number of events excluded by the event
        filter.
    number_of_macb_grouped_events (int): number of events grouped based on MACB.
    total_number_of_events (int): total number of events in the storage file.
  """

  def __init__(self):
    """Initializes an events status."""
    super(EventsStatus, self).__init__()
    self.number_of_duplicate_events = 0
    self.number_of_events_from_time_slice = 0
    self.number_of_filtered_events = 0
    self.number_of_macb_grouped_events = 0
    self.total_number_of_events = 0


class TasksStatus(object):
  """The status of the tasks.

  Attributes:
    number_of_abandoned_tasks (int): number of abandoned tasks.
    number_of_queued_tasks (int): number of active tasks.
    number_of_tasks_pending_merge (int): number of tasks pending merge.
    number_of_tasks_processing (int): number of tasks processing.
    total_number_of_tasks (int): total number of tasks.
  """

  def __init__(self):
    """Initializes a tasks status."""
    super(TasksStatus, self).__init__()
    self.number_of_abandoned_tasks = 0
    self.number_of_queued_tasks = 0
    self.number_of_tasks_pending_merge = 0
    self.number_of_tasks_processing = 0
    self.total_number_of_tasks = 0
