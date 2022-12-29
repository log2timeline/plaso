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

  def _GetFormattedEventNativePython(
      self, output_mediator, event, event_data, event_data_stream, event_tag):
    """Retrieves a native Python string representation of the event.

    Args:
      output_mediator (OutputMediator): mediates interactions between output
          modules and other components, such as storage and dfVFS.
      event (EventObject): event.
      event_data (EventData): event data.
      event_data_stream (EventDataStream): event data stream.
      event_tag (EventTag): event tag.

    Returns:
      str: string representation of the event.
    """
    date_time = dfdatetime_posix_time.PosixTimeInMicroseconds(
        timestamp=event.timestamp)
    date_time_string = date_time.CopyToDateTimeStringISO8601()

    lines_of_text = [
        '+-' * 40,
        '[Timestamp]:',
        '  {0:s}'.format(date_time_string)]

    path_specification = getattr(event_data_stream, 'path_spec', None)
    if not path_specification:
      # Note that support for event_data.pathspec is kept for backwards
      # compatibility.
      path_specification = getattr(event_data, 'pathspec', None)

    if path_specification:
      lines_of_text.extend([
          '',
          '[Pathspec]:'])
      lines_of_text.extend([
          '  {0:s}'.format(line)
          for line in path_specification.comparable.split('\n')])

      # Remove additional empty line.
      lines_of_text.pop()

    reserved_attributes = [
        '',
        '[Reserved attributes]:']
    additional_attributes = [
        '',
        '[Additional attributes]:']

    event_attributes = list(event_data.GetAttributes())
    if event_data_stream:
      event_attributes.extend(event_data_stream.GetAttributes())

    event_attribute_names = [name for name, _ in event_attributes]

    if 'display_name' not in event_attribute_names:
      attribute_value = self._field_formatting_helper.GetFormattedField(
          output_mediator, 'display_name', event, event_data, event_data_stream,
          event_tag)
      event_attributes.append(('display_name', attribute_value))

    if 'filename' not in event_attribute_names:
      attribute_value = self._field_formatting_helper.GetFormattedField(
          output_mediator, 'filename', event, event_data, event_data_stream,
          event_tag)
      event_attributes.append(('filename', attribute_value))

    if 'inode' not in event_attribute_names:
      attribute_value = self._field_formatting_helper.GetFormattedField(
          output_mediator, 'inode', event, event_data, event_data_stream,
          event_tag)
      event_attributes.append(('inode', attribute_value))

    for attribute_name, attribute_value in sorted(event_attributes):
      # Ignore attribute container identifier values.
      if isinstance(attribute_value,
                    containers_interface.AttributeContainerIdentifier):
        continue

      # Ignore date and time values.
      if isinstance(attribute_value, dfdatetime_interface.DateTimeValues):
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

      # Note that support for event_data.pathspec is kept for backwards
      # compatibility. The current value is event_data_stream.path_spec.
      if attribute_name in ('path_spec', 'pathspec'):
        continue

      attribute_string = '  {{{0!s}}} {1!s}'.format(
          attribute_name, attribute_value)

      if attribute_name in definitions.RESERVED_VARIABLE_NAMES:
        reserved_attributes.append(attribute_string)
      else:
        additional_attributes.append(attribute_string)

    lines_of_text.extend(reserved_attributes)
    lines_of_text.extend(additional_attributes)

    if event_tag:
      labels = [
          '\'{0:s}\''.format(label) for label in event_tag.labels]
      lines_of_text.extend([
          '',
          '[Tag]:',
          '  {{labels}} [{0:s}]'.format(', '.join(labels))])

    lines_of_text.append('')

    return '\n'.join(lines_of_text)

  def GetFormattedEvent(
      self, output_mediator, event, event_data, event_data_stream, event_tag):
    """Retrieves a string representation of the event.

    Args:
      output_mediator (OutputMediator): mediates interactions between output
          modules and other components, such as storage and dfVFS.
      event (EventObject): event.
      event_data (EventData): event data.
      event_data_stream (EventDataStream): event data stream.
      event_tag (EventTag): event tag.

    Returns:
      str: string representation of the event.
    """
    return self._GetFormattedEventNativePython(
        output_mediator, event, event_data, event_data_stream, event_tag)


class NativePythonOutputModule(interface.TextFileOutputModule):
  """Output module for native (or "raw") Python output format."""

  NAME = 'rawpy'
  DESCRIPTION = 'native (or "raw") Python output.'

  def __init__(self):
    """Initializes an output module."""
    event_formatting_helper = NativePythonEventFormattingHelper()
    super(NativePythonOutputModule, self).__init__(event_formatting_helper)


manager.OutputManager.RegisterOutput(NativePythonOutputModule)
