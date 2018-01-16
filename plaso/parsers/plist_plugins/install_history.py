# -*- coding: utf-8 -*-
"""Install history plist plugin."""

from __future__ import unicode_literals

from plaso.containers import plist_event
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.parsers import plist
from plaso.parsers.plist_plugins import interface


class InstallHistoryPlugin(interface.PlistPlugin):
  """Plist plugin that extracts the installation history."""

  NAME = 'macosx_install_history'
  DESCRIPTION = 'Parser for installation history plist files.'

  PLIST_PATH = 'InstallHistory.plist'
  PLIST_KEYS = frozenset([
      'date', 'displayName', 'displayVersion', 'processName',
      'packageIdentifiers'])

  # pylint: disable=arguments-differ
  def GetEntries(self, parser_mediator, top_level=None, **unused_kwargs):
    """Extracts relevant install history entries.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      top_level (dict[str, object]): plist top-level key.
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

      event = time_events.PythonDatetimeEvent(
          datetime_value, definitions.TIME_DESCRIPTION_WRITTEN)
      parser_mediator.ProduceEventWithEventData(event, event_data)


plist.PlistParser.RegisterPlugin(InstallHistoryPlugin)
