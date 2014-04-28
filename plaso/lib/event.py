#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2012 The Plaso Project Authors.
# Please see the AUTHORS file for details on individual authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""The core object definitions, e.g. event object and container."""

import collections
import heapq
import logging
import uuid

from plaso.lib import errors
from plaso.lib import eventdata
from plaso.lib import timelib
from plaso.lib import utils

import pytz


class AnalysisReport(object):
  """Class that defines an analysis report."""

  def __init__(self):
    """Initializes the analysis report."""
    super(AnalysisReport, self).__init__()
    self._anomalies = []
    self._tags = []

  def __unicode__(self):
    """Return an unicode string representation of the report."""
    return self.GetString()

  def GetAnomalies(self):
    """Retrieves the list of anomalies that are attached to the report."""
    return self._anomalies

  def GetString(self):
    """Return an unicode string representation of the report."""
    # TODO: Make this a more complete function that includes images
    # and the option of saving as a full fledged HTML document.
    string_list = []
    string_list.append(u'Report generated from: {0:s}'.format(self.plugin_name))

    time_compiled = getattr(self, 'time_compiled', 0)
    if time_compiled:
      time_compiled = timelib.Timestamp.CopyToIsoFormat(time_compiled)
      string_list.append(u'Generated on: {0:s}'.format(time_compiled))

    filter_string = getattr(self, 'filter_string', '')
    if filter_string:
      string_list.append(u'Filter String: {0:s}'.format(filter_string))

    string_list.append(u'')
    string_list.append(u'Report text:')
    string_list.append(self.text)

    return u'\n'.join(string_list)

  def GetTags(self):
    """Retrieves the list of event tags that are attached to the report."""
    return self._tags

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


class CollectionFilter(object):
  """Class that defines a collection filter for targeted collection."""

  def __init__(self, filter_strings):
    """Initializes the collection filter."""
    super(CollectionFilter, self).__init__()
    self._filter_strings = filter_strings

  def BuildFilters(self):
    """Return a list of filters consisting of tuples of paths and file names."""
    list_of_filters = []

    if not self._filter_strings:
      return list_of_filters

    for filter_string in self._filter_strings:
      dir_path, _, file_path = filter_string.rstrip().rpartition(u'/')

      if not file_path:
        logging.warning(
            u'Unable to parse the filter string: {0:s}'.format(filter_string))
        continue

      list_of_filters.append((dir_path, file_path))

    return list_of_filters


