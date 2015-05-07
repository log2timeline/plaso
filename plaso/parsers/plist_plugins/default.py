# -*- coding: utf-8 -*-
"""This file contains a default plist plugin in Plaso."""

import datetime
import logging

from plaso.events import plist_event
from plaso.parsers import plist
from plaso.parsers.plist_plugins import interface


class DefaultPlugin(interface.PlistPlugin):
  """Basic plugin to extract keys with timestamps as values from plists."""

  NAME = u'plist_default'
  DESCRIPTION = u'Parser for plist files.'

  def GetEntries(self, parser_mediator, top_level=None, **unused_kwargs):
    """Simple method to exact date values from a Plist.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      top_level: Plist in dictionary form.
    """
    for root, key, value in interface.RecurseKey(top_level):
      if isinstance(value, datetime.datetime):
        event_object = plist_event.PlistEvent(root, key, value)
        parser_mediator.ProduceEvent(event_object)

      # TODO: Binplist keeps a list of offsets but not mapped to a key.
      # adjust code when there is a way to map keys to offsets.

  # TODO: move this into the parser as with the olecf plugins.
  def Process(self, parser_mediator, plist_name, top_level, **kwargs):
    """Overwrite the default Process function so it always triggers.

    Process() checks if the current plist being processed is a match for a
    plugin by comparing the PATH and KEY requirements defined by a plugin.  If
    both match processing continues; else raise WrongPlistPlugin.

    The purpose of the default plugin is to always trigger on any given plist
    file, thus it needs to overwrite the default behavior of comparing PATH
    and KEY.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      plist_name: Name of the plist file.
      top_level: Plist in dictionary form.
    """
    logging.debug(u'Plist {0:s} plugin used for: {1:s}'.format(
        self.NAME, plist_name))
    self.GetEntries(parser_mediator, top_level=top_level, **kwargs)


plist.PlistParser.RegisterPlugin(DefaultPlugin)
