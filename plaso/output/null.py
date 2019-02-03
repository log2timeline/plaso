# -*- coding: utf-8 -*-
"""Null device output module."""

from __future__ import unicode_literals

from plaso.output import interface
from plaso.output import manager


class NullOutputModule(interface.OutputModule):
  """Null device output module."""

  NAME = 'null'
  DESCRIPTION = 'Output module that does not output anything.'

  # pylint: disable=unused-argument
  def WriteEventBody(self, event):
    """Writes the event object to the output.

    Since this is the null output module nothing is actually written.

    Args:
      event (EventObject): event.
    """
    return


manager.OutputManager.RegisterOutput(NullOutputModule)