class EventContainer(object):
  """The EventContainer serves as a basic storage mechansim for plaso.

  An event container is a simple placeholder that is used to store
  EventObjects. It can also hold other EventContainer objects and basic common
  attributes among the EventObjects that are stored within it.

  An example of this scheme is:
    One container stores all logs from host A. That container therefore stores
    the hostname attribute.
    Then for each file that gets parsed a new container is created, which
    holds the common attributes for that file.

  That way the EventObject does not need to store all these attributes, only
  those that differ between different containers.

  The container also stores two timestamps, one for the first timestamp of
  all EventObjects that it contains, and the second one for the last one.
  That makes timebased filtering easier, since filtering can discard whole
  containers if they are outside the scope instead of going through each
  and every event.
  """
  # Define needed attributes
  events = None
  containers = None
  parent_container = None
  first_timestamp = None
  last_timestamp = None
  attributes = None

  def __init__(self):
    """Initializes the event container."""
    # A placeholder for all EventObjects directly stored.
    self.events = []

    # A placeholder for all EventContainer directly stored.
    self.containers = []

    self.first_timestamp = 0
    self.last_timestamp = 0

    self.attributes = {}

  def __setattr__(self, attr, value):
    """Sets the value to either the default or the attribute store."""
    # TODO: Remove the overwrite of __setattr__.
    try:
      object.__getattribute__(self, attr)
      object.__setattr__(self, attr, value)
    except AttributeError:
      self.attributes.__setitem__(attr, value)

  def __getattr__(self, attr):
    """Return attribute value from either attribute store.

    Args:
      attr: The attribute name

    Returns:
      The attribute value if one is found.

    Raise:
      AttributeError: If the object does not have the attribute
                      in either store.
    """
    # TODO: Remove the overwrite of __getattr__.
    try:
      return object.__getattribute__(self, attr)
    except AttributeError:
      pass

    # Try getting the attributes from the other attribute store.
    try:
      return self.GetValue(attr)
    except AttributeError:
      raise AttributeError(
          u'{0:s}\' object has no attribute \'{1:s}\'.'.format(
              self.__class__.__name__, attr))

  def __len__(self):
    """Retrieves the number of items in the containter and its sub items."""
    counter = len(self.events)
    for container in self.containers:
      counter += len(container)

    return counter

  @property
  def number_of_events(self):
    """The number of events in the container."""
    # TODO: remove the sub containers support, which is not used and change
    # into: return len(self.events)
    return len(self)

  def GetValue(self, attr):
    """Determine if an attribute is set in container or in parent containers.

    Since attributes can be set either at the container level or at the
    event level, we need to provide a mechanism to traverse the tree and
    determine if the attribute has been set or not.

    Args:
      attr: The name of the attribute that needs to be checked.

    Returns:
      The attribute value if it exists, otherwise an exception is raised.

    Raises:
      AttributeError: if the attribute is not defined in either the container
                      itself nor in any parent containers.
    """
    if attr in self.attributes:
      return self.attributes.__getitem__(attr)

    if self.parent_container:
      return self.parent_container.GetValue(attr)

    raise AttributeError(
        u'\'{0:s}\' object has no attribute \'{1:s}\'.'.format(
            self.__class__.__name__, attr))

  def GetAttributes(self):
    """Return a set of all defined attributes.

    This returns attributes defined in the object that do not fall
    under the following criteria:
      + Starts with _
      + Starts with an upper case letter.

    Returns:
      A set that contains all the attributes that are either stored
      in the attribute store or inside the attribute store of any
      of the parent containers.
    """
    res = set(self.attributes.keys())

    if self.parent_container:
      res |= self.parent_container.GetAttributes()

    return res

  def __iter__(self):
    """An iterator that returns all EventObjects stored in the containers."""
    for event in self.events:
      yield event

    for container in self.containers:
      for event in container:
        yield event

  def GetSortedEvents(self):
    """An iterator that returns all EventObjects in a sorted order."""
    all_events = []

    for event in self.events:
      heapq.heappush(all_events, (event.timestamp, event))
    for container in self.containers:
      for event in container:
        heapq.heappush(all_events, (event.timestamp, event))

    for _ in range(len(all_events)):
      yield heapq.heappop(all_events)[1]

  def Append(self, item):
    """Appends an event container or object to the container.

    Args:
      item: The event containter (EventContainer) or object (EventObject)
            to append.

    Raises:
      errors.NotAnEventContainerOrObject: When an object is passed to the
      function that is not an EventObject or an EventContainer.
    """
    try:
      if isinstance(item, EventObject):
        self._Append(item, self.events, item.timestamp)
        return
      elif isinstance(item, EventContainer):
        self._Append(item, self.containers, item.first_timestamp,
                     item.last_timestamp)
        return
    except (AttributeError, TypeError):
      pass

    raise errors.NotAnEventContainerOrObject('Unable to determine the object.')

  def _Append(self, item, storage, timestamp_first, timestamp_last=None):
    """Append objects to container while checking timestamps."""
    item.parent_container = self
    storage.append(item)

    if not timestamp_last:
      timestamp_last = timestamp_first

    if not self.last_timestamp:
      self.last_timestamp = timestamp_last

    if not self.first_timestamp:
      self.first_timestamp = timestamp_first

    if timestamp_last > self.last_timestamp:
      self.last_timestamp = timestamp_last

    if timestamp_first < self.first_timestamp:
      self.first_timestamp = timestamp_first


