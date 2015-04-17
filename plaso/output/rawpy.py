# -*- coding: utf-8 -*-
"""Output module for the "raw" (or native) Python format."""

from plaso.output import interface
from plaso.output import manager


class NativePythonOutputModule(interface.LinearOutputModule):
  """Output module for the "raw" (or native) Python output format."""

  NAME = u'rawpy'
  DESCRIPTION = u'"raw" (or native) Python output.'

  def WriteEventBody(self, event_object):
    """Writes the body of an event object to the output.

    Args:
      event_object: the event object (instance of EventObject).
    """
    self._file_object.filehandle.WriteLine(event_object.GetString())


manager.OutputManager.RegisterOutput(NativePythonOutputModule)
