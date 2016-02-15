# -*- coding: utf-8 -*-
"""The core object definitions, e.g. the event object."""

import abc
import collections
import logging
import re
import uuid

from plaso.lib import definitions
from plaso.lib import py2to3
from plaso.lib import timelib
from plaso.lib import utils

import pytz


class AttributeContainer(object):
  """Class that defines the attribute container interface.

  This is the the base class for those object that exists primarily as
  a container of attributes with basic accessors and mutators.
  """

  @abc.abstractmethod
  def CopyToDict(self):
    """Copies the attribute container to a dictionary.

    Returns:
      A dictionary containing the attribute container attributes.
    """

  @abc.abstractmethod
  def GetAttributes(self):
    """Retrieves the attributes from the attribute container.

    Attributes that are set to None are ignored.

    Yields:
      A tuple containing the attribute container attribute name and value.
    """


class AnalysisReport(object):
  """Class that defines an analysis report.

  Attributes:
    plugin_name: The name of the plugin that generated the report.
  """

  def __init__(self, plugin_name):
    """Initializes the analysis report.

    Args:
      plugin_name: The name of the plugin that's generating this report.
    """
    super(AnalysisReport, self).__init__()
    self._anomalies = []
    self._tags = []
    self.plugin_name = plugin_name

  def GetAnomalies(self):
    """Retrieves the list of anomalies that are attached to the report."""
    return self._anomalies

  def GetString(self):
    """Returns a Unicode representation of the report."""
    # TODO: Make this a more complete function that includes images
    # and the option of saving as a full fledged HTML document.
    string_list = []
    string_list.append(u'Report generated from: {0:s}'.format(self.plugin_name))

    time_compiled = getattr(self, u'time_compiled', 0)
    if time_compiled:
      time_compiled = timelib.Timestamp.CopyToIsoFormat(time_compiled)
      string_list.append(u'Generated on: {0:s}'.format(time_compiled))

    filter_string = getattr(self, u'filter_string', u'')
    if filter_string:
      string_list.append(u'Filter String: {0:s}'.format(filter_string))

    string_list.append(u'')
    string_list.append(u'Report text:')
    string_list.append(self.text)

    return u'\n'.join(string_list)

  def GetTags(self):
    """Retrieves the list of event tags that are attached to the report."""
    return self._tags

  def SetTags(self, tags):
    """Sets the list of event tags that relate to the report.

    Args:
      tags: A list of event tags (instances of EventTag) that belong to the
            report.
    """
    self._tags = tags

  # TODO: rename text to body?
  def SetText(self, lines_of_text):
    """Sets the text based on a list of lines of text.

    Args:
      lines_of_text: a list containing lines of text.
    """
    # Append one empty string to make sure a new line is added to the last
    # line of text as well.
    lines_of_text.append(u'')

    self.text = u'\n'.join(lines_of_text)


