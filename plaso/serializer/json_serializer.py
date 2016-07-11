# -*- coding: utf-8 -*-
"""The json serializer object implementation."""

import binascii
import collections
import json

from dfvfs.path import path_spec as dfvfs_path_spec
from dfvfs.path import factory as dfvfs_path_spec_factory

from plaso.containers import errors
from plaso.containers import event_sources
from plaso.containers import events
from plaso.containers import interface as containers_interface
from plaso.containers import reports
from plaso.containers import sessions
from plaso.lib import event
from plaso.lib import py2to3
from plaso.serializer import interface
from plaso.storage import collection

import pytz  # pylint: disable=wrong-import-order


class _PreprocessObjectJSONDecoder(json.JSONDecoder):
  """A class that implements a preprocessing object JSON decoder."""

  _CLASS_TYPES = frozenset([
      u'bytes', u'collections.Counter', u'PreprocessObject', u'range',
      u'timezone'])

  def __init__(self, *args, **kargs):
    """Initializes the JSON decoder object."""
    super(_PreprocessObjectJSONDecoder, self).__init__(
        *args, object_hook=self._ConvertDictToObject, **kargs)

  def _ConvertDictToCollectionsCounter(self, json_dict):
    """Converts a JSON dict into a collections counter object.

    The dictionary of the JSON serialized objects consists of:
    {
        '__type__': 'collections.Counter'
        ...
    }

    Here '__type__' indicates the object base type. In this case this should
    be 'collections.Counter'. The rest of the elements of the dictionary make up
    the preprocessing object properties.

    Args:
      json_dict: a dictionary of the JSON serialized objects.

    Returns:
      A collections counter object (instance of collections.Counter).
    """
    collections_counter = collections.Counter()

    for key, value in iter(json_dict.items()):
      collections_counter[key] = value

    return collections_counter

  def _ConvertDictToPreprocessObject(self, json_dict):
    """Converts a JSON dict into a preprocessing object.

    The dictionary of the JSON serialized objects consists of:
    {
        '__type__': 'PreprocessObject'
        'collection_information': { ... }
        'counter': { ... }
        'plugin_counter': { ... }
        'store_range': { ... }
        'stores': { ... }
        'zone': { ... }
        ...
    }

    Here '__type__' indicates the object base type. In this case this should
    be 'PreprocessObject'. The rest of the elements of the dictionary make up
    the preprocessing object properties.

    Args:
      json_dict: a dictionary of the JSON serialized objects.

    Returns:
      A preprocessing object (instance of PreprocessObject).
    """
    preprocessing_object = event.PreprocessObject()

    for key, value in iter(json_dict.items()):
      setattr(preprocessing_object, key, value)

    return preprocessing_object

  def _ConvertDictToObject(self, json_dict):
    """Converts a JSON dict into an object.

    Note that json_dict is a dict of dicts and the _ConvertDictToObject
    method will be called for every dict. That is how the deserialized
    objects are created.

    Args:
      json_dict: a dictionary of the JSON serialized objects.

    Returns:
      A deserialized object which can be:
        * a collections counter (instance of collections.Counter);
        * a dictionary;
        * a preprocessing object (instance of PreprocessObject);
        * a pytz timezone object.
    """
    # Use __type__ to indicate the object class type.
    class_type = json_dict.get(u'__type__', None)

    if class_type not in self._CLASS_TYPES:
      # Dealing with a regular dict.
      return json_dict

    # Remove the class type from the JSON dict since we cannot pass it.
    del json_dict[u'__type__']

    if class_type == u'bytes':
      return binascii.a2b_qp(json_dict[u'stream'])

    elif class_type == u'collections.Counter':
      return self._ConvertDictToCollectionsCounter(json_dict)

    elif class_type == u'range':
      return tuple([json_dict[u'start'], json_dict[u'end']])

    elif class_type == u'timezone':
      return pytz.timezone(json_dict.get(u'zone', u'UTC'))

    return self._ConvertDictToPreprocessObject(json_dict)


