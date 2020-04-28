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
    parser (str): string identifying the parser that produced the event data.
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
    self.parser = None
    self.query = None

  def GetAttributeValuesString(self):
    """Retrieves a comparable string of the attribute values.

    Returns:
      str: comparable string of the attribute values.

    Raises:
      TypeError: if the attribute value type is not supported.
    """
    attributes = []
    for attribute_name, attribute_value in sorted(self.__dict__.items()):
      # Not using startswith to improve performance.
      if attribute_name[0] == '_' or attribute_value is None:
        continue

      if isinstance(attribute_value, py2to3.BYTES_TYPE):
        raise TypeError(
            'Attribute: {0:s} value of type bytes not supported.'.format(
                attribute_name))

      if isinstance(attribute_value, dict):
        raise TypeError(
            'Attribute: {0:s} value of type dict not supported.'.format(
                attribute_name))

      attribute_string = '{0:s}: {1!s}'.format(attribute_name, attribute_value)
      attributes.append(attribute_string)

    return ', '.join(attributes)


class EventObject(interface.AttributeContainer):
  """Event attribute container.

  The framework is designed to parse files and create events
  from individual records, log lines or keys extracted from files.
  The event object provides an extensible data store for event
  attributes.

  Attributes:
    event_data_entry_index (int): serialized data stream entry index of
        the event data, this attribute is used by the GZIP storage files
        to uniquely identify the event data linked to the event.
    event_data_row_identifier (int): row number of the serialized event data
        stream, this attribute is used by the SQLite storage files to uniquely
        identify the event data linked to the event.
    event_data_stream_number (int): number of the serialized event data stream,
        this attribute is used by the GZIP storage files to uniquely identify
        the event data linked to the tag.
    parser (str): string identifying the parser that produced the event.
    tag (EventTag): event tag.
    timestamp (int): timestamp, which contains the number of microseconds
        since January 1, 1970, 00:00:00 UTC.
    timestamp_desc (str): description of the meaning of the timestamp.
  """
  CONTAINER_TYPE = 'event'

  def __init__(self):
    """Initializes an event attribute container."""
    super(EventObject, self).__init__()
    self._event_data_identifier = None
    self.event_data_entry_index = None
    self.event_data_row_identifier = None
    self.event_data_stream_number = None
    self.parser = None
    self.tag = None
    self.timestamp = None
    # TODO: rename timestamp_desc to timestamp_description
    self.timestamp_desc = None

  # This method is necessary for heap sort.
  def __lt__(self, other):
    """Compares if the event attribute container is less than the other.

    Events are compared by timestamp.

    Args:
      other (EventObject): event attribute container to compare to.

    Returns:
      bool: True if the event attribute container is less than the other.
    """
    return (self.timestamp < other.timestamp or
            self.timestamp_desc < other.timestamp_desc)

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
        this attribute is used by the GZIP storage files to uniquely identify
        the event linked to the tag.
    event_row_identifier (int): row number of the serialized event stream, this
        attribute is used by the SQLite storage files to uniquely identify
        the event linked to the tag.
    event_stream_number (int): number of the serialized event stream, this
        attribute is used by the GZIP storage files to uniquely identify
        the event linked to the tag.
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
