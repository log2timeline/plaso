# -*- coding: utf-8 -*-
"""Event attribute containers."""

from __future__ import unicode_literals

import re

from plaso.containers import interface
from plaso.containers import manager
from plaso.lib import py2to3


class EventData(interface.AttributeContainer):
  """Event data attribute container.

  Attributes:
    data_type (str): event data type indicator.
    offset (int): offset relative to the start of the data stream where
        the event data is stored.
    query (str): query that was used to obtain the event data.
  """
  CONTAINER_TYPE = 'event_data'

  def __init__(self, data_type=None):
    """Initializes an event data attribute container.

    Args:
      data_type (Optional[str]): event data type indicator.
    """
    super(EventData, self).__init__()
    self.data_type = data_type
    self.offset = None
    self.query = None


class EventObject(interface.AttributeContainer):
  """Event attribute container.

  The framework is designed to parse files and create events
  from individual records, log lines or keys extracted from files.
  The event object provides an extensible data store for event
  attributes.

  Attributes:
    data_type (str): event data type indicator.
    display_name (str): display friendly version of the path specification.
    filename (str): name of the file related to the event.
    hostname (str): name of the host related to the event.
    inode (int): inode of the file related to the event.
    offset (int): offset of the event data.
    pathspec (dfvfs.PathSpec): path specification of the file related to
        the event.
    tag (EventTag): event tag.
    timestamp (int): timestamp, which contains the number of microseconds
        since January 1, 1970, 00:00:00 UTC.
    timestamp_desc (str): description of the meaning of the timestamp.
  """
  CONTAINER_TYPE = 'event'
  # TODO: eventually move data type out of event since the event source
  # has a data type not the event itself.
  DATA_TYPE = None

  def __init__(self):
    """Initializes an event attribute container."""
    super(EventObject, self).__init__()
    self._event_data_identifier = None
    # TODO: move to event data
    self.data_type = self.DATA_TYPE
    # TODO: move to event data
    self.display_name = None
    # TODO: move to event data
    self.filename = None
    # TODO: move to event data
    self.hostname = None
    # TODO: move to event data
    self.inode = None
    # TODO: move to event data
    self.offset = None
    # TODO: move to event data
    self.pathspec = None
    self.tag = None
    self.timestamp = None
    self.timestamp_desc = None

    # TODO: add a solution for event_data_row_identifier

  # This method is necessary for heap sort.
  def __lt__(self, other):
    """Compares if the event attribute container is less than the other.

    Events are compared by timestamp.

    Args:
      other (EventObject): event attribute container to compare to.

    Returns:
      bool: True if the event  attribute container is less than the other.
    """
    return self.timestamp < other.timestamp

  def GetEventDataIdentifier(self):
    """Retrieves the identifier of the event data associated with the event.

    The event data identifier is a storage specific value that should not
    be serialized.

    Returns:
      AttributeContainerIdentifier: event identifier or None when not set.
    """
    return self._event_data_identifier

  def SetEventDataIdentifier(self, event_data_identifier):
    """Sets the identifier of the event data associated with the event.

    The event data identifier is a storage specific value that should not
    be serialized.

    Args:
      event_data_identifier (AttributeContainerIdentifier): event identifier.
    """
    self._event_data_identifier = event_data_identifier


class EventTag(interface.AttributeContainer):
  """Event tag attribute container.

  Attributes:
    comment (str): comments.
    event_entry_index (int): serialized data stream entry index of the event,
        this attribute is used by the ZIP and GZIP storage files to
        uniquely identify the event linked to the tag.
    event_stream_number (int): number of the serialized event stream, this
        attribute is used by the ZIP and GZIP storage files to uniquely
        identify the event linked to the tag.
    labels (list[str]): labels, such as "malware", "application_execution".
  """
  CONTAINER_TYPE = 'event_tag'

  _INVALID_LABEL_CHARACTERS_REGEX = re.compile(r'[^A-Za-z0-9_]')

  _VALID_LABEL_REGEX = re.compile(r'^[A-Za-z0-9_]+$')

  def __init__(self, comment=None):
    """Initializes an event tag attribute container.

    Args:
      comment (Optional[str]): comments.
    """
    super(EventTag, self).__init__()
    self._event_identifier = None
    self.comment = comment
    self.event_entry_index = None
    self.event_row_identifier = None
    self.event_stream_number = None
    self.labels = []

  def AddComment(self, comment):
    """Adds a comment to the event tag.

    Args:
      comment (str): comment.
    """
    if not comment:
      return

    if not self.comment:
      self.comment = comment
    else:
      self.comment = ''.join([self.comment, comment])

  def AddLabel(self, label):
    """Adds a label to the event tag.

    Args:
      label (str): label.

    Raises:
      TypeError: if the label provided is not a string.
      ValueError: if a label is malformed.
    """
    if not isinstance(label, py2to3.STRING_TYPES):
      raise TypeError('label is not a string type. Is {0:s}'.format(
          type(label)))
    if not self._VALID_LABEL_REGEX.match(label):
      raise ValueError((
          'Unsupported label: "{0:s}". A label must only consist of '
          'alphanumeric characters or underscores.').format(label))

    if label not in self.labels:
      self.labels.append(label)

  def AddLabels(self, labels):
    """Adds labels to the event tag.

    Args:
      labels (list[str]): labels.

    Raises:
      ValueError: if a label is malformed.
    """
    for label in labels:
      if not self._VALID_LABEL_REGEX.match(label):
        raise ValueError((
            'Unsupported label: "{0:s}". A label must only consist of '
            'alphanumeric characters or underscores.').format(label))

    for label in labels:
      if label not in self.labels:
        self.labels.append(label)

  def CopyToDict(self):
    """Copies the event tag to a dictionary.

    Returns:
      dict[str, object]: event tag attributes.
    """
    result_dict = {
        'labels': self.labels
    }
    if self.comment:
      result_dict['comment'] = self.comment

    return result_dict

  @classmethod
  def CopyTextToLabel(cls, text, prefix=''):
    """Copies a string to a label.

    A label only supports a limited set of characters therefore
    unsupported characters are replaced with an underscore.

    Args:
      text (str): label text.
      prefix (Optional[str]): label prefix.

    Returns:
      str: label.
    """
    text = '{0:s}{1:s}'.format(prefix, text)
    return cls._INVALID_LABEL_CHARACTERS_REGEX.sub('_', text)

  def GetEventIdentifier(self):
    """Retrieves the identifier of the event associated with the event tag.

    The event identifier is a storage specific value that should not
    be serialized.

    Returns:
      AttributeContainerIdentifier: event identifier or None when not set.
    """
    return self._event_identifier

  def SetEventIdentifier(self, event_identifier):
    """Sets the identifier of the event associated with the event tag.

    The event identifier is a storage specific value that should not
    be serialized.

    Args:
      event_identifier (AttributeContainerIdentifier): event identifier.
    """
    self._event_identifier = event_identifier


manager.AttributeContainersManager.RegisterAttributeContainers([
    EventData, EventObject, EventTag])
