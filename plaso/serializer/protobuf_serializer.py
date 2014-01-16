#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2014 The Plaso Project Authors.
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
"""The protobuf serializer object implementation."""

from plaso.lib import event
from plaso.lib import utils
from plaso.proto import plaso_storage_pb2
from plaso.proto import transmission_pb2
from plaso.serializer import interface

from google.protobuf import message

# TODO: for now the Read and Write function allow for an additional
# parameter to indicate a message type identifier should be added or not.
# pylint: disable-msg=arguments-differ


class ProtobufEventAttributeSerializer(object):
  """Class that implements the protobuf event attribute serializer."""

  @classmethod
  def ReadSerializedObject(cls, proto_attribute):
    """Reads an event attribute from serialized form.

    Args:
      proto_attribute: a protobuf attribute object containing the serialized
                       form.

    Returns:
      A tuple containing the attribute name and value.

    Raises:
      RuntimeError: when the protobuf attribute (field) type is not supported.
    """
    attribute_name = u''
    try:
      if proto_attribute.HasField('key'):
        attribute_name = proto_attribute.key
    except ValueError:
      pass

    if not isinstance(proto_attribute, (
        plaso_storage_pb2.Attribute, plaso_storage_pb2.Value)):
      raise RuntimeError(u'Unsupported protobuf type.')

    if proto_attribute.HasField('string'):
      return attribute_name, proto_attribute.string

    elif proto_attribute.HasField('integer'):
      return attribute_name, proto_attribute.integer

    elif proto_attribute.HasField('boolean'):
      return attribute_name, proto_attribute.boolean

    elif proto_attribute.HasField('dict'):
      attribute_value = {}

      for proto_dict in proto_attribute.dict.attributes:
        dict_key, dict_value = cls.ReadSerializedObject(proto_dict)
        attribute_value[dict_key] = dict_value
      return attribute_name, attribute_value

    elif proto_attribute.HasField('array'):
      attribute_value = []

      for proto_array in proto_attribute.array.values:
        _, list_value = cls.ReadSerializedObject(proto_array)
        attribute_value.append(list_value)
      return attribute_name, attribute_value

    elif proto_attribute.HasField('data'):
      return attribute_name, proto_attribute.data

    elif proto_attribute.HasField('float'):
      return attribute_name, proto_attribute.float

    elif proto_attribute.HasField('none'):
      return attribute_name, None

    else:
      raise RuntimeError(u'Unsupported proto attribute type.')

  @classmethod
  def ReadSerializedDictObject(cls, proto_dict):
    """Reads a dictionary event attribute from serialized form.

    Args:
      proto_dict: a protobuf Dict object containing the serialized form.

    Returns:
      A dictionary object.
    """
    dict_object = {}
    for proto_attribute in proto_dict.attributes:
      dict_key, dict_value = cls.ReadSerializedObject(proto_attribute)
      dict_object[dict_key] = dict_value

    return dict_object

  @classmethod
  def ReadSerializedListObject(cls, proto_list):
    """Reads a list event attribute from serialized form.

    Args:
      proto_list: a protobuf List object containing the serialized form.

    Returns:
      A list object.
    """
    list_object = []
    for proto_value in proto_list.values:
      _, list_value = cls.ReadSerializedObject(proto_value)
      list_object.append(list_value)

    return list_object

  @classmethod
  def WriteSerializedObject(
      cls, proto_attribute, attribute_name, attribute_value):
    """Writes an event attribute to serialized form.

    The attribute of an event object or event container can store almost any
    arbitrary data, so the corresponding protobuf storage must deal with the
    various data types. This method identifies the data type and assigns it
    properly to the attribute protobuf.

    Args:
      proto_attribute: a protobuf attribute object.
      attribute_name: the name of the attribute.
      attribute_value: the value of the attribute.

    Returns:
      A protobuf object containing the serialized form.
    """
    if attribute_name:
      proto_attribute.key = attribute_name

    if isinstance(attribute_value, (str, unicode)):
      proto_attribute.string = utils.GetUnicodeString(attribute_value)

    elif isinstance(attribute_value, bool):
      proto_attribute.boolean = attribute_value

    elif isinstance(attribute_value, (int, long)):
      # TODO: add some bounds checking.
      proto_attribute.integer = attribute_value

    elif isinstance(attribute_value, dict):
      cls.WriteSerializedDictObject(proto_attribute, 'dict', attribute_value)

    elif isinstance(attribute_value, (list, tuple)):
      cls.WriteSerializedListObject(proto_attribute, 'array', attribute_value)

    elif isinstance(attribute_value, float):
      proto_attribute.float = attribute_value

    elif not attribute_value:
      proto_attribute.none = True

    else:
      proto_attribute.data = attribute_value

  @classmethod
  def WriteSerializedDictObject(
      cls, proto_attribute, attribute_name, dict_object):
    """Writes a dictionary event attribute to serialized form.

    Args:
      proto_attribute: a protobuf attribute object.
      attribute_name: the name of the attribute.
      ditctobject: a dictionary object that is the value of the attribute.
    """
    dict_proto = plaso_storage_pb2.Dict()

    for dict_key, dict_value in dict_object.items():
      dict_proto_add = dict_proto.attributes.add()
      cls.WriteSerializedObject(dict_proto_add, dict_key, dict_value)

    dict_attribute = getattr(proto_attribute, attribute_name)
    dict_attribute.MergeFrom(dict_proto)

  @classmethod
  def WriteSerializedListObject(
      cls, proto_attribute, attribute_name, list_object):
    """Writes a list event attribute to serialized form.

    Args:
      proto_attribute: a protobuf attribute object.
      attribute_name: the name of the attribute.
      list_object: a list object that is the value of the attribute.
    """
    list_proto = plaso_storage_pb2.Array()

    for list_value in list_object:
      list_proto_add = list_proto.values.add()
      cls.WriteSerializedObject(list_proto_add, '', list_value)

    list_attribute = getattr(proto_attribute, attribute_name)
    list_attribute.MergeFrom(list_proto)


