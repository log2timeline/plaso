# -*- coding: utf-8 -*-
"""An output module that doesn't output anything."""

from plaso.output import interface
from plaso.output import manager


class NullOutputModule(interface.OutputModule):
  """An output module that doesn't output anything."""

  NAME = u'null'
  DESCRIPTION = u'An output module that doesn\'t output anything.'

  def WriteEventBody(self, event_object):
    """Writes the body of an event object to the output.

    Args:
      event_object: the event object (instance of EventObject).
    """
    pass


manager.OutputManager.RegisterOutput(NullOutputModule)
