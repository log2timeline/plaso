# -*- coding: utf-8 -*-
"""Output module that saves data into a JSON format."""

from plaso.output import interface
from plaso.output import manager
from plaso.output import shared_json


class JSONOutputModule(interface.TextFileOutputModule):
  """Output module for the JSON format."""

  NAME = 'json'
  DESCRIPTION = 'Saves the events into a JSON format.'

  def __init__(self):
    """Initializes an output module."""
    event_formatting_helper = shared_json.JSONEventFormattingHelper()
    super(JSONOutputModule, self).__init__(event_formatting_helper)
    self._event_counter = 0

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
    output_text = self._event_formatting_helper.GetFormattedEvent(
        output_mediator, event, event_data, event_data_stream, event_tag)

    if self._event_counter != 0:
      self.WriteText(', ')

    output_text = '"event_{0:d}": {1:s}\n'.format(
        self._event_counter, output_text)
    self.WriteText(output_text)

    self._event_counter += 1

  def WriteFooter(self):
    """Writes the footer to the output."""
    self.WriteText('}')

  def WriteHeader(self, output_mediator):
    """Writes the header to the output.

    Args:
      output_mediator (OutputMediator): mediates interactions between output
          modules and other components, such as storage and dfVFS.
    """
    self.WriteText('{')
    self._event_counter = 0


manager.OutputManager.RegisterOutput(JSONOutputModule)