class ProtobufAnalysisReportSerializer(interface.AnalysisReportSerializer):
  """Class that implements the protobuf analysis report serializer."""

  @classmethod
  def ReadSerializedObject(cls, proto):
    """Reads an analysis report from serialized form.

    Args:
      proto: a protobuf object containing the serialized form (instance of
             plaso_storage_pb2.AnalysisReport).

    Returns:
      An analysis report (instance of AnalysisReport).
    """
    analysis_report = event.AnalysisReport()

    for proto_attribute, value in proto.ListFields():
      # TODO: replace by ReadSerializedDictObject, need tests first.
      # dict_object = ProtobufEventAttributeSerializer.ReadSerializedDictObject(
      #     proto.report_dict)
      if proto_attribute.name == 'report_dict':
        new_value = {}
        for proto_dict in proto.report_dict.attributes:
          dict_key, dict_value = (
              ProtobufEventAttributeSerializer.ReadSerializedObject(proto_dict))
          new_value[dict_key] = dict_value
        setattr(analysis_report, proto_attribute.name, new_value)

      # TODO: replace by ReadSerializedListObject, need tests first.
      # list_object = ProtobufEventAttributeSerializer.ReadSerializedListObject(
      #     proto.report_array)
      elif proto_attribute.name == 'report_array':
        new_value = []

        for proto_array in proto.report_array.values:
          _, list_value = ProtobufEventAttributeSerializer.ReadSerializedObject(
              proto_array)
          new_value.append(list_value)
        setattr(analysis_report, proto_attribute.name, new_value)

      else:
        setattr(analysis_report, proto_attribute.name, value)

    return analysis_report

  @classmethod
  def ReadSerialized(cls, proto_string):
    """Reads an analysis report from serialized form.

    Args:
      proto_string: a protobuf string containing the serialized form.

    Returns:
      An analysis report (instance of AnalysisReport).

    Raises:
      RuntimeError: when the protobuf string is not prefixed with
                    the analysis report message type.
    """
    proto = plaso_storage_pb2.AnalysisReport()
    proto.ParseFromString(proto_string)

    return cls.ReadSerializedObject(proto)

  @classmethod
  def WriteSerializedObject(cls, analysis_report):
    """Writes an analysis report to serialized form.

    Args:
      analysis_report: an analysis report (instance of AnalysisReport).

    Returns:
      A protobuf object containing the serialized form (instance of
      plaso_storage_pb2.AnalysisReport).
    """
    proto = plaso_storage_pb2.AnalysisReport()
    proto.time_compiled = getattr(analysis_report, 'time_compiled', 0)
    plugin_name = getattr(analysis_report, 'plugin_name', None)

    if plugin_name:
      proto.plugin_name = plugin_name

    proto.text = getattr(analysis_report, 'text', 'N/A')

    for image in getattr(analysis_report, 'images', []):
      proto.images.append(image)

    if hasattr(analysis_report, 'report_dict'):
      dict_proto = plaso_storage_pb2.Dict()
      for key, value in getattr(analysis_report, 'report_dict', {}).iteritems():
        sub_proto = dict_proto.attributes.add()
        ProtobufEventAttributeSerializer.WriteSerializedObject(
            sub_proto, key, value)
      proto.report_dict.MergeFrom(dict_proto)

    if hasattr(analysis_report, 'report_array'):
      list_proto = plaso_storage_pb2.Array()
      for value in getattr(analysis_report, 'report_array', []):
        sub_proto = list_proto.values.add()
        ProtobufEventAttributeSerializer.WriteSerializedObject(
            sub_proto, '', value)

      proto.report_array.MergeFrom(list_proto)

    return proto

  @classmethod
  def WriteSerialized(cls, analysis_report):
    """Writes an analysis report to serialized form.

    Args:
      analysis_report: an analysis report (instance of AnalysisReport).

    Returns:
      A protobuf string containing the serialized form.
    """
    proto = cls.WriteSerializedObject(analysis_report)
    return proto.SerializeToString()


