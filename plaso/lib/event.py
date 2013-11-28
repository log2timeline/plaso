#!/usr/bin/python
# -*- coding: utf-8 -*-
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
"""This file contains the EventObject and all implementations of it.

This file contains the definition for the EventObject and EventContainer,
which are core components of the storage mechanism of plaso.

"""
import heapq
import json
import uuid

from google.protobuf import message
from plaso.lib import errors
from plaso.lib import eventdata
from plaso.lib import timelib
from plaso.lib import utils
from plaso.proto import plaso_storage_pb2
from plaso.proto import transmission_pb2

import pytz


class EventJsonEncoder(json.JSONEncoder):
  """A method that handles encoding EventObject into JSON."""

  # pylint: disable-msg=method-hidden
  def default(self, obj):
    """Overwriting the default JSON encoder to handle EventObjects."""
    if isinstance(obj, EventTag):
      return obj.ToJson()
    else:
      return super(EventJsonEncoder, self).default(obj)


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
    try:
      return object.__getattribute__(self, attr)
    except AttributeError:
      pass

    # Try getting the attributes from the other attribute store.
    try:
      return self.GetValue(attr)
    except AttributeError:
      raise AttributeError('%s\' object has no attribute \'%s\'.' % (
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

    raise AttributeError('\'%s\' object has no attribute \'%s\'.' % (
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

  def ToProto(self):
    """Serialize a container to a protobuf."""
    proto = plaso_storage_pb2.EventContainer()

    proto.first_time = self.first_timestamp
    proto.last_time = self.last_timestamp

    for container in self.containers:
      container_str = container.ToProtoString()
      container_add = proto.containers.add()
      container_add.MergeFromString(container_str)

    for event_object in self.events:
      # TODO: Problem here is that when the EventObject
      # is serialized it will "inherit" all the attributes
      # from the container, thus repeat them. Fix that.
      event_str = event_object.ToProtoString()
      event_add = proto.events.add()
      event_add.MergeFromString(event_str)

    for attribute, value in self.attributes.items():
      if isinstance(attribute, (bool, int, long)) or value:
        proto_attribute = proto.attributes.add()
        AttributeToProto(
            proto_attribute, attribute, value)

    return proto

  def ToProtoString(self):
    """Serialize an event container into a string value."""
    proto = self.ToProto()

    return proto.SerializeToString()

  def FromProto(self, proto):
    """Unserializes the event container from a protobuf.

    Args:
      proto: The protobuf (plaso_storage_pb2.EventContainer).

    Raises:
      RuntimeError: when the protobuf is not of type:
                    plaso_storage_pb2.EventContainer or when an unsupported
                    attribute value type is encountered
    """
    if not isinstance(proto, plaso_storage_pb2.EventContainer):
      raise RuntimeError('Unsupported proto')

    self.last_timestamp = proto.last_time
    self.first_timestamp = proto.first_time

    # Make sure the old attributes are removed.
    self.attributes = {}
    self.attributes.update(dict(AttributeFromProto(a) for a in
                                proto.attributes))

    for container in proto.containers:
      container_object = EventContainer()
      container_object.FromProto(container)
      self.containers.append(container_object)

    for event_proto in proto.events:
      event_object = EventObject()
      event_object.FromProto(event_proto)
      self.events.append(event_object)

  def FromProtoString(self, proto_string):
    """Unserializes the event container from a serialized protobuf."""
    proto = plaso_storage_pb2.EventContainer()
    proto.ParseFromString(proto_string)
    self.FromProto(proto)


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

  # TODO: remove this once source_short has been moved to event formatter.
  # Lists of the mappings between the source short values of the event object
  # and those used in the protobuf.
  _SOURCE_SHORT_FROM_PROTO_MAP = {}
  _SOURCE_SHORT_TO_PROTO_MAP = {}
  for value in plaso_storage_pb2.EventObject.DESCRIPTOR.enum_types_by_name[
      'SourceShort'].values:
    _SOURCE_SHORT_FROM_PROTO_MAP[value.number] = value.name
    _SOURCE_SHORT_TO_PROTO_MAP[value.name] = value.number
  _SOURCE_SHORT_FROM_PROTO_MAP.setdefault(6)
  _SOURCE_SHORT_TO_PROTO_MAP.setdefault('LOG')

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
    try:
      object.__getattribute__(self, attr)
      object.__setattr__(self, attr, value)
    except AttributeError:
      self.attributes.__setitem__(attr, value)

  def __getattr__(self, attr):
    """Determine if attribute is set within the event or in a container."""
    try:
      return object.__getattribute__(self, attr)
    except AttributeError:
      pass

    # Check the attribute store.
    try:
      if attr in self.attributes:
        return self.attributes.__getitem__(attr)
    except TypeError as e:
      raise AttributeError('[Event] %s', e)

    # Check the parent.
    if self.parent_container:
      try:
        return self.parent_container.GetValue(attr)
      except AttributeError:
        raise AttributeError('%s\' object has no attribute \'%s\'.' % (
            self.__class__.__name__, attr))

    raise AttributeError('Attribute [%s] not defined' % attr)

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

  def ToJson(self):
    """Returns a serialized JSON object from the EventObject.

    For faster transfer of serialized objects JSON might be preferred
    over protobuf. However it should not be relied upon for long time
    storage, since this JSON implementation lacks some serialization
    capabilities that are in the protobuf implementation.

    Returns:
      A string containing the EventObject serialized as a JSON object.
    """
    # TODO: Move this to ToSerializedForm and FromSerializedForm or
    # something similar. This function would accept serializing the
    # event using different serialization, whether that is JSON,
    # protobufs or something completely different.
    # This would use a Serializer object interface.
    attributes = self.GetValues()

    # TODO: Support pathspecs in the JSON output.
    if 'pathspec' in attributes:
      del attributes['pathspec']

    return json.dumps(attributes, cls=EventJsonEncoder)

  def FromJson(self, json_string):
    """Deserialize an EventObject from a JSON object."""
    attributes = json.loads(json_string)

    for key, value in attributes.iteritems():
      if key == 'tag':
        tag = EventTag()
        tag.FromJson(value)
        setattr(self, key, tag)
      else:
        setattr(self, key, value)

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
    out_write.append(u'[Timestamp]:\n  %s' %(
        timelib.Timestamp.CopyToIsoFormat(self.timestamp, pytz.utc)))
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
      pathspec_string = unicode(self.pathspec.ToProto()).rstrip()
      out_write.append(
          u'{1}:\n  {0}\n'.format(
              pathspec_string.replace('\n', '\n  '), u'[Pathspec]'))

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

  def FromProto(self, proto):
    """Unserializes the event object from a protobuf.

    Args:
      proto: The protobuf (plaso_storage_pb2.EventObject).

    Raises:
      RuntimeError: when the protobuf is not of type:
                    plaso_storage_pb2.EventObject or when an unsupported
                    attribute value type is encountered
    """
    if not isinstance(proto, plaso_storage_pb2.EventObject):
      raise RuntimeError('Unsupported proto')

    self.data_type = proto.data_type

    for proto_attribute, value in proto.ListFields():
      if proto_attribute.name == 'source_short':
        self.attributes.__setitem__(
            'source_short', self._SOURCE_SHORT_FROM_PROTO_MAP[value])

      elif proto_attribute.name == 'pathspec':
        pathspec_evt = EventPathSpec()
        pathspec_evt.FromProto(proto.pathspec)
        self.attributes.__setitem__(
            'pathspec', pathspec_evt)

      elif proto_attribute.name == 'tag':
        tag_event = EventTag()
        tag_event.FromProto(proto.tag)
        self.attributes.__setitem__(
            'tag', tag_event)

      elif proto_attribute.name == 'attributes':
        continue
      else:
        # Register the attribute correctly.
        # The attribute can be a 'regular' high level attribute or
        # a message (Dict/Array) that need special handling.
        if isinstance(value, message.Message):
          if value.DESCRIPTOR.full_name.endswith('.Dict'):
            value_dict = {}
            for attribute in value.attributes:
              _, value_dict[attribute.key] = AttributeFromProto(attribute)
            value = value_dict
          elif value.DESCRIPTOR.full_name.endswith('.Array'):
            value_list = []
            for value_item in value.values:
              _, value_append = AttributeFromProto(value_item)
              value_list.append(value_append)
            value = value_list
          else:
            value = AttributeFromProto(value)
        self.attributes.__setitem__(proto_attribute.name, value)

    # Make sure the old attributes are removed.
    self.attributes.update(dict(AttributeFromProto(
        attr) for attr in proto.attributes))

  def ToProtoString(self):
    """Serialize an event object into a string value."""
    proto = self.ToProto()

    return proto.SerializeToString()

  def FromProtoString(self, proto_string):
    """Unserializes the event object from a serialized protobuf."""
    proto = plaso_storage_pb2.EventObject()
    proto.ParseFromString(proto_string)
    self.FromProto(proto)

  def ToProto(self):
    """Serializes the event object into a protobuf.

    Returns:
      A protobuf (plaso_storage_pb2.EventObject).
    """
    proto = plaso_storage_pb2.EventObject()

    proto.data_type = getattr(self, 'data_type', 'event')

    for attribute_name in self.GetAttributes():
      if attribute_name == 'source_short':
        proto.source_short = self._SOURCE_SHORT_TO_PROTO_MAP[self.source_short]

      elif attribute_name == 'pathspec':
        pathspec_str = self.pathspec.ToProtoString()
        proto.pathspec.MergeFromString(pathspec_str[1:])

      elif attribute_name == 'tag':
        tag_str = self.tag.ToProtoString()
        proto.tag.MergeFromString(tag_str)

      elif hasattr(proto, attribute_name):
        attribute_value = getattr(self, attribute_name)

        if attribute_value is None:
          continue

        if isinstance(attribute_value, (str, unicode)):
          attribute_value = utils.GetUnicodeString(attribute_value)
          if not attribute_value:
            continue

        if isinstance(attribute_value, dict):
          dict_proto = plaso_storage_pb2.Dict()
          for dict_key, dict_value in attribute_value.items():
            sub_proto = dict_proto.attributes.add()
            AttributeToProto(sub_proto, dict_key, dict_value)
          dict_attribute = getattr(proto, attribute_name)
          dict_attribute.MergeFrom(dict_proto)
        elif isinstance(attribute_value, (list, tuple)):
          list_proto = plaso_storage_pb2.Array()
          for attribute in attribute_value:
            sub_proto = list_proto.values.add()
            AttributeToProto(sub_proto, '', attribute)
          list_attribute = getattr(proto, attribute_name)
          list_attribute.MergeFrom(list_proto)
        else:
          setattr(proto, attribute_name, attribute_value)

      else:
        attribute_value = getattr(self, attribute_name)

        # Serialize the attribute value only if it is an integer type
        # (int or long) or if it has a value.
        # TODO: fix logic.
        if isinstance(
            attribute_value, (bool, int, float, long)) or attribute_value:
          proto_attribute = proto.attributes.add()
          AttributeToProto(
              proto_attribute, attribute_name, attribute_value)

    return proto


class EventPathBundle(object):
  """A native Python object for the PathBundle protobuf."""

  def __init__(self, pattern=''):
    """Initialize a PathBundle object.

    Args:
      pattern: A string containing the pattern used by the collector
      to find all the PathSpecs contained in this bundle. This is used
      by parsers to match if the bundle is the correct one for the parser.
    """
    self._pathspecs = []
    self.pattern = pattern

  def ToProto(self):
    """Serialize an EventPathBundle to PathBundle protobuf."""
    proto = transmission_pb2.PathBundle()

    for pathspec in self._pathspecs:
      proto_pathspec = proto.pathspecs.add()
      proto_pathspec.MergeFrom(pathspec.ToProto())

    proto.pattern = self.pattern

    return proto

  def ToProtoString(self):
    """Serialize the object into a string."""
    proto = self.ToProto()

    # TODO: Remove this "ugly" hack in favor of something more elegant
    # and one that makes more sense.
    return u'B' + proto.SerializeToString()

  def FromProto(self, proto):
    """Unserializes the EventPathBundle from a PathBundle protobuf."""
    self._pathspecs = []
    if not hasattr(proto, 'pattern'):
      raise RuntimeError('Unsupported proto')
    if not hasattr(proto, 'pathspecs'):
      raise RuntimeError('Unsupported proto')

    self.pattern = proto.pattern

    for pathspec in proto.pathspecs:
      pathspec_object = EventPathSpec()
      pathspec_object.FromProto(pathspec)
      self._pathspecs.append(pathspec_object)

  def FromProtoString(self, proto_string):
    """Unserializes the EventPathBundle from a serialized PathBundle."""
    if not proto_string.startswith('B'):
      raise errors.WrongProtobufEntry(
          u'Wrong protobuf type, unable to unserialize')
    proto = transmission_pb2.PathBundle()
    proto.ParseFromString(proto_string[1:])
    self.FromProto(proto)

  def Append(self, pathspec):
    """Append a pathspec to the bundle."""
    self._pathspecs.append(pathspec)

  def _GetHash(self, pathspec):
    """Return a calculated "hash" value from a pathspec based on attributes."""
    if hasattr(pathspec, 'nested_pathspec'):
      extra = self._GetHash(pathspec.nested_pathspec)
    else:
      extra = u''

    return u'{}:{}'.format(u':'.join([
        utils.GetUnicodeString(getattr(pathspec, 'container_path', u'-')),
        utils.GetUnicodeString(getattr(pathspec, 'image_offset', u'-')),
        utils.GetUnicodeString(getattr(pathspec, 'vss_store_number', u'-')),
        utils.GetUnicodeString(getattr(pathspec, 'image_inode', u'-')),
        utils.GetUnicodeString(getattr(pathspec, 'file_path', u'-'))]), extra)

  def ListFiles(self):
    """Return a list of available files inside the pathbundle."""
    for pathspec in self._pathspecs:
      yield self._GetHash(pathspec)

  def GetPathspecFromHash(self, file_hash):
    """Return a PathSpec based on a "hash" value from bundle.

    Args:
      file_hash: A calculated hash value (from self.ListFiles()).

    Returns:
      An EventPathspec object that matches the hash, if one is found.
    """
    for pathspec in self._pathspecs:
      if file_hash == self._GetHash(pathspec):
        return pathspec

  def __str__(self):
    """Return a string representation of the bundle."""
    out_write = []
    out_write.append(u'+-' * 40)

    out_write.append(utils.FormatOutputString('Pattern', self.pattern, 10))

    out_write.append('')

    for pathspec in self._pathspecs:
      out_write.append(utils.FormatOutputString(
          'Hash', self._GetHash(pathspec), 10))
      out_write.append(unicode(pathspec))

    return u'\n'.join(out_write)

  def __iter__(self):
    """A generator that returns all pathspecs from object."""
    for pathspec in self._pathspecs:
      yield pathspec


class EventPathSpec(object):
  """A native Python object for the pathspec definition."""

  _TYPE_FROM_PROTO_MAP = {}
  _TYPE_TO_PROTO_MAP = {}
  for value in transmission_pb2.PathSpec.DESCRIPTOR.enum_types_by_name[
      'FileType'].values:
    _TYPE_FROM_PROTO_MAP[value.number] = value.name
    _TYPE_TO_PROTO_MAP[value.name] = value.number
  _TYPE_FROM_PROTO_MAP.setdefault(-1)

  def __setattr__(self, attr, value):
    """Overwrite the set attribute function to limit it to right attributes."""
    if attr in ('type', 'file_path', 'container_path', 'image_offset',
                'image_offset', 'image_inode', 'nested_pathspec', 'file_offset',
                'file_size', 'transmit_options', 'ntfs_type', 'ntfs_id',
                'vss_store_number', 'path_prepend'):
      object.__setattr__(self, attr, value)
    else:
      raise AttributeError(u'Not allowed attribute: {}'.format(attr))

  def ToProto(self):
    """Serialize an EventPathSpec to PathSpec protobuf."""
    proto = transmission_pb2.PathSpec()

    for attr in self.__dict__:
      if attr == 'type':
        proto.type = self._TYPE_TO_PROTO_MAP.get(self.type, -1)
      elif attr == 'nested_pathspec':
        evt_nested = getattr(self, attr)
        proto_nested = evt_nested.ToProto()
        proto.nested_pathspec.MergeFrom(proto_nested)
      else:
        attribute_value = getattr(self, attr, None)
        if attribute_value != None:
          setattr(proto, attr, attribute_value)

    return proto

  def FromProto(self, proto):
    """Unserializes the EventObject from a PathSpec protobuf.

    Args:
      proto: The protobuf (transmission_pb2.PathSpec).

    Raises:
      RuntimeError: when the protobuf is not of type:
                    transmission_pb2.PathSpec or when an unsupported
                    attribute value type is encountered
    """
    if not isinstance(proto, transmission_pb2.PathSpec):
      raise RuntimeError('Unsupported proto')

    for proto_attribute, value in proto.ListFields():
      if proto_attribute.name == 'type':
        self.type = self._TYPE_FROM_PROTO_MAP[value]

      elif proto_attribute.name == 'nested_pathspec':
        nested_evt = EventPathSpec()
        nested_evt.FromProto(proto.nested_pathspec)
        setattr(self, proto_attribute.name, nested_evt)
      else:
        setattr(self, proto_attribute.name, value)

  def FromProtoString(self, proto_string):
    """Unserializes the EventObject from a serialized PathSpec."""
    if not proto_string.startswith('P'):
      raise errors.WrongProtobufEntry(
          u'Unable to unserialize, illegal type field.')

    proto = transmission_pb2.PathSpec()
    proto.ParseFromString(proto_string[1:])
    self.FromProto(proto)

  def ToProtoString(self):
    """Serialize the object into a string."""
    proto = self.ToProto()

    # TODO: Remove this "ugly" hack in favor of something more elegant
    # and one that makes more sense.
    return 'P' + proto.SerializeToString()

  def __str__(self):
    """Return a string representation of the pathspec."""
    return unicode(self.ToProto())


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

  def __setattr__(self, attr, value):
    """Overwrite the set attribute function to limit it to right attributes."""
    if attr in ('store_number', 'store_index', 'comment', 'color', 'tags',
                'event_uuid'):
      if attr == 'tags' and not isinstance(value, (list, tuple)):
        raise AttributeError(u'Tags needs to be a list.')
      object.__setattr__(self, attr, value)
    else:
      raise AttributeError(u'Not allowed attribute: {}'.format(attr))

  def __str__(self):
    """Define a string representation of the event."""
    ret = []
    ret.append(u'-' * 50)
    if getattr(self, 'store_index', 0):
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

  def ToJson(self):
    """Serialize an EventTag to a JSON object."""
    if not self._IsValidForSerialization():
      raise RuntimeError(
          u'Invalid tag object. Need to define UUID or store information')

    return json.dumps(self.__dict__)

  def FromJson(self, json_string):
    """Deserialize a JSON dump into an EventTag."""
    attributes = json.loads(json_string)

    for key, value in attributes.iteritems():
      setattr(self, key, value)

  def _IsValidForSerialization(self):
    """Return whether or not this is a valid tag object."""
    if getattr(self, 'event_uuid', None):
      return True

    if getattr(self, 'store_number', 0) and getattr(
        self, 'store_index', -1) >= 0:
      return True

    return False

  def ToProto(self):
    """Serialize an EventTag to EventTagging protobuf."""
    proto = plaso_storage_pb2.EventTagging()

    if not self._IsValidForSerialization():
      raise RuntimeError(
          u'Invalid tag object. Need to define UUID or store information')

    for attr in self.__dict__:
      if attr == 'tags':
        for tag in self.tags:
          tag_add = proto.tags.add()
          tag_add.value = tag
      else:
        attribute_value = getattr(self, attr, None)
        if attribute_value != None:
          setattr(proto, attr, attribute_value)

    comment = getattr(self, 'comment', '')
    if comment:
      proto.comment = comment

    color = getattr(self, 'color', '')
    if color:
      proto.color = color

    return proto

  def FromProto(self, proto):
    """Unserializes the EventTagging from a protobuf.

    Args:
      proto: The protobuf (plaso_storage_pb2.EventTagging).

    Raises:
      RuntimeError: when the protobuf is not of type:
                    plaso_storage_pb2.EventTagging or when an unsupported
                    attribute value type is encountered
    """
    if not isinstance(proto, plaso_storage_pb2.EventTagging):
      raise RuntimeError('Unsupported proto')

    for proto_attribute, value in proto.ListFields():
      if proto_attribute.name == 'tags':
        self.tags = []
        for tag in proto.tags:
          self.tags.append(tag.value)
      else:
        setattr(self, proto_attribute.name, value)

  def FromProtoString(self, proto_string):
    """Unserializes the EventTagging from a serialized protobuf."""
    proto = plaso_storage_pb2.EventTagging()
    proto.ParseFromString(proto_string)
    self.FromProto(proto)

  def ToProtoString(self):
    """Serialize the object into a string."""
    proto = self.ToProto()

    return proto.SerializeToString()


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
    for value in value_dict.values():
      if type(value) in (str, unicode) and value[0:4] == 'REGA':
        self.regalert = True

    if offset or type(offset) in [int, long]:
      self.offset = offset

    if source_append:
      self.source_append = source_append


class TextEvent(EventObject):
  """Convenience class for a text log file-based event."""
  # TODO: move this class to parsers/text.py
  DATA_TYPE = 'text'

  def __init__(self, timestamp, attributes):
    """Initializes a text event.

    Args:
      timestamp: The timestamp time value. The timestamp contains the
                 number of microseconds since Jan 1, 1970 00:00:00 UTC.
      attributes: A dict that contains the events attributes.
    """
    super(TextEvent, self).__init__()
    self.timestamp = timestamp
    # TODO: use eventdata.EventTimestamp after class has moved.
    self.timestamp_desc = 'Entry Written'
    for name, value in attributes.items():
      # TODO: Revisit this constraints and see if we can implement
      # it using a more sane solution.
      if isinstance(value, (str, unicode)) and not value:
        continue
      self.attributes.__setitem__(name, value)


def AttributeToProto(proto, name, value):
  """Serializes an event object attribute to a protobuf.

  The attribute in an event object can store almost any arbitrary data, so
  the corresponding protobuf storage must deal with the various data types.
  This method identifies the data type and assigns it properly to the
  attribute protobuf.

  Args:
    proto: The attribute protobuf (plaso_storage_pb2.Attribute).
    name: The name of the attribute.
    value: The value of the attribute.
  """
  if name:
    proto.key = name

  if isinstance(value, (str, unicode)):
    proto.string = utils.GetUnicodeString(value)

  elif isinstance(value, bool):
    proto.boolean = value

  elif isinstance(value, (int, long)):
    # TODO: add some bounds checking.
    proto.integer = value

  elif isinstance(value, dict):
    proto_dict = plaso_storage_pb2.Dict()

    for dict_key, dict_value in value.items():
      sub_proto = proto_dict.attributes.add()
      AttributeToProto(sub_proto, dict_key, dict_value)
    proto.dict.MergeFrom(proto_dict)

  elif isinstance(value, (list, tuple)):
    proto_array = plaso_storage_pb2.Array()

    for list_value in value:
      sub_proto = proto_array.values.add()
      AttributeToProto(sub_proto, '', list_value)
    proto.array.MergeFrom(proto_array)

  elif isinstance(value, float):
    proto.float = value

  elif not value:
    proto.none = True

  else:
    proto.data = value


def AttributeFromProto(proto):
  """Unserializes an event object attribute from a protobuf.

  Args:
    proto: The attribute protobuf (plaso_storage_pb2.Attribute).

  Returns:
    A list containing the name and value of the attribute.

  Raises:
    RuntimeError: when the protobuf is not of type:
                  plaso_storage_pb2.Attribute or if the attribute
                  cannot be unserialized.
  """
  key = u''
  try:
    if proto.HasField('key'):
      key = proto.key
  except ValueError:
    pass

  if not isinstance(proto, (
      plaso_storage_pb2.Attribute, plaso_storage_pb2.Value)):
    raise RuntimeError('Unsupported proto')

  if proto.HasField('string'):
    return key, proto.string

  elif proto.HasField('integer'):
    return key, proto.integer

  elif proto.HasField('boolean'):
    return key, proto.boolean

  elif proto.HasField('dict'):
    value = {}

    for proto_dict in proto.dict.attributes:
      dict_key, dict_value = AttributeFromProto(proto_dict)
      value[dict_key] = dict_value
    return key, value

  elif proto.HasField('array'):
    value = []

    for proto_array in proto.array.values:
      _, list_value = AttributeFromProto(proto_array)
      value.append(list_value)
    return key, value

  elif proto.HasField('data'):
    return key, proto.data

  elif proto.HasField('float'):
    return key, proto.float

  elif proto.HasField('none'):
    return key, None

  else:
    raise RuntimeError('Unsupported proto attribute type.')
