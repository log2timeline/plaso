# -*- coding: utf-8 -*-
"""Event related attribute container object definitions."""

import re
import uuid

from plaso.containers import interface
from plaso.containers import manager
from plaso.lib import py2to3


# TODO: split event into source and event components.
# https://github.com/log2timeline/plaso/wiki/Scribbles-about-events

class EventObject(interface.AttributeContainer):
  """Class to represent an event attribute container.

  The framework is designed to parse files and create events
  from individual records, log lines or keys extracted from files.
  The event object provides an extensible data storage for event
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
    store_index (int): store index of the event within the storage file.
    store_number (int): store number of the event within the storage file.
    tag (EventTag): event tag.
    timestamp (int): timestamp, which contains the number of microseconds
        since January 1, 1970, 00:00:00 UTC.
    uuid (str): unique identifier (UUID).
  """
  CONTAINER_TYPE = u'event'
  # TODO: eventually move data type out of event since the event source
  # has a data type not the event itself.
  DATA_TYPE = None

  # This is a reserved variable just used for comparison operation and defines
  # attributes that should not be used during evaluation of whether two
  # event objects are the same.
  COMPARE_EXCLUDE = frozenset([
      u'data_type',
      u'display_name',
      u'filename',
      u'inode',
      u'pathspec',
      u'store_index',
      u'store_number',
      u'tag',
      u'timestamp',
      u'uuid'])

  def __init__(self):
    """Initializes an event object."""
    super(EventObject, self).__init__()
    self.data_type = self.DATA_TYPE
    self.display_name = None
    self.filename = None
    self.hostname = None
    self.inode = None
    self.offset = None
    self.pathspec = None
    self.store_index = None
    self.store_number = None
    self.tag = None
    self.timestamp = None
    self.uuid = u'{0:s}'.format(uuid.uuid4().get_hex())

  def __eq__(self, event_object):
    """Return a boolean indicating if two event objects are considered equal.

    Compares two event objects together and evaluates if they are
    the same or close enough to be considered to represent the same event.

    For two event objects to be considered the same they need to
    have the following conditions:
    * Have the same timestamp.
    * Have the same data_type value.
    * Have the same set of attributes.
    * Compare all other attributes than those that are reserved, and
    they all have to match.

    The following attributes are considered to be 'reserved' and not used
    for the comparison, so they may be different yet the event object is still
    considered to be equal:
    * inode
    * pathspec
    * filename
    * display_name
    * store_number
    * store_index

    Args:
      event (EventObject): event to compare to.

    Returns:
      bool: True if both event objects are considered equal.
    """
    # Note: if this method changes, the above EqualityString method MUST be
    # updated accordingly.
    if (not isinstance(event_object, EventObject) or
        self.timestamp != event_object.timestamp or
        self.data_type != event_object.data_type):
      return False

    attribute_names = set(self.__dict__.keys())
    if attribute_names != set(event_object.__dict__.keys()):
      return False

    # Here we have to deal with "near" duplicates, so not all attributes
    # should be compared.
    for attribute in attribute_names.difference(self.COMPARE_EXCLUDE):
      if getattr(self, attribute) != getattr(event_object, attribute):
        return False

    # If we are dealing with a file system event the inode number is
    # the attribute that really matters.
    if self.data_type.startswith(u'fs:'):
      inode = self.inode
      if isinstance(inode, py2to3.BYTES_TYPE):
        inode = inode.decode(u'utf8', errors=u'ignore')
      elif not isinstance(inode, py2to3.UNICODE_TYPE):
        inode = u'{0!s}'.format(inode)

      event_object_inode = event_object.inode
      if isinstance(event_object_inode, py2to3.BYTES_TYPE):
        event_object_inode = event_object_inode.decode(
            u'utf8', errors=u'ignore')
      elif not isinstance(inode, py2to3.UNICODE_TYPE):
        event_object_inode = u'{0!s}'.format(event_object_inode)

      return self.inode == event_object.inode

    return True

  def EqualityString(self):
    """Returns a string describing the event object in terms of object equality.

    The details of this function must match the logic of __eq__. EqualityStrings
    of two event objects should be the same if and only if the event objects are
    equal as described in __eq__.

    Returns:
      str: string representation of the event object that can be used for
          equality comparison.
    """
    attribute_names = set(self.__dict__.keys())
    fields = sorted(list(attribute_names.difference(self.COMPARE_EXCLUDE)))

    # TODO: Review this (after 1.1.0 release). Is there a better/more clean
    # method of removing the timestamp description field out of the fields list?
    parser = getattr(self, u'parser', u'')
    if parser == u'filestat':
      # We don't want to compare the timestamp description field when comparing
      # filestat events. This is done to be able to join together FILE events
      # that have the same timestamp, yet different description field (as in an
      # event that has for instance the same timestamp for mtime and atime,
      # joining it together into a single event).
      try:
        timestamp_desc_index = fields.index(u'timestamp_desc')
        del fields[timestamp_desc_index]
      except ValueError:
        pass

    basic = [self.timestamp, self.data_type]
    attributes = []
    for attribute in fields:
      value = getattr(self, attribute)
      if isinstance(value, dict):
        attributes.append(sorted(value.items()))
      elif isinstance(value, set):
        attributes.append(sorted(list(value)))
      else:
        attributes.append(value)
    identity = basic + [x for pair in zip(fields, attributes) for x in pair]

    if parser == u'filestat':
      inode = self.inode
      if not self.inode:
        inode = u'_{0:s}'.format(uuid.uuid4())
      identity.append(u'inode')
      identity.append(inode)

    try:
      return u'|'.join(map(py2to3.UNICODE_TYPE, identity))

    except UnicodeDecodeError:
      # If we cannot properly decode the equality string we give back the UUID
      # which is unique to this event and thus will not trigger an equal string
      # with another event.
      return self.uuid

  def GetAttributeNames(self):
    """Retrieves the attribute names from the event object.

    Attributes that are set to None are ignored.

    Returns:
      list[str]: attribute names.
    """
    attribute_names = []
    for attribute_name in iter(self.__dict__.keys()):
      attribute_value = getattr(self, attribute_name, None)
      if attribute_value is not None:
        attribute_names.append(attribute_name)

    return attribute_names