class ProtobufEventContainerSerializer(interface.EventContainerSerializer):
  """Class that implements the protobuf event container serializer."""

  @classmethod
  def ReadSerializedObject(cls, proto):
    """Reads an event container from serialized form.

    Args:
      proto: a protobuf object containing the serialized form (instance of
             plaso_storage_pb2.EventContainer).

    Returns:
      An event container (instance of EventContainer).
    """
    event_container = event.EventContainer()
    event_container.last_timestamp = proto.last_time
    event_container.first_timestamp = proto.first_time

    # The plaso_storage_pb2.EventContainer protobuf contains a field named
    # attributes which technically not a Dict but behaves similar.
    dict_object = ProtobufEventAttributeSerializer.ReadSerializedDictObject(
        proto)
    event_container.attributes.update(dict_object)

    for container_proto in proto.containers:
      container_object = ProtobufEventContainerSerializer.ReadSerializedObject(
         container_proto)
      event_container.containers.append(container_object)

    for event_proto in proto.events:
      event_object = ProtobufEventObjectSerializer.ReadSerializedObject(
         event_proto)
      event_container.events.append(event_object)

    return event_container

  @classmethod
  def ReadSerialized(cls, proto_string):
    """Reads an event container from serialized form.

    Args:
      proto_string: a protobuf string containing the serialized form.

    Returns:
      An event container (instance of EventContainer).

    Raises:
      RuntimeError: when the protobuf string is not prefixed with
                    the event container message type.
    """
    proto = plaso_storage_pb2.EventContainer()
    proto.ParseFromString(proto_string)

    return cls.ReadSerializedObject(proto)

  @classmethod
  def WriteSerializedObject(cls, event_container):
    """Writes an event container to serialized form.

    Args:
      event_container: an event container (instance of EventContainer).

    Returns:
      A protobuf object containing the serialized form (instance of
      plaso_storage_pb2.EventContainer).
    """
    proto = plaso_storage_pb2.EventContainer()

    proto.first_time = event_container.first_timestamp
    proto.last_time = event_container.last_timestamp

    for sub_container in event_container.containers:
      sub_container_proto = cls.WriteSerializedObject(sub_container)
      container_add = proto.containers.add()
      container_add.MergeFrom(sub_container_proto)

    for event_object in event_container.events:
      # TODO: check if the next TODO still applies.
      # TODO: Problem here is that when the EventObject
      # is serialized it will "inherit" all the attributes
      # from the container, thus repeat them. Fix that.
      event_object_proto = ProtobufEventObjectSerializer.WriteSerializedObject(
          event_object)
      event_object_proto_add = proto.events.add()
      event_object_proto_add.MergeFrom(event_object_proto)

    for attribute_name, attribute_value in event_container.attributes.items():
      if isinstance(attribute_value, (bool, int, long)) or attribute_value:
        proto_attribute = proto.attributes.add()
        ProtobufEventAttributeSerializer.WriteSerializedObject(
            proto_attribute, attribute_name, attribute_value)

    return proto

  @classmethod
  def WriteSerialized(cls, event_container):
    """Writes an event container to serialized form.

    Args:
      event_container: an event container (instance of EventContainer).

    Returns:
      A protobuf string containing the serialized form.
    """
    proto = cls.WriteSerializedObject(event_container)
    return proto.SerializeToString()