class _PreprocessObjectJSONEncoder(json.JSONEncoder):
  """A class that implements a preprocessing object JSON encoder."""

  def _ConvertCollectionInformationToDict(self, collection_information):
    """Converts a collection information dictionary into a JSON dictionary.

    Args:
      collection_information: a collection information dictionary.

    Returns:
      A dictionary of the JSON serialized objects.
    """
    json_dict = {}
    for attribute_name, attribute_value in iter(collection_information.items()):
      if attribute_value is None:
        continue

      if attribute_name == u'configured_zone':
        attribute_value = {
            u'__type__': u'timezone',
            u'zone': u'{0!s}'.format(attribute_value)
        }

      elif isinstance(attribute_value, py2to3.BYTES_TYPE):
        attribute_value = {
            u'__type__': u'bytes',
            u'stream': u'{0:s}'.format(binascii.b2a_qp(attribute_value))
        }

      json_dict[attribute_name] = attribute_value

    return json_dict

  def _ConvertCollectionsCounterToDict(self, collections_counter):
    """Converts a collections counter object into a JSON dictionary.

    The resulting dictionary of the JSON serialized objects consists of:
    {
        '__type__': 'collections.Counter'
        ...
    }

    Here '__type__' indicates the object base type. In this case
    'collections.Counter'. The rest of the elements of the dictionary make up
    the collections counter object attributes.

    Args:
      collections_counter: a collections counter object (instance of
                           collections.Counter).

    Returns:
      A dictionary of the JSON serialized objects.

    Raises:
      TypeError: if not an instance of collections.Counter.
    """
    if not isinstance(collections_counter, collections.Counter):
      raise TypeError

    json_dict = {u'__type__': u'collections.Counter'}
    for attribute_name, attribute_value in iter(collections_counter.items()):
      if attribute_value is None:
        continue

      if isinstance(attribute_value, py2to3.BYTES_TYPE):
        attribute_value = {
            u'__type__': u'bytes',
            u'stream': u'{0:s}'.format(binascii.b2a_qp(attribute_value))
        }

      json_dict[attribute_name] = attribute_value

    return json_dict

  # Note: that the following functions do not follow the style guide
  # because they are part of the json.JSONEncoder object interface.

  # pylint: disable=method-hidden
  def default(self, preprocessing_object):
    """Converts a preprocessing object into a JSON dictionary.

    The resulting dictionary of the JSON serialized objects consists of:
    {
        '__type__': 'PreprocessObject'
        'collection_information': { ... }
        'counter': { ... }
        'plugin_counter': { ... }
        'store_range': { ... }
        'stores': { ... }
        'zone': { ... }
        ...
    }

    Here '__type__' indicates the object base type. In this case
    'PreprocessObject'. The rest of the elements of the dictionary
    make up the preprocessing object attributes.

    Args:
      preprocessing_object: a preprocessing object (instance of
                            PreprocessObject).

    Returns:
      A dictionary of the JSON serialized objects.

    Raises:
      TypeError: if not an instance of PreprocessObject.
    """
    if not isinstance(preprocessing_object, event.PreprocessObject):
      raise TypeError

    json_dict = {u'__type__': u'PreprocessObject'}
    for attribute_name in iter(preprocessing_object.__dict__.keys()):
      attribute_value = getattr(preprocessing_object, attribute_name, None)
      if attribute_value is None:
        continue

      if attribute_name == u'collection_information':
        attribute_value = self._ConvertCollectionInformationToDict(
            attribute_value)

      elif attribute_name in [u'counter', u'plugin_counter']:
        attribute_value = self._ConvertCollectionsCounterToDict(attribute_value)

      elif attribute_name == u'store_range':
        attribute_value = {
            u'__type__': u'range',
            u'end': attribute_value[1],
            u'start': attribute_value[0]
        }

      elif attribute_name == u'zone':
        attribute_value = {
            u'__type__': u'timezone',
            u'zone': u'{0!s}'.format(attribute_value)
        }

      elif isinstance(attribute_value, py2to3.BYTES_TYPE):
        attribute_value = {
            u'__type__': u'bytes',
            u'stream': u'{0:s}'.format(binascii.b2a_qp(attribute_value))
        }

      json_dict[attribute_name] = attribute_value

    return json_dict