class EventObject(object):
  """An event object is the main datastore for an event in plaso.

  The framework is designed to parse files and create an event
  from every single record, line or key extracted from the file.

  An EventContainer is the main data store for that event, however
  the container only contains information about common atttributes
  to the event and information about all the EventObjects that are
  associated to that event. The EventObject is more tailored to the
  content of the parsed data and it will contain the actual data
  portion of the Event.

  This class defines the high level interface of EventObject.
  Before creating an EventObject a class needs to be implemented
  that inherits from EventObject and implements the functions in it.

  The EventObject is then used by output processing for saving
  in other forms, such as a protobuff, AFF4 container, CSV files,
  databases, etc.

  The goal of the EventObject is to provide a easily extensible
  data storage of each events internally in the tool.

  The main EventObject only exposes those functions that the
  implementations need to implement. The functions that are needed
  simply provide information about the event, or describe the
  attributes that are necessary. How they are assembled is totally
  up to the implementation.

  All required attributes of the EventObject are passed to the
  constructor of the object while the optional ones are set
  using the method SetValue(attribute, value).
  """
  # This is a convenience variable to define event object as
  # simple value objects. Its runtime equivalent data_type
  # should be used in code logic.
  DATA_TYPE = ''

  # This is a reserved variable just used for comparison operation and defines
  # attributes that should not be used during evaluation of whether two
  # EventObjects are the same.
  COMPARE_EXCLUDE = frozenset([
      'timestamp', 'inode', 'pathspec', 'filename', 'uuid',
      'data_type', 'display_name', 'store_number', 'store_index'])

  parent_container = None
  attributes = None

  def __init__(self):
    """Initializes the event object."""
    self.attributes = {}
    self.uuid = uuid.uuid4().get_hex()
    if self.DATA_TYPE:
      self.data_type = self.DATA_TYPE

  def __setattr__(self, attr, value):
    """Sets the value to either the default or the attribute store."""
    # TODO: Remove the overwrite of __setattr__.
    try:
      object.__getattribute__(self, attr)
      object.__setattr__(self, attr, value)
    except AttributeError:
      self.attributes.__setitem__(attr, value)

  def __getattr__(self, attr):
    """Determine if attribute is set within the event or in a container."""
    # TODO: Remove the overwrite of __getattr__.
    try:
      return object.__getattribute__(self, attr)
    except AttributeError:
      pass

    # Check the attribute store.
    try:
      if attr in self.attributes:
        return self.attributes.__getitem__(attr)
    except TypeError as exception:
      raise AttributeError(u'[Event] {0:s}'.format(exception))

    # Check the parent.
    if self.parent_container:
      try:
        return self.parent_container.GetValue(attr)
      except AttributeError:
        raise AttributeError(
            u'{0:s}\' object has no attribute \'{1:s}\'.'.format(
                self.__class__.__name__, attr))

    raise AttributeError(u'Attribute [{0:s}] not defined'.format(attr))

  def EqualityString(self):
    """Return a string describing the EventObject in terms of object equality.

    The details of this function must match the logic of __eq__. EqualityStrings
    of two event objects should be the same if and only if the EventObjects are
    equal as described in __eq__.

    Returns:
      String: will match another EventObject's Equality String if and only if
              the EventObjects are equal
    """

    fields = sorted(list(self.GetAttributes().difference(self.COMPARE_EXCLUDE)))

    basic = [self.timestamp, self.data_type]
    attributes = []
    for attribute in fields:
      value = getattr(self, attribute)
      if type(value) is dict:
        attributes.append(sorted(value.items()))
      elif type(value) is set:
        attributes.append(sorted(list(value)))
      else:
        attributes.append(value)
    identity = basic + [x for pair in zip(fields, attributes) for x in pair]

    if 'PfileStatParser' in getattr(self, 'parser', ''):
      inode = getattr(self, 'inode', 'a')
      if inode == 'a':
        inode = '_' + str(uuid.uuid4())
      identity.append('inode')
      identity.append(inode)

    return u'|'.join(map(unicode, identity))

  def __eq__(self, event_object):
    """Return a boolean indicating if two EventObject are considered equal.

    Compares two EventObject objects together and evaluates if they are
    the same or close enough to be considered to represent the same event.

    For two EventObject objects to be considered the same they need to
    have the following conditions:
      + Have the same timestamp.
      + Have the same data_type value.
      + Have the same set of attributes.
      + Compare all other attributes than those that are reserved, and
      they all have to match.

    The following attributes are considered to be 'reserved' and not used
    for the comparison, so they may be different yet the EventObject is still
    considered to be equal:
      + inode
      + pathspec
      + filename
      + display_name
      + store_number
      + store_index

    Args:
      event_object: The EventObject that is being compared to this one.

    Returns:
      True: if both EventObjects are considered equal, otherwise False.
    """

    # Note: if this method changes, the above EqualityString method MUST be
    # updated as well
    if not isinstance(event_object, EventObject):
      return False

    if self.timestamp != event_object.timestamp:
      return False

    if self.data_type != event_object.data_type:
      return False

    attributes = self.GetAttributes()
    if attributes != event_object.GetAttributes():
      return False

    # Here we have to deal with "near" duplicates, so not all attributes
    # should be compared.
    for attribute in attributes.difference(self.COMPARE_EXCLUDE):
      if getattr(self, attribute) != getattr(event_object, attribute):
        return False

    # If we are dealing with the stat parser the inode number is the one
    # attribute that really matters, unlike others.
    if 'PfileStatParser' in getattr(self, 'parser', ''):
      return utils.GetUnicodeString(getattr(
          self, 'inode', 'a')) == utils.GetUnicodeString(getattr(
              event_object, 'inode', 'b'))

    return True

  def GetAttributes(self):
    """Return a list of all defined attributes."""
    res = set(self.attributes.keys())

    if self.parent_container:
      res |= self.parent_container.GetAttributes()

    return res

  def GetValues(self):
    """Returns a dictionary of all defined attributes and their values."""
    values = {}
    for attribute_name in self.GetAttributes():
      values[attribute_name] = getattr(self, attribute_name)
    return values

  def GetString(self):
    """Return a unicode string representation of an EventObject."""
    return unicode(self)

  def __str__(self):
    """Return a string object of the EventObject."""
    return unicode(self).encode('utf-8')

  def __unicode__(self):
    """Print a human readable string from the EventObject."""
    out_write = []

    out_write.append(u'+-' * 40)
    out_write.append(u'[Timestamp]:\n  {0:s}'.format(
        timelib.Timestamp.CopyToIsoFormat(self.timestamp)))
    out_write.append(u'\n[Message Strings]:')

    event_formatter = eventdata.EventFormatterManager.GetFormatter(self)
    if not event_formatter:
      out_write.append(u'None')
    else:
      msg, msg_short = event_formatter.GetMessages(self)
      source_short, source_long = event_formatter.GetSources(self)
      out_write.append(u'{2:>7}: {0}\n{3:>7}: {1}\n'.format(
          utils.GetUnicodeString(msg_short), utils.GetUnicodeString(msg),
          'Short', 'Long'))
      out_write.append(u'{2:>7}: {0}\n{3:>7}: {1}\n'.format(
          utils.GetUnicodeString(source_short),
          utils.GetUnicodeString(source_long), 'Source Short', 'Source Long'))

    if hasattr(self, 'pathspec'):
      pathspec_string = self.pathspec.comparable
      out_write.append(u'[Pathspec]:\n  {0:s}\n'.format(
          pathspec_string.replace('\n', '\n  ')))

    out_additional = []
    out_write.append(u'[Reserved attributes]:')
    out_additional.append(u'[Additional attributes]:')

    for attr_key, attr_value in sorted(self.GetValues().items()):
      if attr_key in utils.RESERVED_VARIABLES:
        if attr_key == 'pathspec':
          continue
        else:
          out_write.append(u'  {{{key}}} {value}'.format(
                key=attr_key, value=attr_value))
      else:
        out_additional.append(u'  {{{key}}} {value}'.format(
              key=attr_key, value=attr_value))

    out_write.append(u'\n')
    out_additional.append(u'')

    part_1 = u'\n'.join(out_write)
    part_2 = u'\n'.join(out_additional)
    return part_1 + part_2


