# -*- coding: utf-8 -*-
"""The processing status classes."""

import time


class ProcessStatus(object):
  """The status of an individual process.

  Attributes:
    display_name (str): human readable of the file entry currently being
        processed by the process.
    identifier (str): process identifier.
    last_running_time (int): timestamp of the last update when the process had
        a running process status.
    number_of_consumed_errors (int): total number of errors consumed by
        the process.
    number_of_consumed_errors_delta (int): number of errors consumed by
        the process since the last status update.
    number_of_consumed_events (int): total number of events consumed by
        the process.
    number_of_consumed_events_delta (int): number of events consumed by
        the process since the last status update.
    number_of_consumed_sources (int): total number of event sources consumed
        by the process.
    number_of_consumed_sources_delta (int): number of event sources consumed
        by the process since the last status update.
    number_of_produced_errors (int): total number of errors produced by
        the process.
    number_of_produced_errors_delta (int): number of errors produced by
        the process since the last status update.
    number_of_produced_events (int): total number of events produced by
        the process.
    number_of_produced_events_delta (int): number of events produced by
        the process since the last status update.
    number_of_produced_sources (int): total number of event sources
        produced by the process.
    number_of_produced_sources_delta (int): number of event sources produced
        by the process since the last status update.
    pid (int): process identifier (PID).
    status (str): human readable status indication e.g. 'Hashing', 'Idle'.
  """

  def __init__(self):
    """Initializes the process status object."""
    super(ProcessStatus, self).__init__()
    self.display_name = None
    self.identifier = None
    self.last_running_time = 0
    self.number_of_consumed_errors = 0
    self.number_of_consumed_errors_delta = 0
    self.number_of_consumed_events = 0
    self.number_of_consumed_events_delta = 0
    self.number_of_consumed_sources = 0
    self.number_of_consumed_sources_delta = 0
    self.number_of_produced_errors = 0
    self.number_of_produced_errors_delta = 0
    self.number_of_produced_events = 0
    self.number_of_produced_events_delta = 0
    self.number_of_produced_sources = 0
    self.number_of_produced_sources_delta = 0
    self.pid = None
    self.status = None

  def UpdateNumberOfErrors(
      self, number_of_consumed_errors, number_of_produced_errors):
    """Updates the number of errors.

    Args:
      number_of_consumed_errors (int): total number of errors consumed by
          the process.
      number_of_produced_errors (int): total number of errors produced by
          the process.

    Returns:
      bool: True if either number of errors has increased.

    Raises:
      ValueError: if the consumer or produced number of errors is smaller
          than the value of the previous update.
    """
    if number_of_consumed_errors < self.number_of_consumed_errors:
      raise ValueError(
          u'Number of consumed errors smaller than previous update.')

    if number_of_produced_errors < self.number_of_produced_errors:
      raise ValueError(
          u'Number of produced errors smaller than previous update.')

    consumed_errors_delta = (
        number_of_consumed_errors - self.number_of_consumed_errors)

    self.number_of_consumed_errors = number_of_consumed_errors
    self.number_of_consumed_errors_delta = consumed_errors_delta

    produced_errors_delta = (
        number_of_produced_errors - self.number_of_produced_errors)

    self.number_of_produced_errors = number_of_produced_errors
    self.number_of_produced_errors_delta = produced_errors_delta

    return consumed_errors_delta > 0 or produced_errors_delta > 0

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
      ValueError: if the consumer or produced number of events is smaller
          than the value of the previous update.
    """
    if number_of_consumed_events < self.number_of_consumed_events:
      raise ValueError(
          u'Number of consumed events smaller than previous update.')

    if number_of_produced_events < self.number_of_produced_events:
      raise ValueError(
          u'Number of produced events smaller than previous update.')

    consumed_events_delta = (
        number_of_consumed_events - self.number_of_consumed_events)

    self.number_of_consumed_events = number_of_consumed_events
    self.number_of_consumed_events_delta = consumed_events_delta

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
      ValueError: if the consumer or produced number of event sources is
          smaller than the value of the previous update.
    """
    if number_of_consumed_sources < self.number_of_consumed_sources:
      raise ValueError(
          u'Number of consumed sources smaller than previous update.')

    if number_of_produced_sources < self.number_of_produced_sources:
      raise ValueError(
          u'Number of produced sources smaller than previous update.')

    consumed_sources_delta = (
        number_of_consumed_sources - self.number_of_consumed_sources)

    self.number_of_consumed_sources = number_of_consumed_sources
    self.number_of_consumed_sources_delta = consumed_sources_delta

    produced_sources_delta = (
        number_of_produced_sources - self.number_of_produced_sources)

    self.number_of_produced_sources = number_of_produced_sources
    self.number_of_produced_sources_delta = produced_sources_delta

    return consumed_sources_delta > 0 or produced_sources_delta > 0


