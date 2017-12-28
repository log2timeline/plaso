# -*- coding: utf-8 -*-
"""The event tag index."""

from __future__ import unicode_literals


class EventTagIndex(object):
  """Event tag index."""

  def __init__(self):
    """Initializes an event tag index."""
    super(EventTagIndex, self).__init__()
    self._index = None

  def _Build(self, storage_file):
    """Builds the event tag index.

    Args:
      storage_file (BaseStorageFile): storage file.
    """
    self._index = {}
    for event_tag in storage_file.GetEventTags():
      event_identifier = event_tag.GetEventIdentifier()
      lookup_key = event_identifier.CopyToString()
      self._index[lookup_key] = event_tag.GetIdentifier()

  def GetEventTagByIdentifier(self, storage_file, event_identifier):
    """Retrieves an event tag by the event identifier.

    Args:
      storage_file (BaseStorageFile): storage file.
      event_identifier (AttributeContainerIdentifier): event attribute
          container identifier.

    Returns:
      EventTag: event tag or None.
    """
    if not self._index:
      self._Build(storage_file)

    lookup_key = event_identifier.CopyToString()
    event_tag_identifier = self._index.get(lookup_key, None)
    if not event_tag_identifier:
      return

    return storage_file.GetEventTagByIdentifier(event_tag_identifier)

  def UpdateEventTag(self, event_tag):
    """Updates an event tag in the index.

    Args:
      event_tag (EventTag): event tag.
    """
    event_identifier = event_tag.GetEventIdentifier()

    lookup_key = event_identifier.CopyToString()
    self._index[lookup_key] = event_tag.GetIdentifier()