class EventTag(object):
  """A native Python object for the EventTagging protobuf.

  The EventTag object should have the following attributes:
  (optional attributes surrounded with brackets)
    + store_number: An integer, pointing to the store the EventObject is.
    + store_index: An index into the store where the EventObject is.
    + event_uuid: An UUID value of the event this tag belongs to.
    + [comment]: An arbitrary string containing comments about the event.
    + [color]: A string containing color information.
    + [tags]: A list of strings with tags, eg: 'Malware', 'Entry Point'.

  The tag either needs to have an event_uuid defined or both the store_number
  and store_index to be valid (not both, if both defined the store_number and
  store_index will be used).
  """

  # TODO: Enable __slots__ once we tested the first round of changes.
  @property
  def string_key(self):
    """Return a string index key for this tag."""
    if not self.IsValidForSerialization():
      return ''

    uuid_string = getattr(self, 'event_uuid', None)
    if uuid_string:
      return uuid_string

    return u'{}:{}'.format(self.store_number, self.store_index)

  def GetString(self):
    """Retrieves a string representation of the event."""
    ret = []
    ret.append(u'-' * 50)
    if getattr(self, 'store_number', 0):
      ret.append(u'{0:>7}:\n\tNumber: {1}\n\tIndex: {2}'.format(
          'Store', self.store_number, self.store_index))
    else:
      ret.append(u'{0:>7}:\n\tUUID: {1}'.format('Store', self.event_uuid))
    if hasattr(self, 'comment'):
      ret.append(u'{:>7}: {}'.format('Comment', self.comment))
    if hasattr(self, 'color'):
      ret.append(u'{:>7}: {}'.format('Color', self.color))
    if hasattr(self, 'tags'):
      ret.append(u'{:>7}: {}'.format('Tags', u','.join(self.tags)))

    return u'\n'.join(ret)

  def IsValidForSerialization(self):
    """Return whether or not this is a valid tag object."""
    if getattr(self, 'event_uuid', None):
      return True

    if getattr(self, 'store_number', 0) and getattr(
        self, 'store_index', -1) >= 0:
      return True

    return False