class ProtobufEventObjectSerializer(interface.EventObjectSerializer):
  """Class that implements the protobuf event object serializer."""

  # TODO: check if the next TODO still applies.
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

  @classmethod
  def ReadSerializedObject(cls, proto):
    """Reads an event object from serialized form.

    Args:
      proto: a protobuf object containing the serialized form (instance of
             plaso_storage_pb2.EventObject).

    Returns:
      An event object (instance of EventObject).
    """
    event_object = event.EventObject()
    event_object.data_type = proto.data_type

    for proto_attribute, value in proto.ListFields():
      if proto_attribute.name == 'source_short':
        event_object.source_short = cls._SOURCE_SHORT_FROM_PROTO_MAP[value]

      elif proto_attribute.name == 'pathspec':
        if hasattr(proto_attribute, 'pathspec'):
          event_object.pathspec = (
             ProtobufEventPathSpecSerializer.ReadSerializedObject(
                 proto.pathspec))

      elif proto_attribute.name == 'tag':
        if hasattr(proto_attribute, 'tag'):
          event_object.tag = ProtobufEventTagSerializer.ReadSerializedObject(
             proto.tag)

      elif proto_attribute.name == 'attributes':
        continue

      else:
        # Register the attribute correctly.
        # The attribute can be a 'regular' high level attribute or
        # a message (Dict/Array) that need special handling.
        if isinstance(value, message.Message):
          if value.DESCRIPTOR.full_name.endswith('.Dict'):
            value = ProtobufEventAttributeSerializer.ReadSerializedDictObject(
                value)
          elif value.DESCRIPTOR.full_name.endswith('.Array'):
            value = ProtobufEventAttributeSerializer.ReadSerializedListObject(
                value)
          else:
            value = ProtobufEventAttributeSerializer.ReadSerializedObject(value)

        setattr(event_object, proto_attribute.name, value)

    # The plaso_storage_pb2.EventContainer protobuf contains a field named
    # attributes which technically not a Dict but behaves similar.
    dict_object = ProtobufEventAttributeSerializer.ReadSerializedDictObject(
        proto)

    event_object.attributes.update(dict_object)

    return event_object

  @classmethod
  def ReadSerialized(cls, proto_string):
    """Reads an event object from serialized form.

    Args:
      proto_string: a protobuf string containing the serialized form.

    Returns:
      An event object (instance of EventObject).

    Raises:
      RuntimeError: when the protobuf string is not prefixed with
                    the event object message type.
    """
    proto = plaso_storage_pb2.EventObject()
    proto.ParseFromString(proto_string)

    return cls.ReadSerializedObject(proto)

  @classmethod
  def WriteSerializedObject(cls, event_object):
    """Writes an event object to serialized form.

    Args:
      event_object: an event object (instance of EventObject).

    Returns:
      A protobuf object containing the serialized form (instance of
      plaso_storage_pb2.EventObject).
    """
    proto = plaso_storage_pb2.EventObject()

    proto.data_type = getattr(event_object, 'data_type', 'event')

    for attribute_name in event_object.GetAttributes():
      if attribute_name == 'source_short':
        proto.source_short = cls._SOURCE_SHORT_TO_PROTO_MAP[
            event_object.source_short]

      elif attribute_name == 'pathspec':
        attribute_value = getattr(event_object, attribute_name, None)
        if attribute_value:
          event_path_spec_proto = (
              ProtobufEventPathSpecSerializer.WriteSerializedObject(
                  attribute_value))
          proto.pathspec.MergeFrom(event_path_spec_proto)

      elif attribute_name == 'tag':
        attribute_value = getattr(event_object, attribute_name, None)
        if attribute_value:
          event_tag_proto = ProtobufEventTagSerializer.WriteSerializedObject(
              attribute_value)
          proto.tag.MergeFrom(event_tag_proto)

      elif hasattr(proto, attribute_name):
        attribute_value = getattr(event_object, attribute_name)

        if attribute_value is None:
          continue

        if isinstance(attribute_value, (str, unicode)):
          attribute_value = utils.GetUnicodeString(attribute_value)
          if not attribute_value:
            continue

        if isinstance(attribute_value, dict):
          ProtobufEventAttributeSerializer.WriteSerializedDictObject(
              proto, attribute_name, attribute_value)

        elif isinstance(attribute_value, (list, tuple)):
          ProtobufEventAttributeSerializer.WriteSerializedListObject(
              proto, attribute_name, attribute_value)

        else:
          setattr(proto, attribute_name, attribute_value)

      else:
        attribute_value = getattr(event_object, attribute_name)

        # TODO: check if the next TODO still applies.
        # Serialize the attribute value only if it is an integer type
        # (int or long) or if it has a value.
        # TODO: fix logic.
        if (isinstance(attribute_value, (bool, int, float, long)) or
            attribute_value):
          proto_attribute = proto.attributes.add()
          ProtobufEventAttributeSerializer.WriteSerializedObject(
              proto_attribute, attribute_name, attribute_value)

    return proto

  @classmethod
  def WriteSerialized(cls, event_object):
    """Writes an event object to serialized form.

    Args:
      event_object: an event object (instance of EventObject).

    Returns:
      A protobuf string containing the serialized form.
    """
    proto = cls.WriteSerializedObject(event_object)
    return proto.SerializeToString()


