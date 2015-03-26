# -*- coding: utf-8 -*-
"""The json serializer object implementation."""

import logging
import json

from dfvfs.serializer import json_serializer as dfvfs_json_serializer

from plaso.lib import event
from plaso.serializer import interface
from plaso.storage import collection


class _EventTypeJsonEncoder(json.JSONEncoder):
  """A class that implements an event type object JSON encoder."""

  # pylint: disable=method-hidden
  def default(self, object_instance):
    """Returns a serialized version of an event type object.

    Args:
      object_instance: instance of an event type object.
    """
    # TODO: add support for the rest of the event type objects.
    if isinstance(object_instance, event.EventTag):
      return JsonEventTagSerializer.WriteSerialized(object_instance)

    else:
      return super(_EventTypeJsonEncoder, self).default(object_instance)


class JsonAnalysisReportSerializer(interface.AnalysisReportSerializer):
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


class JsonEventObjectSerializer(interface.EventObjectSerializer):
  """Class that implements the json event object serializer."""

  @classmethod
  def ReadSerialized(cls, json_string):
    """Reads an event object from serialized form.

    Args:
      json_string: an object containing the serialized form.

    Returns:
      An event object (instance of EventObject).
    """
    event_object = event.EventObject()
    json_attributes = json.loads(json_string)

    for key, value in json_attributes.iteritems():
      if key == 'tag':
        value = JsonEventTagSerializer.ReadSerialized(value)
      elif key == 'pathspec':
        value = dfvfs_json_serializer.JsonPathSpecSerializer.ReadSerialized(
            value)

      setattr(event_object, key, value)

    return event_object

  @classmethod
  def WriteSerialized(cls, event_object):
    """Writes an event object to serialized form.

    Args:
      event_object: an event object (instance of EventObject).

    Returns:
      An object containing the serialized form or None if the event
      cannot be serialized.
    """
    event_attributes = event_object.GetValues()

    serializer = dfvfs_json_serializer.JsonPathSpecSerializer
    if 'pathspec' in event_attributes:
      event_attributes['pathspec'] = serializer.WriteSerialized(
          event_attributes['pathspec'])

    try:
      return json.dumps(event_attributes, cls=_EventTypeJsonEncoder)
    except UnicodeDecodeError as exception:
      # TODO: Add better error handling so this can be traced to a parser or
      # a plugin and to which file that caused it.
      logging.error(u'Unable to serialize event with error: {0:s}'.format(
          exception))


class JsonEventTagSerializer(interface.EventTagSerializer):
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

    for key, value in json_attributes.iteritems():
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


class JsonPathFilterSerializer(interface.PathFilterSerializer):
  """Class that implements the json path filter serializer."""

  @classmethod
  def ReadSerialized(cls, serialized):
    """Reads a path filter from serialized form.

    Args:
      serialized: a JSON string containing the serialized form.

    Returns:
      A path filter (instance of PathFilter).
    """
    # TODO: implement.
    pass

  @classmethod
  def WriteSerialized(cls, path_filter):
    """Writes a path filter to serialized form.

    Args:
      path_filter: a path filter (instance of PathFilter).

    Returns:
      A JSON string containing the serialized form.
    """
    # TODO: implement.
    pass


class JsonPreprocessObjectSerializer(interface.PreprocessObjectSerializer):
  """Class that implements the json preprocessing object serializer."""

  @classmethod
  def ReadSerialized(cls, json_string):
    """Reads a path filter from serialized form.

    Args:
      json_string: a JSON string containing the serialized form.

    Returns:
      A preprocessing object (instance of PreprocessObject).
    """
    # TODO: implement.
    pass

  @classmethod
  def WriteSerialized(cls, pre_obj):
    """Writes a preprocessing object to serialized form.

    Args:
      pro_obj: a preprocessing object (instance of PreprocessObject).

    Returns:
      A JSON string containing the serialized form.
    """
    # TODO: implement.
    pass


class JsonCollectionInformationObjectSerializer(
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

    for key, value in json_dict.iteritems():
      if key == collection_information_object.RESERVED_COUNTER_KEYWORD:
        for identifier, value_dict in value.iteritems():
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
