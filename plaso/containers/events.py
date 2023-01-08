# -*- coding: utf-8 -*-
"""Event attribute containers."""

import hashlib
import re

from acstore.containers import interface
from acstore.containers import manager

from dfdatetime import interface as dfdatetime_interface


def CalculateEventValuesHash(event_data, event_data_stream):
  """Calculates a digest hash of the event values.

  Args:
    event_data (EventData): event data.
    event_data_stream (EventDataStream): an event data stream or None if not
        available.

  Returns:
    str: digest hash of the event values content.

  Raises:
    RuntimeError: if the event values hash cannot be determined.
  """
  attributes = ['data_type: {0:s}'.format(event_data.data_type)]

  for attribute_name, attribute_value in sorted(event_data.GetAttributes()):
    # Note that parser is kept for backwards compatibility.
    if attribute_value is None or attribute_name in (
        '_event_data_stream_identifier', '_event_values_hash', '_parser_chain',
        'data_type', 'parser'):
      continue

    # Ignore date and time values.
    if isinstance(attribute_value, dfdatetime_interface.DateTimeValues):
      continue

    if (isinstance(attribute_value, list) and attribute_value and
        isinstance(attribute_value[0],
                     dfdatetime_interface.DateTimeValues)):
      continue

    if not isinstance(attribute_value, (bool, float, int, list, str)):
      raise RuntimeError(
          'Unsupported attribute: {0:s} value type: {1!s}'.format(
              attribute_name, type(attribute_value)))

    try:
      attribute_string = '{0:s}: {1!s}'.format(
          attribute_name, attribute_value)
      attributes.append(attribute_string)
    except UnicodeDecodeError:
      raise RuntimeError(
          'Failed to decode attribute {0:s}'.format(attribute_name))

  if event_data_stream:
    for attribute_name, attribute_value in sorted(
        event_data_stream.GetAttributes()):

      if attribute_name == 'path_spec':
        attribute_value = attribute_value.comparable

      elif not isinstance(attribute_value, (bool, float, int, list, str)):
        raise RuntimeError(
            'Unsupported attribute: {0:s} value type: {1!s}'.format(
                attribute_name, type(attribute_value)))

      try:
        attribute_string = '{0:s}: {1!s}'.format(
            attribute_name, attribute_value)
        attributes.append(attribute_string)
      except UnicodeDecodeError:
        raise RuntimeError(
            'Failed to decode attribute {0:s}'.format(attribute_name))

  content = ', '.join(attributes)
  content_data = content.encode('utf-8')

  md5_context = hashlib.md5(content_data)

  return md5_context.hexdigest()


class EventData(interface.AttributeContainer):
  """Event data attribute container.

  The event data attribute container represents the attributes of an entity,
  such as a database record or log line.

  Attributes:
    data_type (str): event data type indicator.
  """

  CONTAINER_TYPE = 'event_data'

  _SERIALIZABLE_PROTECTED_ATTRIBUTES = [
      '_event_data_stream_identifier',
      '_event_values_hash',
      '_parser_chain']

  def __init__(self, data_type=None):
    """Initializes an event data attribute container.

    Args:
      data_type (Optional[str]): event data type indicator.
    """
    super(EventData, self).__init__()
    self._event_data_stream_identifier = None
    self._event_values_hash = None
    self._parser_chain = None

    self.data_type = data_type

  # Setter and getter for backwards compatibility of older schema.

  @property
  def parser(self):
    """str: string identifying the parser that produced the event data."""
    return self._parser_chain

  @parser.setter
  def parser(self, parser):
    """Sets the the parser chain.

    Args:
      parser (str): string identifying the parser that produced the event data.
    """
    self._parser_chain = parser

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

      if isinstance(attribute_value, bytes):
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

  def GetEventDataStreamIdentifier(self):
    """Retrieves the identifier of the associated event data stream.

    The event data stream identifier is a storage specific value that requires
    special handling during serialization.

    Returns:
      AttributeContainerIdentifier: event data stream or None when not set.
    """
    return self._event_data_stream_identifier

  def SetEventDataStreamIdentifier(self, event_data_stream_identifier):
    """Sets the identifier of the associated event data stream.

    The event data stream identifier is a storage specific value that requires
    special handling during serialization.

    Args:
      event_data_stream_identifier (AttributeContainerIdentifier): event data
          stream identifier.
    """
    self._event_data_stream_identifier = event_data_stream_identifier


class EventDataStream(interface.AttributeContainer):
  """Event data stream attribute container.

  The event data stream attribute container represents the attributes of
  a data stream, such as the content of a file or extended attribute.

  Attributes:
    file_entropy (str): byte entropy value of the data stream.
    md5_hash (str): MD5 digest hash of the data stream.
    path_spec (dfvfs.PathSpec): path specification of the data stream.
    sha1_hash (str): SHA-1 digest hash of the data stream.
    sha256_hash (str): SHA-256 digest hash of the data stream.
    yara_match (list[str]): names of the Yara rules that matched the data
        stream.
  """

  CONTAINER_TYPE = 'event_data_stream'

  SCHEMA = {
      'file_entropy': 'str',
      'md5_hash': 'str',
      'path_spec': 'dfvfs.PathSpec',
      'sha1_hash': 'str',
      'sha256_hash': 'str',
      'yara_match': 'List[str]'}

  def __init__(self):
    """Initializes an event data attribute container."""
    super(EventDataStream, self).__init__()
    self.file_entropy = None
    self.md5_hash = None
    self.path_spec = None
    self.sha1_hash = None
    self.sha256_hash = None
    self.yara_match = None


