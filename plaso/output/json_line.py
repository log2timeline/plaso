# -*- coding: utf-8 -*-
"""An output module that saves data into a JSON line format.

JSON line format is a single JSON entry or event per line instead
of grouping all the output into a single JSON entity.
"""

from plaso.lib import errors
from plaso.output import interface
from plaso.output import manager
from plaso.serializer import json_serializer


class JSONLineOutputModule(interface.LinearOutputModule):
  """Output module for the JSON line format."""

  NAME = u'json_line'
  DESCRIPTION = u'Saves the events into a JSON line format.'

  def WriteEventBody(self, event_object):
    """Writes the body of an event object to the output.

    Args:
      event_object: the event object (instance of EventObject).
    """
    try:
      message, _ = self._output_mediator.GetFormattedMessages(event_object)
    except errors.WrongFormatter:
      message = None

    if message:
      event_object.message = message

    self._WriteLine(json_serializer.JSONEventObjectSerializer.WriteSerialized(
        event_object))
    self._WriteLine(u'\n')


manager.OutputManager.RegisterOutput(JSONLineOutputModule)
