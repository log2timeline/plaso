# -*- coding: utf-8 -*-
"""Classes to assist in merging attribute containers of tasks."""

from plaso.containers import analysis_results
from plaso.containers import artifacts
from plaso.containers import event_sources
from plaso.containers import events
from plaso.containers import reports
from plaso.containers import warnings


class BaseTaskMergeHelper(object):
  """Interface of heler for merging task related attribute containers.

  Attributes:
    task_identifier (str): identifier of the task that is merged.
  """

  _CONTAINER_TYPES = ()

  def __init__(self, task_storage_reader, task_identifier):
    """Initialize a helper for merging task related attribute containers.

    Args:
      task_storage_reader (StorageReader): task storage reader.
      task_identifier (str): identifier of the task that is merged.
    """
    super(BaseTaskMergeHelper, self).__init__()
    self._container_identifier_mappings = {}
    self._generator = self._GetAttributeContainers(task_storage_reader)
    self._task_storage_reader = task_storage_reader

    self.fully_merged = False
    self.task_identifier = task_identifier

  def _GetAttributeContainers(self, task_storage_reader):
    """Retrieves attribute containers to merge.

    Args:
      task_storage_reader (StorageReader): task storage reader.

    Yields:
      AttributeContainer: attribute container.
    """
    for container_type in self._CONTAINER_TYPES:
      for container in task_storage_reader.GetAttributeContainers(
          container_type):
        yield container

    self.fully_merged = True

  def Close(self):
    """Closes the task storage reader."""
    self._task_storage_reader.Close()
    self._task_storage_reader = None

  def GetAttributeContainer(self):
    """Retrieves an attribute container to merge.

    Returns:
      AttributeContainer: attribute container or None if not available.
    """
    try:
      container = next(self._generator)
    except StopIteration:
      container = None

    return container

  def GetAttributeContainerIdentifier(self, lookup_key):
    """Retrieves an attribute container.

    Args:
      lookup_key (str): lookup key that identifies the attribute container.

    Returns:
      AttributeContainerIdentifier: attribute container identifier that maps
          to the lookup key or None if not available.
    """
    return self._container_identifier_mappings.get(lookup_key, None)

  def SetAttributeContainerIdentifier(self, lookup_key, identifier):
    """Sets an attribute container.

    Args:
      lookup_key (str): lookup key that identifies the attribute container.
      identifier (AttributeContainerIdentifier): attribute container identifier.
    """
    self._container_identifier_mappings[lookup_key] = identifier


class AnalysisTaskMergeHelper(BaseTaskMergeHelper):
  """Assists in merging attribute containers of an analysis task."""

  # Container types produced by the analysis worker processes that need to be
  # merged. Note that some container types reference other container types and
  # therefore container types that are referenced, must be defined before
  # container types that reference them.

  _CONTAINER_TYPES = (
      events.EventTag.CONTAINER_TYPE,
      reports.AnalysisReport.CONTAINER_TYPE,
      warnings.AnalysisWarning.CONTAINER_TYPE,
      analysis_results.BrowserSearchAnalysisResult.CONTAINER_TYPE,
      analysis_results.ChromeExtensionAnalysisResult.CONTAINER_TYPE)


class ExtractionTaskMergeHelper(BaseTaskMergeHelper):
  """Assists in merging attribute containers of an extraction task."""

  # Container types produced by the extraction worker processes that need to be
  # merged. Note that some container types reference other container types and
  # therefore container types that are referenced, must be defined before
  # container types that reference them.

  _CONTAINER_TYPES = (
      event_sources.EventSource.CONTAINER_TYPE,
      events.EventDataStream.CONTAINER_TYPE,
      # The year-less log helper is needed to generate event from the event
      # data by the timeliner and therefore needs to be merged before event
      # data containers.
      events.YearLessLogHelper.CONTAINER_TYPE,
      events.EventData.CONTAINER_TYPE,
      warnings.ExtractionWarning.CONTAINER_TYPE,
      warnings.RecoveryWarning.CONTAINER_TYPE,
      artifacts.WindowsEventLogMessageFileArtifact.CONTAINER_TYPE,
      artifacts.WindowsEventLogMessageStringArtifact.CONTAINER_TYPE,
      artifacts.WindowsWevtTemplateEvent.CONTAINER_TYPE)
