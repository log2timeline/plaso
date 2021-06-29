# -*- coding: utf-8 -*-
"""Plist parser plugin for iPod, iPad and iPhone storage plist files."""

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.parsers import plist
from plaso.parsers.plist_plugins import interface


# TODO: add more attributes.
class IPodPlistEventData(events.EventData):
  """iPod plist event data.

  Attributes:
    device_id (str): unique identifier of the iPod device.
  """

  DATA_TYPE = 'ipod:device:entry'

  def __init__(self):
    """Initializes event data."""
    super(IPodPlistEventData, self).__init__(data_type=self.DATA_TYPE)
    self.device_id = None


class IPodPlugin(interface.PlistPlugin):
  """Plist parser plugin for iPod, iPad and iPhone storage plist files."""

  NAME = 'ipod_device'
  DATA_FORMAT = 'iPod, iPad and iPhone plist file'

  PLIST_PATH_FILTERS = frozenset([
      interface.PlistPathFilter('com.apple.iPod.plist')])

  PLIST_KEYS = frozenset(['Devices'])

  # pylint: disable=arguments-differ
  def _ParsePlist(self, parser_mediator, match=None, **unused_kwargs):
    """Extract device information from the iPod plist.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      match (Optional[dict[str: object]]): keys extracted from PLIST_KEYS.
    """
    devices = match.get('Devices', {})
    for device_identifier, device_information in devices.items():
      datetime_value = device_information.get('Connected', None)
      if not datetime_value:
        continue

      event_data = IPodPlistEventData()
      event_data.device_id = device_identifier

      # TODO: refactor.
      for key, value in device_information.items():
        if key == 'Connected':
          continue

        attribute_name = key.lower().replace(' ', '_')
        setattr(event_data, attribute_name, value)

      date_time = dfdatetime_time_elements.TimeElementsInMicroseconds()
      date_time.CopyFromDatetime(datetime_value)

      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_LAST_CONNECTED)
      parser_mediator.ProduceEventWithEventData(event, event_data)


plist.PlistParser.RegisterPlugin(IPodPlugin)
