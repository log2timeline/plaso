# -*- coding: utf-8 -*-
"""Shared functionality for JSON based output modules."""

import json

from plaso.lib import errors
from plaso.output import dynamic
from plaso.output import formatting_helper
from plaso.serializer import json_serializer


class JSONEventFormattingHelper(formatting_helper.EventFormattingHelper):
  """JSON output module event formatting helper."""

  _JSON_SERIALIZER = json_serializer.JSONAttributeContainerSerializer

  def __init__(self, output_mediator):
    """Initializes a JSON output module event formatting helper.

    Args:
      output_mediator (OutputMediator): output mediator.
    """
    super(JSONEventFormattingHelper, self).__init__(output_mediator)
    self._field_formatting_helper = dynamic.DynamicFieldFormattingHelper()

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

    display_name = event_data_json_dict.get('display_name', None)
    if display_name is None:
      display_name = self._field_formatting_helper.GetFormattedField(
          self._output_mediator, 'display_name', event, event_data,
          event_data_stream, event_tag)
      event_data_json_dict['display_name'] = display_name

    filename = event_data_json_dict.get('filename', None)
    if filename is None:
      filename = self._field_formatting_helper.GetFormattedField(
          self._output_mediator, 'filename', event, event_data,
          event_data_stream, event_tag)
      event_data_json_dict['filename'] = filename

    inode = event_data_json_dict.get('inode', None)
    if inode is None:
      inode = self._field_formatting_helper.GetFormattedField(
          self._output_mediator, 'inode', event, event_data,
          event_data_stream, event_tag)
      event_data_json_dict['inode'] = inode

    try:
      message = self._field_formatting_helper.GetFormattedField(
          self._output_mediator, 'message', event, event_data,
          event_data_stream, event_tag)
      event_data_json_dict['message'] = message
    except (errors.NoFormatterFound, errors.WrongFormatter):
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

  def GetFormattedEvent(self, event, event_data, event_data_stream, event_tag):
    """Retrieves a string representation of the event.

    Args:
      event (EventObject): event.
      event_data (EventData): event data.
      event_data_stream (EventDataStream): event data stream.
      event_tag (EventTag): event tag.

    Returns:
      str: string representation of the event.
    """
    json_dict = self._WriteSerializedDict(
        event, event_data, event_data_stream, event_tag)

    return json.dumps(json_dict, sort_keys=True)
