# -*- coding: utf-8 -*-
"""Shared functionality for JSON based output modules."""

import abc

from acstore.containers import interface as containers_interface

from dfdatetime import interface as dfdatetime_interface

from plaso.lib import errors
from plaso.output import dynamic
from plaso.output import text_file
from plaso.serializer import json_serializer


class SharedJSONOutputModule(text_file.TextFileOutputModule):
  """Shared functionality for JSON based output modules."""

  _JSON_SERIALIZER = json_serializer.JSONAttributeContainerSerializer

  def __init__(self):
    """Initializes an output module."""
    super(SharedJSONOutputModule, self).__init__()
    self._field_formatting_helper = dynamic.DynamicFieldFormattingHelper()

  def _GetFieldValues(
      self, output_mediator, event, event_data, event_data_stream, event_tag):
    """Retrieves the output field values.

    Args:
      output_mediator (OutputMediator): mediates interactions between output
          modules and other components, such as storage and dfVFS.
      event (EventObject): event.
      event_data (EventData): event data.
      event_data_stream (EventDataStream): event data stream.
      event_tag (EventTag): event tag.

    Returns:
      dict[str, str]: output field values per name.
    """
    field_values = {
        '__container_type__': 'event',
        '__type__': 'AttributeContainer'}

    if event_data:
      for attribute_name, attribute_value in event_data.GetAttributes():
        # Ignore attribute container identifier and date and time values.
        if isinstance(attribute_value, (
            containers_interface.AttributeContainerIdentifier,
            dfdatetime_interface.DateTimeValues)):
          continue

        # Ignore date and time values.
        if isinstance(attribute_value, dfdatetime_interface.DateTimeValues):
          continue

        if (isinstance(attribute_value, list) and attribute_value and
            isinstance(attribute_value[0],
                       dfdatetime_interface.DateTimeValues)):
          continue

        # Output _parser_chain as parser for backwards compatibility.
        if attribute_name == '_parser_chain':
          attribute_name = 'parser'

        field_values[attribute_name] = attribute_value

    if event_data_stream:
      for attribute_name, attribute_value in event_data_stream.GetAttributes():
        # Output path_spec as pathspec for backwards compatibility.
        if attribute_name == 'path_spec':
          attribute_name = 'pathspec'
          attribute_value = self._JSON_SERIALIZER.WriteSerializedDict(
              attribute_value)

        field_values[attribute_name] = attribute_value

    if event:
      for attribute_name, attribute_value in event.GetAttributes():
        # Ignore attribute container identifier values.
        if isinstance(attribute_value,
                      containers_interface.AttributeContainerIdentifier):
          continue

        if attribute_name == 'date_time':
          attribute_value = self._JSON_SERIALIZER.WriteSerializedDict(
              attribute_value)

        field_values[attribute_name] = attribute_value

    display_name = field_values.get('display_name', None)
    if display_name is None:
      display_name = self._field_formatting_helper.GetFormattedField(
          output_mediator, 'display_name', event, event_data, event_data_stream,
          event_tag)
      field_values['display_name'] = display_name

    filename = field_values.get('filename', None)
    if filename is None:
      filename = self._field_formatting_helper.GetFormattedField(
          output_mediator, 'filename', event, event_data, event_data_stream,
          event_tag)
      field_values['filename'] = filename

    inode = field_values.get('inode', None)
    if inode is None:
      inode = self._field_formatting_helper.GetFormattedField(
          output_mediator, 'inode', event, event_data, event_data_stream,
          event_tag)
      field_values['inode'] = inode

    try:
      message = self._field_formatting_helper.GetFormattedField(
          output_mediator, 'message', event, event_data, event_data_stream,
          event_tag)
      field_values['message'] = message
    except errors.NoFormatterFound:
      pass

    if event_tag:
      event_tag_values = {
          '__container_type__': 'event_tag',
          '__type__': 'AttributeContainer'}

      for attribute_name, attribute_value in event_tag.GetAttributes():
        # Ignore attribute container identifier values.
        if isinstance(attribute_value,
                      containers_interface.AttributeContainerIdentifier):
          continue

        event_tag_values[attribute_name] = attribute_value

      field_values['tag'] = event_tag_values

    return field_values

  @abc.abstractmethod
  def _WriteFieldValues(self, output_mediator, field_values):
    """Writes field values to the output.

    Args:
      output_mediator (OutputMediator): mediates interactions between output
          modules and other components, such as storage and dfVFS.
      field_values (dict[str, str]): output field values per name.
    """