class ProtobufEventPathBundleSerializer(interface.EventPathBundleSerializer):
  """Class that implements the protobuf event path bundle serializer."""

  @classmethod
  def ReadSerializedObject(cls, proto):
    """Reads an event path bundle from serialized form.

    Args:
      proto: a protobuf object containing the serialized form (instance of
             transmission_pb2.PathBundle).

    Returns:
      An event path bundle (instance of EventPathBundle).

    Raises:
      RuntimeError: when the protobuf object does not contain a pattern or
                    pathspecs field.
    """
    if not hasattr(proto, 'pattern'):
      raise RuntimeError(u'Unsupported protobuf type - missing pattern field.')
    if not hasattr(proto, 'pathspecs'):
      raise RuntimeError(
          u'Unsupported protobuf type - missing pathspecs field.')

    event_path_bundle = event.EventPathBundle()
    event_path_bundle.pattern = proto.pattern

    for proto_pathspec in proto.pathspecs:
      event_path_spec = ProtobufEventPathSpecSerializer.ReadSerializedObject(
          proto_pathspec)
      event_path_bundle.AppendPathspec(event_path_spec)

    return event_path_bundle

  @classmethod
  def ReadSerialized(cls, proto_string):
    """Reads an event path bundle from serialized form.

    Args:
      proto_string: a protobuf string containing the serialized form.

    Returns:
      An event path bundle (instance of EventPathBundle).

    Raises:
      RuntimeError: when the protobuf string is not prefixed with
                    the path bundle message type.
    """
    proto = transmission_pb2.PathBundle()
    proto.ParseFromString(proto_string)

    return cls.ReadSerializedObject(proto)

  @classmethod
  def WriteSerializedObject(cls, event_path_bundle):
    """Writes an event path bundle to serialized form.

    Args:
      event_path_bundle: an event path bundle (instance of EventPathBundle).

    Returns:
      A protobuf object containing the serialized form (instance of
      transmission_pb2.PathBundle).
    """
    proto = transmission_pb2.PathBundle()
    proto.pattern = event_path_bundle.pattern

    for event_path_spec in event_path_bundle.GetPathspecs():
      proto_pathspec = (
          ProtobufEventPathSpecSerializer.WriteSerializedObject(
            event_path_spec))

      proto_pathspec_add = proto.pathspecs.add()
      proto_pathspec_add.MergeFrom(proto_pathspec)

    return proto

  @classmethod
  def WriteSerialized(cls, event_path_bundle):
    """Writes an event path bundle to serialized form.

    Args:
      event_path_bundle: an event path bundle (instance of EventPathBundle).

    Returns:
      A protobuf string containing the serialized form.
    """
    proto = cls.WriteSerializedObject(event_path_bundle)
    return proto.SerializeToString()


