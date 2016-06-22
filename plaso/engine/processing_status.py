# -*- coding: utf-8 -*-
"""The processing status classes."""

import logging
import time

from plaso.lib import definitions


class WorkerStatus(object):
  """The worker status.

  Attributes:
    consumed_number_of_events: an integer containing the total number of events
                               consumed by the worker.
    consumed_number_of_events_delta: an integer containing the number of events
                                     consumed by the worker since the last
                                     status update.
    consumed_number_of_sources: an integer containing the total number of
                                event sources consumed by the worker.
    consumed_number_of_sources_delta: an integer containin the number of
                                      event sources consumed by the
                                      worker since the last status update.
    display_name: a string containing the display name of the file entry
                  currently being processed by the worker.
    identifier: a string containing the worker identifier.
    last_running_time: an integer containing the timestamp of the last update
                       when the process had a running process status.
    pid: an integer containing the process identifier (PID).
    process_status: a string containing the process status.
    produced_number_of_events: an integer containing the total number of events
                               produced by the worker.
    produced_number_of_events_delta: an integer containing the number of events
                                     produced by the worker since the last
                                     status update.
    produced_number_of_sources: an integer containing the total number of
                                event sources produced by the worker.
    produced_number_of_sources_delta: an integer containing the number of
                                      event sources produced by the
                                      worker since the last status update.
    status: string containing the worker status.
  """

  def __init__(self):
    """Initializes the worker status object."""
    super(WorkerStatus, self).__init__()
    self.consumed_number_of_events = 0
    self.consumed_number_of_events_delta = 0
    self.consumed_number_of_sources = 0
    self.consumed_number_of_sources_delta = 0
    self.display_name = None
    self.identifier = None
    self.last_running_time = 0
    self.number_of_events = 0
    self.number_of_events_delta = 0
    self.pid = None
    self.process_status = None
    self.produced_number_of_events = 0
    self.produced_number_of_events_delta = 0
    self.produced_number_of_sources = 0
    self.produced_number_of_sources_delta = 0
    self.status = None


