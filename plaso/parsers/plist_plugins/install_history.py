# -*- coding: utf-8 -*-
"""Plist parser plugin for MacOS install history plist files."""

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import plist_event
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.parsers import plist
from plaso.parsers.plist_plugins import interface


class InstallHistoryPlugin(interface.PlistPlugin):
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
          and other components, such as storage and dfvfs.
      top_level (Optional[dict[str, object]]): plist top-level item.
    """
    for entry in top_level:
      datetime_value = entry.get('date', None)
      package_identifiers = entry.get('packageIdentifiers', [])

      if not datetime_value or not package_identifiers:
        continue

      display_name = entry.get('displayName', '<UNKNOWN>')
      display_version = entry.get('displayVersion', '<DISPLAY_VERSION>')
      process_name = entry.get('processName', '<PROCESS_NAME>')
      package_identifiers = ', '.join(package_identifiers)

      event_data = plist_event.PlistTimeEventData()
      event_data.desc = (
          'Installation of [{0:s} {1:s}] using [{2:s}]. Packages: '
          '{3:s}.').format(
              display_name, display_version, process_name, package_identifiers)
      event_data.key = ''
      event_data.root = '/item'

      date_time = dfdatetime_time_elements.TimeElementsInMicroseconds()
      date_time.CopyFromDatetime(datetime_value)

      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_WRITTEN)
      parser_mediator.ProduceEventWithEventData(event, event_data)


plist.PlistParser.RegisterPlugin(InstallHistoryPlugin)
