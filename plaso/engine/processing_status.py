# -*- coding: utf-8 -*-
"""The processing status classes."""

import logging
import time

from plaso.lib import definitions


class CollectorStatus(object):
  """The collector status.

  Attributes:
    identifier: the extraction worker identifier.
    last_running_time: timestamp of the last update when the process
                       had a running process status.
    path_spec_queue_port: the port that the path specification queue is bound
                          to, or None if the queue is not yet bound, or the
                          queue does not use a port.
    pid: the collector process identifier (PID).
    process_status: string containing the process status.
    produced_number_of_path_specs: the total number of path specifications
                                   produced by the collector.
    produced_number_of_path_specs_delta: the number of path specifications
                                         produced since the last status update.
    status: string containing the collector status.
    """

  def __init__(self):
    """Initializes the collector status object."""
    super(CollectorStatus, self).__init__()
    self.identifier = None
    self.last_running_time = 0
    self.path_spec_queue_port = None
    self.pid = None
    self.process_status = None
    self.produced_number_of_path_specs = 0
    self.produced_number_of_path_specs_delta = 0
    self.status = None


class ExtractionWorkerStatus(object):
  """The extraction worker status.

  Attributes:
    consumed_number_of_path_specs: the total number of path specifications
                                   consumed by the extraction worker.
    consumed_number_of_path_specs_delta: the number of path specifications
                                         consumed since the last status update.
    display_name: the display name of the file entry currently being
                  processed by the extraction worker.
    identifier: the extraction worker identifier.
    last_running_time: timestamp of the last update when the process
                       had a running process status.
    number_of_events: the total number of events extracted
                      by the extraction worker.
    number_of_events_delta: the number of events since the last status update.
    pid: the extraction worker process identifier (PID).
    process_status: string containing the process status.
    produced_number_of_path_specs: the total number of path specifications
                                   produced by the collector.
    produced_number_of_path_specs_delta: the number of path specifications
                                         produced since the last status update.
    status: string containing the extraction worker status.
    """

  def __init__(self):
    """Initializes the extraction worker status object."""
    super(ExtractionWorkerStatus, self).__init__()
    self.consumed_number_of_path_specs = 0
    self.consumed_number_of_path_specs_delta = 0
    self.display_name = None
    self.identifier = None
    self.last_running_time = 0
    self.number_of_events = 0
    self.number_of_events_delta = 0
    self.pid = None
    self.process_status = None
    self.produced_number_of_path_specs = 0
    self.produced_number_of_path_specs_delta = 0
    self.status = None


class StorageWriterStatus(object):
  """The storage writer status.

  Attributes:
    event_object_queue_port: the port that the event object queue is bound to,
                             or None if the queue is not yet bound, or the
                             queue does not use a port.
    identifier: the extraction worker identifier.
    last_running_time: timestamp of the last update when the process
                       had a running process status.
    number_of_events: the total number of events received
                      by the storage writer.
    parse_error_queue_port: the port that the path spec queue is bound to, or
                            None if the queue is not yet bound, or the the queue
                            does not use a port.
    pid: the storage writer process identifier (PID).
    process_status: string containing the process status.
    status: string containing the storage writer status.
    """

  def __init__(self):
    """Initializes the storage writer status object."""
    super(StorageWriterStatus, self).__init__()
    self.identifier = None
    self.last_running_time = 0
    self.number_of_events = 0
    self.number_of_events_delta = 0
    self.pid = None
    self.process_status = None
    self.status = None


