# -*- coding: utf-8 -*-
"""Output module that saves data into a JSON line format.

JSON line format is a single JSON entry or event per line instead
of grouping all the output into a single JSON entity.
"""

from __future__ import unicode_literals

from plaso.output import manager
from plaso.output import shared_json


class JSONLineOutputModule(shared_json.SharedJSONOutputModule):
  """Output module for the JSON line format."""

  NAME = 'json_line'
  DESCRIPTION = 'Saves the events into a JSON line format.'

  def WriteEventBody(self, event, event_data, event_tag):
    """Writes event values to the output.

    Args:
      event (EventObject): event.
      event_data (EventData): event data.
      event_tag (EventTag): event tag.
    """
    json_string = self._WriteSerialized(event, event_data, event_tag)

    self._output_writer.Write(json_string)
    self._output_writer.Write('\n')


manager.OutputManager.RegisterOutput(JSONLineOutputModule)