# TODO: Re-design the event object to make it lighter, perhaps template
# based. The current design is too slow and needs to be improved.
class EventObject(object):
  """An event object is the main datastore for an event in plaso.

  The framework is designed to parse files and create an event
  from every single record, line or key extracted from the file.

  An event object is the main data storage for an event in plaso.

  This class defines the high level interface of event object.
  Before creating an event object a class needs to be implemented
  that inherits from event object and implements the functions in it.

  The event object is then used by output processing for saving
  in other forms, such as a protobuf, AFF4 container, CSV files,
  databases, etc.

  The goal of the event object is to provide a easily extensible
  data storage of each events internally in the tool.

  The main event object only exposes those functions that the
  implementations need to implement. The functions that are needed
  simply provide information about the event, or describe the
  attributes that are necessary. How they are assembled is totally
  up to the implementation.

  All required attributes of the event object are passed to the
  constructor of the object while the optional ones are set
  using the method SetValue(attribute, value).

  Attributes:
    data_type: the data type indicator string.
    uuid: unique identifier (UUID) for the event object.
  """
  # This is a convenience variable to define event object as
  # simple value objects. Its runtime equivalent data_type
  # should be used in code logic.
  DATA_TYPE = u''

  # This is a reserved variable just used for comparison operation and defines
  # attributes that should not be used during evaluation of whether two
  # event objects are the same.
  COMPARE_EXCLUDE = frozenset([
      u'timestamp', u'inode', u'pathspec', u'filename', u'uuid',
      u'data_type', u'display_name', u'store_number', u'store_index', u'tag'])

  def __init__(self):
    """Initializes the event object."""
    super(EventObject, self).__init__()
    self.uuid = u'{0:s}'.format(uuid.uuid4().get_hex())
    if self.DATA_TYPE:
      self.data_type = self.DATA_TYPE

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
      event_object: The event object to compare to (instance of EventObject).

    Returns:
      A boolean value indicating if both event objects are considered equal.
    """
    # Note: if this method changes, the above EqualityString method MUST be
    # updated accordingly.
    if (not isinstance(event_object, EventObject) or
        self.timestamp != event_object.timestamp or
        self.data_type != event_object.data_type):
      return False

    attributes = self.GetAttributes()
    if attributes != event_object.GetAttributes():
      return False

    # Here we have to deal with "near" duplicates, so not all attributes
    # should be compared.
    for attribute in attributes.difference(self.COMPARE_EXCLUDE):
      if getattr(self, attribute) != getattr(event_object, attribute):
        return False

    # If we are dealing with a filesystem event the inode number is
    # the attribute that really matters.
    if self.data_type.startswith(u'fs:'):
      inode = getattr(self, u'inode', None)
      if inode is not None:
        inode = utils.GetUnicodeString(inode)

      event_object_inode = getattr(event_object, u'inode', None)
      if event_object_inode is not None:
        event_object_inode = utils.GetUnicodeString(event_object_inode)

      return inode == event_object_inode

    return True

  def __str__(self):
    """Returns a string representation."""
    string = self.GetString()
    return string.encode(u'utf-8')

  # TODO: replace with a Python 3 compatible solution.
  def __unicode__(self):
    """Returns a string representation."""
    return self.GetString()

  def EqualityString(self):
    """Return a string describing the event object in terms of object equality.

    The details of this function must match the logic of __eq__. EqualityStrings
    of two event objects should be the same if and only if the event objects are
    equal as described in __eq__.

    Returns:
      String: will match another EventObject's Equality String if and only if
              the EventObjects are equal
    """
    fields = sorted(list(self.GetAttributes().difference(self.COMPARE_EXCLUDE)))

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
      inode = getattr(self, u'inode', u'a')
      if inode == u'a':
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

  def GetAttributes(self):
    """Return a list of all defined attributes."""
    return set(self.__dict__.keys())

  def GetString(self):
    """Retrieves a string representation of the event object.

    Returns:
      A Unicode string containing the string representation of the event object.
    """
    time_string = timelib.Timestamp.CopyToIsoFormat(self.timestamp)

    out_write = [
        u'+-' * 40,
        u'[Timestamp]:',
        u'  {0:s}'.format(time_string)]

    pathspec = getattr(self, u'pathspec', None)
    if pathspec:
      out_write.append(u'[Pathspec]:')
      attribute_string = pathspec.comparable.replace(u'\n', u'\n  ')
      attribute_string = u'  {0:s}\n'.format(attribute_string)
      out_write.append(attribute_string)

    out_write.append(u'[Reserved attributes]:')
    out_additional = [u'[Additional attributes]:']

    for name, value in sorted(self.GetValues().items()):
      if name not in definitions.RESERVED_VARIABLE_NAMES:
        attribute_string = u'  {{{0!s}}} {1!s}'.format(name, value)
        out_additional.append(attribute_string)

      elif name != u'pathspec':
        attribute_string = u'  {{{0!s}}} {1!s}'.format(name, value)
        out_write.append(attribute_string)

    out_write.append(u'')
    out_additional.append(u'')

    out_write.extend(out_additional)
    return u'\n'.join(out_write)

  def GetValues(self):
    """Returns a dictionary of all defined attributes and their values."""
    values = {}
    for attribute_name in set(self.__dict__.keys()):
      values[attribute_name] = getattr(self, attribute_name)
    return values


# TODO: deprecate store number and index.

class EventTag(AttributeContainer):
  """Class to represent an event tag attribute container.

  The event tag either needs to have an event_uuid defined or both
  the store_number and store_index to be valid. If both defined
  the store_number and store_index is preferred.

  Attributes:
    comment: a string containing comments or None if not set.
    event_uuid: a string containing the event identifier (UUID) or None
                if not set.
    labels: a list of strings containing labels. e.g. "malware",
            "application_execution".
    store_index: an integer containing the store index of the corresponding
                 event or None if not set.
    store_number: an integer containing the store number of the corresponding
                  event or None if not set.
  """
  _ATTRIBUTE_NAMES = frozenset([
      u'comment', u'event_uuid', u'labels', u'store_index', u'store_number'])

  _VALID_LABEL_REGEX = re.compile(r'^[A-Za-z0-9_]+$')

  INVALID_TAG_CHARACTER_REGEX = re.compile(r'[^A-Za-z0-9_]')

  def __init__(self, comment=None, event_uuid=None):
    """Initializes an event tag.

    Args:
      comment: optional string containing comments.
      event_uuid: optional string containing the event identifier (UUID).
    """
    super(EventTag, self).__init__()
    self.comment = comment
    self.event_uuid = event_uuid
    self.labels = []
    self.store_index = None
    self.store_number = None

  @property
  def string_key(self):
    """Return a string index key for this tag."""
    if not self.IsValidForSerialization():
      return u''

    if self.event_uuid is not None:
      return self.event_uuid

    return u'{0:d}:{1:d}'.format(self.store_number, self.store_index)

  def AddComment(self, comment):
    """Adds a comment to the event tag.

    Args:
      comment: a string containing the comment.
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
      label: a string containing the label.

    Raises:
      ValueError: if a label is malformed.
    """
    if not self._VALID_LABEL_REGEX.match(label):
      raise ValueError((
          u'Unusupported label: "{0:s}". A label must only consist of '
          u'alphanumeric characters or underscores.').format(label))

    if not label in self.labels:
      self.labels.append(label)

  def AddLabels(self, labels):
    """Adds labels to the event tag.

    Args:
      labels: a list of strings containing the labels.

    Raises:
      ValueError: if a label is malformed.
    """
    for label in labels:
      if not self._VALID_LABEL_REGEX.match(label):
        raise ValueError((
            u'Unusupported label: "{0:s}". A label must only consist of '
            u'alphanumeric characters or underscores.').format(label))

    for label in labels:
      if not label in self.labels:
        self.labels.append(label)

  def CopyToDict(self):
    """Copies the event tag to a dictionary.

    Returns:
      A dictionary containing the event tag attributes.
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

  def GetAttributes(self):
    """Retrieves the attributes from the event tag object.

    Attributes that are set to None are ignored.

    Yields:
      A tuple containing the event tag attribute name and value.
    """
    for attribute_name in self._ATTRIBUTE_NAMES:
      attribute_value = getattr(self, attribute_name, None)
      if attribute_value is not None:
        yield attribute_name, attribute_value

  def IsValidForSerialization(self):
    """Return whether or not this is a valid tag object."""
    if self.event_uuid is not None:
      return True

    if (self.store_number is not None and self.store_index is not None and
        self.store_number > -1 and self.store_index > -1):
      return True

    return False