class ProcessingStatus(object):
  """The processing status.

  Attributes:
    error_detected: boolean value to indicate if an error was detected
                    during processing.
    error_path_specs: a list of path specification strings that caused
                      critical errors during processing.
  """

  # The idle timeout in seconds.
  _IDLE_TIMEOUT = 5 * 60

  def __init__(self):
    """Initializes the processing status object."""
    super(ProcessingStatus, self).__init__()
    self._collector = None
    self._collector_completed = False
    self._collector_completed_count = 0
    self._extraction_workers = {}
    self._extraction_workers_last_running_time = 0
    self._storage_writer = None

    self.error_detected = False
    self.error_path_specs = []

  @property
  def collector(self):
    """The collector status object."""
    return self._collector

  @property
  def extraction_workers(self):
    """The extraction worker status objects sorted by identifier."""
    return [
        self._extraction_workers[identifier]
        for identifier in sorted(self._extraction_workers.keys())]

  @property
  def storage_writer(self):
    """The storage writer status object."""
    return self._storage_writer

  def GetExtractionCompleted(self):
    """Determines whether extraction is completed.

    Extraction is considered complete when the collector has finished producing
    path specifications, and all workers have stopped running.

    Returns:
      A boolean value indicating the extraction completed status.
    """
    if not self._collector_completed:
      return False

    produced_number_of_path_specs = self.GetProducedNumberOfPathSpecs()
    consumed_number_of_path_specs = self.GetConsumedNumberOfPathSpecs()
    path_specs_remaining = (
        produced_number_of_path_specs - consumed_number_of_path_specs)
    if path_specs_remaining > 0:
      logging.debug(
          (u'[ProcessingStatus] {0:d} pathspecs produced, {1:d} processed. '
           u'{2:d} remaining. Extraction incomplete.').format(
              produced_number_of_path_specs, consumed_number_of_path_specs,
              path_specs_remaining))
      return False

    workers_running = self.WorkersRunning()

    # Determining if extraction is completed can be a bit flaky
    # at the moment. Hence we wait until the condition is met at least
    # consecutive 3 times.
    if workers_running:
      self._collector_completed_count = 0

    elif self._collector_completed_count < 3:
      self._collector_completed_count += 1
      workers_running = True

    return not workers_running

  def GetNumberOfExtractedEvents(self):
    """Retrieves the number of extracted events."""
    number_of_events = 0
    for extraction_worker_status in iter(self._extraction_workers.values()):
      number_of_events += extraction_worker_status.number_of_events
    return number_of_events

  def GetConsumedNumberOfPathSpecs(self):
    """Retrieves the number of consumed path specifications."""
    number_of_path_specs = 0
    for extraction_worker_status in iter(self._extraction_workers.values()):
      number_of_path_specs += (
          extraction_worker_status.consumed_number_of_path_specs)
    return number_of_path_specs

  def GetProducedNumberOfPathSpecs(self):
    """Retrieves the number of consumed path specifications."""
    number_of_path_specs = self._collector.produced_number_of_path_specs
    for extraction_worker_status in iter(self._extraction_workers.values()):
      number_of_path_specs += (
          extraction_worker_status.produced_number_of_path_specs)
    return number_of_path_specs

  def GetProcessingCompleted(self):
    """Determines the processing completed status.

    Returns:
      A boolean value indicating the extraction completed status.
    """
    extraction_completed = self.GetExtractionCompleted()
    number_of_extracted_events = self.GetNumberOfExtractedEvents()

    number_of_written_events = 0
    if self._storage_writer:
      number_of_written_events = self._storage_writer.number_of_events

    events_remaining = number_of_extracted_events - number_of_written_events

    if not extraction_completed:
      logging.debug(u'Processing incomplete, extraction still in progress.')
      return False

    if events_remaining > 0:
      logging.debug((
          u'{0:d} events extracted, {1:d} written to storage. {2:d} '
          u'remaining').format(
              number_of_extracted_events, number_of_written_events,
              events_remaining))
      return False

    return True

  def UpdateCollectorStatus(
      self, identifier, pid, produced_number_of_path_specs, status,
      process_status):
    """Updates the collector status.

    Args:
      identifier: the extraction worker identifier.
      pid: the collector process identifier (PID).
      produced_number_of_path_specs: the total number of path specifications
                                     produced by the collector.
      status: string containing the collector status.
      process_status: string containing the process status.
    """
    if not self._collector:
      self._collector = CollectorStatus()

    produced_number_of_path_specs_delta = produced_number_of_path_specs
    if produced_number_of_path_specs_delta > 0:
      produced_number_of_path_specs_delta -= (
          self._collector.produced_number_of_path_specs)

    self._collector.identifier = identifier
    self._collector.pid = pid
    self._collector.process_status = process_status
    self._collector.produced_number_of_path_specs = (
        produced_number_of_path_specs)
    self._collector.produced_number_of_path_specs_delta = (
        produced_number_of_path_specs)
    self._collector.status = status

    if status == definitions.PROCESSING_STATUS_COMPLETED:
      self._collector_completed = True
    else:
      self._collector.last_running_time = time.time()

  def UpdateExtractionWorkerStatus(
      self, identifier, pid, display_name, number_of_events,
      consumed_number_of_path_specs, produced_number_of_path_specs, status,
      process_status):
    """Updates the extraction worker status.

    Args:
      identifier: the extraction worker identifier.
      pid: the extraction worker process identifier (PID).
      display_name: the display name of the file entry currently being
                    processed by the extraction worker.
      number_of_events: the total number of events extracted
                        by the extraction worker.
      consumed_number_of_path_specs: the total number of path specifications
                                     consumed by the extraction worker.
      produced_number_of_path_specs: the total number of path specifications
                                     produced by the collector.
      status: string containing the extraction worker status.
      process_status: string containing the process status.
    """
    if identifier not in self._extraction_workers:
      self._extraction_workers[identifier] = ExtractionWorkerStatus()

    extraction_worker_status = self._extraction_workers[identifier]

    number_of_events_delta = number_of_events
    if number_of_events_delta > 0:
      number_of_events_delta -= extraction_worker_status.number_of_events

    consumed_number_of_path_specs_delta = consumed_number_of_path_specs
    if consumed_number_of_path_specs_delta > 0:
      consumed_number_of_path_specs_delta -= (
          extraction_worker_status.consumed_number_of_path_specs)

    produced_number_of_path_specs_delta = produced_number_of_path_specs
    if produced_number_of_path_specs_delta > 0:
      produced_number_of_path_specs_delta -= (
          extraction_worker_status.produced_number_of_path_specs)

    extraction_worker_status.consumed_number_of_path_specs = (
        consumed_number_of_path_specs)
    extraction_worker_status.consumed_number_of_path_specs_delta = (
        consumed_number_of_path_specs_delta)
    extraction_worker_status.display_name = display_name
    extraction_worker_status.identifier = identifier
    extraction_worker_status.number_of_events = number_of_events
    extraction_worker_status.number_of_events_delta = number_of_events_delta
    extraction_worker_status.pid = pid
    extraction_worker_status.process_status = process_status
    extraction_worker_status.produced_number_of_path_specs = (
        produced_number_of_path_specs)
    extraction_worker_status.produced_number_of_path_specs_delta = (
        produced_number_of_path_specs_delta)
    extraction_worker_status.status = status

    if (number_of_events_delta > 0 or
        consumed_number_of_path_specs_delta > 0 or
        produced_number_of_path_specs_delta > 0):
      timestamp = time.time()
      extraction_worker_status.last_running_time = timestamp
      self._extraction_workers_last_running_time = timestamp

  def UpdateStorageWriterStatus(
      self, identifier, pid, number_of_events, status, process_status):
    """Updates the storage writer status.

    Args:
      identifier: the extraction worker identifier.
      pid: the storage writer process identifier (PID).
      number_of_events: the total number of events received
                        by the storage writer.
      status: string containing the storage writer status.
      process_status: string containing the process status.
    """
    if not self._storage_writer:
      self._storage_writer = StorageWriterStatus()

    number_of_events_delta = number_of_events
    if number_of_events_delta > 0:
      number_of_events_delta -= self._storage_writer.number_of_events

    self._storage_writer.identifier = identifier
    self._storage_writer.number_of_events = number_of_events
    self._storage_writer.number_of_events_delta = number_of_events_delta
    self._storage_writer.pid = pid
    self._storage_writer.process_status = process_status
    self._storage_writer.status = status

    if number_of_events_delta > 0:
      self._storage_writer.last_running_time = time.time()

  def StorageWriterIdle(self):
    """Determines if the storage writer is idle."""
    timestamp = time.time()
    if (self._storage_writer.last_running_time == 0 or
        self._storage_writer.last_running_time >= timestamp):
      return False

    timestamp -= self._storage_writer.last_running_time
    if timestamp < self._IDLE_TIMEOUT:
      return False
    return True

  def WorkersIdle(self):
    """Determines if the workers are idle."""
    timestamp = time.time()
    if (self._extraction_workers_last_running_time == 0 or
        self._extraction_workers_last_running_time >= timestamp):
      return False

    timestamp -= self._extraction_workers_last_running_time
    if timestamp < self._IDLE_TIMEOUT:
      return False
    return True

  def WorkersRunning(self):
    """Determines if the workers are running."""
    for extraction_worker_status in iter(self._extraction_workers.values()):
      if (extraction_worker_status.status ==
          definitions.PROCESSING_STATUS_COMPLETED):
        logging.debug(u'Worker completed.')
        continue
      if (extraction_worker_status.number_of_events_delta > 0 or
          extraction_worker_status.consumed_number_of_path_specs_delta > 0 or
          extraction_worker_status.produced_number_of_path_specs_delta > 0):
        return True

    return False