class ProcessingStatus(object):
  """The processing status.

  Attributes:
    error_detected: boolean value to indicate if an error was detected
                    during processing.
    error_path_specs: a list of path specification strings that caused
                      critical errors during processing.
    foreman_status: the foreman status (instance of WorkerStatus).
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

  def _SetWorkerStatus(
      self, worker_status, identifier, status, pid, process_status,
      display_name, consumed_number_of_sources,
      produced_number_of_sources, consumed_number_of_events,
      produced_number_of_events):
    """Sets a worker status.

    Args:
      worker_status: a worker status object (instance of WorkerStatus).
      identifier: a string containing the worker identifier.
      status: a string containing the worker status.
      pid: an integer containing the worker process identifier (PID).
      process_status: string containing the process status.
      display_name: a string containing the display name of the file entry
                    currently being processed by the worker.
      consumed_number_of_sources: an integer containing the total number
                                  of event sources consumed by the worker.
      produced_number_of_sources: an integer containing the total number
                                  of event sources produced by the worker.
      consumed_number_of_events: an integer containing the total number of
                                 events consumed by the worker.
      produced_number_of_events: an integer containing the total number of
                                 events produced by the worker.
    """
    timestamp = 0

    number_of_events_delta = consumed_number_of_events
    if number_of_events_delta > 0:
      number_of_events_delta -= worker_status.consumed_number_of_events

    worker_status.consumed_number_of_events = consumed_number_of_events
    worker_status.consumed_number_of_events_delta = number_of_events_delta

    if not timestamp and number_of_events_delta > 0:
      timestamp = time.time()

    number_of_sources_delta = consumed_number_of_sources
    if number_of_sources_delta > 0:
      number_of_sources_delta -= worker_status.consumed_number_of_sources

    worker_status.consumed_number_of_sources = consumed_number_of_sources
    worker_status.consumed_number_of_sources_delta = number_of_sources_delta

    if not timestamp and number_of_sources_delta > 0:
      timestamp = time.time()

    worker_status.display_name = display_name
    worker_status.identifier = identifier
    worker_status.pid = pid
    worker_status.process_status = process_status

    number_of_events_delta = produced_number_of_events
    if number_of_events_delta > 0:
      number_of_events_delta -= worker_status.produced_number_of_events

    worker_status.produced_number_of_events = produced_number_of_events
    worker_status.produced_number_of_events_delta = number_of_events_delta

    if not timestamp and number_of_events_delta > 0:
      timestamp = time.time()

    number_of_sources_delta = produced_number_of_sources
    if number_of_sources_delta > 0:
      number_of_sources_delta -= worker_status.produced_number_of_sources

    worker_status.produced_number_of_sources = produced_number_of_sources
    worker_status.produced_number_of_sources_delta = number_of_sources_delta

    if not timestamp and number_of_sources_delta > 0:
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
      A boolean value indicating the completed status.
    """
    produced_number_of_sources = self.GetProducedNumberOfEventSources()
    consumed_number_of_sources = self.GetConsumedNumberOfEventSources()
    sources_remaining = (
        produced_number_of_sources - consumed_number_of_sources)
    if sources_remaining > 0:
      logging.debug(
          (u'[ProcessingStatus] {0:d} pathspecs produced, {1:d} processed. '
           u'{2:d} remaining. Extraction incomplete.').format(
               produced_number_of_sources, consumed_number_of_sources,
               sources_remaining))
      return False

    return self.WorkersRunning()

  def GetConsumedNumberOfEventSources(self):
    """Retrieves the number of consumed event sources."""
    number_of_sources = 0
    for worker_status in iter(self._workers_status.values()):
      number_of_sources += worker_status.consumed_number_of_sources
    return number_of_sources

  def GetProducedNumberOfEvents(self):
    """Retrieves the number of produced events."""
    number_of_events = 0
    for worker_status in iter(self._workers_status.values()):
      number_of_events += worker_status.number_of_events
    return number_of_events

  def GetProducedNumberOfEventSources(self):
    """Retrieves the number of consumed event sources."""
    number_of_sources = self.foreman_status.produced_number_of_sources
    for worker_status in iter(self._workers_status.values()):
      number_of_sources += worker_status.produced_number_of_sources
    return number_of_sources

  # TODO: deprecate.
  def GetProcessingCompleted(self):
    """Determines the processing completed status.

    Processing is considered complete when the storage writer has consumed
    the event objects produces by the workers.

    Returns:
      A boolean value indicating the completed status.
    """
    if not self._storage_writer:
      logging.debug(u'Processing incomplete - missing storage writer.')
      return False

    extraction_completed = self.GetExtractionCompleted()
    if not extraction_completed:
      logging.debug(u'Processing incomplete - extraction still in progress.')
      return False

    number_of_extracted_events = self.GetProducedNumberOfEvents()
    number_of_written_events = self._storage_writer.number_of_events
    events_remaining = number_of_extracted_events - number_of_written_events

    if events_remaining > 0:
      logging.debug((
          u'{0:d} events extracted, {1:d} written to storage. {2:d} '
          u'remaining').format(
              number_of_extracted_events, number_of_written_events,
              events_remaining))
      return False

    return True

  def UpdateForemanStatus(
      self, identifier, status, pid, process_status,
      display_name, consumed_number_of_sources,
      produced_number_of_sources, consumed_number_of_events,
      produced_number_of_events):
    """Updates the status of the foreman.

    Args:
      identifier: a string containing the worker identifier.
      status: a string containing the worker status.
      pid: an integer containing the worker process identifier (PID).
      process_status: string containing the process status.
      display_name: a string containing the display name of the file entry
                    currently being processed by the worker.
      consumed_number_of_sources: an integer containing the total number
                                  of event sources consumed by the worker.
      produced_number_of_sources: an integer containing the total number
                                  of event sources produced by the worker.
      consumed_number_of_events: an integer containing the total number of
                                 events consumed by the worker.
      produced_number_of_events: an integer containing the total number of
                                 events produced by the worker.
    """
    if not self.foreman_status:
      self.foreman_status = WorkerStatus()

    self._SetWorkerStatus(
        self.foreman_status, identifier, status, pid, process_status,
        display_name, consumed_number_of_sources,
        produced_number_of_sources, consumed_number_of_events,
        produced_number_of_events)

  def UpdateWorkerStatus(
      self, identifier, status, pid, process_status,
      display_name, consumed_number_of_sources,
      produced_number_of_sources, consumed_number_of_events,
      produced_number_of_events):
    """Updates the status of a worker.

    Args:
      identifier: a string containing the worker identifier.
      status: a string containing the worker status.
      pid: an integer containing the worker process identifier (PID).
      process_status: string containing the process status.
      display_name: a string containing the display name of the file entry
                    currently being processed by the worker.
      consumed_number_of_sources: an integer containing the total number
                                  of event sources consumed by the worker.
      produced_number_of_sources: an integer containing the total number
                                  of event sources produced by the worker.
      consumed_number_of_events: an integer containing the total number of
                                 events consumed by the worker.
      produced_number_of_events: an integer containing the total number of
                                 events produced by the worker.
    """
    if identifier not in self._workers_status:
      self._workers_status[identifier] = WorkerStatus()

    self._SetWorkerStatus(
        self._workers_status[identifier], identifier, status, pid,
        process_status, display_name, consumed_number_of_sources,
        produced_number_of_sources, consumed_number_of_events,
        produced_number_of_events)

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
          worker_status.consumed_number_of_sources_delta > 0 or
          worker_status.produced_number_of_sources_delta > 0 or
          worker_status.status == definitions.PROCESSING_STATUS_HASHING):
        logging.debug(u'Workers are running.')
        return True

    logging.debug(u'Workers are not running.')
    return False
