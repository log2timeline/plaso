# -*- coding: utf-8 -*-
"""Default plist parser plugin."""

from __future__ import unicode_literals

import datetime

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import plist_event
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.parsers import logger
from plaso.parsers import plist
from plaso.parsers.plist_plugins import interface


class DefaultPlugin(interface.PlistPlugin):
  """Default plist parser plugin."""

  NAME = 'plist_default'
  DATA_FORMAT = 'plist file'

  # pylint: disable=arguments-differ
  def GetEntries(self, parser_mediator, top_level=None, **unused_kwargs):
    """Extracts events from the values of entries within a plist.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      top_level (Optional[dict[str, object]]): plist top-level key.
    """
    for root, key, datetime_value in interface.RecurseKey(top_level):
      if not isinstance(datetime_value, datetime.datetime):
        continue

      event_data = plist_event.PlistTimeEventData()
      event_data.key = key
      event_data.root = root

      date_time = dfdatetime_time_elements.TimeElementsInMicroseconds()
      date_time.CopyFromDatetime(datetime_value)

      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_WRITTEN)
      parser_mediator.ProduceEventWithEventData(event, event_data)

      # TODO: adjust code when there is a way to map keys to offsets.

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
    logger.debug('Plist {0:s} plugin used for: {1:s}'.format(
        self.NAME, plist_name))
    self.GetEntries(parser_mediator, top_level=top_level, **kwargs)


plist.PlistParser.RegisterPlugin(DefaultPlugin)