class ProtobufEventPathSpecSerializer(interface.EventPathSpecSerializer):
  """Class that implements the protobuf event path specification serializer."""

  _TYPE_FROM_PROTO_MAP = {}
  _TYPE_TO_PROTO_MAP = {}
  for value in transmission_pb2.PathSpec.DESCRIPTOR.enum_types_by_name[
      'FileType'].values:
    _TYPE_FROM_PROTO_MAP[value.number] = value.name
    _TYPE_TO_PROTO_MAP[value.name] = value.number
  _TYPE_FROM_PROTO_MAP.setdefault(-1)

  @classmethod
  def ReadSerializedObject(cls, proto):
    """Reads an event path specification from serialized form.

    Args:
      proto: a protobuf object containing the serialized form (instance of
             transmission_pb2.PathSpec)

    Returns:
      An event path specification (instance of EventPathSpec).

    Raises:
      RuntimeError: when the protobuf object does not contain a type field.
    """
    if not hasattr(proto, 'type'):
      raise RuntimeError(u'Unsupported protobuf type - missing type field.')

    event_path_spec = event.EventPathSpec()

    for proto_attribute, attribute_value in proto.ListFields():
      if proto_attribute.name == 'type':
        attribute_value = cls._TYPE_FROM_PROTO_MAP[attribute_value]

      elif proto_attribute.name == 'nested_pathspec':
        attribute_value = ProtobufEventPathSpecSerializer.ReadSerializedObject(
            attribute_value)

      setattr(event_path_spec, proto_attribute.name, attribute_value)

    return event_path_spec

  @classmethod
  def ReadSerialized(cls, proto_string):
    """Reads an event path specification from serialized form.

    Args:
      proto_string: a protobuf string containing the serialized form.

    Returns:
      An event path specification (instance of EventPathSpec).

    Raises:
      RuntimeError: when the protobuf string is not prefixed with
                    the path specification message type.
    """
    proto = transmission_pb2.PathSpec()
    proto.ParseFromString(proto_string)

    return cls.ReadSerializedObject(proto)

  @classmethod
  def WriteSerializedObject(cls, event_path_spec):
    """Writes an event path specification to serialized form.

    Args:
      event_path_spec: an event path specification (instance of EventPathSpec).

    Returns:
      A protobuf object containing the serialized form (instance of
      transmission_pb2.PathSpec).
    """
    proto = transmission_pb2.PathSpec()

    for attribute_name in event_path_spec.__dict__:
      attribute_value = getattr(event_path_spec, attribute_name, None)

      if attribute_name == 'nested_pathspec':
        proto_nested_pathspec = (
            ProtobufEventPathSpecSerializer.WriteSerializedObject(
                attribute_value))

        proto.nested_pathspec.MergeFrom(proto_nested_pathspec)

      else:
        if attribute_name == 'type':
          attribute_value = cls._TYPE_TO_PROTO_MAP.get(
              attribute_value, -1)

        if attribute_value is not None:
          setattr(proto, attribute_name, attribute_value)

    return proto

  @classmethod
  def WriteSerialized(cls, event_path_spec):
    """Writes an event path specification to serialized form.

    Args:
      event_path_spec: an event path specification (instance of EventPathSpec).

    Returns:
      A protobuf string containing the serialized form.
    """
    proto = cls.WriteSerializedObject(event_path_spec)
    return proto.SerializeToString()


