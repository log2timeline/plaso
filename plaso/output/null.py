# -*- coding: utf-8 -*-
"""Null device output module."""

from plaso.output import interface
from plaso.output import manager


class NullOutputModule(interface.OutputModule):
  """Null device output module."""

  NAME = u'null'
  DESCRIPTION = u'Output module that does not output anything.'

  def WriteEventBody(self, unused_event_object):
    """Writes the body of an event object to a null device.

    Args:
      event_object: the event object (instance of EventObject).
    """
    pass


manager.OutputManager.RegisterOutput(NullOutputModule)
