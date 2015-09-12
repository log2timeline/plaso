# -*- coding: utf-8 -*-
"""Parser for the CCleaner Registry key."""

from plaso.events import time_events
from plaso.events import windows_events
from plaso.lib import errors
from plaso.lib import eventdata
from plaso.lib import timelib
from plaso.parsers import winreg
from plaso.parsers.winreg_plugins import interface


__author__ = 'Marc Seguin (segumarc@gmail.com)'


class CCleanerUpdateEvent(time_events.TimestampEvent):
  """Convenience class for a Windows installation event.

  Attributes:
    key_path: the Windows Registry key path.
  """

  DATA_TYPE = 'ccleaner:update'

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

  REG_KEYS = [u'\\Software\\Piriform\\CCleaner']
  REG_TYPE = u'NTUSER'

  URLS = [(u'http://cheeky4n6monkey.blogspot.com/2012/02/writing-ccleaner'
           u'-regripper-plugin-part_05.html')]

  _SOURCE_APPEND = u': CCleaner Registry key'

  def GetEntries(
      self, parser_mediator, registry_key, codepage=u'cp1252',
      registry_file_type=None, **unused_kwargs):
    """Extracts event objects from a CCleaner Registry key.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      registry_key: A Windows Registry key (instance of
                    dfwinreg.WinRegistryKey).
      codepage: Optional extended ASCII string codepage. The default is cp1252.
      registry_file_type: Optional string containing the Windows Registry file
                          type, e.g. NTUSER, SOFTWARE. The default is None.
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
        values_dict[registry_value.name] = registry_value.data

    if update_key_value:
      try:
        # Date and time string in the form: MM/DD/YYYY hh:mm:ss [A|P]M
        # e.g. 07/13/2013 10:03:14 AM
        # TODO: does this hold for other locales?
        timestamp = timelib.Timestamp.FromTimeString(
            update_key_value.data, timezone=parser_mediator.timezone)
      except errors.TimestampError:
        timestamp = None
        parser_mediator.ProduceParseError(
            u'unable to parse time string: {0:s}'.format(update_key_value.data))

      if timestamp is not None:
        event_object = CCleanerUpdateEvent(timestamp, registry_key.path)
        parser_mediator.ProduceEvent(event_object)

    event_object = windows_events.WindowsRegistryEvent(
        registry_key.last_written_time, registry_key.path, values_dict,
        offset=registry_key.offset, registry_file_type=registry_file_type,
        source_append=self._SOURCE_APPEND)
    parser_mediator.ProduceEvent(event_object)


winreg.WinRegistryParser.RegisterPlugin(CCleanerPlugin)
