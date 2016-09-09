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

  def WriteEventBody(self, event):
    """Writes the body of an event object to the output.

    Args:
      event (EventObject): event.
    """
    inode = getattr(event, u'inode', None)
    if inode is None:
      event.inode = 0

    try:
      message, _ = self._output_mediator.GetFormattedMessages(event)
    except errors.WrongFormatter:
      message = None

    if message:
      event.message = message

    json_string = (
        json_serializer.JSONAttributeContainerSerializer.WriteSerialized(event))
    self._WriteLine(json_string)
    self._WriteLine(u'\n')


manager.OutputManager.RegisterOutput(JSONLineOutputModule)