class ProtobufEventTagSerializer(interface.EventTagSerializer):
  """Class that implements the protobuf event tag serializer."""

  @classmethod
  def ReadSerializedObject(cls, proto):
    """Reads an event tag from serialized form.

    Args:
      proto: a protobuf object containing the serialized form (instance of
             plaso_storage_pb2.EventTag).

    Returns:
      An event tag (instance of EventTag).
    """
    event_tag = event.EventTag()

    for proto_attribute, attribute_value in proto.ListFields():
      if proto_attribute.name == 'tags':
        event_tag.tags = []
        for proto_tag in proto.tags:
          event_tag.tags.append(proto_tag.value)
      else:
        setattr(event_tag, proto_attribute.name, attribute_value)

    return event_tag

  @classmethod
  def ReadSerialized(cls, proto_string):
    """Reads an event tag from serialized form.

    Args:
      proto_string: a protobuf string containing the serialized form.

    Returns:
      An event tag (instance of EventTag).

    Raises:
      RuntimeError: when the protobuf string is not prefixed with
                    the event tag message type.
    """
    proto = plaso_storage_pb2.EventTagging()
    proto.ParseFromString(proto_string)

    return cls.ReadSerializedObject(proto)

  @classmethod
  def WriteSerializedObject(cls, event_tag):
    """Writes an event tag to serialized form.

    Args:
      event_tag: an event tag (instance of EventTag).

    Returns:
      A protobuf object containing the serialized form (instance of
      plaso_storage_pb2.EventTagging).
    """
    proto = plaso_storage_pb2.EventTagging()

    for attribute_name in event_tag.__dict__:
      attribute_value = getattr(event_tag, attribute_name, None)

      if attribute_name == 'tags':
        for tag_string in attribute_value:
          proto_tag_add = proto.tags.add()
          proto_tag_add.value = tag_string

      elif attribute_value is not None:
        setattr(proto, attribute_name, attribute_value)

    comment = getattr(event_tag, 'comment', '')
    if comment:
      proto.comment = comment

    color = getattr(event_tag, 'color', '')
    if color:
      proto.color = color

    return proto

  @classmethod
  def WriteSerialized(cls, event_tag):
    """Writes an event tag to serialized form.

    Args:
      event_tag: an event tag (instance of EventTag).

    Returns:
      A protobuf string containing the serialized form.

    Raises:
      RuntimeError: when the event tag is not valid for serialization.
    """
    if not event_tag.IsValidForSerialization():
      raise RuntimeError(u'Invalid tag object not valid for serialization.')

    proto = cls.WriteSerializedObject(event_tag)
    return proto.SerializeToString()


class ProtobufPathFilterSerializer(interface.PathFilterSerializer):
  """Class that implements the protobuf path filter serializer."""

  @classmethod
  def ReadSerializedObject(cls, proto):
    """Reads a path filter from serialized form.

    Args:
      proto: a protobuf object containing the serialized form (instance of
             plaso_storage_pb2.PathFilter).

    Returns:
      A path filter (instance of PathFilter).
    """
    # TODO: implement.
    pass

  @classmethod
  def ReadSerialized(cls, proto_string):
    """Reads a path filter from serialized form.

    Args:
      serialized: a protobuf object containing the serialized form (instance of
                  transmission_pb2.PathFilter).

    Returns:
      A path filter (instance of PathFilter).
    """
    # TODO: implement.
    pass

  @classmethod
  def WriteSerializedObject(cls, path_filter):
    """Writes a path filter to serialized form.

    Args:
      path_filter: a path filter (instance of PathFilter).

    Returns:
      A protobuf object containing the serialized form (instance of
      plaso_storage_pb2.PathFilter).
    """
    # TODO: implement.
    pass

  @classmethod
  def WriteSerialized(cls, path_filter):
    """Writes a path filter to serialized form.

    Args:
      path_filter: a path filter (instance of PathFilter).

    Returns:
      A protobuf string containing the serialized form.
    """
    # TODO: implement.
    pass


