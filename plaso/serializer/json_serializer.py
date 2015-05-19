# -*- coding: utf-8 -*-
"""The json serializer object implementation."""

import collections
import json

from dfvfs.path import path_spec as dfvfs_path_spec
from dfvfs.path import factory as dfvfs_path_spec_factory

from plaso.lib import event
from plaso.serializer import interface
from plaso.storage import collection

import pytz


class _EventObjectJSONDecoder(json.JSONDecoder):
  """A class that implements an event object JSON decoder."""

  _CLASS_TYPES = frozenset([u'EventObject', u'EventTag', u'PathSpec'])

  def __init__(self, *args, **kargs):
    """Initializes the JSON decoder object."""
    super(_EventObjectJSONDecoder, self).__init__(
        *args, object_hook=self._ConvertDictToObject, **kargs)

  def _ConvertDictToEventObject(self, json_dict):
    """Converts a JSON dict into an event object.

    The dictionary of the JSON serialized objects consists of:
    {
        '__type__': 'EventObject'
        'pathspec': { ... }
        'tag': { ... }
        ...
    }

    Here '__type__' indicates the object base type. In this case this should
    be 'EventObject'. The rest of the elements of the dictionary make up the
    event object properties.

    Args:
      json_dict: a dictionary of the JSON serialized objects.

    Returns:
      An event object (instance of EventObject).
    """
    event_object = event.EventObject()

    for key, value in iter(json_dict.items()):
      setattr(event_object, key, value)

    return event_object

  def _ConvertDictToEventTag(self, json_dict):
    """Converts a JSON dict into an event tag object.

    The dictionary of the JSON serialized objects consists of:
    {
        '__type__': 'EventTag'
        ...
    }

    Here '__type__' indicates the object base type. In this case this should
    be 'EventTag'. The rest of the elements of the dictionary make up the
    event tag object properties.

    Args:
      json_dict: a dictionary of the JSON serialized objects.

    Returns:
      An event tag (instance of EventTag).
    """
    event_tag = event.EventTag()

    for key, value in iter(json_dict.items()):
      setattr(event_tag, key, value)

    return event_tag

  def _ConvertDictToPathSpec(self, json_dict):
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

    return dfvfs_path_spec_factory.Factory.NewPathSpec(
        type_indicator, **json_dict)

  def _ConvertDictToObject(self, json_dict):
    """Converts a JSON dict into an object.

    Note that json_dict is a dict of dicts and the _ConvertDictToObject
    method will be called for every dict. That is how the deserialized
    objects are created.

    Args:
      json_dict: a dictionary of the JSON serialized objects.

    Returns:
      A deserialized object which can be:
        * a dictionary;
        * an event object (instance of EventObject);
        * an event tag (instance of EventTag);
        * a path specification (instance of dfvfs.PathSpec).
    """
    # Use __type__ to indicate the object class type.
    class_type = json_dict.get(u'__type__', None)

    if class_type not in self._CLASS_TYPES:
      # Dealing with a regular dict.
      return json_dict

    # Remove the class type from the JSON dict since we cannot pass it.
    del json_dict[u'__type__']

    if class_type == u'EventTag':
      return self._ConvertDictToEventTag(json_dict)

    # Since we would like the JSON as flat as possible we handle decoding
    # a path specification.
    if class_type == u'PathSpec':
      return self._ConvertDictToPathSpec(json_dict)

    return self._ConvertDictToEventObject(json_dict)


class _PreprocessObjectJSONDecoder(json.JSONDecoder):
  """A class that implements a preprocessing object JSON decoder."""

  _CLASS_TYPES = frozenset([
      u'collections.Counter', u'PreprocessObject', u'timezone'])

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
      setattr(collections_counter, key, value)

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

    if class_type == u'collections.Counter':
      return self._ConvertDictToCollectionsCounter(json_dict)

    elif class_type == u'timezone':
      return pytz.timezone(json_dict.get(u'zone', u'UTC'))

    return self._ConvertDictToPreprocessObject(json_dict)