class EventObject(interface.AttributeContainer):
  """Event attribute container.

  The framework is designed to parse files and create events
  from individual records, log lines or keys extracted from files.
  The event object provides an extensible data store for event
  attributes.

  Attributes:
    date_time (dfdatetime.DateTimeValues): date and time values.
    timestamp (int): timestamp, which contains the number of microseconds
        since January 1, 1970, 00:00:00 UTC.
    timestamp_desc (str): description of the meaning of the timestamp.
  """

  CONTAINER_TYPE = 'event'

  SCHEMA = {
      '_event_data_identifier': 'AttributeContainerIdentifier',
      'date_time': 'dfdatetime.DateTimeValues',
      'timestamp': 'int',
      'timestamp_desc': 'str'}

  _SERIALIZABLE_PROTECTED_ATTRIBUTES = [
      '_event_data_identifier']

  def __init__(self):
    """Initializes an event attribute container."""
    super(EventObject, self).__init__()
    self._event_data_identifier = None
    self.date_time = None
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
    """Retrieves the identifier of the associated event data.

    The event data identifier is a storage specific value that requires special
    handling during serialization.

    Returns:
      AttributeContainerIdentifier: event data identifier or None when not set.
    """
    return self._event_data_identifier

  def SetEventDataIdentifier(self, event_data_identifier):
    """Sets the identifier of the associated event data.

    The event data identifier is a storage specific value that requires special
    handling during serialization.

    Args:
      event_data_identifier (AttributeContainerIdentifier): event data
          identifier.
    """
    self._event_data_identifier = event_data_identifier


class EventTag(interface.AttributeContainer):
  """Event tag attribute container.

  Attributes:
    labels (list[str]): labels, such as "malware", "application_execution".
  """

  CONTAINER_TYPE = 'event_tag'

  SCHEMA = {
      '_event_identifier': 'AttributeContainerIdentifier',
      'labels': 'List[str]'}

  _INVALID_LABEL_CHARACTERS_REGEX = re.compile(r'[^A-Za-z0-9_]')

  _SERIALIZABLE_PROTECTED_ATTRIBUTES = [
      '_event_identifier']

  _VALID_LABEL_REGEX = re.compile(r'^[A-Za-z0-9_]+$')

  def __init__(self):
    """Initializes an event tag attribute container."""
    super(EventTag, self).__init__()
    self._event_identifier = None
    self.labels = []

  def AddLabel(self, label):
    """Adds a label to the event tag.

    Args:
      label (str): label.

    Raises:
      TypeError: if the label provided is not a string.
      ValueError: if a label is malformed.
    """
    if not isinstance(label, str):
      raise TypeError('label is not a string type. Is {0!s}'.format(
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
      if not label or not self._VALID_LABEL_REGEX.match(label):
        raise ValueError((
            'Unsupported label: "{0!s}". A label must only consist of '
            'alphanumeric characters or underscores.').format(label))

    for label in labels:
      if label not in self.labels:
        self.labels.append(label)

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
    """Retrieves the identifier of the associated event.

    The event identifier is a storage specific value that requires special
    handling during serialization.

    Returns:
      AttributeContainerIdentifier: event identifier or None when not set.
    """
    return self._event_identifier

  def SetEventIdentifier(self, event_identifier):
    """Sets the identifier of the associated event.

    The event identifier is a storage specific value that requires special
    handling during serialization.

    Args:
      event_identifier (AttributeContainerIdentifier): event identifier.
    """
    self._event_identifier = event_identifier


class YearLessLogHelper(interface.AttributeContainer):
  """Year-less log helper attribute container.

  Attributes:
    earliest_year (int): earliest possible year the event data stream was
        created.
    last_relative_year (int): last relative year determined by the year-less
        log helper.
    latest_year (int): latest possible year the event data stream was created.
  """

  CONTAINER_TYPE = 'year_less_log_helper'

  SCHEMA = {
      '_event_data_stream_identifier': 'AttributeContainerIdentifier',
      'earliest_year': 'int',
      'last_relative_year': 'int',
      'latest_year': 'int'}

  _SERIALIZABLE_PROTECTED_ATTRIBUTES = [
      '_event_data_stream_identifier']

  def __init__(self):
    """Initializes a year-less log helper attribute container."""
    super(YearLessLogHelper, self).__init__()
    self._event_data_stream_identifier = None
    self.earliest_year = None
    self.last_relative_year = None
    self.latest_year = None

  def GetEventDataStreamIdentifier(self):
    """Retrieves the identifier of the associated event data stream.

    The event data stream identifier is a storage specific value that requires
    special handling during serialization.

    Returns:
      AttributeContainerIdentifier: event data stream or None when not set.
    """
    return self._event_data_stream_identifier

  def SetEventDataStreamIdentifier(self, event_data_stream_identifier):
    """Sets the identifier of the associated event data stream.

    The event data stream identifier is a storage specific value that requires
    special handling during serialization.

    Args:
      event_data_stream_identifier (AttributeContainerIdentifier): event data
          stream identifier.
    """
    self._event_data_stream_identifier = event_data_stream_identifier


manager.AttributeContainersManager.RegisterAttributeContainers([
    EventData, EventDataStream, EventObject, EventTag, YearLessLogHelper])
