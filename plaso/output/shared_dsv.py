# -*- coding: utf-8 -*-
"""Shared functionality for delimiter separated values output modules."""

from __future__ import unicode_literals

from plaso.output import interface


class DSVOutputModule(interface.LinearOutputModule):
  """Shared functionality for delimiter separated values output modules."""

  def __init__(
      self, output_mediator, formatting_helper, names, delimiter=',',
      header=None):
    """Initializes an output module object.

    Args:
      output_mediator (OutputMediator): an output mediator.
      formatting_helper (FieldFormattingHelper): field formatting helper.
      names (list[str]): names of the fields to output.
      delimiter (Optional[str]): field delimiter.
      header (Optional[str]): header, where None will have WriteHeader
          generate a header from the field names.
    """
    super(DSVOutputModule, self).__init__(output_mediator)
    self._field_delimiter = delimiter
    self._field_names = names
    self._field_formatting_helper = formatting_helper
    self._header = header

  def _SanitizeField(self, field):
    """Sanitizes a field for output.

    This method replaces any field delimiters with a space.

    Args:
      field (str): name of the field to sanitize.

    Returns:
      str: value of the field.
    """
    if self._field_delimiter and isinstance(field, str):
      return field.replace(self._field_delimiter, ' ')
    return field

  def SetFieldDelimiter(self, field_delimiter):
    """Sets the field delimiter.

    Args:
      field_delimiter (str): field delimiter.
    """
    self._field_delimiter = field_delimiter

  def SetFields(self, names):
    """Sets the names of the fields to output.

    Args:
      names (list[str]): names of the fields to output.
    """
    self._field_names = names

  def WriteEventBody(self, event, event_data, event_data_stream, event_tag):
    """Writes event values to the output.

    Args:
      event (EventObject): event.
      event_data (EventData): event data.
      event_data_stream (EventDataStream): event data stream.
      event_tag (EventTag): event tag.
    """
    output_values = []
    for field_name in self._field_names:
      output_value = self._field_formatting_helper.GetFormattedField(
          field_name, event, event_data, event_data_stream, event_tag)

      output_value = self._SanitizeField(output_value)
      output_values.append(output_value)

    output_line = '{0:s}\n'.format(self._field_delimiter.join(output_values))
    self._output_writer.Write(output_line)

  def WriteHeader(self):
    """Writes the header to the output."""
    if self._header:
      output_text = self._header
    else:
      output_text = self._field_delimiter.join(self._field_names)

    output_text = '{0:s}\n'.format(output_text)
    self._output_writer.Write(output_text)
