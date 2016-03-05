# -*- coding: utf-8 -*-
"""Output module for the "raw" (or native) Python format."""

from plaso.lib import definitions
from plaso.lib import timelib
from plaso.output import interface
from plaso.output import manager


class NativePythonFormatterHelper(object):
  """Helper for outputting as "raw" (or native) Python."""

  @classmethod
  def GetFormattedEventObject(cls, event_object):
    """Retrieves a string representation of the event object.

    Returns:
      A Unicode string containing the string representation of the event object.
    """
    time_string = timelib.Timestamp.CopyToIsoFormat(event_object.timestamp)

    lines_of_text = [
        u'+-' * 40,
        u'[Timestamp]:',
        u'  {0:s}'.format(time_string)]

    pathspec = getattr(event_object, u'pathspec', None)
    if pathspec:
      lines_of_text.append(u'[Pathspec]:')
      attribute_string = pathspec.comparable.replace(u'\n', u'\n  ')
      attribute_string = u'  {0:s}\n'.format(attribute_string)
      lines_of_text.append(attribute_string)

    lines_of_text.append(u'[Reserved attributes]:')
    out_additional = [u'[Additional attributes]:']

    for attribute_name, attribute_value in sorted(event_object.GetAttributes()):
      if attribute_name not in definitions.RESERVED_VARIABLE_NAMES:
        attribute_string = u'  {{{0!s}}} {1!s}'.format(
            attribute_name, attribute_value)
        out_additional.append(attribute_string)

      elif attribute_name != u'pathspec':
        attribute_string = u'  {{{0!s}}} {1!s}'.format(
            attribute_name, attribute_value)
        lines_of_text.append(attribute_string)

    lines_of_text.append(u'')
    out_additional.append(u'')

    lines_of_text.extend(out_additional)
    return u'\n'.join(lines_of_text)


class NativePythonOutputModule(interface.LinearOutputModule):
  """Output module for the "raw" (or native) Python output format."""

  NAME = u'rawpy'
  DESCRIPTION = u'"raw" (or native) Python output.'

  def WriteEventBody(self, event_object):
    """Writes the body of an event object to the output.

    Args:
      event_object: the event object (instance of EventObject).
    """
    output_string = NativePythonFormatterHelper.GetFormattedEventObject(
        event_object)
    self._WriteLine(output_string)


manager.OutputManager.RegisterOutput(NativePythonOutputModule)
