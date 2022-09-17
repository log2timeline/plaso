# -*- coding: utf-8 -*-
"""Plist parser plugin for Spotlight volume configuration plist files."""

from dfdatetime import semantic_time as dfdatetime_semantic_time
from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.parsers import plist
from plaso.parsers.plist_plugins import interface


class SpotlightVolumeConfigurationEventData(events.EventData):
  """Spotlight volume configuration event data.

  Attributes:
    partial_path (str): part of the path.
    volume_identifier (str): identifier of the volume.
  """

  DATA_TYPE = 'spotlight_volume_configuration:store'

  def __init__(self):
    """Initializes event data."""
    super(SpotlightVolumeConfigurationEventData, self).__init__(
        data_type=self.DATA_TYPE)
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
    for volume_identifier, volume in stores.items():
      event_data = SpotlightVolumeConfigurationEventData()
      event_data.partial_path = volume.get('PartialPath', None)
      event_data.volume_identifier = volume_identifier

      datetime_value = volume.get('CreationDate', None)
      if not datetime_value:
        date_time = dfdatetime_semantic_time.NotSet()
      else:
        date_time = dfdatetime_time_elements.TimeElementsInMicroseconds()
        date_time.CopyFromDatetime(datetime_value)

      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_CREATION)
      parser_mediator.ProduceEventWithEventData(event, event_data)


plist.PlistParser.RegisterPlugin(SpotlightVolumeConfigurationPlistPlugin)
