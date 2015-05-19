# -*- coding: utf-8 -*-
"""An output module that saves data into a JSON format."""

from plaso.output import interface
from plaso.output import manager
from plaso.serializer import json_serializer


class JSONOutputModule(interface.LinearOutputModule):
  """Output module for the JSON format."""

  NAME = u'json'
  DESCRIPTION = u'Saves the events into a JSON format.'

  def __init__(self, output_mediator, **kwargs):
    """Initializes the output module object.

    Args:
      output_mediator: The output mediator object (instance of OutputMediator).
    """
    super(JSONOutputModule, self).__init__(output_mediator, **kwargs)
    self._event_counter = 0

  def WriteEventBody(self, event_object):
    """Writes the body of an event object to the output.

    Args:
      event_object: the event object (instance of EventObject).
    """
    json_string = json_serializer.JSONEventObjectSerializer.WriteSerialized(
        event_object)

    if self._event_counter == 0:
      self._WriteLine(u'"event_{0:d}": {1:s}\n'.format(
          self._event_counter, json_string))
    else:
      self._WriteLine(u', "event_{0:d}": {1:s}\n'.format(
          self._event_counter, json_string))

    self._event_counter += 1

  def WriteFooter(self):
    """Writes the footer to the output."""
    self._WriteLine(u'}')

  def WriteHeader(self):
    """Writes the header to the output."""
    self._WriteLine(u'{')
    self._event_counter = 0


manager.OutputManager.RegisterOutput(JSONOutputModule)
