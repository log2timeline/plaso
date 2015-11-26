# -*- coding: utf-8 -*-
"""The protobuf serializer object implementation."""

import logging

from dfvfs.serializer import protobuf_serializer as dfvfs_protobuf_serializer
from google.protobuf import message

from plaso.lib import event
from plaso.lib import py2to3
from plaso.lib import utils
from plaso.proto import plaso_storage_pb2
from plaso.serializer import interface
from plaso.storage import collection


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
      if proto_attribute.HasField(u'key'):
        attribute_name = proto_attribute.key
    except ValueError:
      pass

    if not isinstance(proto_attribute, (
        plaso_storage_pb2.Attribute, plaso_storage_pb2.Value)):
      raise RuntimeError(u'Unsupported protobuf type.')

    if proto_attribute.HasField(u'string'):
      return attribute_name, proto_attribute.string

    elif proto_attribute.HasField(u'integer'):
      return attribute_name, proto_attribute.integer

    elif proto_attribute.HasField(u'boolean'):
      return attribute_name, proto_attribute.boolean

    elif proto_attribute.HasField(u'dict'):
      attribute_value = {}

      for proto_dict in proto_attribute.dict.attributes:
        dict_key, dict_value = cls.ReadSerializedObject(proto_dict)
        attribute_value[dict_key] = dict_value
      return attribute_name, attribute_value

    elif proto_attribute.HasField(u'array'):
      attribute_value = []

      for proto_array in proto_attribute.array.values:
        _, list_value = cls.ReadSerializedObject(proto_array)
        attribute_value.append(list_value)
      return attribute_name, attribute_value

    elif proto_attribute.HasField(u'data'):
      return attribute_name, proto_attribute.data

    elif proto_attribute.HasField(u'float'):
      return attribute_name, proto_attribute.float

    elif proto_attribute.HasField(u'none'):
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

    The attribute of an event object can store almost any
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

    if isinstance(attribute_value, basestring):
      proto_attribute.string = utils.GetUnicodeString(attribute_value)

    elif isinstance(attribute_value, bool):
      proto_attribute.boolean = attribute_value

    elif isinstance(attribute_value, py2to3.INTEGER_TYPES):
      # TODO: add some bounds checking.
      proto_attribute.integer = attribute_value

    elif isinstance(attribute_value, dict):
      cls.WriteSerializedDictObject(proto_attribute, u'dict', attribute_value)

    elif isinstance(attribute_value, (list, tuple)):
      cls.WriteSerializedListObject(proto_attribute, u'array', attribute_value)

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

    Raises:
      AttributeError: if the attribute cannot be merged with the dictionary.
    """
    dict_proto = plaso_storage_pb2.Dict()

    for dict_key, dict_value in iter(dict_object.items()):
      dict_proto_add = dict_proto.attributes.add()
      cls.WriteSerializedObject(dict_proto_add, dict_key, dict_value)

    dict_attribute = getattr(proto_attribute, attribute_name)
    try:
      dict_attribute.MergeFrom(dict_proto)
    except AttributeError as exception:
      raise AttributeError(
          u'Unable to merge attribute: {0:s} with error: {1:s}'.format(
              attribute_name, exception))

  @classmethod
  def WriteSerializedListObject(
      cls, proto_attribute, attribute_name, list_object):
    """Writes a list event attribute to serialized form.

    Args:
      proto_attribute: a protobuf attribute object.
      attribute_name: the name of the attribute.
      list_object: a list object that is the value of the attribute.

    Raises:
      AttributeError: if the attribute cannot be merged with the list.
    """
    list_proto = plaso_storage_pb2.Array()

    for list_value in list_object:
      list_proto_add = list_proto.values.add()
      cls.WriteSerializedObject(list_proto_add, u'', list_value)

    list_attribute = getattr(proto_attribute, attribute_name)
    try:
      list_attribute.MergeFrom(list_proto)
    except AttributeError as exception:
      raise AttributeError(
          u'Unable to merge attribute: {0:s} with error: {1:s}'.format(
              attribute_name, exception))


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
    # Plugin name is set as one of the attributes.
    analysis_report = event.AnalysisReport(u'')

    for proto_attribute, value in proto.ListFields():
      # TODO: replace by ReadSerializedDictObject, need tests first.
      # dict_object = ProtobufEventAttributeSerializer.ReadSerializedDictObject(
      #     proto.report_dict)
      if proto_attribute.name == u'report_dict':
        new_value = {}
        for proto_dict in proto.report_dict.attributes:
          dict_key, dict_value = (
              ProtobufEventAttributeSerializer.ReadSerializedObject(proto_dict))
          new_value[dict_key] = dict_value
        setattr(analysis_report, proto_attribute.name, new_value)

      # TODO: replace by ReadSerializedListObject, need tests first.
      # list_object = ProtobufEventAttributeSerializer.ReadSerializedListObject(
      #     proto.report_array)
      elif proto_attribute.name == u'report_array':
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
    proto.time_compiled = getattr(analysis_report, u'time_compiled', 0)
    plugin_name = getattr(analysis_report, u'plugin_name', None)

    if plugin_name:
      proto.plugin_name = plugin_name

    proto.text = getattr(analysis_report, u'text', u'N/A')

    for image in getattr(analysis_report, u'images', []):
      proto.images.append(image)

    if hasattr(analysis_report, u'report_dict'):
      dict_proto = plaso_storage_pb2.Dict()
      dict_object = getattr(analysis_report, u'report_dict', {})
      for key, value in iter(dict_object.items()):
        sub_proto = dict_proto.attributes.add()
        ProtobufEventAttributeSerializer.WriteSerializedObject(
            sub_proto, key, value)
      proto.report_dict.MergeFrom(dict_proto)

    if hasattr(analysis_report, u'report_array'):
      list_proto = plaso_storage_pb2.Array()
      for value in getattr(analysis_report, u'report_array', []):
        sub_proto = list_proto.values.add()
        ProtobufEventAttributeSerializer.WriteSerializedObject(
            sub_proto, u'', value)

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


class ProtobufEventObjectSerializer(interface.EventObjectSerializer):
  """Class that implements the protobuf event object serializer."""

  # TODO: check if the next TODO still applies.
  # TODO: remove this once source_short has been moved to event formatter.
  # Lists of the mappings between the source short values of the event object
  # and those used in the protobuf.
  _SOURCE_SHORT_FROM_PROTO_MAP = {}
  _SOURCE_SHORT_TO_PROTO_MAP = {}
  for value in plaso_storage_pb2.EventObject.DESCRIPTOR.enum_types_by_name[
      u'SourceShort'].values:
    _SOURCE_SHORT_FROM_PROTO_MAP[value.number] = value.name
    _SOURCE_SHORT_TO_PROTO_MAP[value.name] = value.number
  _SOURCE_SHORT_FROM_PROTO_MAP.setdefault(6)
  _SOURCE_SHORT_TO_PROTO_MAP.setdefault(u'LOG')

  _path_spec_serializer = dfvfs_protobuf_serializer.ProtobufPathSpecSerializer

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
      if proto_attribute.name == u'source_short':
        event_object.source_short = cls._SOURCE_SHORT_FROM_PROTO_MAP[value]

      elif proto_attribute.name == u'pathspec':
        event_object.pathspec = (
            cls._path_spec_serializer.ReadSerialized(proto.pathspec))

      elif proto_attribute.name == u'tag':
        event_object.tag = ProtobufEventTagSerializer.ReadSerializedObject(
            proto.tag)

      elif proto_attribute.name == u'attributes':
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

    # The plaso_storage_pb2.EventObject protobuf contains a field named
    # attributes which technically not a Dict but behaves similar.
    dict_object = ProtobufEventAttributeSerializer.ReadSerializedDictObject(
        proto)

    for attribute, value in iter(dict_object.items()):
      setattr(event_object, attribute, value)

    return event_object

  @classmethod
  def ReadSerialized(cls, proto_string):
    """Reads an event object from serialized form.

    Args:
      proto_string: a protobuf string containing the serialized form.

    Returns:
      An event object (instance of EventObject).
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

    proto.data_type = getattr(event_object, u'data_type', u'event')

    for attribute_name in event_object.GetAttributes():
      if attribute_name == u'source_short':
        proto.source_short = cls._SOURCE_SHORT_TO_PROTO_MAP[
            event_object.source_short]

      elif attribute_name == u'pathspec':
        attribute_value = getattr(event_object, attribute_name, None)
        if attribute_value:
          attribute_value = cls._path_spec_serializer.WriteSerialized(
              attribute_value)
          setattr(proto, attribute_name, attribute_value)

      elif attribute_name == u'tag':
        attribute_value = getattr(event_object, attribute_name, None)
        if attribute_value:
          event_tag_proto = ProtobufEventTagSerializer.WriteSerializedObject(
              attribute_value)
          proto.tag.MergeFrom(event_tag_proto)

      elif hasattr(proto, attribute_name):
        attribute_value = getattr(event_object, attribute_name)

        if attribute_value is None:
          continue

        if isinstance(attribute_value, basestring):
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
          try:
            setattr(proto, attribute_name, attribute_value)
          except ValueError as exception:
            path_spec = getattr(event_object, u'pathspec', None)
            path = getattr(path_spec, u'location', u'')
            logging.error((
                u'Unable to save value for: {0:s} [{1:s}] with error: {2:s} '
                u'coming from file: {3:s}').format(
                    attribute_name, type(attribute_value), exception, path))
            # Catch potential out of range errors.
            if isinstance(attribute_value, py2to3.INTEGER_TYPES):
              setattr(proto, attribute_name, -1)

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
      A protobuf string containing the serialized form or None if
      there is an error encoding the protobuf.
    """
    proto = cls.WriteSerializedObject(event_object)
    try:
      return proto.SerializeToString()
    except message.EncodeError:
      # TODO: Add better error handling so this can be traced to a parser or
      # a plugin and to which file that caused it.
      logging.error(u'Unable to serialize event object.')


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
      if proto_attribute.name == u'tags':
        event_tag._tags = []
        for proto_tag in proto.tags:
          event_tag._tags.append(proto_tag.value)
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

    # TODO: Once we move EventTag to slots we need to query __slots__
    # instead of __dict__
    for attribute_name in event_tag.__dict__:
      attribute_value = getattr(event_tag, attribute_name, None)

      if (attribute_name == u'_tags' and
          isinstance(attribute_value, (tuple, list))):
        for tag_string in attribute_value:
          proto_tag_add = proto.tags.add()
          proto_tag_add.value = tag_string

      elif attribute_value is not None:
        setattr(proto, attribute_name, attribute_value)

    comment = getattr(event_tag, u'comment', u'')
    if comment:
      proto.comment = comment

    color = getattr(event_tag, u'color', u'')
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
      if key == u'zone':
        pre_obj.SetTimezone(value)
      else:
        setattr(pre_obj, key, value)

    if proto.HasField(u'counter'):
      dict_object = ProtobufEventAttributeSerializer.ReadSerializedDictObject(
          proto.counter)
      pre_obj.SetCounterValues(dict_object)

    if proto.HasField(u'plugin_counter'):
      dict_object = ProtobufEventAttributeSerializer.ReadSerializedDictObject(
          proto.plugin_counter)
      pre_obj.SetPluginCounterValues(dict_object)

    if proto.HasField(u'store_range'):
      range_list = []
      for value in proto.store_range.values:
        if value.HasField(u'integer'):
          range_list.append(value.integer)
      pre_obj.store_range = (range_list[0], range_list[-1])

    if proto.HasField(u'collection_information'):
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

    for attribute, value in iter(pre_obj.__dict__.items()):
      if attribute == u'collection_information':
        zone = value.get(u'configured_zone', u'')
        if zone and hasattr(zone, u'zone'):
          value[u'configured_zone'] = zone.zone
        ProtobufEventAttributeSerializer.WriteSerializedDictObject(
            proto, u'collection_information', value)

      elif attribute == u'counter':
        value_dict = dict(value.items())
        ProtobufEventAttributeSerializer.WriteSerializedDictObject(
            proto, u'counter', value_dict)

      elif attribute == u'plugin_counter':
        value_dict = dict(value.items())
        ProtobufEventAttributeSerializer.WriteSerializedDictObject(
            proto, u'plugin_counter', value_dict)

      elif attribute == u'store_range':
        range_proto = plaso_storage_pb2.Array()
        range_start = range_proto.values.add()
        range_start.integer = int(value[0])
        range_end = range_proto.values.add()
        range_end.integer = int(value[-1])
        proto.store_range.MergeFrom(range_proto)

      else:
        if attribute == u'zone':
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


class ProtobufCollectionInformationObjectSerializer(
    interface.CollectionInformationObjectSerializer):
  """Class that implements the collection information serializer interface."""

  @classmethod
  def ReadSerializedObject(cls, proto):
    """Reads a collection information object from serialized form."""
    collection_information_object = collection.CollectionInformation()

    for attribute in proto.attributes:
      key = attribute.key
      if key == collection_information_object.RESERVED_COUNTER_KEYWORD:
        _, counter_dict = ProtobufEventAttributeSerializer.ReadSerializedObject(
            attribute)
        for identifier, value_dict in iter(counter_dict.items()):
          collection_information_object.AddCounterDict(identifier, value_dict)
      else:
        _, value = ProtobufEventAttributeSerializer.ReadSerializedObject(
            attribute)
        collection_information_object.SetValue(key, value)

    return collection_information_object

  @classmethod
  def ReadSerialized(cls, serialized):
    """Reads a path filter from serialized form.

    Args:
      serialized: an object containing the serialized form.

    Returns:
      A collection information object (instance of CollectionInformation).
    """
    proto = plaso_storage_pb2.Dict()
    proto.ParseFromString(serialized)

    return cls.ReadSerializedObject(proto)

  @classmethod
  def WriteSerializedObject(cls, collection_information_object):
    """Writes a collection information object to serialized form.

    Args:
      collection_information_object: a collection information object (instance
                                     of CollectionInformation).

    Returns:
      A protobuf object containing the serialized form (instance of
      plaso_storage_pb2.Dict).

    Raises:
      RuntimeError: when the collection information object is malformed.
    """
    if not hasattr(collection_information_object, u'GetValues'):
      raise RuntimeError(
          u'Unable to serialize collection information, missing value getting.')

    if not hasattr(collection_information_object, u'AddCounter'):
      raise RuntimeError(
          u'Unable to serialize collection information, missing counters.')

    proto = plaso_storage_pb2.Dict()

    dict_object = collection_information_object.GetValueDict()
    for key, value in iter(dict_object. items()):
      attribute = proto.attributes.add()
      if u'zone' in key and not isinstance(value, basestring):
        value = getattr(value, u'zone', u'{0!s}'.format(value))

      ProtobufEventAttributeSerializer.WriteSerializedObject(
          attribute, key, value)

    if collection_information_object.HasCounters():
      attribute = proto.attributes.add()
      counter_dict = dict(collection_information_object.GetCounters())
      ProtobufEventAttributeSerializer.WriteSerializedObject(
          attribute, collection_information_object.RESERVED_COUNTER_KEYWORD,
          counter_dict)

    return proto

  @classmethod
  def WriteSerialized(cls, collection_information_object):
    """Writes a collection information object to serialized form.

    Args:
      collection_information_object: a collection information object (instance
                                     of CollectionInformation).

    Returns:
      A protobuf string containing the serialized form.
    """
    proto = cls.WriteSerializedObject(collection_information_object)
    return proto.SerializeToString()