class TimestampEvent(EventObject):
  """Convenience class for a timestamp-based event."""

  def __init__(self, timestamp, usage, data_type=None):
    """Initializes a timestamp-based event object.

    Args:
      timestamp: The timestamp value.
      usage: The description of the usage of the time value.
      data_type: The event data type. If not set data_type is derived
                 from DATA_TYPE.
    """
    super(TimestampEvent, self).__init__()
    self.timestamp = timestamp
    self.timestamp_desc = usage

    if data_type:
      self.data_type = data_type


class FatDateTimeEvent(TimestampEvent):
  """Convenience class for a FAT date time-based event."""

  def __init__(self, fat_date_time, usage, data_type=None):
    """Initializes a FAT date time-based event object.

    Args:
      fat_date_time: The FAT date time value.
      usage: The description of the usage of the time value.
      data_type: The event data type. If not set data_type is derived
                 from DATA_TYPE.
    """
    super(FatDateTimeEvent, self).__init__(
        timelib.Timestamp.FromFatDateTime(fat_date_time), usage, data_type)


class FiletimeEvent(TimestampEvent):
  """Convenience class for a FILETIME timestamp-based event."""

  def __init__(self, filetime, usage, data_type=None):
    """Initializes a FILETIME timestamp-based event object.

    Args:
      filetime: The FILETIME timestamp value.
      usage: The description of the usage of the time value.
      data_type: The event data type. If not set data_type is derived
                 from DATA_TYPE.
    """
    super(FiletimeEvent, self).__init__(
        timelib.Timestamp.FromFiletime(filetime), usage, data_type)


