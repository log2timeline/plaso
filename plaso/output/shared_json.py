# -*- coding: utf-8 -*-
"""Shared functionality for JSON based output modules."""

import abc

from acstore.containers import interface as containers_interface

from dfdatetime import interface as dfdatetime_interface

from plaso.output import formatting_helper
from plaso.output import text_file
from plaso.serializer import json_serializer


class JSONFieldFormattingHelper(formatting_helper.FieldFormattingHelper):
  """JSON output module field formatting helper."""

  # Maps the name of a fields to a a callback function that formats
  # the field value.
  _FIELD_FORMAT_CALLBACKS = {
      'display_name': '_FormatDisplayName',
      'filename': '_FormatFilename',
      'inode': '_FormatInode',
      'message': '_FormatMessage',
      'values': '_FormatValues'}

  # The field format callback methods require specific arguments hence
  # the check for unused arguments is disabled here.
  # pylint: disable=unused-argument

  def _FormatValues(
      self, output_mediator, event, event_data, event_data_stream):
    """Formats a values.

    Args:
      output_mediator (OutputMediator): mediates interactions between output
          modules and other components, such as storage and dfVFS.
      event (EventObject): event.
      event_data (EventData): event data.
      event_data_stream (EventDataStream): event data stream.

    Returns:
      list[dict[str, str]]: values field.
    """
    values = event_data.values
    if isinstance(values, list) and event_data.data_type in (
        'windows:registry:key_value', 'windows:registry:service'):
      values = [
          {'data': data, 'data_type': data_type, 'name': name}
          for name, data_type, data in sorted(values)]

    return values

  # pylint: enable=unused-argument

  def GetFormattedField(
      self, output_mediator, field_name, event, event_data, event_data_stream,
      event_tag):
    """Formats the specified field.

    Args:
      output_mediator (OutputMediator): mediates interactions between output
          modules and other components, such as storage and dfVFS.
      field_name (str): name of the field.
      event (EventObject): event.
      event_data (EventData): event data.
      event_data_stream (EventDataStream): event data stream.
      event_tag (EventTag): event tag.

    Returns:
      object: value of the field or None if not available.
    """
    if field_name in self._event_tag_field_names:
      return self._FormatTag(output_mediator, event_tag)

    callback_function = self._callback_functions.get(field_name, None)
    if callback_function:
      output_value = callback_function(
          output_mediator, event, event_data, event_data_stream)
    elif field_name in self._event_data_stream_field_names:
      output_value = getattr(event_data_stream, field_name, None)
    else:
      output_value = getattr(event_data, field_name, None)

    return output_value


class SharedJSONOutputModule(text_file.TextFileOutputModule):
  """Shared functionality for JSON based output modules."""

  _JSON_SERIALIZER = json_serializer.JSONAttributeContainerSerializer

  _GENERATED_FIELD_VALUES = ['display_name', 'filename', 'inode']

  def __init__(self):
    """Initializes an output module."""
    super(SharedJSONOutputModule, self).__init__()
    self._field_formatting_helper = JSONFieldFormattingHelper()

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

        if (isinstance(attribute_value, list) and attribute_value and
            isinstance(attribute_value[0],
                       dfdatetime_interface.DateTimeValues)):
          continue

        # Output _parser_chain as parser for backwards compatibility.
        if attribute_name == '_parser_chain':
          attribute_name = 'parser'

        field_value = self._field_formatting_helper.GetFormattedField(
            output_mediator, attribute_name, event, event_data,
            event_data_stream, event_tag)
        field_values[attribute_name] = field_value

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

    for field_name in self._GENERATED_FIELD_VALUES:
      field_value = field_values.get(field_name, None)
      if field_value is None:
        field_value = self._field_formatting_helper.GetFormattedField(
            output_mediator, field_name, event, event_data, event_data_stream,
            event_tag)
        field_values[field_name] = field_value

    field_values['message'] = self._field_formatting_helper.GetFormattedField(
        output_mediator, 'message', event, event_data, event_data_stream,
        event_tag)

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
