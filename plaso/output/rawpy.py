# -*- coding: utf-8 -*-
"""Output module for the native (or "raw") Python format."""

from acstore.containers import interface as containers_interface

from dfdatetime import interface as dfdatetime_interface
from dfdatetime import posix_time as dfdatetime_posix_time

from plaso.output import dynamic
from plaso.output import logger
from plaso.output import manager
from plaso.output import text_file


class NativePythonOutputModule(text_file.TextFileOutputModule):
  """Output module for native (or "raw") Python output format."""

  NAME = 'rawpy'
  DESCRIPTION = 'native (or "raw") Python output.'

  # TODO: remove attributes that are no longer considered reserved.
  _RESERVED_ATTRIBUTES = frozenset([
      'body',
      'data_type',
      'display_name',
      'filename',
      'hostname',
      'http_headers',
      'inode',
      'mapped_files',
      'metadata',
      'offset',
      'parser',
      'pathspec',
      'query',
      'source_long',
      'source_short',
      'tag',
      'timestamp',
      'timestamp_desc',
      'timezone',
      'username'])

  def __init__(self):
    """Initializes an output module."""
    super(NativePythonOutputModule, self).__init__()
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
    event_identifier = event.GetIdentifier()
    event_identifier_string = event_identifier.CopyToString()

    date_time = dfdatetime_posix_time.PosixTimeInMicroseconds(
        timestamp=event.timestamp)
    date_time_string = date_time.CopyToDateTimeStringISO8601()

    field_values = {
        '_event_identifier': event_identifier_string,
        '_timestamp': date_time_string}

    event_attributes = list(event_data.GetAttributes())
    if event_data_stream:
      event_attributes.extend(event_data_stream.GetAttributes())

    for attribute_name, attribute_value in sorted(event_attributes):
      # Ignore attribute container identifier and date and time values.
      if isinstance(attribute_value, (
          containers_interface.AttributeContainerIdentifier,
          dfdatetime_interface.DateTimeValues)):
        continue

      if (isinstance(attribute_value, list) and attribute_value and
          isinstance(attribute_value[0],
                     dfdatetime_interface.DateTimeValues)):
        continue

      # Some parsers have written bytes values to storage.
      if isinstance(attribute_value, bytes):
        attribute_value = attribute_value.decode('utf-8', 'replace')
        logger.warning(
            'Found bytes value for attribute "{0:s}" for data type: '
            '{1!s}. Value was converted to UTF-8: "{2:s}"'.format(
                attribute_name, event_data.data_type, attribute_value))

      # Output _parser_chain as parser for backwards compatibility.
      if attribute_name == '_parser_chain':
        attribute_name = 'parser'

      field_values[attribute_name] = attribute_value

    if 'display_name' not in field_values:
      field_values['display_name'] = (
          self._field_formatting_helper.GetFormattedField(
              output_mediator, 'display_name', event, event_data,
              event_data_stream, event_tag))

    if 'filename' not in field_values:
      field_values['filename'] = (
          self._field_formatting_helper.GetFormattedField(
              output_mediator, 'filename', event, event_data, event_data_stream,
              event_tag))

    if 'inode' not in field_values:
      field_values['inode'] = self._field_formatting_helper.GetFormattedField(
          output_mediator, 'inode', event, event_data, event_data_stream,
          event_tag)

    if event_tag:
      field_values['_event_tag_labels'] = event_tag.labels

    return field_values

  def _GetString(self, field_values):
    """Retrieves an output string.

    Args:
      field_values (dict[str, str]): output field values per name.

    Returns:
      str: output string.
    """
    reserved_attributes = []
    additional_attributes = []

    for field_name, field_value in sorted(field_values.items()):
      if field_name in (
          '_event_identifier', '_event_tag_labels', '_timestamp', 'path_spec'):
        continue

      field_string = '  {{{0!s}}} {1!s}'.format(field_name, field_value)

      if field_name in self._RESERVED_ATTRIBUTES:
        reserved_attributes.append(field_string)
      else:
        additional_attributes.append(field_string)

    lines_of_text = [
        '+-' * 40,
        '[Timestamp]:',
        '  {0:s}'.format(field_values['_timestamp'])]

    path_specification = field_values.get('path_spec', None)
    if path_specification:
      lines_of_text.extend([
          '',
          '[Pathspec]:'])
      lines_of_text.extend([
          '  {0:s}'.format(line)
          for line in path_specification.comparable.split('\n')])

      # Remove additional empty line.
      lines_of_text.pop()

    lines_of_text.extend([
        '',
        '[Reserved attributes]:'])
    lines_of_text.extend(reserved_attributes)

    lines_of_text.extend([
        '',
        '[Additional attributes]:'])
    lines_of_text.extend(additional_attributes)

    event_tag_labels = field_values.get('_event_tag_labels', None)
    if event_tag_labels:
      labels = ', '.join([
          '\'{0:s}\''.format(label) for label in event_tag_labels])
      lines_of_text.extend([
          '',
          '[Tag]:',
          '  {{labels}} [{0:s}]'.format(labels)])

    lines_of_text.append('')

    return '\n'.join(lines_of_text)

  def _WriteFieldValues(self, output_mediator, field_values):
    """Writes field values to the output.

    Args:
      output_mediator (OutputMediator): mediates interactions between output
          modules and other components, such as storage and dfVFS.
      field_values (dict[str, str]): output field values per name.
    """
    output_text = self._GetString(field_values)

    self.WriteLine(output_text)


manager.OutputManager.RegisterOutput(NativePythonOutputModule)
