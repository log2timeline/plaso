# -*- coding: utf-8 -*-
"""Shared functionality for delimiter separated values output modules."""

import collections

from plaso.output import formatting_helper
from plaso.output import text_file


class DSVEventFormattingHelper(formatting_helper.EventFormattingHelper):
  """Delimiter separated values output module event formatting helper.

  Attributes:
    field_delimiter (str): field delimiter.
  """

  def __init__(self, field_formatting_helper, field_names, field_delimiter=','):
    """Initializes a delimiter separated values event formatting helper.

    Args:
      field_formatting_helper (FieldFormattingHelper): field formatting helper.
      field_names (list[str]): names of the fields to output.
      field_delimiter (Optional[str]): field delimiter.
    """
    super(DSVEventFormattingHelper, self).__init__()
    self._custom_fields = {}
    self._field_names = field_names
    self._field_formatting_helper = field_formatting_helper

    self.field_delimiter = field_delimiter

  def _SanitizeField(self, field):
    """Sanitizes a field for output.

    This method replaces any field delimiters with a space.

    Args:
      field (str): value of the field to sanitize.

    Returns:
      str: sanitized value of the field.
    """
    if self.field_delimiter and isinstance(field, str):
      return field.replace(self.field_delimiter, ' ')
    return field

  def GetFieldValues(
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
    field_values = collections.OrderedDict()
    for field_name in self._field_names:
      field_value = self._field_formatting_helper.GetFormattedField(
          output_mediator, field_name, event, event_data, event_data_stream,
          event_tag)

      if field_value is None and field_name in self._custom_fields:
        field_value = self._custom_fields.get(field_name, None)

      if field_value is None:
        field_value = '-'

      field_value = self._SanitizeField(field_value)
      field_values[field_name] = field_value

    return field_values

  def GetFormattedFieldNames(self):
    """Retrieves a string representation of the field names.

    Returns:
      str: string representation of the field names.
    """
    return self.field_delimiter.join(self._field_names)

  def SetAdditionalFields(self, field_names):
    """Sets the names of additional fields to output.

    Args:
      field_names (list[str]): names of additional fields to output.
    """
    self._field_names.extend(field_names)

  def SetCustomFields(self, field_names_and_values):
    """Sets the names and values of custom fields to output.

    Args:
      field_names_and_values (list[tuple[str, str]]): names and values of
          custom fields to output.
    """
    self._custom_fields = dict(field_names_and_values)
    self._field_names.extend(self._custom_fields.keys())

  def SetFieldDelimiter(self, field_delimiter):
    """Sets the field delimiter.

    Args:
      field_delimiter (str): field delimiter.
    """
    self.field_delimiter = field_delimiter

  def SetFields(self, field_names):
    """Sets the names of the fields to output.

    Args:
      field_names (list[str]): names of the fields to output.
    """
    self._field_names = field_names


class DSVOutputModule(text_file.SortedTextFileOutputModule):
  """Shared functionality for delimiter separated values output modules."""

  def __init__(
      self, field_formatting_helper, names, delimiter=',', header=None):
    """Initializes a delimiter separated values output module.

    Args:
      field_formatting_helper (FieldFormattingHelper): field formatting helper.
      names (list[str]): names of the fields to output.
      delimiter (Optional[str]): field delimiter.
      header (Optional[str]): header, where None will have WriteHeader
          generate a header from the field names.
    """
    event_formatting_helper = DSVEventFormattingHelper(
        field_formatting_helper, names, field_delimiter=delimiter)
    super(DSVOutputModule, self).__init__(event_formatting_helper)
    self._header = header

  def _GetString(self, output_mediator, field_values):
    """Retrieves an output string.

    Args:
      output_mediator (OutputMediator): mediates interactions between output
          modules and other components, such as storage and dfVFS.
      field_values (dict[str, str]): output field values per name.

    Returns:
      str: output string.
    """
    output_text = self._event_formatting_helper.field_delimiter.join(
        field_values.values())
    return ''.join([output_text, '\n'])

  def SetAdditionalFields(self, field_names):
    """Sets the names of additional fields to output.

    Args:
      field_names (list[str]): names of additional fields to output.
    """
    self._event_formatting_helper.SetAdditionalFields(field_names)

  def SetCustomFields(self, field_names_and_values):
    """Sets the names and values of custom fields to output.

    Args:
      field_names_and_values (list[tuple[str, str]]): names and values of
          custom fields to output.
    """
    self._event_formatting_helper.SetCustomFields(field_names_and_values)

  def SetFieldDelimiter(self, field_delimiter):
    """Sets the field delimiter.

    Args:
      field_delimiter (str): field delimiter.
    """
    self._event_formatting_helper.SetFieldDelimiter(field_delimiter)

  def SetFields(self, field_names):
    """Sets the names of the fields to output.

    Args:
      field_names (list[str]): names of the fields to output.
    """
    self._event_formatting_helper.SetFields(field_names)

  def WriteHeader(self, output_mediator):
    """Writes the header to the output.

    Args:
      output_mediator (OutputMediator): mediates interactions between output
          modules and other components, such as storage and dfVFS.
    """
    if self._header:
      output_text = self._header
    else:
      output_text = self._event_formatting_helper.GetFormattedFieldNames()

    self.WriteLine(output_text)
