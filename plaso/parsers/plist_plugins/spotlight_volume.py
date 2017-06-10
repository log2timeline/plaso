# -*- coding: utf-8 -*-
"""Spotlight Volume Configuration plist plugin."""

from dfdatetime import posix_time as dfdatetime_posix_time

from plaso.containers import plist_event
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.lib import timelib
from plaso.parsers import plist
from plaso.parsers.plist_plugins import interface


__author__ = 'Joaquin Moreno Garijo (Joaquin.MorenoGarijo.2013@live.rhul.ac.uk)'


class SpotlightVolumePlugin(interface.PlistPlugin):
  """Basic plugin to extract the Spotlight Volume Configuration."""

  NAME = u'spotlight_volume'
  DESCRIPTION = u'Parser for Spotlight volume configuration plist files.'

  PLIST_PATH = u'VolumeConfiguration.plist'
  PLIST_KEYS = frozenset([u'Stores'])

  def GetEntries(self, parser_mediator, match=None, **unused_kwargs):
    """Extracts relevant Volume Configuration Spotlight entries.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      match (Optional[dict[str: object]]): keys extracted from PLIST_KEYS.
    """
    stores = match.get(u'Stores', {})
    for volume_name, volume in iter(stores.items()):
      datetime_value = volume.get(u'CreationDate', None)
      if not datetime_value:
        continue

      partial_path = volume[u'PartialPath']

      event_data = plist_event.PlistTimeEventData()
      event_data.desc = u'Spotlight Volume {0:s} ({1:s}) activated.'.format(
          volume_name, partial_path)
      event_data.key = u''
      event_data.root = u'/Stores'

      timestamp = timelib.Timestamp.FromPythonDatetime(datetime_value)
      date_time = dfdatetime_posix_time.PosixTimeInMicroseconds(
          timestamp=timestamp)
      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_WRITTEN)
      parser_mediator.ProduceEventWithEventData(event, event_data)


plist.PlistParser.RegisterPlugin(SpotlightVolumePlugin)
