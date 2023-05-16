# -*- coding: utf-8 -*-
"""Plist parser plugin for MacOS install history plist files."""

from plaso.containers import events
from plaso.parsers import plist
from plaso.parsers.plist_plugins import interface


class MacOSInstallHistoryEventData(events.EventData):
  """MacOS install history event data.

  Attributes:
    identifiers (list[str]): identifiers of the installed package.
    name (str): display name of the installed package.
    process_name (str): name of the process that installed the package.
    version (str): display version of the installed package.
    written_time (dfdatetime.DateTimeValues): entry written date and time.
  """

  DATA_TYPE = 'macos:install_history:entry'

  def __init__(self):
    """Initializes event data."""
    super(MacOSInstallHistoryEventData, self).__init__(data_type=self.DATA_TYPE)
    self.identifiers = None
    self.name = None
    self.process_name = None
    self.version = None
    self.written_time = None


class MacOSInstallHistoryPlistPlugin(interface.PlistPlugin):
  """Plist parser plugin for MacOS install history plist files."""

  NAME = 'macosx_install_history'
  DATA_FORMAT = 'MacOS installation history plist file'

  PLIST_PATH_FILTERS = frozenset([
      interface.PlistPathFilter('InstallHistory.plist')])

  PLIST_KEYS = frozenset([
      'date', 'displayName', 'displayVersion', 'processName',
      'packageIdentifiers'])

  # pylint: disable=arguments-differ
  def _ParsePlist(self, parser_mediator, top_level=None, **unused_kwargs):
    """Extracts relevant install history entries.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      top_level (Optional[dict[str, object]]): plist top-level item.
    """
    for plist_key in top_level:
      event_data = MacOSInstallHistoryEventData()
      event_data.identifiers = plist_key.get('packageIdentifiers', None)
      event_data.name = plist_key.get('displayName', None)
      event_data.process_name = plist_key.get('processName', None)
      event_data.version = plist_key.get('displayVersion', None)
      event_data.written_time = self._GetDateTimeValueFromPlistKey(
          plist_key, 'date')

      parser_mediator.ProduceEventData(event_data)


plist.PlistParser.RegisterPlugin(MacOSInstallHistoryPlistPlugin)
