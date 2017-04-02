# -*- coding: utf-8 -*-
"""Windows Registry plugin for parsing the last shutdown time of a system."""

import construct

from dfdatetime import filetime as dfdatetime_filetime
from dfdatetime import semantic_time as dfdatetime_semantic_time

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.parsers import winreg
from plaso.parsers.winreg_plugins import interface


__author__ = 'Preston Miller, dpmforensics.com, github.com/prmiller91'


class ShutdownWindowsRegistryEventData(events.EventData):
  """Shutdown Windows Registry event data.

  Attributes:
    key_path (str): Windows Registry key path.
    value_name (str): name of the Windows Registry value.
  """

  DATA_TYPE = u'windows:registry:shutdown'

  def __init__(self):
    """Initializes event data."""
    super(ShutdownWindowsRegistryEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.key_path = None
    self.value_name = None


class ShutdownPlugin(interface.WindowsRegistryPlugin):
  """Windows Registry plugin for parsing the last shutdown time of a system."""

  NAME = u'windows_shutdown'
  DESCRIPTION = u'Parser for ShutdownTime Registry value.'

  FILTERS = frozenset([
      interface.WindowsRegistryKeyPathFilter(
          u'HKEY_LOCAL_MACHINE\\System\\CurrentControlSet\\Control\\Windows')])

  _UINT64_STRUCT = construct.ULInt64(u'value')

  def ExtractEvents(self, parser_mediator, registry_key, **kwargs):
    """Extracts events from a ShutdownTime Windows Registry value.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
    """
    shutdown_value = registry_key.GetValueByName(u'ShutdownTime')
    if not shutdown_value:
      return

    # Directly parse the Windows Registry value data in case it is defined
    # as binary data.
    try:
      timestamp = self._UINT64_STRUCT.parse(shutdown_value.data)
    except construct.FieldError as exception:
      timestamp = None
      parser_mediator.ProduceExtractionError(
          u'unable to determine shutdown timestamp with error: {0:s}'.format(
              exception))

    if not timestamp:
      date_time = dfdatetime_semantic_time.SemanticTime(u'Not set')
    else:
      date_time = dfdatetime_filetime.Filetime(timestamp=timestamp)

    event_data = ShutdownWindowsRegistryEventData()
    event_data.key_path = registry_key.path
    event_data.offset = shutdown_value.offset
    event_data.value_name = shutdown_value.name

    event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_LAST_SHUTDOWN)
    parser_mediator.ProduceEventWithEventData(event, event_data)


winreg.WinRegistryParser.RegisterPlugin(ShutdownPlugin)
