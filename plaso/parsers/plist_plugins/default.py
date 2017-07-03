# -*- coding: utf-8 -*-
"""This file contains a default plist plugin in Plaso."""

import datetime
import logging

from dfdatetime import posix_time as dfdatetime_posix_time

from plaso.containers import plist_event
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.lib import timelib
from plaso.parsers import plist
from plaso.parsers.plist_plugins import interface


class DefaultPlugin(interface.PlistPlugin):
  """Basic plugin to extract keys with timestamps as values from plists."""

  NAME = u'plist_default'
  DESCRIPTION = u'Parser for plist files.'

  def GetEntries(self, parser_mediator, top_level=None, **unused_kwargs):
    """Simple method to exact date values from a Plist.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      top_level (dict[str, object]): plist top-level key.
    """
    for root, key, value in interface.RecurseKey(top_level):
      if not isinstance(value, datetime.datetime):
        continue

      event_data = plist_event.PlistTimeEventData()
      event_data.key = key
      event_data.root = root

      timestamp = timelib.Timestamp.FromPythonDatetime(value)
      date_time = dfdatetime_posix_time.PosixTimeInMicroseconds(
          timestamp=timestamp)
      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_WRITTEN)
      parser_mediator.ProduceEventWithEventData(event, event_data)

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
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      plist_name (str): name of the plist.
      top_level (dict[str, object]): plist top-level key.
    """
    logging.debug(u'Plist {0:s} plugin used for: {1:s}'.format(
        self.NAME, plist_name))
    self.GetEntries(parser_mediator, top_level=top_level, **kwargs)


plist.PlistParser.RegisterPlugin(DefaultPlugin)
