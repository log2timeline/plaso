# -*- coding: utf-8 -*-
"""Output module for the native (or "raw") Python format."""

from dfdatetime import interface as dfdatetime_interface
from dfdatetime import posix_time as dfdatetime_posix_time

from plaso.containers import interface as containers_interface
from plaso.lib import definitions
from plaso.output import dynamic
from plaso.output import formatting_helper
from plaso.output import interface
from plaso.output import logger
from plaso.output import manager


class NativePythonEventFormattingHelper(
    formatting_helper.EventFormattingHelper):
  """Native (or "raw") Python output module event formatting helper."""

  def __init__(self):
    """Initializes a Native Python output module event formatting helper."""
    super(NativePythonEventFormattingHelper, self).__init__()
    self._field_formatting_helper = dynamic.DynamicFieldFormattingHelper()

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
    date_time = dfdatetime_posix_time.PosixTimeInMicroseconds(
        timestamp=event.timestamp)
    date_time_string = date_time.CopyToDateTimeStringISO8601()

    field_values = {'timestamp': date_time_string}

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

    return field_values


class NativePythonOutputModule(interface.TextFileOutputModule):
  """Output module for native (or "raw") Python output format."""

  NAME = 'rawpy'
  DESCRIPTION = 'native (or "raw") Python output.'

  def __init__(self):
    """Initializes an output module."""
    event_formatting_helper = NativePythonEventFormattingHelper()
    super(NativePythonOutputModule, self).__init__(event_formatting_helper)

  def WriteEventBody(
      self, output_mediator, event, event_data, event_data_stream, event_tag):
    """Writes event values to the output.

    Args:
      output_mediator (OutputMediator): mediates interactions between output
          modules and other components, such as storage and dfVFS.
      event (EventObject): event.
      event_data (EventData): event data.
      event_data_stream (EventDataStream): event data stream.
      event_tag (EventTag): event tag.
    """
    field_values = self._event_formatting_helper.GetFieldValues(
      output_mediator, event, event_data, event_data_stream, event_tag)

    reserved_attributes = []
    additional_attributes = []

    for field_name, field_value in sorted(field_values.items()):
      if field_name in ('path_spec', 'timestamp'):
        continue

      field_string = '  {{{0!s}}} {1!s}'.format(field_name, field_value)

      if field_name in definitions.RESERVED_VARIABLE_NAMES:
        reserved_attributes.append(field_string)
      else:
        additional_attributes.append(field_string)

    lines_of_text = [
        '+-' * 40,
        '[Timestamp]:',
        '  {0:s}'.format(field_values['timestamp'])]

    if field_values['path_spec']:
      lines_of_text.extend([
          '',
          '[Pathspec]:'])
      lines_of_text.extend([
          '  {0:s}'.format(line)
          for line in field_values['path_spec'].comparable.split('\n')])

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

    if event_tag:
      labels = [
          '\'{0:s}\''.format(label) for label in event_tag.labels]
      lines_of_text.extend([
          '',
          '[Tag]:',
          '  {{labels}} [{0:s}]'.format(', '.join(labels))])

    lines_of_text.append('')

    output_text = '\n'.join(lines_of_text)

    self.WriteLine(output_text)


manager.OutputManager.RegisterOutput(NativePythonOutputModule)
