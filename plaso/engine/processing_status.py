# -*- coding: utf-8 -*-
"""The processing status classes."""

import time


class ProcessStatus(object):
  """The process status.

  Attributes:
    display_name (str): display name of the file entry currently being
                        processed by the worker.
    identifier (str): worker identifier.
    last_running_time (int): timestamp of the last update when the process had
                             a running process status.
    number_of_consumed_events (int): total number of events consumed by
                                     the worker.
    number_of_consumed_events_delta (int): number of events consumed by
                                           the worker since the last
                                           status update.
    number_of_consumed_sources (int): total number of event sources consumed
                                      by the worker.
    number_of_consumed_sources_delta (int): number of event sources consumed
                                            by the worker since the last status
                                            update.
    number_of_produced_events (int): total number of events produced by
                                     the worker.
    number_of_produced_events_delta (int): number of events produced by
                                           the worker since the last status
                                           update.
    number_of_produced_sources (int): total number of event sources
                                      produced by the worker.
    number_of_produced_sources_delta (int): number of event sources produced
                                            by the worker since the last status
                                            update.
    pid (int): process identifier (PID).
    status (str): human readable status indication e.g. 'Hashing', 'Idle'.
  """

  def __init__(self):
    """Initializes the process status object."""
    super(ProcessStatus, self).__init__()
    self.display_name = None
    self.identifier = None
    self.last_running_time = 0
    self.number_of_consumed_events = 0
    self.number_of_consumed_events_delta = 0
    self.number_of_consumed_sources = 0
    self.number_of_consumed_sources_delta = 0
    self.number_of_produced_events = 0
    self.number_of_produced_events_delta = 0
    self.number_of_produced_sources = 0
    self.number_of_produced_sources_delta = 0
    self.pid = None
    self.status = None