class ProcessingStatus(object):
  """The status of the overall extraction process (processing).

  Attributes:
    aborted (bool): True if processing was aborted.
    error_path_specs (list[str]): path specification strings that caused
        critical errors during processing.
    foreman_status (ProcessingStatus): foreman processing status.
  """

  def __init__(self):
    """Initializes the processing status object."""
    super(ProcessingStatus, self).__init__()
    self._workers_status = {}

    self.aborted = False
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
      number_of_consumed_events, number_of_produced_events,
      number_of_consumed_errors, number_of_produced_errors):
    """Updates a process status.

    Args:
      process_status (ProcessStatus): process status.
      identifier (str): process identifier.
      status (str): human readable status of the process e.g. 'Idle'.
      pid (int): process identifier (PID).
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
      number_of_consumed_errors (int): total number of errors consumed by
          the process.
      number_of_produced_errors (int): total number of errors produced by
          the process.
    """
    new_sources = process_status.UpdateNumberOfEventSources(
        number_of_consumed_sources, number_of_produced_sources)

    new_events = process_status.UpdateNumberOfEvents(
        number_of_consumed_events, number_of_produced_events)

    new_errors = process_status.UpdateNumberOfErrors(
        number_of_consumed_errors, number_of_produced_errors)

    process_status.display_name = display_name
    process_status.identifier = identifier
    process_status.pid = pid
    process_status.status = status

    if new_sources or new_events or new_errors:
      process_status.last_running_time = time.time()

  def UpdateForemanStatus(
      self, identifier, status, pid, display_name,
      number_of_consumed_sources, number_of_produced_sources,
      number_of_consumed_events, number_of_produced_events,
      number_of_consumed_errors, number_of_produced_errors):
    """Updates the status of the foreman.

    Args:
      identifier (str): foreman identifier.
      status (str): human readable status of the foreman e.g. 'Idle'.
      pid (int): process identifier (PID).
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
      number_of_consumed_errors (int): total number of errors consumed by
          the foreman.
      number_of_produced_errors (int): total number of errors produced by
          the foreman.
    """
    if not self.foreman_status:
      self.foreman_status = ProcessStatus()

    self._UpdateProcessStatus(
        self.foreman_status, identifier, status, pid, display_name,
        number_of_consumed_sources, number_of_produced_sources,
        number_of_consumed_events, number_of_produced_events,
        number_of_consumed_errors, number_of_produced_errors)

  def UpdateWorkerStatus(
      self, identifier, status, pid, display_name,
      number_of_consumed_sources, number_of_produced_sources,
      number_of_consumed_events, number_of_produced_events,
      number_of_consumed_errors, number_of_produced_errors):
    """Updates the status of a worker.

    Args:
      identifier (str): worker identifier.
      status (str): human readable status of the worker e.g. 'Idle'.
      pid (int): process identifier (PID).
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
      number_of_consumed_errors (int): total number of errors consumed by
          the worker.
      number_of_produced_errors (int): total number of errors produced by
          the worker.
    """
    if identifier not in self._workers_status:
      self._workers_status[identifier] = ProcessStatus()

    process_status = self._workers_status[identifier]
    self._UpdateProcessStatus(
        process_status, identifier, status, pid, display_name,
        number_of_consumed_sources, number_of_produced_sources,
        number_of_consumed_events, number_of_produced_events,
        number_of_consumed_errors, number_of_produced_errors)
