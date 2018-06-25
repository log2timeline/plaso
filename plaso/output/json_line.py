# -*- coding: utf-8 -*-
"""Output module that saves data into a JSON line format.

JSON line format is a single JSON entry or event per line instead
of grouping all the output into a single JSON entity.
"""

from __future__ import unicode_literals

import codecs
import json

from plaso.lib import errors
from plaso.lib import py2to3
from plaso.output import interface
from plaso.output import manager
from plaso.serializer import json_serializer


class JSONLineOutputModule(interface.LinearOutputModule):
  """Output module for the JSON line format."""

  NAME = 'json_line'
  DESCRIPTION = 'Saves the events into a JSON line format.'

  _JSON_SERIALIZER = json_serializer.JSONAttributeContainerSerializer

  def WriteEventBody(self, event):
    """Writes the body of an event object to the output.

    Args:
      event (EventObject): event.
    """
    inode = getattr(event, 'inode', None)
    if inode is None:
      event.inode = 0

    try:
      message, _ = self._output_mediator.GetFormattedMessages(event)
    except errors.WrongFormatter:
      message = None

    if message:
      event.message = message

    json_dict = self._JSON_SERIALIZER.WriteSerializedDict(event)
    json_string = json.dumps(json_dict, sort_keys=True)
    # dumps() returns an ascii-encoded byte string in Python 2.
    if py2to3.PY_2:
      json_string = codecs.decode(json_string, 'ascii')
    self._output_writer.Write(json_string)
    self._output_writer.Write('\n')


manager.OutputManager.RegisterOutput(JSONLineOutputModule)
