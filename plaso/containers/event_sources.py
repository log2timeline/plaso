# -*- coding: utf-8 -*-
"""Event source attribute containers."""

from acstore.containers import interface
from acstore.containers import manager


class EventSource(interface.AttributeContainer):
  """Event source attribute container.

  The event source object contains information about where a specific
  event originates e.g. a file, the $STANDARD_INFORMATION MFT attribute,
  or Application Compatibility cache.

  Attributes:
    data_type (str): attribute container type indicator.
    file_entry_type (str): dfVFS file entry type.
    path_spec (dfvfs.PathSpec): path specification.
  """
  CONTAINER_TYPE = 'event_source'
  DATA_TYPE = None

  SCHEMA = {
      'data_type': 'str',
      'file_entry_type': 'str',
      'path_spec': 'dfvfs.PathSpec'}

  def __init__(self, file_entry_type=None, path_spec=None):
    """Initializes an event source.

    Args:
      file_entry_type (Optional[str]): dfVFS file entry type.
      path_spec (Optional[dfvfs.PathSpec]): path specification.
    """
    super(EventSource, self).__init__()
    self.data_type = self.DATA_TYPE
    self.file_entry_type = file_entry_type
    self.path_spec = path_spec

  # This method is necessary for heap sort.
  def __lt__(self, other):
    """Compares if the event source attribute container is less than the other.

    Args:
      other (EventSource): event source attribute container to compare to.

    Returns:
      bool: True if the event source attribute container is less than the other.
    """
    return self.path_spec.comparable < other.path_spec.comparable


class FileEntryEventSource(EventSource):
  """File entry event source.

  The file entry event source is an event source that represents a file
  within a file system.
  """
  DATA_TYPE = 'file_entry'


manager.AttributeContainersManager.RegisterAttributeContainer(EventSource)
