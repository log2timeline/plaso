# -*- coding: utf-8 -*-
"""Output module for the "raw" (or native) Python format."""

from __future__ import unicode_literals

from dfdatetime import posix_time as dfdatetime_posix_time

from plaso.lib import definitions
from plaso.lib import py2to3
from plaso.output import interface
from plaso.output import logger
from plaso.output import manager


class NativePythonFormatterHelper(object):
  """Helper for outputting as "raw" (or native) Python."""

  @classmethod
  def GetFormattedEvent(cls, event, event_data, event_tag):
    """Retrieves a string representation of the event.

    Args:
      event (EventObject): event.
      event_data (EventData): event data.
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

    pathspec = getattr(event_data, 'pathspec', None)
    if pathspec:
      lines_of_text.extend([
          '',
          '[Pathspec]:'])
      lines_of_text.extend([
          '  {0:s}'.format(line) for line in pathspec.comparable.split('\n')])

      # Remove additional empty line.
      lines_of_text.pop()

    reserved_attributes = [
        '',
        '[Reserved attributes]:']
    additional_attributes = [
        '',
        '[Additional attributes]:']

    for attribute_name, attribute_value in sorted(event_data.GetAttributes()):
      # Some parsers have written bytes values to storage.
      if isinstance(attribute_value, py2to3.BYTES_TYPE):
        attribute_value = attribute_value.decode('utf-8', 'replace')
        logger.warning(
            'Found bytes value for attribute "{0:s}" for data type: '
            '{1!s}. Value was converted to UTF-8: "{2:s}"'.format(
                attribute_name, event_data.data_type, attribute_value))

      if attribute_name == 'pathspec':
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

    lines_of_text.extend(['', ''])

    return '\n'.join(lines_of_text)


class NativePythonOutputModule(interface.LinearOutputModule):
  """Output module for the "raw" (or native) Python output format."""

  NAME = 'rawpy'
  DESCRIPTION = '"raw" (or native) Python output.'

  def WriteEventBody(self, event, event_data, event_tag):
    """Writes event values to the output.

    Args:
      event (EventObject): event.
      event_data (EventData): event data.
      event_tag (EventTag): event tag.
    """
    output_string = NativePythonFormatterHelper.GetFormattedEvent(
        event, event_data, event_tag)
    self._output_writer.Write(output_string)


manager.OutputManager.RegisterOutput(NativePythonOutputModule)
