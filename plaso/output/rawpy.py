# -*- coding: utf-8 -*-
"""Output module for the "raw" (or native) Python format."""

from __future__ import unicode_literals

from plaso.lib import definitions
from plaso.lib import timelib
from plaso.output import interface
from plaso.output import manager


class NativePythonFormatterHelper(object):
  """Helper for outputting as "raw" (or native) Python."""

  @classmethod
  def GetFormattedEventObject(cls, event):
    """Retrieves a string representation of the event.

    Args:
      event (EventObject): event.

    Returns:
      str: string representation of the event.
    """
    time_string = timelib.Timestamp.CopyToIsoFormat(event.timestamp)

    lines_of_text = [
        '+-' * 40,
        '[Timestamp]:',
        '  {0:s}'.format(time_string)]

    pathspec = getattr(event, 'pathspec', None)
    if pathspec:
      lines_of_text.append('[Pathspec]:')
      attribute_string = pathspec.comparable.replace('\n', '\n  ')
      attribute_string = '  {0:s}\n'.format(attribute_string)
      lines_of_text.append(attribute_string)

    # TODO: add support for event tag after event clean up.

    lines_of_text.append('[Reserved attributes]:')
    out_additional = ['[Additional attributes]:']

    for attribute_name, attribute_value in sorted(event.GetAttributes()):
      if attribute_name not in definitions.RESERVED_VARIABLE_NAMES:
        attribute_string = '  {{{0!s}}} {1!s}'.format(
            attribute_name, attribute_value)
        out_additional.append(attribute_string)

      elif attribute_name not in ('pathspec', 'tag'):
        attribute_string = '  {{{0!s}}} {1!s}'.format(
            attribute_name, attribute_value)
        lines_of_text.append(attribute_string)

    lines_of_text.append('')
    out_additional.append('')

    lines_of_text.extend(out_additional)
    return '\n'.join(lines_of_text)


class NativePythonOutputModule(interface.LinearOutputModule):
  """Output module for the "raw" (or native) Python output format."""

  NAME = 'rawpy'
  DESCRIPTION = '"raw" (or native) Python output.'

  def WriteEventBody(self, event):
    """Writes the body of an event to the output.

    Args:
      event (EventObject): event.
    """
    output_string = NativePythonFormatterHelper.GetFormattedEventObject(event)
    self._output_writer.Write(output_string)


manager.OutputManager.RegisterOutput(NativePythonOutputModule)