class JavaTimeEvent(TimestampEvent):
  """Convenience class for a Java time-based event."""

  def __init__(self, java_time, usage, data_type=None):
    """Initializes a Java time-based event object.

    Args:
      java_time: The Java time value.
      usage: The description of the usage of the time value.
      data_type: The event data type. If not set data_type is derived
                 from DATA_TYPE.
    """
    super(JavaTimeEvent, self).__init__(
        timelib.Timestamp.FromJavaTime(java_time), usage, data_type)


class PosixTimeEvent(TimestampEvent):
  """Convenience class for a POSIX time-based event."""

  def __init__(self, posix_time, usage, data_type=None):
    """Initializes a POSIX time-based event object.

    Args:
      posix_time: The POSIX time value.
      usage: The description of the usage of the time value.
      data_type: The event data type. If not set data_type is derived
                 from DATA_TYPE.
    """
    super(PosixTimeEvent, self).__init__(
        timelib.Timestamp.FromPosixTime(posix_time), usage, data_type)


class WinRegistryEvent(EventObject):
  """Convenience class for a Windows Registry-based event."""
  DATA_TYPE = 'windows:registry:key_value'

  def __init__(self, key, value_dict, timestamp=None, usage=None, offset=None,
               source_append=None):
    """Initializes a Windows registry event.

    Args:
      key: Name of the registry key being parsed.
      value_dict: The interpreted value of the key, stored as a dictionary.
      timestamp: Optional timestamp time value. The timestamp contains the
                 number of microseconds since Jan 1, 1970 00:00:00 UTC.
      usage: The description of the usage of the time value.
      offset: The (data) offset of the Registry key or value.
      source_append: To append values to the source_long of an event.
    """
    super(WinRegistryEvent, self).__init__()
    self.timestamp = timestamp
    self.timestamp_desc = usage or 'Last Written'

    if key:
      self.keyname = key

    # TODO: why is regalert handled in this way? See if this can be
    # changed in a better solution.
    self.regvalue = value_dict
    for value in value_dict.itervalues():
      if isinstance(value, basestring) and value.startswith('REGALERT'):
        self.regalert = True

    if offset or type(offset) in [int, long]:
      self.offset = offset

    if source_append:
      self.source_append = source_append


class TextEvent(EventObject):
  """Convenience class for a text log file-based event."""

  # TODO: move this class to parsers/text.py
  DATA_TYPE = 'text:entry'

  def __init__(self, timestamp, attributes):
    """Initializes a text event.

    Args:
      timestamp: The timestamp time value. The timestamp contains the
                 number of microseconds since Jan 1, 1970 00:00:00 UTC.
      attributes: A dict that contains the events attributes.
    """
    super(TextEvent, self).__init__()
    self.timestamp = timestamp

    self.timestamp_desc = eventdata.EventTimestamp.WRITTEN_TIME

    for name, value in attributes.iteritems():
      # TODO: Revisit this constraints and see if we can implement
      # it using a more sane solution.
      if isinstance(value, (str, unicode)) and not value:
        continue
      self.attributes.__setitem__(name, value)


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

    for user in getattr(self, 'users', []):
      if u'sid' in user:
        user_id = user.get('sid', '')
      elif 'uid' in user:
        user_id = user.get('uid', '')
      else:
        user_id = ''

      if user_id:
        self._user_ids_to_names[user_id] = user.get('name', user_id)

    return self._user_ids_to_names

  def GetUsernameById(self, user_id):
    """Returns a username for a specific user identifier.

    Args:
      user_id: The user identifier, either a SID or UID.

    Returns:
      If available the user name for the identifier, otherwise the string '-'.
    """
    user_ids_to_names = self.GetUserMappings()

    return user_ids_to_names.get(user_id, '-')

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

    if 'configure_zone' in self.collection_information:
      self.collection_information['configure_zone'] = pytz.timezone(
          self.collection_information['configure_zone'])

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
