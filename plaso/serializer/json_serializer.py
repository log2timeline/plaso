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
"""The json serializer object implementation."""

import json

from plaso.lib import event
from plaso.serializer import interface


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
      # TODO: Add pathspec support.
      if key == 'tag':
        value = JsonEventTagSerializer.ReadSerialized(value)

      setattr(event_object, key, value)

    return event_object

  @classmethod
  def WriteSerialized(cls, event_object):
    """Writes an event object to serialized form.

    Args:
      event_object: an event object (instance of EventObject).

    Returns:
      An object containing the serialized form.
    """
    event_attributes = event_object.GetValues()

    # TODO: Add pathspec support.
    if 'pathspec' in event_attributes:
      del event_attributes['pathspec']

    return json.dumps(event_attributes, cls=_EventTypeJsonEncoder)


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
