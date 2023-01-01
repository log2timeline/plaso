# -*- coding: utf-8 -*-
"""JSON attribute container serializer."""

import binascii
import codecs
import collections
import json

from acstore.containers import interface as containers_interface
from acstore.containers import manager as containers_manager

from dfdatetime import interface as dfdatetime_interface
from dfdatetime import serializer as dfdatetime_serializer

from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import path_spec as dfvfs_path_spec
from dfvfs.path import factory as dfvfs_path_spec_factory

# The following import is needed to make sure TSKTime is registered with
# the dfDateTime factory.
from dfvfs.vfs import tsk_file_entry  # pylint: disable=unused-import

from plaso.serializer import logger


class JSONAttributeContainerSerializer(object):
  """JSON attribute container serializer."""

  _convert_json_to_value = {}

  @classmethod
  def _ConvertAttributeContainerToJSON(cls, attribute_container):
    """Converts an attribute container object into a JSON dictionary.

    The resulting dictionary of the JSON serialized objects consists of:
    {
        '__type__': 'AttributeContainer'
        '__container_type__': ...
        ...
    }

    Here '__type__' indicates the object base type. In this case
    'AttributeContainer'.

    '__container_type__' indicates the container type and rest of the elements
    of the dictionary make up the attributes of the container.

    Args:
      attribute_container (AttributeContainer): attribute container.

    Returns:
      dict[str, object]: JSON serialized objects.
    """
    json_dict = {
        '__type__': 'AttributeContainer',
        '__container_type__': attribute_container.CONTAINER_TYPE}

    for attribute_name, attribute_value in attribute_container.GetAttributes():
      json_dict[attribute_name] = cls._ConvertValueToJSON(attribute_value)

    return json_dict

  @classmethod
  def _ConvertBytesToJSON(cls, bytes_value):
    """Converts a bytes value into a JSON dictionary.

    Args:
      bytes_value (bytes): a bytes value.

    Returns:
      dict: JSON serialized object of a bytes value.
    """
    encoded_value = binascii.b2a_qp(bytes_value)
    encoded_value = codecs.decode(encoded_value, 'ascii')
    return {
        '__type__': 'bytes',
        'stream': '{0:s}'.format(encoded_value)}

  @classmethod
  def _ConvertCollectionsCounterToJSON(cls, counter_value):
    """Converts a collections.Counter object into a JSON dictionary.

    The resulting dictionary of the JSON serialized objects consists of:
    {
        '__type__': 'collections.Counter'
        ...
    }

    Here '__type__' indicates the object base type. In this case
    'collections.Counter'. The rest of the elements of the dictionary make up
    the collections.Counter object attributes.

    Args:
      counter_value (collections.Counter): a collections.Counter value.

    Returns:
      dict[str, object]: JSON serialized objects.
    """
    json_dict = {'__type__': 'collections.Counter'}
    for attribute_name, attribute_value in counter_value.items():
      if attribute_value:
        if isinstance(attribute_value, bytes):
          attribute_value = cls._ConvertBytesToJSON(attribute_value)

        json_dict[attribute_name] = attribute_value

    return json_dict

  @classmethod
  def _ConvertJSONToAttributeContainer(cls, json_dict):
    """Converts a JSON dictionary into an attribute container.

    The dictionary of the JSON serialized objects consists of:
    {
        '__type__': 'AttributeContainer'
        '__container_type__': ...
        ...
    }

    Args:
      json_dict (dict[str, object]): JSON serialized objects.

    Returns:
      AttributeContainer: an attribute container.

    Raises:
      ValueError: if the container type or attribute type of an event data
          attribute container is not supported.
    """
    # Use __container_type__ to indicate the attribute container type.
    container_type = json_dict.get('__container_type__', None)

    attribute_container = (
        containers_manager.AttributeContainersManager.CreateAttributeContainer(
            container_type))

    supported_attribute_names = attribute_container.GetAttributeNames()
    for attribute_name, attribute_value in json_dict.items():
      # Be strict about which attributes to set in non event data attribute
      # containers.
      if (container_type != 'event_data' and
          attribute_name not in supported_attribute_names):

        if attribute_name not in ('__container_type__', '__type__'):
          logger.debug((
              '[_ConvertJSONToAttributeContainer] unsupported attribute name: '
              '{0:s}.{1:s}').format(container_type, attribute_name))

        continue

      if isinstance(attribute_value, dict):
        attribute_value = cls._ConvertJSONToValue(attribute_value)

      elif isinstance(attribute_value, list):
        attribute_value = cls._ConvertListToValue(attribute_value)

      if container_type == 'event_data':
        if isinstance(attribute_value, bytes):
          raise ValueError((
              'Event data attribute value: {0:s} of type bytes is not '
              'supported.').format(attribute_name))

        if isinstance(attribute_value, dict):
          raise ValueError((
              'Event data attribute value: {0:s} of type dict is not '
              'supported.').format(attribute_name))

      setattr(attribute_container, attribute_name, attribute_value)

    return attribute_container

  @classmethod
  def _ConvertJSONToBytes(cls, json_dict):
    """Converts a JSON dictionary into a bytes value.

    The dictionary of the JSON serialized objects consists of:
    {
        '__type__': 'bytes'
        'stream': an encoded bytes values.
    }

    Args:
      json_dict (dict[str, object]): JSON serialized objects.

    Returns:
      bytes: a bytes value.
    """
    return binascii.a2b_qp(json_dict['stream'])

  @classmethod
  def _ConvertJSONToCollectionsCounter(cls, json_dict):
    """Converts a JSON dictionary into a collections.Counter.

    The dictionary of the JSON serialized objects consists of:
    {
        '__type__': 'collections.Counter'
        ...
    }

    Here '__type__' indicates the object base type. In this case
    'collections.Counter'. The rest of the elements of the dictionary make up
    the collections.Counter object attributes.

    Args:
      json_dict (dict[str, object]): JSON serialized objects.

    Returns:
      collections.Counter: a collections.Counter value.
    """
    collections_counter = collections.Counter()

    for key, value in json_dict.items():
      if key != '__type__':
        collections_counter[key] = value

    return collections_counter

  @classmethod
  def _ConvertJSONToTuple(cls, json_dict):
    """Converts a JSON dictionary into a tuple value.

    The dictionary of the JSON serialized objects consists of:
    {
        '__type__': 'tuple'
        'values': elements of the tuple.
    }

    Args:
      json_dict (dict[str, object]): JSON serialized objects.

    Returns:
      tuple: a tuple value.
    """
    return tuple(cls._ConvertListToValue(json_dict['values']))

  # Pylint is confused by the formatting of the return type.
  # pylint: disable=missing-return-type-doc
  @classmethod
  def _ConvertJSONToValue(cls, json_dict):
    """Converts a JSON dictionary into a value.

    The dictionary of the JSON serialized objects consists of:
    {
        '__type__': 'AttributeContainer'
        '__container_type__': ...
        ...
    }

    Here '__type__' indicates the object base type. In this case
    'AttributeContainer'.

    '__container_type__' indicates the attribute container type.

    The rest of the elements of the dictionary make up the attributes.

    Args:
      json_dict (dict[str, object]): JSON serialized objects.

    Returns:
      AttributeContainer|dict|list|tuple: deserialized object.

    Raises:
      ValueError: if the type of a JSON dictionary value is not supported.
    """
    if not cls._convert_json_to_value:
      cls._convert_json_to_value = {
        'AttributeContainer': cls._ConvertJSONToAttributeContainer,
        'bytes': cls._ConvertJSONToBytes,
        'collections.Counter': cls._ConvertJSONToCollectionsCounter,
        'DateTimeValues': (
            dfdatetime_serializer.Serializer.ConvertDictToDateTimeValues),
        'PathSpec': cls._ConvertJSONToPathSpec,
        'tuple': cls._ConvertJSONToTuple}

    json_dict_type = json_dict.get('__type__', None)
    if not json_dict_type:
      return json_dict

    convert_function = cls._convert_json_to_value.get(json_dict_type, None)
    if not convert_function:
      raise ValueError('Unsupported JSON dictionary type: {0:s}'.format(
          json_dict_type))

    return convert_function(json_dict)

  @classmethod
  def _ConvertJSONToPathSpec(cls, json_dict):
    """Converts a JSON dictionary into a path specification object.

    The dictionary of the JSON serialized objects consists of:
    {
        '__type__': 'PathSpec'
        'type_indicator': 'OS'
        'parent': { ... }
        ...
    }

    Here '__type__' indicates the object base type. In this case this should
    be 'PathSpec'. The rest of the elements of the dictionary make up the
    path specification object properties.

    Args:
      json_dict (dict[str, object]): JSON serialized objects.

    Returns:
      dfvfs.PathSpec: path specification.
    """
    type_indicator = json_dict.get('type_indicator', None)
    if type_indicator:
      del json_dict['type_indicator']

    if 'parent' in json_dict:
      json_dict['parent'] = cls._ConvertJSONToPathSpec(json_dict['parent'])

    # Remove the class type from the JSON dictionary since we cannot pass it.
    del json_dict['__type__']

    path_spec = dfvfs_path_spec_factory.Factory.NewPathSpec(
        type_indicator, **json_dict)

    if type_indicator == dfvfs_definitions.TYPE_INDICATOR_OS:
      # dfvfs.OSPathSpec() will change the location to an absolute path
      # here we want to preserve the original location.
      path_spec.location = json_dict.get('location', None)

    return path_spec

  @classmethod
  def _ConvertListToJSON(cls, value):
    """Converts a list value into a JSON dictionary.

    Args:
      value (list): a list value.

    Returns:
      list: JSON serialized object of a list value.
    """
    return [cls._ConvertValueToJSON(element) for element in value]

  @classmethod
  def _ConvertListToValue(cls, json_list):
    """Converts a JSON list into an object.

    Args:
      json_list (list[object]): JSON serialized objects.

    Returns:
      list[object]: a deserialized list.
    """
    list_value = []
    for json_list_element in json_list:
      if isinstance(json_list_element, dict):
        list_value.append(cls._ConvertJSONToValue(json_list_element))

      elif isinstance(json_list_element, list):
        list_value.append(cls._ConvertListToValue(json_list_element))

      else:
        list_value.append(json_list_element)

    return list_value

  @classmethod
  def _ConvertTupleToJSON(cls, value):
    """Converts a tuple value into a JSON dictionary.

    The dictionary of the JSON serialized objects consists of:
    {
        '__type__': 'tuple'
        'values': elements of the tuple.
    }

    Args:
      value (tuple): a tuple value.

    Returns:
      dict: JSON serialized object of a tuple value.
    """
    return {
      '__type__': 'tuple',
        'values': cls._ConvertListToJSON(value)}

  @classmethod
  def _ConvertPathSpecToJSON(cls, path_spec_object):
    """Converts a path specification object into a JSON dictionary.

    The resulting dictionary of the JSON serialized objects consists of:
    {
        '__type__': 'PathSpec'
        'type_indicator': 'OS'
        'parent': { ... }
        ...
    }

    Here '__type__' indicates the object base type. In this case 'PathSpec'.
    The rest of the elements of the dictionary make up the path specification
    object properties. The supported property names are defined in
    path_spec_factory.Factory.PROPERTY_NAMES. Note that this method is called
    recursively for every path specification object and creates a dict of
    dicts in the process.

    Args:
      path_spec_object (dfvfs.PathSpec): path specification.

    Returns:
      dict[str, object]: JSON serialized objects.

    Raises:
      TypeError: if not an instance of dfvfs.PathSpec.
    """
    if not isinstance(path_spec_object, dfvfs_path_spec.PathSpec):
      raise TypeError

    json_dict = {'__type__': 'PathSpec'}
    for property_name in dfvfs_path_spec_factory.Factory.PROPERTY_NAMES:
      property_value = getattr(path_spec_object, property_name, None)
      if property_value is not None:
        json_dict[property_name] = property_value

    if path_spec_object.HasParent():
      json_dict['parent'] = cls._ConvertPathSpecToJSON(path_spec_object.parent)

    json_dict['type_indicator'] = path_spec_object.type_indicator
    location = getattr(path_spec_object, 'location', None)
    if location:
      json_dict['location'] = location

    return json_dict

  # Pylint is confused by the formatting of the return type.
  # pylint: disable=missing-return-type-doc
  @classmethod
  def _ConvertValueToJSON(cls, attribute_value):
    """Converts a value into a JSON dictionary.

    Args:
      attribute_value (object): an attribute value.

    Returns:
      dict|list: The JSON serialized object which can be a dictionary or a list.
    """
    convert_function = None

    if isinstance(attribute_value, bytes):
      convert_function = cls._ConvertBytesToJSON

    elif isinstance(attribute_value, list):
      convert_function = cls._ConvertListToJSON

    elif isinstance(attribute_value, tuple):
      convert_function = cls._ConvertTupleToJSON

    elif isinstance(attribute_value, collections.Counter):
      convert_function = cls._ConvertCollectionsCounterToJSON

    elif isinstance(attribute_value, dfdatetime_interface.DateTimeValues):
      convert_function = (
          dfdatetime_serializer.Serializer.ConvertDateTimeValuesToDict)

    elif isinstance(attribute_value, dfvfs_path_spec.PathSpec):
      convert_function = cls._ConvertPathSpecToJSON

    elif isinstance(attribute_value, containers_interface.AttributeContainer):
      convert_function = cls._ConvertAttributeContainerToJSON

    if convert_function:
      attribute_value = convert_function(attribute_value)

    return attribute_value

  @classmethod
  def ReadSerialized(cls, json_string):  # pylint: disable=arguments-renamed
    """Reads an attribute container from serialized form.

    Args:
      json_string (str): JSON serialized attribute container.

    Returns:
      AttributeContainer: attribute container or None.
    """
    if json_string:
      json_dict = json.loads(json_string)
      return cls.ReadSerializedDict(json_dict)

    return None

  @classmethod
  def ReadSerializedDict(cls, json_dict):
    """Reads an attribute container from serialized dictionary form.

    Args:
      json_dict (dict[str, object]): JSON serialized objects.

    Returns:
      AttributeContainer: attribute container or None.

    Raises:
      TypeError: if the serialized dictionary does not contain an
          AttributeContainer.
    """
    if not json_dict:
      return None

    if isinstance(json_dict, list):
      return json_dict

    json_object = cls._ConvertJSONToValue(json_dict)

    if isinstance(json_object, dfdatetime_interface.DateTimeValues):
      return json_object

    if isinstance(json_object, dfvfs_path_spec.PathSpec):
      return json_object

    if not isinstance(json_object, containers_interface.AttributeContainer):
      raise TypeError('{0!s} is not an attribute container type.'.format(
          type(json_object)))

    return json_object

  @classmethod
  def WriteSerialized(cls, attribute_container):
    """Writes an attribute container to serialized form.

    Args:
      attribute_container (AttributeContainer): attribute container.

    Returns:
      str: A JSON string containing the serialized form.
    """
    json_dict = cls.WriteSerializedDict(attribute_container)
    return json.dumps(json_dict)

  @classmethod
  def WriteSerializedDict(cls, attribute_container):
    """Writes an attribute container to serialized form.

    Args:
      attribute_container (AttributeContainer): attribute container.

    Returns:
      dict[str, object]: JSON serialized objects.
    """
    if isinstance(attribute_container, list):
      return attribute_container

    if isinstance(attribute_container, dfdatetime_interface.DateTimeValues):
      return dfdatetime_serializer.Serializer.ConvertDateTimeValuesToDict(
          attribute_container)

    if isinstance(attribute_container, dfvfs_path_spec.PathSpec):
      return cls._ConvertPathSpecToJSON(attribute_container)

    return cls._ConvertAttributeContainerToJSON(attribute_container)
