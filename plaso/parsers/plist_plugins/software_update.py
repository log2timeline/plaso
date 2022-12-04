# -*- coding: utf-8 -*-
"""Plist parser plugin for MacOS software update plist files."""

from plaso.containers import events
from plaso.parsers import plist
from plaso.parsers.plist_plugins import interface


class MacOSSoftwareUpdateEventData(events.EventData):
  """MacOS software update event data.

  Attributes:
    full_update_time (dfdatetime.DateTimeValues): date and time of last
        full MacOS software update.
    recommended_updates (list[str]): recommended updates.
    system_version (str): operating system version.
    update_time (dfdatetime.DateTimeValues): date and time of last
        MacOS software update.
  """

  DATA_TYPE = 'macos:software_updata:entry'

  def __init__(self):
    """Initializes event data."""
    super(MacOSSoftwareUpdateEventData, self).__init__(data_type=self.DATA_TYPE)
    self.full_update_time = None
    self.recommended_updates = None
    self.system_version = None
    self.update_time = None


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
    last_full_successful_date = match.get('LastFullSuccessfulDate', None)
    last_successful_date = match.get('LastSuccessfulDate', None)

    recommended_updates = []
    if match.get('LastUpdatesAvailable', None):
      for update_property in match.get('RecommendedUpdates', []):
        identifier = update_property.get('Identifier', None)
        product_key = update_property.get('Product Key', None)

        recommended_updates.append(
            '{0:s} ({1:s})'.format(identifier, product_key))

    event_data = MacOSSoftwareUpdateEventData()
    event_data.full_update_time = self._GetDateTimeValueFromPlistKey(
         match, 'LastFullSuccessfulDate')
    event_data.recommended_updates = recommended_updates or None
    event_data.system_version = match.get('LastAttemptSystemVersion', None)

    # Only set update_time if it differs from full_update_time.
    if (last_successful_date and
        last_successful_date != last_full_successful_date):
      event_data.update_time = self._GetDateTimeValueFromPlistKey(
           match, 'LastSuccessfulDate')

    parser_mediator.ProduceEventData(event_data)


plist.PlistParser.RegisterPlugin(MacOSSoftwareUpdatePlistPlugin)
