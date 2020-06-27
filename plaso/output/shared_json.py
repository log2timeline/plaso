# -*- coding: utf-8 -*-
"""Shared functionality for JSON based output modules."""

from __future__ import unicode_literals

import abc
import json

from plaso.lib import errors
from plaso.output import interface
from plaso.serializer import json_serializer


class SharedJSONOutputModule(interface.LinearOutputModule):
  """Shared functionality for a JSON output module."""

  _JSON_SERIALIZER = json_serializer.JSONAttributeContainerSerializer

  def _WriteSerialized(self, event, event_data, event_data_stream, event_tag):
    """Writes an event, event data and event tag to serialized form.

    Args:
      event (EventObject): event.
      event_data (EventData): event data.
      event_data_stream (EventDataStream): event data stream.
      event_tag (EventTag): event tag.

    Returns:
      str: A JSON string containing the serialized form.
    """
    json_dict = self._WriteSerializedDict(
        event, event_data, event_data_stream, event_tag)

    return json.dumps(json_dict, sort_keys=True)

  def _WriteSerializedDict(
      self, event, event_data, event_data_stream, event_tag):
    """Writes an event, event data and event tag to serialized form.

    Args:
      event (EventObject): event.
      event_data (EventData): event data.
      event_data_stream (EventDataStream): event data stream.
      event_tag (EventTag): event tag.

    Returns:
      dict[str, object]: JSON serialized objects.
    """
    event_data_json_dict = self._JSON_SERIALIZER.WriteSerializedDict(event_data)
    del event_data_json_dict['__container_type__']
    del event_data_json_dict['__type__']

    inode = event_data_json_dict.get('inode', None)
    if inode is None:
      event_data_json_dict['inode'] = 0

    try:
      message, _ = self._output_mediator.GetFormattedMessages(event_data)
      event_data_json_dict['message'] = message
    except errors.WrongFormatter:
      pass

    event_json_dict = self._JSON_SERIALIZER.WriteSerializedDict(event)
    event_json_dict['__container_type__'] = 'event'

    event_json_dict.update(event_data_json_dict)

    if event_data_stream:
      event_data_stream_json_dict = self._JSON_SERIALIZER.WriteSerializedDict(
          event_data_stream)
      del event_data_stream_json_dict['__container_type__']

      path_spec = event_data_stream_json_dict.pop('path_spec', None)
      if path_spec:
        event_data_stream_json_dict['pathspec'] = path_spec

      event_json_dict.update(event_data_stream_json_dict)

    if event_tag:
      event_tag_json_dict = self._JSON_SERIALIZER.WriteSerializedDict(event_tag)

      event_json_dict['tag'] = event_tag_json_dict

    return event_json_dict

  @abc.abstractmethod
  def WriteEventBody(self, event, event_data, event_data_stream, event_tag):
    """Writes event values to the output.

    Args:
      event (EventObject): event.
      event_data (EventData): event data.
      event_data_stream (EventDataStream): event data stream.
      event_tag (EventTag): event tag.
    """
