# -*- coding: utf-8 -*-
"""Output module that saves data into a JSON line format.

JSON line format is a single JSON entry or event per line instead
of grouping all the output into a single JSON entity.
"""

from plaso.output import interface
from plaso.output import manager
from plaso.output import shared_json


class JSONLineOutputModule(interface.TextFileOutputModule):
  """Output module for the JSON line format."""

  NAME = 'json_line'
  DESCRIPTION = 'Saves the events into a JSON line format.'

  def __init__(self, output_mediator):
    """Initializes the output module object.

    Args:
      output_mediator (OutputMediator): mediates interactions between output
          modules and other components, such as storage and dfvfs.
    """
    event_formatting_helper = shared_json.JSONEventFormattingHelper(
        output_mediator)
    super(JSONLineOutputModule, self).__init__(
        output_mediator, event_formatting_helper)

  def WriteEventBody(self, event, event_data, event_data_stream, event_tag):
    """Writes event values to the output.

    Args:
      event (EventObject): event.
      event_data (EventData): event data.
      event_data_stream (EventDataStream): event data stream.
      event_tag (EventTag): event tag.
    """
    output_text = self._event_formatting_helper.GetFormattedEvent(
        event, event_data, event_data_stream, event_tag)

    self.WriteLine(output_text)


manager.OutputManager.RegisterOutput(JSONLineOutputModule)
