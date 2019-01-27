# -*- coding: utf-8 -*-
"""The json serializer object implementation."""

from __future__ import unicode_literals

import binascii
import codecs
import collections
import json

from dfvfs.path import path_spec as dfvfs_path_spec
from dfvfs.path import factory as dfvfs_path_spec_factory

from plaso.containers import interface as containers_interface
from plaso.containers import manager as containers_manager
from plaso.lib import py2to3
from plaso.serializer import interface
from plaso.serializer import logger


class JSONAttributeContainerSerializer(interface.AttributeContainerSerializer):
  """Class that implements the json attribute container serializer."""

  @classmethod
  def _ConvertAttributeContainerToDict(cls, attribute_container):
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

    Raises:
      TypeError: if not an instance of AttributeContainer.
      ValueError: if the attribute container type is not supported.
    """
    if not isinstance(
        attribute_container, containers_interface.AttributeContainer):
      raise TypeError('{0:s} is not an attribute container type.'.format(
          type(attribute_container)))

    container_type = getattr(attribute_container, 'CONTAINER_TYPE', None)
    if not container_type:
      raise ValueError('Unsupported attribute container type: {0:s}.'.format(
          type(attribute_container)))

    json_dict = {
        '__type__': 'AttributeContainer',
        '__container_type__': container_type,
    }

    for attribute_name, attribute_value in attribute_container.GetAttributes():
      json_dict[attribute_name] = cls._ConvertAttributeValueToDict(
          attribute_value)

    return json_dict

  # Pylint is confused by the formatting of the return type.
  # pylint: disable=missing-return-type-doc
  @classmethod
  def _ConvertAttributeValueToDict(cls, attribute_value):
    """Converts an attribute value into a JSON dictionary.

    Args:
      attribute_value (object): an attribute value.

    Returns:
      dict|list: The JSON serialized object which can be a dictionary or a list.
    """
    if isinstance(attribute_value, py2to3.BYTES_TYPE):
      encoded_value = binascii.b2a_qp(attribute_value)
      encoded_value = codecs.decode(encoded_value, 'ascii')
      attribute_value = {
          '__type__': 'bytes',
          'stream': '{0:s}'.format(encoded_value)
      }

    elif isinstance(attribute_value, (list, tuple)):
      json_list = []
      for list_element in attribute_value:
        json_dict = cls._ConvertAttributeValueToDict(list_element)
        json_list.append(json_dict)

      if isinstance(attribute_value, list):
        attribute_value = json_list
      else:
        attribute_value = {
            '__type__': 'tuple',
            'values': json_list
        }

    elif isinstance(attribute_value, collections.Counter):
      attribute_value = cls._ConvertCollectionsCounterToDict(attribute_value)

    elif isinstance(attribute_value, dfvfs_path_spec.PathSpec):
      attribute_value = cls._ConvertPathSpecToDict(attribute_value)

    elif isinstance(attribute_value, containers_interface.AttributeContainer):
      attribute_value = cls._ConvertAttributeContainerToDict(attribute_value)

    return attribute_value

  @classmethod
  def _ConvertCollectionsCounterToDict(cls, collections_counter):
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
      collections_counter (collections.Counter): counter.

    Returns:
      dict[str, object]: JSON serialized objects.

    Raises:
      TypeError: if not an instance of collections.Counter.
    """
    if not isinstance(collections_counter, collections.Counter):
      raise TypeError

    json_dict = {'__type__': 'collections.Counter'}
    for attribute_name, attribute_value in iter(collections_counter.items()):
      if attribute_value is None:
        continue

      if isinstance(attribute_value, py2to3.BYTES_TYPE):
        attribute_value = {
            '__type__': 'bytes',
            'stream': '{0:s}'.format(binascii.b2a_qp(attribute_value))
        }

      json_dict[attribute_name] = attribute_value

    return json_dict

  # Pylint is confused by the formatting of the return type.
  # pylint: disable=missing-return-type-doc
  @classmethod
  def _ConvertDictToObject(cls, json_dict):
    """Converts a JSON dict into an object.

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
      ValueError: if the class type or container type is not supported.
    """
    # Use __type__ to indicate the object class type.
    class_type = json_dict.get('__type__', None)
    if not class_type:
      # Dealing with a regular dict.
      return json_dict

    if class_type == 'bytes':
      return binascii.a2b_qp(json_dict['stream'])

    if class_type == 'tuple':
      return tuple(cls._ConvertListToObject(json_dict['values']))

    if class_type == 'collections.Counter':
      return cls._ConvertDictToCollectionsCounter(json_dict)

    if class_type == 'AttributeContainer':
      # Use __container_type__ to indicate the attribute container type.
      container_type = json_dict.get('__container_type__', None)

    # Since we would like the JSON as flat as possible we handle decoding
    # a path specification.
    elif class_type == 'PathSpec':
      return cls._ConvertDictToPathSpec(json_dict)

    else:
      raise ValueError('Unsupported class type: {0:s}'.format(class_type))

    container_class = (
        containers_manager.AttributeContainersManager.GetAttributeContainer(
            container_type))
    if not container_class:
      raise ValueError('Unsupported container type: {0:s}'.format(
          container_type))

    container_object = container_class()
    supported_attribute_names = container_object.GetAttributeNames()
    for attribute_name, attribute_value in iter(json_dict.items()):
      # Be strict about which attributes to set in non event values.
      if (container_type not in ('event', 'event_data') and
          attribute_name not in supported_attribute_names):

        if attribute_name not in ('__container_type__', '__type__'):
          logger.debug((
              '[ConvertDictToObject] unsupported attribute name: '
              '{0:s}.{1:s}').format(container_type, attribute_name))

        continue

      if isinstance(attribute_value, dict):
        attribute_value = cls._ConvertDictToObject(attribute_value)

      elif isinstance(attribute_value, list):
        attribute_value = cls._ConvertListToObject(attribute_value)

      setattr(container_object, attribute_name, attribute_value)

    return container_object

  @classmethod
  def _ConvertDictToCollectionsCounter(cls, json_dict):
    """Converts a JSON dict into a collections.Counter.

    The dictionary of the JSON serialized objects consists of:
    {
        '__type__': 'collections.Counter'
        ...
    }

    Here '__type__' indicates the object base type. In this case this should
    be 'collections.Counter'. The rest of the elements of the dictionary make up
    the preprocessing object properties.

    Args:
      json_dict (dict[str, object]): JSON serialized objects.

    Returns:
      collections.Counter: counter.
    """
    collections_counter = collections.Counter()

    for key, value in iter(json_dict.items()):
      if key == '__type__':
        continue
      collections_counter[key] = value

    return collections_counter

  @classmethod
  def _ConvertListToObject(cls, json_list):
    """Converts a JSON list into an object.

    Args:
      json_list (list[object]): JSON serialized objects.

    Returns:
      list[object]: a deserialized list.
    """
    list_value = []
    for json_list_element in json_list:
      if isinstance(json_list_element, dict):
        list_value.append(cls._ConvertDictToObject(json_list_element))

      elif isinstance(json_list_element, list):
        list_value.append(cls._ConvertListToObject(json_list_element))

      else:
        list_value.append(json_list_element)

    return list_value

  @classmethod
  def _ConvertDictToPathSpec(cls, json_dict):
    """Converts a JSON dict into a path specification object.

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
      path.PathSpec: path specification.
    """
    type_indicator = json_dict.get('type_indicator', None)
    if type_indicator:
      del json_dict['type_indicator']

    if 'parent' in json_dict:
      json_dict['parent'] = cls._ConvertDictToPathSpec(json_dict['parent'])

    # Remove the class type from the JSON dict since we cannot pass it.
    del json_dict['__type__']

    return dfvfs_path_spec_factory.Factory.NewPathSpec(
        type_indicator, **json_dict)

  @classmethod
  def _ConvertPathSpecToDict(cls, path_spec_object):
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
      json_dict['parent'] = cls._ConvertPathSpecToDict(path_spec_object.parent)

    json_dict['type_indicator'] = path_spec_object.type_indicator
    location = getattr(path_spec_object, 'location', None)
    if location:
      json_dict['location'] = location

    return json_dict

  @classmethod
  def ReadSerialized(cls, json_string):  # pylint: disable=arguments-differ
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
    if json_dict:
      json_object = cls._ConvertDictToObject(json_dict)
      if not isinstance(json_object, containers_interface.AttributeContainer):
        raise TypeError('{0:s} is not an attribute container type.'.format(
            type(json_object)))
      return json_object

    return None

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
    return cls._ConvertAttributeContainerToDict(attribute_container)
