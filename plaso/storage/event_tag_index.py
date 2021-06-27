# -*- coding: utf-8 -*-
"""The event tag index."""

from plaso.containers import events


class EventTagIndex(object):
  """Event tag index.

  The event tag index is used to map event tags to events.

  It is necessary for the ZIP storage files since previously
  stored event tags cannot be altered.
  """

  _CONTAINER_TYPE_EVENT_TAG = events.EventTag.CONTAINER_TYPE

  def __init__(self):
    """Initializes an event tag index."""
    super(EventTagIndex, self).__init__()
    self._index = None

  def _Build(self, storage_reader):
    """Builds the event tag index.

    Args:
      storage_reader (StorageReader): storage reader.
    """
    self._index = {}
    for event_tag in storage_reader.GetAttributeContainers(
        self._CONTAINER_TYPE_EVENT_TAG):
      self.SetEventTag(event_tag)

  def GetEventTagByIdentifier(self, storage_reader, event_identifier):
    """Retrieves the most recently updated event tag for an event.

    Args:
      storage_reader (StorageReader): storage reader.
      event_identifier (AttributeContainerIdentifier): event attribute
          container identifier.

    Returns:
      EventTag: event tag or None if the event has no event tag.
    """
    if self._index is None:
      self._Build(storage_reader)

    lookup_key = event_identifier.CopyToString()
    event_tag_identifier = self._index.get(lookup_key, None)
    if not event_tag_identifier:
      return None

    return storage_reader.GetAttributeContainerByIdentifier(
        events.EventTag.CONTAINER_TYPE, event_tag_identifier)

  def SetEventTag(self, event_tag):
    """Sets an event tag in the index.

    Args:
      event_tag (EventTag): event tag.
    """
    event_identifier = event_tag.GetEventIdentifier()

    lookup_key = event_identifier.CopyToString()
    self._index[lookup_key] = event_tag.GetIdentifier()
