# -*- coding: utf-8 -*-
"""Shared functionality for delimiter separated values output modules."""

from plaso.output import formatting_helper
from plaso.output import interface


class DSVEventFormattingHelper(formatting_helper.EventFormattingHelper):
  """Delimiter separated values output module event formatting helper."""

  def __init__(
      self, output_mediator, field_formatting_helper, field_names,
      field_delimiter=','):
    """Initializes a delimiter separated values event formatting helper.

    Args:
      output_mediator (OutputMediator): output mediator.
      field_formatting_helper (FieldFormattingHelper): field formatting helper.
      field_names (list[str]): names of the fields to output.
      field_delimiter (Optional[str]): field delimiter.
    """
    super(DSVEventFormattingHelper, self).__init__(output_mediator)
    self._field_delimiter = field_delimiter
    self._field_names = field_names
    self._field_formatting_helper = field_formatting_helper

  def _SanitizeField(self, field):
    """Sanitizes a field for output.

    This method replaces any field delimiters with a space.

    Args:
      field (str): value of the field to sanitize.

    Returns:
      str: sanitized value of the field.
    """
    if self._field_delimiter and isinstance(field, str):
      return field.replace(self._field_delimiter, ' ')
    return field

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
    field_values = []
    for field_name in self._field_names:
      field_value = self._field_formatting_helper.GetFormattedField(
          self._output_mediator, field_name, event, event_data,
          event_data_stream, event_tag)

      field_value = self._SanitizeField(field_value)
      field_values.append(field_value)

    return self._field_delimiter.join(field_values)

  def GetFormattedFieldNames(self):
    """Retrieves a string representation of the field names.

    Returns:
      str: string representation of the field names.
    """
    return self._field_delimiter.join(self._field_names)

  def SetFieldDelimiter(self, field_delimiter):
    """Sets the field delimiter.

    Args:
      field_delimiter (str): field delimiter.
    """
    self._field_delimiter = field_delimiter

  def SetFields(self, field_names):
    """Sets the names of the fields to output.

    Args:
      field_names (list[str]): names of the fields to output.
    """
    self._field_names = field_names


class DSVOutputModule(interface.TextFileOutputModule):
  """Shared functionality for delimiter separated values output modules."""

  def __init__(
      self, output_mediator, field_formatting_helper, names, delimiter=',',
      header=None):
    """Initializes a delimiter separated values output module.

    Args:
      output_mediator (OutputMediator): an output mediator.
      field_formatting_helper (FieldFormattingHelper): field formatting helper.
      names (list[str]): names of the fields to output.
      delimiter (Optional[str]): field delimiter.
      header (Optional[str]): header, where None will have WriteHeader
          generate a header from the field names.
    """
    event_formatting_helper = DSVEventFormattingHelper(
        output_mediator, field_formatting_helper, names,
        field_delimiter=delimiter)
    super(DSVOutputModule, self).__init__(
        output_mediator, event_formatting_helper)
    self._header = header

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

  def WriteHeader(self):
    """Writes the header to the output."""
    if self._header:
      output_text = self._header
    else:
      output_text = self._event_formatting_helper.GetFormattedFieldNames()

    self.WriteLine(output_text)
