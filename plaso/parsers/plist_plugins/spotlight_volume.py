# -*- coding: utf-8 -*-
"""Plist parser plugin for Spotlight volume configuration plist files."""

from plaso.containers import events
from plaso.parsers import plist
from plaso.parsers.plist_plugins import interface


class SpotlightVolumeConfigurationEventData(events.EventData):
  """Spotlight volume configuration event data.

  Attributes:
    creation_time (dfdatetime.DateTimeValues): volume creation date and time.
    partial_path (str): part of the path.
    volume_identifier (str): identifier of the volume.
  """

  DATA_TYPE = 'spotlight_volume_configuration:store'

  def __init__(self):
    """Initializes event data."""
    super(SpotlightVolumeConfigurationEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.creation_time = None
    self.partial_path = None
    self.volume_identifier = None


class SpotlightVolumeConfigurationPlistPlugin(interface.PlistPlugin):
  """Plist parser plugin for Spotlight volume configuration plist files."""

  NAME = 'spotlight_volume'
  DATA_FORMAT = 'Spotlight volume configuration plist file'

  PLIST_PATH_FILTERS = frozenset([
      interface.PlistPathFilter('VolumeConfiguration.plist')])

  PLIST_KEYS = frozenset(['Stores'])

  # pylint: disable=arguments-differ
  def _ParsePlist(self, parser_mediator, match=None, **unused_kwargs):
    """Extracts relevant Volume Configuration Spotlight entries.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      match (Optional[dict[str: object]]): keys extracted from PLIST_KEYS.
    """
    stores = match.get('Stores', {})
    for volume_identifier, plist_key in stores.items():
      event_data = SpotlightVolumeConfigurationEventData()
      event_data.creation_time = self._GetDateTimeValueFromPlistKey(
          plist_key, 'CreationDate')
      event_data.partial_path = plist_key.get('PartialPath', None)
      event_data.volume_identifier = volume_identifier

      parser_mediator.ProduceEventData(event_data)


plist.PlistParser.RegisterPlugin(SpotlightVolumeConfigurationPlistPlugin)
