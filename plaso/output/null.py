# -*- coding: utf-8 -*-
"""Null device output module."""

from __future__ import unicode_literals

from plaso.output import interface
from plaso.output import manager


class NullOutputModule(interface.OutputModule):
  """Null device output module."""

  NAME = 'null'
  DESCRIPTION = 'Output module that does not output anything.'

  def WriteEventBody(self, unused_event_object):
    """Writes the event object to the output.

    Since this is the null output module nothing is actually written.

    Args:
      event_object (EventObject): event object.
    """
    pass


manager.OutputManager.RegisterOutput(NullOutputModule)