class PreprocessObject(object):
  """Object used to store all information gained from preprocessing."""

  def __init__(self):
    """Initializes the preprocess object."""
    super(PreprocessObject, self).__init__()
    self._user_ids_to_names = None
    self.zone = pytz.UTC

  def GetUserMappings(self):
    """Returns a dictionary objects mapping SIDs or UIDs to usernames."""
    if self._user_ids_to_names is None:
      self._user_ids_to_names = {}

    if self._user_ids_to_names:
      return self._user_ids_to_names

    for user in getattr(self, u'users', []):
      if u'sid' in user:
        user_id = user.get(u'sid', u'')
      elif u'uid' in user:
        user_id = user.get(u'uid', u'')
      else:
        user_id = u''

      if user_id:
        self._user_ids_to_names[user_id] = user.get(u'name', user_id)

    return self._user_ids_to_names

  def GetUsernameById(self, user_id):
    """Returns a username for a specific user identifier.

    Args:
      user_id: The user identifier, either a SID or UID.

    Returns:
      If available the user name for the identifier, otherwise the string '-'.
    """
    user_ids_to_names = self.GetUserMappings()

    return user_ids_to_names.get(user_id, u'-')

  # TODO: change to property with getter and setter.
  def SetTimezone(self, timezone_identifier):
    """Sets the timezone.

    Args:
      timezone_identifier: string containing the identifier of the timezone,
                           e.g. 'UTC' or 'Iceland'.
    """
    try:
      self.zone = pytz.timezone(timezone_identifier)
    except pytz.UnknownTimeZoneError as exception:
      logging.warning(
          u'Unable to set timezone: {0:s} with error: {1:s}.'.format(
              timezone_identifier, exception))

  def SetCollectionInformationValues(self, dict_object):
    """Sets the collection information values.

    Args:
      dict_object: dictionary object containing the collection information
                   values.
    """
    self.collection_information = dict(dict_object)

    if u'configure_zone' in self.collection_information:
      self.collection_information[u'configure_zone'] = pytz.timezone(
          self.collection_information[u'configure_zone'])

  def SetCounterValues(self, dict_object):
    """Sets the counter values.

    Args:
      dict_object: dictionary object containing the counter values.
    """
    self.counter = collections.Counter()
    for key, value in dict_object.iteritems():
      self.counter[key] = value

  def SetPluginCounterValues(self, dict_object):
    """Sets the plugin counter values.

    Args:
      dict_object: dictionary object containing the plugin counter values.
    """
    self.plugin_counter = collections.Counter()
    for key, value in dict_object.iteritems():
      self.plugin_counter[key] = value


# Named tuple that defines a parse error.
#
# Attributes:
#   name: The parser or plugin name.
#   description: The description of the error.
#   path_spec: Optional path specification of the file entry (instance of
#              dfvfs.PathSpec).
ParseError = collections.namedtuple(
    u'ParseError', u'name description path_spec')