class ProtobufPreprocessObjectSerializer(interface.PreprocessObjectSerializer):
  """Class that implements the protobuf preprocessing object serializer."""

  @classmethod
  def ReadSerializedObject(cls, proto):
    """Reads a preprocess object from serialized form.

    Args:
      proto: a protobuf object containing the serialized form (instance of
             plaso_storage_pb2.Preprocess).

    Returns:
      A preprocessing object (instance of PreprocessObject).
    """
    pre_obj = event.PreprocessObject()

    for attribute in proto.attributes:
      key, value = ProtobufEventAttributeSerializer.ReadSerializedObject(
          attribute)
      if key == 'zone':
        pre_obj.SetTimezone(value)
      else:
        setattr(pre_obj, key, value)

    if proto.HasField('counter'):
      dict_object = ProtobufEventAttributeSerializer.ReadSerializedDictObject(
          proto.counter)
      pre_obj.SetCounterValues(dict_object)

    if proto.HasField('plugin_counter'):
      dict_object = ProtobufEventAttributeSerializer.ReadSerializedDictObject(
          proto.plugin_counter)
      pre_obj.SetPluginCounterValues(dict_object)

    if proto.HasField('store_range'):
      range_list = []
      for value in proto.store_range.values:
        if value.HasField('integer'):
          range_list.append(value.integer)
      pre_obj.store_range = (range_list[0], range_list[-1])

    if proto.HasField('collection_information'):
      dict_object = ProtobufEventAttributeSerializer.ReadSerializedDictObject(
          proto.collection_information)
      pre_obj.SetCollectionInformationValues(dict_object)

    return pre_obj

  @classmethod
  def ReadSerialized(cls, proto_string):
    """Reads a preprocess object from serialized form.

    Args:
      proto_string: a protobuf string containing the serialized form.

    Returns:
      A preprocessing object (instance of PreprocessObject).

    Raises:
      RuntimeError: when the protobuf string is not prefixed with
                    the preprocess object message type.
    """
    proto = plaso_storage_pb2.PreProcess()
    proto.ParseFromString(proto_string)

    return cls.ReadSerializedObject(proto)

  @classmethod
  def WriteSerializedObject(cls, pre_obj):
    """Writes a preprocessing object to serialized form.

    Args:
      pre_obj: a preprocessing object (instance of PreprocessObject).

    Returns:
      A protobuf object containing the serialized form (instance of
      plaso_storage_pb2.PreProcess).
    """
    proto = plaso_storage_pb2.PreProcess()

    for attribute, value in pre_obj.__dict__.items():
      if attribute == 'collection_information':
        zone = value.get('configured_zone', '')
        if zone and hasattr(zone, 'zone'):
          value['configured_zone'] = zone.zone
        ProtobufEventAttributeSerializer.WriteSerializedDictObject(
            proto, 'collection_information', value)
      elif attribute == 'counter':
        value_dict = dict(value.items())
        ProtobufEventAttributeSerializer.WriteSerializedDictObject(
            proto, 'counter', value_dict)
      elif attribute == 'plugin_counter':
        value_dict = dict(value.items())
        ProtobufEventAttributeSerializer.WriteSerializedDictObject(
            proto, 'plugin_counter', value_dict)
      elif attribute == 'store_range':
        range_proto = plaso_storage_pb2.Array()
        range_start = range_proto.values.add()
        range_start.integer = int(value[0])
        range_end = range_proto.values.add()
        range_end.integer = int(value[-1])
        proto.store_range.MergeFrom(range_proto)
      else:
        if attribute == 'zone':
          value = value.zone
        if isinstance(value, (bool, int, float, long)) or value:
          proto_attribute = proto.attributes.add()
          ProtobufEventAttributeSerializer.WriteSerializedObject(
              proto_attribute, attribute, value)

    return proto

  @classmethod
  def WriteSerialized(cls, pre_obj):
    """Writes a preprocessing object to serialized form.

    Args:
      pre_obj: a preprocessing object (instance of PreprocessObject).

    Returns:
      A protobuf string containing the serialized form.
    """
    proto = cls.WriteSerializedObject(pre_obj)
    return proto.SerializeToString()
