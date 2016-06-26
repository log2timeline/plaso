# -*- coding: utf-8 -*-
"""The processing status classes."""

import logging
import time

from plaso.lib import definitions


class WorkerStatus(object):
  """The worker status.

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
    process_status (str): status of the process.
    status (str): human readable status of the worker e.g. 'Idle'.
  """

  def __init__(self):
    """Initializes the worker status object."""
    super(WorkerStatus, self).__init__()
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
    self.process_status = None
    self.status = None


class ProcessingStatus(object):
  """The processing status.

  Attributes:
    error_detected (bool): True if an error was detected during processing.
    error_path_specs (list[str]): path specification strings that caused
                                  critical errors during processing.
    foreman_status (WorkerStatus): foreman status.
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
    # TODO: change foreman status to a different type.
    self.foreman_status = None

  @property
  def workers_status(self):
    """The worker status objects sorted by identifier."""
    return [self._workers_status[identifier]
            for identifier in sorted(self._workers_status.keys())]

  def _UpdateWorkerStatus(
      self, worker_status, identifier, status, pid, process_status,
      display_name, number_of_consumed_sources, number_of_produced_sources,
      number_of_consumed_events, number_of_produced_events):
    """Updates a worker status.

    Args:
      worker_status (WorkerStatus): worker status.
      identifier (str): worker identifier.
      status (str): human readable status of the worker e.g. 'Idle'.
      pid (int): process identifier (PID).
      process_status (str): status of the process.
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
      number_of_events_delta -= worker_status.number_of_consumed_events

    worker_status.number_of_consumed_events = number_of_consumed_events
    worker_status.number_of_consumed_events_delta = number_of_events_delta

    number_of_sources_delta = number_of_consumed_sources
    if number_of_sources_delta > 0:
      number_of_sources_delta -= worker_status.number_of_consumed_sources

    worker_status.number_of_consumed_sources = number_of_consumed_sources
    worker_status.number_of_consumed_sources_delta = number_of_sources_delta

    if number_of_events_delta > 0 or number_of_sources_delta > 0:
      timestamp = time.time()

    worker_status.display_name = display_name
    worker_status.identifier = identifier
    worker_status.pid = pid
    worker_status.process_status = process_status

    number_of_events_delta = number_of_produced_events
    if number_of_events_delta > 0:
      number_of_events_delta -= worker_status.number_of_produced_events

    worker_status.number_of_produced_events = number_of_produced_events
    worker_status.number_of_produced_events_delta = number_of_events_delta

    number_of_sources_delta = number_of_produced_sources
    if number_of_sources_delta > 0:
      number_of_sources_delta -= worker_status.number_of_produced_sources

    worker_status.number_of_produced_sources = number_of_produced_sources
    worker_status.number_of_produced_sources_delta = number_of_sources_delta

    if ((number_of_events_delta > 0 or number_of_sources_delta > 0) and
        not timestamp):
      timestamp = time.time()

    worker_status.status = status

    if timestamp:
      worker_status.last_running_time = timestamp
      self._workers_last_running_time = timestamp

  # TODO: deprecate.
  def GetExtractionCompleted(self):
    """Determines whether extraction is completed.

    Extraction is considered complete when the collector has finished producing
    path specifications and all workers have stopped running.

    Returns:
      bool: True if extraction complete.
    """
    number_of_consumed_sources = self.GetNumberOfConsumedEventSources()
    number_of_produced_sources = self.GetNumberOfProducedEventSources()
    sources_remaining = (
        number_of_produced_sources - number_of_consumed_sources)
    if sources_remaining > 0:
      logging.debug(
          (u'[ProcessingStatus] {0:d} pathspecs produced, {1:d} processed. '
           u'{2:d} remaining. Extraction incomplete.').format(
               number_of_produced_sources, number_of_consumed_sources,
               sources_remaining))
      return False

    return self.WorkersRunning()

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
      self, identifier, status, pid, process_status,
      display_name, number_of_consumed_sources, number_of_produced_sources,
      number_of_consumed_events, number_of_produced_events):
    """Updates the status of the foreman.

    Args:
      identifier (str): foremane identifier.
      status (str): human readable status of the foremane e.g. 'Idle'.
      pid (int): process identifier (PID).
      process_status (str): status of the process.
      display_name (str): display name of the file entry currently being
                          processed by the foremane.
      number_of_consumed_sources (int): total number of event sources consumed
                                        by the foremane.
      number_of_produced_sources (int): total number of event sources produced
                                        by the foremane.
      number_of_consumed_events (int): total number of events consumed by
                                       the foremane.
      number_of_produced_events (int): total number of events produced by
                                       the foremane.
    """
    if not self.foreman_status:
      self.foreman_status = WorkerStatus()

    self._UpdateWorkerStatus(
        self.foreman_status, identifier, status, pid, process_status,
        display_name, number_of_consumed_sources, number_of_produced_sources,
        number_of_consumed_events, number_of_produced_events)

  def UpdateWorkerStatus(
      self, identifier, status, pid, process_status,
      display_name, number_of_consumed_sources, number_of_produced_sources,
      number_of_consumed_events, number_of_produced_events):
    """Updates the status of a worker.

    Args:
      identifier (str): worker identifier.
      status (str): human readable status of the worker e.g. 'Idle'.
      pid (int): process identifier (PID).
      process_status (str): status of the process.
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
      self._workers_status[identifier] = WorkerStatus()

    self._UpdateWorkerStatus(
        self._workers_status[identifier], identifier, status, pid,
        process_status, display_name, number_of_consumed_sources,
        number_of_produced_sources, number_of_consumed_events,
        number_of_produced_events)

  def WorkersIdle(self):
    """Determines if the workers are idle."""
    timestamp = time.time()
    if (self._workers_last_running_time == 0 or
        self._workers_last_running_time >= timestamp):
      return False

    timestamp -= self._workers_last_running_time
    if timestamp < self._IDLE_TIMEOUT:
      return False
    return True

  def WorkersRunning(self):
    """Determines if the workers are running."""
    for worker_name, worker_status in iter(
        self._workers_status.items()):

      if worker_status.status == definitions.PROCESSING_STATUS_COMPLETED:
        logging.debug(u'{0:s} has completed.'.format(worker_name))
        continue
      logging.debug(u'{0:s} is {1:s}.'.format(
          worker_name, worker_status.status))
      if (worker_status.number_of_events_delta > 0 or
          worker_status.number_of_consumed_sources_delta > 0 or
          worker_status.number_of_produced_sources_delta > 0 or
          worker_status.status == definitions.PROCESSING_STATUS_HASHING):
        logging.debug(u'Workers are running.')
        return True

    logging.debug(u'Workers are not running.')
    return False
