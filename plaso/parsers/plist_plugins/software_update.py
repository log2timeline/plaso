# -*- coding: utf-8 -*-
"""Plist parser plugin for MacOS software update plist files."""

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.parsers import plist
from plaso.parsers.plist_plugins import interface


class MacOSSoftwareUpdateEventData(events.EventData):
  """MacOS software update event data.

  Attributes:
    recommended_updates (list[str]): recommended updates.
    system_version (str): operating system version.
  """

  DATA_TYPE = 'macos:software_updata:entry'

  def __init__(self):
    """Initializes event data."""
    super(MacOSSoftwareUpdateEventData, self).__init__(data_type=self.DATA_TYPE)
    self.recommended_updates = None
    self.system_version = None


class MacOSSoftwareUpdatePlistPlugin(interface.PlistPlugin):
  """Plist parser plugin for MacOS software update plist files.

  Further details about the extracted fields:
    LastFullSuccessfulDate:
      timestamp when MacOS was full update.
    LastSuccessfulDate:
      timestamp when MacOS was partially update.
  """

  NAME = 'macos_software_update'
  DATA_FORMAT = 'MacOS software update plist file'

  PLIST_PATH_FILTERS = frozenset([
      interface.PlistPathFilter('com.apple.SoftwareUpdate.plist')])

  PLIST_KEYS = frozenset([
      'LastFullSuccessfulDate', 'LastSuccessfulDate',
      'LastAttemptSystemVersion', 'LastUpdatesAvailable',
      'LastRecommendedUpdatesAvailable', 'RecommendedUpdates'])

  # pylint: disable=arguments-differ
  def _ParsePlist(self, parser_mediator, match=None, **unused_kwargs):
    """Extracts relevant MacOS update entries.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      match (Optional[dict[str: object]]): keys extracted from PLIST_KEYS.
    """
    event_data = MacOSSoftwareUpdateEventData()
    event_data.system_version = match.get('LastAttemptSystemVersion', None)

    if match.get('LastUpdatesAvailable', None):
      recommended_updates = []
      for update_property in match.get('RecommendedUpdates', []):
        identifier = update_property.get('Identifier', None)
        product_key = update_property.get('Product Key', None)

        recommended_updates.append(
            '{0:s} ({1:s})'.format(identifier, product_key))

        event_data.recommended_updates = recommended_updates

    last_full_successful_date = match.get('LastFullSuccessfulDate', None)
    if last_full_successful_date:
      date_time = dfdatetime_time_elements.TimeElementsInMicroseconds()
      date_time.CopyFromDatetime(last_full_successful_date)

      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_UPDATE)
      parser_mediator.ProduceEventWithEventData(event, event_data)

    last_successful_date = match.get('LastSuccessfulDate', None)
    if (last_successful_date and
        last_successful_date != last_full_successful_date):
      date_time = dfdatetime_time_elements.TimeElementsInMicroseconds()
      date_time.CopyFromDatetime(last_successful_date)

      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_UPDATE)
      parser_mediator.ProduceEventWithEventData(event, event_data)


plist.PlistParser.RegisterPlugin(MacOSSoftwareUpdatePlistPlugin)
