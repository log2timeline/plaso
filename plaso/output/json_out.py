# -*- coding: utf-8 -*-
"""Output module that saves data into a JSON format."""

import json

from plaso.output import manager
from plaso.output import shared_json


class JSONOutputModule(shared_json.SharedJSONOutputModule):
  """Output module for the JSON format."""

  NAME = 'json'
  DESCRIPTION = 'Saves the events into a JSON format.'

  def __init__(self):
    """Initializes an output module."""
    super(JSONOutputModule, self).__init__()
    self._event_counter = 0

  def _WriteFieldValues(self, output_mediator, field_values):
    """Writes field values to the output.

    Args:
      output_mediator (OutputMediator): mediates interactions between output
          modules and other components, such as storage and dfVFS.
      field_values (dict[str, str]): output field values per name.
    """
    if self._event_counter != 0:
      self.WriteText(', ')

    json_string = json.dumps(field_values, sort_keys=True)
    output_text = '"event_{0:d}": {1:s}\n'.format(
        self._event_counter, json_string)
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
