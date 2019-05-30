# -*- coding: utf-8 -*-
"""Output module that saves data into a JSON format."""

from __future__ import unicode_literals

import copy
import json

from plaso.output import interface
from plaso.output import manager
from plaso.serializer import json_serializer


class JSONOutputModule(interface.LinearOutputModule):
  """Output module for the JSON format."""

  NAME = 'json'
  DESCRIPTION = 'Saves the events into a JSON format.'

  _JSON_SERIALIZER = json_serializer.JSONAttributeContainerSerializer

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
    # TODO: since the internal serializer can change move functionality
    # to serialize into a shared json output module class.
    # TODO: refactor to separately serialize event and event data
    copy_of_event = copy.deepcopy(event)
    for attribute_name, attribute_value in event_data.GetAttributes():
      setattr(copy_of_event, attribute_name, attribute_value)

    copy_of_event.tag = event_tag

    inode = getattr(event_data, 'inode', None)
    if inode is None:
      copy_of_event.inode = 0

    json_dict = self._JSON_SERIALIZER.WriteSerializedDict(copy_of_event)
    json_string = json.dumps(json_dict, sort_keys=True)

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
