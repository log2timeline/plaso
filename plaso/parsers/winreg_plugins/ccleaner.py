# -*- coding: utf-8 -*-
"""Parser for the CCleaner Registry key."""

from plaso.containers import time_events
from plaso.containers import windows_events
from plaso.lib import errors
from plaso.lib import eventdata
from plaso.lib import timelib
from plaso.parsers import winreg
from plaso.parsers.winreg_plugins import interface


__author__ = 'Marc Seguin (segumarc@gmail.com)'


class CCleanerUpdateEvent(time_events.TimestampEvent):
  """Convenience class for a Windows installation event.

  Attributes:
    key_path (str): Windows Registry key path.
  """

  DATA_TYPE = u'ccleaner:update'

  def __init__(self, timestamp, key_path):
    """Initializes an event object.

    Args:
      timestamp: The timestamp which is an integer containing the number
                 of micro seconds since January 1, 1970, 00:00:00 UTC.
      key_path: the Windows Registry key path.
    """
    super(CCleanerUpdateEvent, self).__init__(
        timestamp, eventdata.EventTimestamp.UPDATE_TIME)

    self.key_path = key_path


class CCleanerPlugin(interface.WindowsRegistryPlugin):
  """Gathers the CCleaner Keys for NTUSER hive."""

  NAME = u'ccleaner'
  DESCRIPTION = u'Parser for CCleaner Registry data.'

  FILTERS = frozenset([
      interface.WindowsRegistryKeyPathFilter(
          u'HKEY_CURRENT_USER\\Software\\Piriform\\CCleaner')])

  URLS = [(u'http://cheeky4n6monkey.blogspot.com/2012/02/writing-ccleaner'
           u'-regripper-plugin-part_05.html')]

  _SOURCE_APPEND = u': CCleaner Registry key'

  def ExtractEvents(self, parser_mediator, registry_key, **kwargs):
    """Extracts events from a Windows Registry key.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
    """
    update_key_value = None
    values_dict = {}
    for registry_value in registry_key.GetValues():
      if not registry_value.name or not registry_value.data:
        continue

      if (registry_value.name == u'UpdateKey' and
          registry_value.DataIsString()):
        update_key_value = registry_value

      else:
        values_dict[registry_value.name] = registry_value.GetDataAsObject()

    if update_key_value:
      date_time_string = update_key_value.GetDataAsObject()
      try:
        # Date and time string in the form: MM/DD/YYYY hh:mm:ss [A|P]M
        # e.g. 07/13/2013 10:03:14 AM
        # TODO: does this hold for other locales?
        timestamp = timelib.Timestamp.FromTimeString(
            date_time_string, timezone=parser_mediator.timezone)
      except errors.TimestampError:
        timestamp = None
        parser_mediator.ProduceExtractionError(
            u'unable to parse time string: {0:s}'.format(date_time_string))

      if timestamp is not None:
        event = CCleanerUpdateEvent(timestamp, registry_key.path)
        parser_mediator.ProduceEvent(event)

    event_data = windows_events.WindowsRegistryEventData()
    event_data.key_path = registry_key.path
    event_data.offset = registry_key.offset
    event_data.regvalue = values_dict
    event_data.source_append = self._SOURCE_APPEND
    event_data.urls = self.URLS

    event = time_events.DateTimeValuesEvent(
        registry_key.last_written_time, eventdata.EventTimestamp.WRITTEN_TIME)
    parser_mediator.ProduceEventWithEventData(event, event_data)


winreg.WinRegistryParser.RegisterPlugin(CCleanerPlugin)
