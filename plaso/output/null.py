# -*- coding: utf-8 -*-
"""An output module that doesn't output anything."""
from plaso.output import interface
from plaso.output import manager


# We don't need to implement any functionality here, so the methods in
# the interface don't need to be overwritten.
# pylint: disable=abstract-method
class NullOutputModule(interface.OutputModule):
  """An output module that doesn't output anything."""

  NAME = u'null'
  DESCRIPTION = u'An output module that doesn\'t output anything.'


manager.OutputManager.RegisterOutput(NullOutputModule)
