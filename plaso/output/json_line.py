# -*- coding: utf-8 -*-
"""Output module that saves data into a JSON line format.

JSON line format is a single JSON entry or event per line instead
of grouping all the output into a single JSON entity.
"""

import json

from plaso.output import interface
from plaso.output import manager
from plaso.output import shared_json


class JSONLineOutputModule(interface.TextFileOutputModule):
  """Output module for the JSON line format."""

  NAME = 'json_line'
  DESCRIPTION = 'Saves the events into a JSON line format.'

  def __init__(self):
    """Initializes an output module."""
    event_formatting_helper = shared_json.JSONEventFormattingHelper()
    super(JSONLineOutputModule, self).__init__(event_formatting_helper)

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

    output_text = json.dumps(field_values, sort_keys=True)

    self.WriteLine(output_text)


manager.OutputManager.RegisterOutput(JSONLineOutputModule)
