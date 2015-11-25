# -*- coding: utf-8 -*-
"""The core object definitions, e.g. the event object."""

import collections
import logging
import re
import uuid

from plaso.lib import definitions
from plaso.lib import timelib
from plaso.lib import utils

import pytz


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
    self.plugin_name = plugin_name
    self._tags = []

  def __unicode__(self):
    """Returns a Unicode representation of the report."""
    return self.GetString()

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
      text = u'|'.join(map(unicode, identity))
      return text
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


class EventTag(object):
  """A native Python object for the EventTagging protobuf.

  The EventTag object should have the following attributes:
  (optional attributes surrounded with brackets)
  * store_number: An integer, pointing to the store the EventObject is.
  * store_index: An index into the store where the EventObject is.
  * event_uuid: An UUID value of the event this tag belongs to.
  * [comment]: An arbitrary string containing comments about the event.
  * [color]: A string containing color information.
  * [tags]: A list of strings with tags, eg: 'Malware', 'Entry Point'.

  The tag either needs to have an event_uuid defined or both the store_number
  and store_index to be valid (not both, if both defined the store_number and
  store_index will be used).
  """

  VALID_TAG_REGEX = re.compile(r'[A-Za-z0-9_]+')
  INVALID_TAG_CHARACTER_REGEX = re.compile(r'[^A-Za-z0-9_]')

  def __init__(self):
    """Initializes a new EventTag."""
    super(EventTag, self).__init__()
    self._tags = []

  # TODO: Enable __slots__ once we tested the first round of changes.
  @property
  def string_key(self):
    """Return a string index key for this tag."""
    if not self.IsValidForSerialization():
      return u''

    uuid_string = getattr(self, u'event_uuid', None)
    if uuid_string:
      return uuid_string

    return u'{0:d}:{1:d}'.format(self.store_number, self.store_index)

  @property
  def tags(self):
    """The string tags in an event tag."""
    return self._tags

  @tags.setter
  def tags(self, value):
    """Sets the string tags in an event tag.

    Args:
      value: a list of strings to set as string tags in this event tag. The tags
             must only contain alphanumeric characters and underscores.

    Raises:
      AttributeError: If the provided value is not a list, or contains strings
                      that are not valid string tags.
    """

    if not isinstance(value, list):
      raise AttributeError(u'{0:s} is a not a list.'.format(value))
    for tag in value:
      if not self.VALID_TAG_REGEX.match(tag):
        raise AttributeError((
            u'{0:s} is not a valid tag. Tags must consist of alphanumeric '
            u'characters and underscores only').format(tag))
    self._tags = value


  def GetString(self):
    """Retrieves a string representation of the event."""
    ret = []
    ret.append(u'-' * 50)
    if getattr(self, u'store_number', 0):
      ret.append(u'{0:>7}:\n\tNumber: {1}\n\tIndex: {2}'.format(
          u'Store', self.store_number, self.store_index))
    else:
      ret.append(u'{0:>7}:\n\tUUID: {1}'.format(u'Store', self.event_uuid))
    if hasattr(self, u'comment'):
      ret.append(u'{:>7}: {}'.format(u'Comment', self.comment))
    if hasattr(self, u'color'):
      ret.append(u'{:>7}: {}'.format(u'Color', self.color))
    if hasattr(self, u'tags'):
      ret.append(u'{:>7}: {}'.format(u'Tags', u','.join(self.tags)))

    return u'\n'.join(ret)

  def IsValidForSerialization(self):
    """Return whether or not this is a valid tag object."""
    if getattr(self, u'event_uuid', None):
      return True

    if getattr(self, u'store_number', 0) and getattr(
        self, u'store_index', -1) >= 0:
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
#              dfvfs.PathSpec). The default is None.
ParseError = collections.namedtuple(
    u'ParseError', u'name description path_spec')