class _EventObjectJSONEncoder(json.JSONEncoder):
  """A class that implements an event object JSON encoder."""

  def _ConvertEventTagToDict(self, event_tag):
    """Converts an event tag object into a JSON dictionary.

    The resulting dictionary of the JSON serialized objects consists of:
    {
        '__type__': 'EventTag'
        ...
    }

    Here '__type__' indicates the object base type. In this case 'EventTag'.
    The rest of the elements of the dictionary make up the event tag object
    attributes.

    Args:
      event_tag: an event tag object (instance of EventTag).

    Returns:
      A dictionary of the JSON serialized objects.

    Raises:
      TypeError: if not an instance of EventTag.
    """
    if not isinstance(event_tag, event.EventTag):
      raise TypeError

    json_dict = {u'__type__': u'EventTag'}
    for attribute_name, attribute_value in iter(event_tag.__dict__.items()):
      if attribute_value is None:
        continue

      json_dict[attribute_name] = attribute_value

    return json_dict

  def _ConvertPathSpecToDict(self, path_spec_object):
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
      json_dict[u'parent'] = self._ConvertPathSpecToDict(
          path_spec_object.parent)

    json_dict[u'type_indicator'] = path_spec_object.type_indicator
    location = getattr(path_spec_object, u'location', None)
    if location:
      json_dict[u'location'] = location

    return json_dict

  # Note: that the following functions do not follow the style guide
  # because they are part of the json.JSONEncoder object interface.

  # pylint: disable=method-hidden
  def default(self, event_object):
    """Converts an event object into a JSON dictionary.

    The resulting dictionary of the JSON serialized objects consists of:
    {
        '__type__': 'EventObject'
        'pathspec': { ... }
        'tag': { ... }
        ...
    }

    Here '__type__' indicates the object base type. In this case 'EventObject'.
    The rest of the elements of the dictionary make up the event object
    attributes.

    Args:
      event_object: an event object (instance of EventObject).

    Returns:
      A dictionary of the JSON serialized objects.

    Raises:
      TypeError: if not an instance of EventObject.
    """
    if not isinstance(event_object, event.EventObject):
      raise TypeError

    json_dict = {u'__type__': u'EventObject'}
    for attribute_name in event_object.GetAttributes():
      attribute_value = getattr(event_object, attribute_name, None)
      if attribute_value is None:
        continue

      if attribute_name == u'pathspec':
        attribute_value = self._ConvertPathSpecToDict(attribute_value)

      elif attribute_name == u'tag':
        attribute_value = self._ConvertEventTagToDict(attribute_value)

      json_dict[attribute_name] = attribute_value

    return json_dict


class _PreprocessObjectJSONEncoder(json.JSONEncoder):
  """A class that implements a preprocessing object JSON encoder."""

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
      preprocessing_object: an preprocessing object (instance of
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

      if attribute_name in [u'counter', u'plugin_counter']:
        attribute_value = self._ConvertCollectionsCounterToDict(attribute_value)

      elif attribute_name == u'zone':
        attribute_value = {
            u'__type__': u'timezone',
            u'zone': u'{0!s}'.format(attribute_value)
        }

      json_dict[attribute_name] = attribute_value

    return json_dict


class JSONAnalysisReportSerializer(interface.AnalysisReportSerializer):
  """Class that implements the json analysis report serializer."""

  @classmethod
  def ReadSerialized(cls, json_string):
    """Reads an analysis report from serialized form.

    Args:
      json_string: a JSON string containing the serialized form.

    Returns:
      An analysis report (instance of AnalysisReport).
    """
    # TODO: implement.
    pass

  @classmethod
  def WriteSerialized(cls, analysis_report):
    """Writes an analysis report to serialized form.

    Args:
      analysis_report: an analysis report (instance of AnalysisReport).

    Returns:
      A JSON string containing the serialized form.
    """
    # TODO: implement.
    pass


class JSONEventObjectSerializer(interface.EventObjectSerializer):
  """Class that implements the json event object serializer."""

  @classmethod
  def ReadSerialized(cls, json_string):
    """Reads an event object from serialized form.

    Args:
      json_string: an object containing the serialized form.

    Returns:
      An event object (instance of EventObject).
    """
    json_decoder = _EventObjectJSONDecoder()
    return json_decoder.decode(json_string)

  @classmethod
  def WriteSerialized(cls, event_object):
    """Writes an event object to serialized form.

    Args:
      event_object: an event object (instance of EventObject).

    Returns:
      An object containing the serialized form or None if the event
      cannot be serialized.
    """
    return json.dumps(event_object, cls=_EventObjectJSONEncoder)


class JSONEventTagSerializer(interface.EventTagSerializer):
  """Class that implements the json event tag serializer."""

  @classmethod
  def ReadSerialized(cls, json_string):
    """Reads an event tag from serialized form.

    Args:
      json_string: a JSON string containing the serialized form.

    Returns:
      An event tag (instance of EventTag).
    """
    if not json_string:
      return

    event_tag = event.EventTag()

    json_attributes = json.loads(json_string)

    for key, value in iter(json_attributes.items()):
      setattr(event_tag, key, value)

    return event_tag

  @classmethod
  def WriteSerialized(cls, event_tag):
    """Writes an event tag to serialized form.

    Args:
      event_tag: an event tag (instance of EventTag).

    Returns:
      A JSON string containing the serialized form.

    Raises:
      RuntimeError: when the event tag is not valid for serialization.
    """
    if not event_tag.IsValidForSerialization():
      raise RuntimeError(u'Invalid tag object not valid for serialization.')

    return json.dumps(event_tag.__dict__)


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
  def WriteSerialized(cls, pre_obj):
    """Writes a preprocessing object to serialized form.

    Args:
      pro_obj: a preprocessing object (instance of PreprocessObject).

    Returns:
      A JSON string containing the serialized form.
    """
    return json.dumps(pre_obj, cls=_PreprocessObjectJSONEncoder)


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
