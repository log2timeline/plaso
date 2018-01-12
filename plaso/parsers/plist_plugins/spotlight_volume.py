# -*- coding: utf-8 -*-
"""Spotlight Volume Configuration plist plugin."""

from __future__ import unicode_literals

from plaso.containers import plist_event
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.parsers import plist
from plaso.parsers.plist_plugins import interface


class SpotlightVolumePlugin(interface.PlistPlugin):
  """Basic plugin to extract the Spotlight Volume Configuration."""

  NAME = 'spotlight_volume'
  DESCRIPTION = 'Parser for Spotlight volume configuration plist files.'

  PLIST_PATH = 'VolumeConfiguration.plist'
  PLIST_KEYS = frozenset(['Stores'])

  # pylint: disable=arguments-differ
  def GetEntries(self, parser_mediator, match=None, **unused_kwargs):
    """Extracts relevant Volume Configuration Spotlight entries.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      match (Optional[dict[str: object]]): keys extracted from PLIST_KEYS.
    """
    stores = match.get('Stores', {})
    for volume_name, volume in iter(stores.items()):
      datetime_value = volume.get('CreationDate', None)
      if not datetime_value:
        continue

      partial_path = volume['PartialPath']

      event_data = plist_event.PlistTimeEventData()
      event_data.desc = 'Spotlight Volume {0:s} ({1:s}) activated.'.format(
          volume_name, partial_path)
      event_data.key = ''
      event_data.root = '/Stores'

      event = time_events.PythonDatetimeEvent(
          datetime_value, definitions.TIME_DESCRIPTION_WRITTEN)
      parser_mediator.ProduceEventWithEventData(event, event_data)


plist.PlistParser.RegisterPlugin(SpotlightVolumePlugin)
