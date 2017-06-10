# -*- coding: utf-8 -*-
"""Install history plist plugin."""

from dfdatetime import posix_time as dfdatetime_posix_time

from plaso.containers import plist_event
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.lib import timelib
from plaso.parsers import plist
from plaso.parsers.plist_plugins import interface


__author__ = 'Joaquin Moreno Garijo (Joaquin.MorenoGarijo.2013@live.rhul.ac.uk)'


class InstallHistoryPlugin(interface.PlistPlugin):
  """Plist plugin that extracts the installation history."""

  NAME = u'macosx_install_history'
  DESCRIPTION = u'Parser for installation history plist files.'

  PLIST_PATH = u'InstallHistory.plist'
  PLIST_KEYS = frozenset([
      u'date', u'displayName', u'displayVersion', u'processName',
      u'packageIdentifiers'])

  def GetEntries(self, parser_mediator, top_level=None, **unused_kwargs):
    """Extracts relevant install history entries.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      top_level (dict[str, object]): plist top-level key.
    """
    for entry in top_level:
      datetime_value = entry.get(u'date', None)
      package_identifiers = entry.get(u'packageIdentifiers', [])

      if not datetime_value or not package_identifiers:
        continue

      display_name = entry.get(u'displayName', u'<UNKNOWN>')
      display_version = entry.get(u'displayVersion', u'<DISPLAY_VERSION>')
      process_name = entry.get(u'processName', u'<PROCESS_NAME>')
      package_identifiers = u', '.join(package_identifiers)

      event_data = plist_event.PlistTimeEventData()
      event_data.desc = (
          u'Installation of [{0:s} {1:s}] using [{2:s}]. Packages: '
          u'{3:s}.').format(
              display_name, display_version, process_name, package_identifiers)
      event_data.key = u''
      event_data.root = u'/item'

      timestamp = timelib.Timestamp.FromPythonDatetime(datetime_value)
      date_time = dfdatetime_posix_time.PosixTimeInMicroseconds(
          timestamp=timestamp)
      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_WRITTEN)
      parser_mediator.ProduceEventWithEventData(event, event_data)


plist.PlistParser.RegisterPlugin(InstallHistoryPlugin)
