# -*- coding: utf-8 -*-
"""Plist parser plugin for Safari Downloads.plist files."""

from plaso.containers import events
from plaso.parsers import plist
from plaso.parsers.plist_plugins import interface


class SafariDownloadEventData(events.EventData):
  """Safari download event data.

  Attributes:
    end_time (dfdatetime.DateTimeValues): date and time the download was
        finished.
    full_path (str): full path where the file was downloaded to.
    received_bytes (int): number of bytes received while downloading.
    remove_on_completion (bool): remove the download when completed (done).
    start_time (dfdatetime.DateTimeValues): date and time the download was
        started.
    total_bytes (int): total number of bytes to download.
    url (str): URL of the downloaded file.
  """

  DATA_TYPE = 'safari:downloads:entry'

  def __init__(self):
    """Initializes event data."""
    super(SafariDownloadEventData, self).__init__(data_type=self.DATA_TYPE)
    self.end_time = None
    self.full_path = None
    self.received_bytes = None
    self.remove_on_completion = None
    self.start_time = None
    self.total_bytes = None
    self.url = None


class SafariDownloadsPlistPlugin(interface.PlistPlugin):
  """Plist parser plugin for Safari Downloads.plist files."""

  NAME = 'safari_downloads'
  DATA_FORMAT = 'Safari Downloads plist file'

  PLIST_PATH_FILTERS = frozenset([
      interface.PlistPathFilter('Downloads.plist')])

  PLIST_KEYS = frozenset(['DownloadHistory'])

  # pylint: disable=arguments-differ
  def _ParsePlist(self, parser_mediator, match=None, **unused_kwargs):
    """Extracts relevant entries.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      match (Optional[dict[str: object]]): keys extracted from PLIST_KEYS.
    """
    for plist_key in match.get('DownloadHistory', []):
      event_data = SafariDownloadEventData()
      event_data.end_time = self._GetDateTimeValueFromPlistKey(
          plist_key, 'DownloadEntryDateFinishedKey')
      event_data.full_path = plist_key.get('DownloadEntryPath', None)
      event_data.received_bytes = plist_key.get(
          'DownloadEntryProgressBytesSoFar', None)
      event_data.remove_on_completion = plist_key.get(
          'DownloadEntryRemoveWhenDoneKey', None)
      event_data.start_time = self._GetDateTimeValueFromPlistKey(
          plist_key, 'DownloadEntryDateAddedKey')
      event_data.total_bytes = plist_key.get(
          'DownloadEntryProgressTotalToLoad', None)
      event_data.url = plist_key.get('DownloadEntryURL', None)

      parser_mediator.ProduceEventData(event_data)


plist.PlistParser.RegisterPlugin(SafariDownloadsPlistPlugin)
