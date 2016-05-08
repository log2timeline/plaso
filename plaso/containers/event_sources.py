# -*- coding: utf-8 -*-
"""Event source related attribute container object definitions."""

from plaso.containers import interface


class EventSource(interface.AttributeContainer):
  """Class to represent an event source attribute container.

  The event source object contains information about where a specific
  event originates e.g. a file, the $STANDARD_INFORMATION MFT attribute,
  or Application Compatibility cache.

  Attributes:
    data_type: a string containing the event data type indicator.
    path_spec: a path specification (instance of dfvfs.PathSpec) or None.
    storage_session: an integer containing the storage session number or
                     0 if not set.
  """
  CONTAINER_TYPE = u'event_source'
  DATA_TYPE = None

  def __init__(self, path_spec=None):
    """Initializes an event source.

    Args:
      path_spec: optional path specification (instance of dfvfs.PathSpec)
                 or None.
    """
    super(EventSource, self).__init__()
    self.data_type = self.DATA_TYPE
    self.path_spec = path_spec
    self.storage_session = 0


class FileEntryEventSource(EventSource):
  """Class to represent a file entry event source.

  The file entry event source is an event source that represents a file
  within a file system.
  """
  DATA_TYPE = u'file_entry'
