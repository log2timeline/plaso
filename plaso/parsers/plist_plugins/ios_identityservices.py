# -*- coding: utf-8 -*-
"""Plist parser plugin for iOS com.apple.identityservices.idstatuscache.plist
files."""

from dfdatetime import cocoa_time as dfdatetime_cocoa_time

from plaso.containers import events
from plaso.parsers import plist
from plaso.parsers.plist_plugins import interface


class IOSIdstatusacheEventData(events.EventData):
  """iOS com.apple.identityservices.idstatuscache.plist event.

  Attributes:
    process_name: (str) Name of the process that looked up an identifier.
    apple_identifier: (str) type and value of the identifier.
    lookup_time (dfdatetime.DateTimeValues): date and time of the lookup.
  """

  DATA_TYPE = 'ios:idstatuscache:lookup'

  def __init__(self):
    """Initializes event data."""
    super(IOSIdstatusacheEventData, self).__init__(data_type=self.DATA_TYPE)
    self.process_name = None
    self.apple_identifier = None
    self.lookup_time = None


class IOSIdstatusachePlistPlugin(interface.PlistPlugin):
  """Plist parser plugin for com.apple.identityservices.idstatuscache.plist
  files."""

  NAME = 'io_identityservices_idstatuscache'
  DATA_FORMAT = 'Idstatuscache plist file'

  PLIST_PATH_FILTERS = frozenset([interface.PlistPathFilter(
      'com.apple.identityservices.idstatuscache.plist')])

  def _GetDateTimeValueFromPlistKey(self, plist_key, plist_value_name):
    """Retrieves a date and time value from a specific value in a plist key.

    Args:
      plist_key (object): plist key.
      plist_value_name (str): name of the value in the plist key.

    Returns:
      dfdatetime.TimeElementsInMicroseconds: date and time or None if not
          available.
    """
    timestamp = plist_key.get(plist_value_name, None)
    if not timestamp:
      return None

    return dfdatetime_cocoa_time.CocoaTime(timestamp=timestamp)

  # pylint: disable=arguments-differ
  def _ParsePlist(
      self, parser_mediator, match=None, top_level=None, **unused_kwargs):
    """Extract Apple ids queried by process name.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      match (Optional[dict[str: object]]): keys extracted from PLIST_KEYS.
    """
    for _, process_name, process_values in self._RecurseKey(top_level, depth=1):

      if process_name == 'CacheVersion':
        continue

      for apple_identifier, apple_identifier_values in process_values.items():
        event_data = IOSIdstatusacheEventData()
        event_data.process_name = process_name
        event_data.apple_identifier = apple_identifier
        event_data.lookup_time = self._GetDateTimeValueFromPlistKey(
          apple_identifier_values, 'LookupDate')

        parser_mediator.ProduceEventData(event_data)


plist.PlistParser.RegisterPlugin(IOSIdstatusachePlistPlugin)
