# -*- coding: utf-8 -*-
"""Output module that saves data into a JSON format."""

from __future__ import unicode_literals

from plaso.output import manager
from plaso.output import shared_json


class JSONOutputModule(shared_json.SharedJSONOutputModule):
  """Output module for the JSON format."""

  NAME = 'json'
  DESCRIPTION = 'Saves the events into a JSON format.'

  def __init__(self, output_mediator):
    """Initializes the output module object.

    Args:
      output_mediator (OutputMediator): mediates interactions between output
          modules and other components, such as storage and dfvfs.
    """
    super(JSONOutputModule, self).__init__(output_mediator)
    self._event_counter = 0

  def WriteEventBody(self, event, event_data, event_tag):
    """Writes event values to the output.

    Args:
      event (EventObject): event.
      event_data (EventData): event data.
      event_tag (EventTag): event tag.
    """
    json_string = self._WriteSerialized(event, event_data, event_tag)

    if self._event_counter != 0:
      self._output_writer.Write(', ')

    line = '"event_{0:d}": {1:s}\n'.format(self._event_counter, json_string)
    self._output_writer.Write(line)

    self._event_counter += 1

  def WriteFooter(self):
    """Writes the footer to the output."""
    self._output_writer.Write('}')

  def WriteHeader(self):
    """Writes the header to the output."""
    self._output_writer.Write('{')
    self._event_counter = 0


manager.OutputManager.RegisterOutput(JSONOutputModule)