class EventTag(interface.AttributeContainer):
  """Class to represent an event tag attribute container.

  The event tag either needs to have an event_uuid defined or both
  the store_number and store_index to be valid. If both defined
  the store_number and store_index is preferred.

  Attributes:
    comment (str): comments.
    event_uuid (str): event identifier (UUID).
    labels (list[str]): labels, such as "malware", "application_execution".
    store_index (int): store index of the corresponding event.
    store_number (int): store number of the corresponding event.
  """
  CONTAINER_TYPE = u'event_tag'

  _ATTRIBUTE_NAMES = frozenset([
      u'comment', u'event_uuid', u'labels', u'store_index', u'store_number'])

  _INVALID_LABEL_CHARACTERS_REGEX = re.compile(r'[^A-Za-z0-9_]')

  _VALID_LABEL_REGEX = re.compile(r'^[A-Za-z0-9_]+$')

  def __init__(self, comment=None, event_uuid=None):
    """Initializes an event tag.

    Args:
      comment (Optional[str]): comments.
      event_uuid (Optional[str]): event identifier (UUID).
    """
    super(EventTag, self).__init__()
    self.comment = comment
    self.event_uuid = event_uuid
    self.labels = []
    # TODO: deprecate store number and index.
    self.store_index = None
    self.store_number = None

  @property
  def string_key(self):
    """str: string index key for this tag."""
    if self.event_uuid is not None:
      return self.event_uuid

    return u'{0:d}:{1:d}'.format(self.store_number, self.store_index)

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
      self.comment = u''.join([self.comment, comment])

  def AddLabel(self, label):
    """Adds a label to the event tag.

    Args:
      label (str): label.

    Raises:
      ValueError: if a label is malformed.
    """
    if not isinstance(label, py2to3.STRING_TYPES):
      raise TypeError(u'label is not a string type. Is {0:s}'.format(
          type(label)))
    if not self._VALID_LABEL_REGEX.match(label):
      raise ValueError((
          u'Unsupported label: "{0:s}". A label must only consist of '
          u'alphanumeric characters or underscores.').format(label))

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
            u'Unsupported label: "{0:s}". A label must only consist of '
            u'alphanumeric characters or underscores.').format(label))

    for label in labels:
      if label not in self.labels:
        self.labels.append(label)

  def CopyToDict(self):
    """Copies the event tag to a dictionary.

    Returns:
      dict[str, object]: event tag attributes.
    """
    result_dict = {
        u'labels': self.labels
    }
    if (self.store_number is not None and self.store_index is not None and
        self.store_number > -1 and self.store_index > -1):
      result_dict[u'store_number'] = self.store_number
      result_dict[u'store_index'] = self.store_index
    else:
      result_dict[u'event_uuid'] = self.event_uuid

    if self.comment:
      result_dict[u'comment'] = self.comment

    return result_dict

  @classmethod
  def CopyTextToLabel(cls, text, prefix=u''):
    """Copies a string to a label.

    A label only supports a limited set of characters therefore
    unsupported characters are replaced with an underscore.

    Args:
      text (str): label text.
      prefix (Optional[str]): label prefix.

    Returns:
      str: label.
    """
    text = u'{0:s}{1:s}'.format(prefix, text)
    return cls._INVALID_LABEL_CHARACTERS_REGEX.sub(u'_', text)

  def GetAttributes(self):
    """Retrieves the attributes from the event tag object.

    Attributes that are set to None are ignored.

    Yields:
      tuple[str, str]: event tag attribute name and value.
    """
    for attribute_name in self._ATTRIBUTE_NAMES:
      attribute_value = getattr(self, attribute_name, None)
      if attribute_value is not None:
        yield attribute_name, attribute_value


manager.AttributeContainersManager.RegisterAttributeContainers([
    EventObject, EventTag])