class JSONAttributeContainerSerializer(interface.AttributeContainerSerializer):
  """Class that implements the json attribute container serializer."""

  _CONTAINER_CLASS_PER_TYPE = {
      u'analysis_report': reports.AnalysisReport,
      u'event': events.EventObject,
      u'event_source': event_sources.EventSource,
      u'event_tag': events.EventTag,
      u'extraction_error': errors.ExtractionError,
      u'session_completion': sessions.SessionCompletion,
      u'session_start': sessions.SessionStart,
  }

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
      attribute_container: an attribute container (instance of
                           AttributeContainer).

    Returns:
      A dictionary of the JSON serialized objects.

    Raises:
      TypeError: if not an instance of AttributeContainer.
      ValueError: if the attribute container type is not supported.
    """
    if not isinstance(
        attribute_container, containers_interface.AttributeContainer):
      raise TypeError(u'{0:s} is not an attribute container type.'.format(
          type(attribute_container)))

    container_type = getattr(attribute_container, u'CONTAINER_TYPE', None)
    if not container_type:
      raise ValueError(u'Unsupported attribute container type: {0:s}.'.format(
          type(attribute_container)))

    json_dict = {
        u'__type__': u'AttributeContainer',
        u'__container_type__': container_type,
    }

    for attribute_name, attribute_value in attribute_container.GetAttributes():
      if attribute_value is None:
        continue

      json_dict[attribute_name] = cls._ConvertAttributeValueToDict(
          attribute_value)

    return json_dict

  @classmethod
  def _ConvertAttributeValueToDict(cls, attribute_value):
    """Converts an attribute value into a JSON dictionary.

    Args:
      attribute_value: an attribute value.

    Returns:
      The JSON serialized object which can be:
        * a dictionary;
        * a list.
    """
    if isinstance(attribute_value, py2to3.BYTES_TYPE):
      attribute_value = {
          u'__type__': u'bytes',
          u'stream': u'{0:s}'.format(binascii.b2a_qp(attribute_value))
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
            u'__type__': u'tuple',
            u'values': json_list
        }

    elif isinstance(attribute_value, dfvfs_path_spec.PathSpec):
      attribute_value = cls._ConvertPathSpecToDict(attribute_value)

    elif isinstance(attribute_value, containers_interface.AttributeContainer):
      attribute_value = cls._ConvertAttributeContainerToDict(attribute_value)

    return attribute_value

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
      json_dict: a dictionary of the JSON serialized objects.

    Returns:
      A deserialized object which can be:
        * an attribute container (instance of AttributeContainer);
        * a dictionary;
        * a list;
        * a tuple.

    Raises:
      ValueError: if the class type or container type is not supported.
    """
    # Use __type__ to indicate the object class type.
    class_type = json_dict.get(u'__type__', None)
    if not class_type:
      # Dealing with a regular dict.
      return json_dict

    if class_type == u'bytes':
      return binascii.a2b_qp(json_dict[u'stream'])

    elif class_type == u'tuple':
      return tuple(cls._ConvertListToObject(json_dict[u'values']))

    elif class_type == u'AttributeContainer':
      # Use __container_type__ to indicate the attribute container type.
      container_type = json_dict.get(u'__container_type__', None)

    # Since we would like the JSON as flat as possible we handle decoding
    # a path specification.
    elif class_type == u'PathSpec':
      return cls._ConvertDictToPathSpec(json_dict)

    # Provide backwards compatibility.
    elif class_type == u'EventObject':
      container_type = u'event'

    elif class_type == u'EventTag':
      container_type = u'event_tag'

    elif class_type == u'AnalysisReport':
      container_type = u'analysis_report'

    else:
      raise ValueError(u'Unsupported class type: {0:s}'.format(class_type))

    container_class = cls._CONTAINER_CLASS_PER_TYPE.get(container_type, None)
    if not container_class:
      raise ValueError(u'Unsupported container type: {0:s}'.format(
          container_type))

    container_object = container_class()
    for attribute_name, attribute_value in iter(json_dict.items()):
      if attribute_name.startswith(u'__'):
        continue

      # Be strict about which attributes to set in non event objects.
      if (container_type != u'event' and
          attribute_name not in container_object.__dict__):
        continue

      # Note that "_tags" is the name for "labels" in EventTag prior to
      # version 1.4.1-20160131
      if container_type == u'event_tag' and attribute_name == u'_event_tags':
        attribute_name = u'labels'

      if isinstance(attribute_value, dict):
        attribute_value = cls._ConvertDictToObject(attribute_value)

      elif isinstance(attribute_value, list):
        attribute_value = cls._ConvertListToObject(attribute_value)

      setattr(container_object, attribute_name, attribute_value)

    return container_object

  @classmethod
  def _ConvertListToObject(cls, json_list):
    """Converts a JSON list into an object.

    Args:
      json_list: a list of the JSON serialized objects.

    Returns:
      A deserialized list.
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
      json_dict: a dictionary of the JSON serialized objects.

    Returns:
      A path specification (instance of path.PathSpec).
    """
    type_indicator = json_dict.get(u'type_indicator', None)
    if type_indicator:
      del json_dict[u'type_indicator']

    if u'parent' in json_dict:
      json_dict[u'parent'] = cls._ConvertDictToPathSpec(json_dict[u'parent'])

    # Remove the class type from the JSON dict since we cannot pass it.
    del json_dict[u'__type__']

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
      path_spec_object: a path specification (instance of dfvfs.PathSpec).

    Returns:
      A dictionary of the JSON serialized objects.

    Raises:
      TypeError: if not an instance of dfvfs.PathSpec.
    """
    if not isinstance(path_spec_object, dfvfs_path_spec.PathSpec):
      raise TypeError

    json_dict = {u'__type__': u'PathSpec'}
    for property_name in dfvfs_path_spec_factory.Factory.PROPERTY_NAMES:
      property_value = getattr(path_spec_object, property_name, None)
      if property_value is not None:
        json_dict[property_name] = property_value

    if path_spec_object.HasParent():
      json_dict[u'parent'] = cls._ConvertPathSpecToDict(path_spec_object.parent)

    json_dict[u'type_indicator'] = path_spec_object.type_indicator
    location = getattr(path_spec_object, u'location', None)
    if location:
      json_dict[u'location'] = location

    return json_dict

  @classmethod
  def ReadSerialized(cls, json_string):
    """Reads an attribute container from serialized form.

    Args:
      json_string: a JSON string containing the serialized form.

    Returns:
      An attribute container (instance of AttributeContainer) or None.
    """
    if not json_string:
      return

    json_dict = json.loads(json_string)
    return cls.ReadSerializedDict(json_dict)

  @classmethod
  def ReadSerializedDict(cls, json_dict):
    """Reads an attribute container from serialized dictionary form.

    Args:
      json_dict: a dictionary of the JSON serialized objects.

    Returns:
      An attribute container (instance of AttributeContainer) or None.
    """
    if not json_dict:
      return

    return cls._ConvertDictToObject(json_dict)

  @classmethod
  def WriteSerialized(cls, attribute_container):
    """Writes an attribute container to serialized form.

    Args:
      attribute_container: an attribute container (instance of
                           AttributeContainer).

    Returns:
      A JSON string containing the serialized form.
    """
    json_dict = cls.WriteSerializedDict(attribute_container)
    return json.dumps(json_dict)

  @classmethod
  def WriteSerializedDict(cls, attribute_container):
    """Writes an attribute container to serialized form.

    Args:
      attribute_container: an attribute container (instance of
                           AttributeContainer).

    Returns:
      A dictionary of the JSON serialized objects.
    """
    return cls._ConvertAttributeContainerToDict(attribute_container)


class JSONPreprocessObjectSerializer(interface.PreprocessObjectSerializer):
  """Class that implements the json preprocessing object serializer."""

  @classmethod
  def ReadSerialized(cls, json_string):
    """Reads a path filter from serialized form.

    Args:
      json_string: a JSON string containing the serialized form.

    Returns:
      A preprocessing object (instance of PreprocessObject).
    """
    json_decoder = _PreprocessObjectJSONDecoder()
    return json_decoder.decode(json_string)

  @classmethod
  def WriteSerialized(cls, preprocess_object):
    """Writes a preprocessing object to serialized form.

    Args:
      preprocess_object: a preprocessing object (instance of PreprocessObject).

    Returns:
      A JSON string containing the serialized form.
    """
    return json.dumps(preprocess_object, cls=_PreprocessObjectJSONEncoder)


class JSONCollectionInformationObjectSerializer(
    interface.CollectionInformationObjectSerializer):
  """Class that implements the collection information serializer interface."""

  @classmethod
  def ReadSerialized(cls, serialized):
    """Reads a path filter from serialized form.

    Args:
      serialized: an object containing the serialized form.

    Returns:
      A collection information object (instance of CollectionInformation).
    """
    json_dict = json.loads(serialized)
    collection_information_object = collection.CollectionInformation()

    for key, value in iter(json_dict.items()):
      if key == collection_information_object.RESERVED_COUNTER_KEYWORD:
        for identifier, value_dict in iter(value.items()):
          collection_information_object.AddCounterDict(identifier, value_dict)
      else:
        collection_information_object.SetValue(key, value)

    return collection_information_object

  @classmethod
  def WriteSerialized(cls, collection_information_object):
    """Writes a collection information object to serialized form.

    Args:
      collection_information_object: a collection information object (instance
                                     of CollectionInformation).

    Returns:
      An object containing the serialized form.
    """
    if not hasattr(collection_information_object, u'GetValues'):
      raise RuntimeError(
          u'Unable to serialize collection information, missing value getting.')

    if not hasattr(collection_information_object, u'AddCounter'):
      raise RuntimeError(
          u'Unable to serialize collection information, missing counters.')

    full_dict = dict(collection_information_object.GetValueDict())

    if collection_information_object.HasCounters():
      counter_dict = dict(collection_information_object.GetCounters())
      full_dict[
          collection_information_object.RESERVED_COUNTER_KEYWORD] = counter_dict

    return json.dumps(full_dict)
