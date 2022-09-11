# -*- coding: utf-8 -*-
"""Plist parser plugin for MacOS install history plist files."""

from dfdatetime import semantic_time as dfdatetime_semantic_time
from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.parsers import plist
from plaso.parsers.plist_plugins import interface


class MacOSInstallHistoryEventData(events.EventData):
  """MacOS install history event data.

  Attributes:
    identifiers (list[str]): indentifiers of the installed package.
    name (str): display name of the installed package.
    process_name (str): name of the process that installed the package.
    version (str): display version of the installed package.
  """

  DATA_TYPE = 'macos:install_history:entry'

  def __init__(self):
    """Initializes event data."""
    super(MacOSInstallHistoryEventData, self).__init__(data_type=self.DATA_TYPE)
    self.identifiers = None
    self.name = None
    self.process_name = None
    self.version = None


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
    for entry in top_level:
      event_data = MacOSInstallHistoryEventData()
      event_data.identifiers = entry.get('packageIdentifiers', None)
      event_data.name = entry.get('displayName', None)
      event_data.process_name = entry.get('processName', None)
      event_data.version = entry.get('displayVersion', None)

      datetime_value = entry.get('date', None)
      if not datetime_value:
        date_time = dfdatetime_semantic_time.NotSet()
      else:
        date_time = dfdatetime_time_elements.TimeElements()
        date_time.CopyFromDatetime(datetime_value)

      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_WRITTEN)
      parser_mediator.ProduceEventWithEventData(event, event_data)


plist.PlistParser.RegisterPlugin(MacOSInstallHistoryPlistPlugin)