class ProcessingStatus(object):
  """The processing status.

  Attributes:
    error_detected (bool): True if an error was detected during processing.
    error_path_specs (list[str]): path specification strings that caused
                                  critical errors during processing.
    foreman_status (ProcessingStatus): foreman processing status.
  """

  # The idle timeout in seconds.
  _IDLE_TIMEOUT = 5 * 60

  def __init__(self):
    """Initializes the processing status object."""
    super(ProcessingStatus, self).__init__()
    self._workers_last_running_time = 0
    self._workers_status = {}

    self.error_detected = False
    self.error_path_specs = []
    self.foreman_status = None

  @property
  def workers_status(self):
    """The worker status objects sorted by identifier."""
    return [self._workers_status[identifier]
            for identifier in sorted(self._workers_status.keys())]

  def _UpdateProcessStatus(
      self, process_status, identifier, status, pid, display_name,
      number_of_consumed_sources, number_of_produced_sources,
      number_of_consumed_events, number_of_produced_events):
    """Updates a process status.

    Args:
      process_status (ProcessStatus): process status.
      identifier (str): worker identifier.
      status (str): human readable status of the worker e.g. 'Idle'.
      pid (int): process identifier (PID).
      display_name (str): display name of the file entry currently being
                          processed by the worker.
      number_of_consumed_sources (int): total number of event sources consumed
                                        by the worker.
      number_of_produced_sources (int): total number of event sources produced
                                        by the worker.
      number_of_consumed_events (int): total number of events consumed by
                                       the worker.
      number_of_produced_events (int): total number of events produced by
                                       the worker.
    """
    timestamp = 0

    number_of_events_delta = number_of_consumed_events
    if number_of_events_delta > 0:
      number_of_events_delta -= process_status.number_of_consumed_events

    process_status.number_of_consumed_events = number_of_consumed_events
    process_status.number_of_consumed_events_delta = number_of_events_delta

    number_of_sources_delta = number_of_consumed_sources
    if number_of_sources_delta > 0:
      number_of_sources_delta -= process_status.number_of_consumed_sources

    process_status.number_of_consumed_sources = number_of_consumed_sources
    process_status.number_of_consumed_sources_delta = number_of_sources_delta

    if number_of_events_delta > 0 or number_of_sources_delta > 0:
      timestamp = time.time()

    process_status.display_name = display_name
    process_status.identifier = identifier
    process_status.pid = pid

    number_of_events_delta = number_of_produced_events
    if number_of_events_delta > 0:
      number_of_events_delta -= process_status.number_of_produced_events

    process_status.number_of_produced_events = number_of_produced_events
    process_status.number_of_produced_events_delta = number_of_events_delta

    number_of_sources_delta = number_of_produced_sources
    if number_of_sources_delta > 0:
      number_of_sources_delta -= process_status.number_of_produced_sources

    process_status.number_of_produced_sources = number_of_produced_sources
    process_status.number_of_produced_sources_delta = number_of_sources_delta

    if ((number_of_events_delta > 0 or number_of_sources_delta > 0) and
        not timestamp):
      timestamp = time.time()

    process_status.status = status

    if timestamp:
      process_status.last_running_time = timestamp
      self._workers_last_running_time = timestamp

  def GetNumberOfConsumedEventSources(self):
    """Retrieves the number of consumed event sources."""
    number_of_sources = 0
    for worker_status in iter(self._workers_status.values()):
      number_of_sources += worker_status.number_of_consumed_sources
    return number_of_sources

  def GetNumberOfProducedEvents(self):
    """Retrieves the number of produced events."""
    number_of_events = 0
    for worker_status in iter(self._workers_status.values()):
      number_of_events += worker_status.number_of_events
    return number_of_events

  def GetNumberOfProducedEventSources(self):
    """Retrieves the number of consumed event sources."""
    number_of_sources = self.foreman_status.number_of_produced_sources
    for worker_status in iter(self._workers_status.values()):
      number_of_sources += worker_status.number_of_produced_sources
    return number_of_sources

  def UpdateForemanStatus(
      self, identifier, status, pid, display_name,
      number_of_consumed_sources, number_of_produced_sources,
      number_of_consumed_events, number_of_produced_events):
    """Updates the status of the foreman.

    Args:
      identifier (str): foreman identifier.
      status (str): human readable status of the foreman e.g. 'Idle'.
      pid (int): process identifier (PID).
      display_name (str): display name of the file entry currently being
                          processed by the foreman.
      number_of_consumed_sources (int): total number of event sources consumed
                                        by the foreman.
      number_of_produced_sources (int): total number of event sources produced
                                        by the foreman.
      number_of_consumed_events (int): total number of events consumed by
                                       the foreman.
      number_of_produced_events (int): total number of events produced by
                                       the foreman.
    """
    if not self.foreman_status:
      self.foreman_status = ProcessStatus()

    self._UpdateProcessStatus(
        self.foreman_status, identifier, status, pid, display_name,
        number_of_consumed_sources, number_of_produced_sources,
        number_of_consumed_events, number_of_produced_events)

  def UpdateWorkerStatus(
      self, identifier, status, pid, display_name,
      number_of_consumed_sources, number_of_produced_sources,
      number_of_consumed_events, number_of_produced_events):
    """Updates the status of a worker.

    Args:
      identifier (str): worker identifier.
      status (str): human readable status of the worker e.g. 'Idle'.
      pid (int): process identifier (PID).
      display_name (str): display name of the file entry currently being
                          processed by the worker.
      number_of_consumed_sources (int): total number of event sources consumed
                                        by the worker.
      number_of_produced_sources (int): total number of event sources produced
                                        by the worker.
      number_of_consumed_events (int): total number of events consumed by
                                       the worker.
      number_of_produced_events (int): total number of events produced by
                                       the worker.
    """
    if identifier not in self._workers_status:
      self._workers_status[identifier] = ProcessStatus()

    self._UpdateProcessStatus(
        self._workers_status[identifier], identifier, status, pid,
        display_name, number_of_consumed_sources, number_of_produced_sources,
        number_of_consumed_events, number_of_produced_events)
