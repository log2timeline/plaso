# -*- coding: utf-8 -*-
"""The processing status classes."""


class ExtractionWorkerStatus(object):
  """The extraction worker status."""

  def __init__(self):
    """Initializes the extraction worker status object."""
    super(ExtractionWorkerStatus, self).__init__()
    self.display_name = None
    self.identifier = None
    self.is_running = False
    self.last_number_of_events = 0
    self.number_of_events = 0
    self.number_of_path_specs = 0
    self.pid = None
    self.status = None


class ProcessingStatus(object):
  """The processing status."""

  def __init__(self):
    """Initializes the processing status object."""
    super(ProcessingStatus, self).__init__()
    self._extraction_workers = {}

    self.collector_completed = False
    self.extraction_completed = False
    self.number_of_events = 0
    self.number_of_path_specs = 0

  @property
  def extraction_workers(self):
    """The extraction worker status objects sorted by identifier."""
    return [
        self._extraction_workers[identifier]
        for identifier in sorted(self._extraction_workers.keys())]

  def GetNumberOfExtractedEvents(self):
    """Retrieves the number of extracted events."""
    number_of_events = 0
    for extraction_worker_status in self._extraction_workers.itervalues():
      number_of_events += extraction_worker_status.number_of_events
    return number_of_events

  def GetNumberOfExtractedPathSpecs(self):
    """Retrieves the number of extracted path specifications."""
    number_of_path_specs = 0
    for extraction_worker_status in self._extraction_workers.itervalues():
      number_of_path_specs += extraction_worker_status.number_of_path_specs
    return number_of_path_specs

  # TODO: deprecate is_running in favor of status.
  def UpdateExtractionWorkerStatus(
      self, identifier, pid, display_name, number_of_events,
      number_of_path_specs, status, is_running):
    """Updates the extraction worker status.

    Args:
      identifier: the extraction worker identifier.
      pid: the extraction worker process identifier (PID).
      display_name: the display name of the file entry currently being
                    processed by the extraction worker.
      number_of_events: the total number of events extracted
                        by the extraction worker.
      number_of_path_specs: the total number of path specifications
                            processed by the extraction worker.
      status: the extraction worker status.
      is_running: value to indicate the extraction is running.
    """
    if identifier not in self._extraction_workers:
      self._extraction_workers[identifier] = ExtractionWorkerStatus()

    extraction_worker_status = self._extraction_workers[identifier]
    extraction_worker_status.display_name = display_name
    extraction_worker_status.identifier = identifier
    extraction_worker_status.is_running = is_running
    extraction_worker_status.last_number_of_events = (
        extraction_worker_status.number_of_events)
    extraction_worker_status.number_of_events = number_of_events
    extraction_worker_status.number_of_path_specs = number_of_path_specs
    extraction_worker_status.pid = pid
    extraction_worker_status.status = status
