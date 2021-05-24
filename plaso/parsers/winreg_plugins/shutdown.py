# -*- coding: utf-8 -*-
"""Windows Registry plugin for parsing the last shutdown time of a system."""

from dfdatetime import filetime as dfdatetime_filetime
from dfdatetime import semantic_time as dfdatetime_semantic_time

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.lib import errors
from plaso.parsers import winreg_parser
from plaso.parsers.winreg_plugins import dtfabric_plugin
from plaso.parsers.winreg_plugins import interface


class ShutdownWindowsRegistryEventData(events.EventData):
  """Shutdown Windows Registry event data.

  Attributes:
    key_path (str): Windows Registry key path.
    value_name (str): name of the Windows Registry value.
  """

  DATA_TYPE = 'windows:registry:shutdown'

  def __init__(self):
    """Initializes event data."""
    super(ShutdownWindowsRegistryEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.key_path = None
    self.value_name = None


class ShutdownWindowsRegistryPlugin(
    dtfabric_plugin.DtFabricBaseWindowsRegistryPlugin):
  """Windows Registry plugin for parsing the last shutdown time of a system."""

  NAME = 'windows_shutdown'
  DATA_FORMAT = 'Windows last shutdown Registry data'

  FILTERS = frozenset([
      interface.WindowsRegistryKeyPathFilter(
          'HKEY_LOCAL_MACHINE\\System\\CurrentControlSet\\Control\\Windows')])

  _DEFINITION_FILE = 'filetime.yaml'

  def _ParseFiletime(self, byte_stream):
    """Parses a FILETIME date and time value from a byte stream.

    Args:
      byte_stream (bytes): byte stream.

    Returns:
      dfdatetime.DateTimeValues: a FILETIME date and time values or a semantic
        date and time values if the FILETIME date and time value is not set.

    Raises:
      ParseError: if the FILETIME could not be parsed.
    """
    filetime_map = self._GetDataTypeMap('filetime')

    try:
      filetime = self._ReadStructureFromByteStream(
          byte_stream, 0, filetime_map)
    except (ValueError, errors.ParseError) as exception:
      raise errors.ParseError(
          'Unable to parse FILETIME value with error: {0!s}'.format(
              exception))

    if filetime == 0:
      return dfdatetime_semantic_time.NotSet()

    try:
      return dfdatetime_filetime.Filetime(timestamp=filetime)
    except ValueError:
      raise errors.ParseError('Invalid FILETIME value: 0x{0:08x}'.format(
          filetime))

  def ExtractEvents(self, parser_mediator, registry_key, **kwargs):
    """Extracts events from a ShutdownTime Windows Registry value.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
    """
    shutdown_value = registry_key.GetValueByName('ShutdownTime')
    if shutdown_value:
      try:
        date_time = self._ParseFiletime(shutdown_value.data)
      except errors.ParseError as exception:
        parser_mediator.ProduceExtractionWarning(
            'unable to determine shutdown timestamp with error: {0!s}'.format(
                exception))
        date_time = None

      if date_time:
        event_data = ShutdownWindowsRegistryEventData()
        event_data.key_path = registry_key.path
        event_data.value_name = shutdown_value.name

        event = time_events.DateTimeValuesEvent(
            date_time, definitions.TIME_DESCRIPTION_LAST_SHUTDOWN)
        parser_mediator.ProduceEventWithEventData(event, event_data)

    self._ProduceDefaultWindowsRegistryEvent(
        parser_mediator, registry_key, names_to_skip=['ShutdownTime'])


winreg_parser.WinRegistryParser.RegisterPlugin(ShutdownWindowsRegistryPlugin)
