# -*- coding: utf-8 -*-
"""Plug-in to collect evidence of execution from RADAR HeapLeakDetection
Diagnosed Applications."""

from os.path import dirname, join

from dfdatetime import filetime as dfdatetime_filetime
from dfdatetime import semantic_time as dfdatetime_semantic_time

from plaso.containers import events
from plaso.lib import dtfabric_helper
from plaso.lib import errors
from plaso.parsers import winreg_parser
from plaso.parsers.winreg_plugins import interface


class WindowsRegistryDiagnosedApplicationsEventData(events.EventData):
  """Windows Diagnosed Application event data attribute container.

  Attributes:
    process_name (str): Name of the process diagnosed by RADAR.
    last_detection_time (dfdatetime.DateTimeValues): process last
        detected by RADAR date and time.
    key_path (str): Windows Registry key path.
    last_written_time (dfdatetime.DateTimeValues): entry last written date
        and time.
  """

  DATA_TYPE = 'windows:registry:diagnosed_applications'

  def __init__(self):
    """Initializes event data."""
    super(WindowsRegistryDiagnosedApplicationsEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.process_name = None
    self.last_detection_time = None
    self.key_path = None
    self.last_written_time = None


class DiagnosedApplicationsPlugin(
    interface.WindowsRegistryPlugin, dtfabric_helper.DtFabricHelper):
  """Plug-in to collect information about the Motherboard and BIOS."""

  NAME = 'diagnosed_applications'
  DATA_FORMAT = 'Diagnosed Applications Registry data'

  FILTERS = frozenset([
    interface.WindowsRegistryKeyPathFilter(
      'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\RADAR\\HeapLeakDetection\\'
      'DiagnosedApplications')])
  _DEFINITION_FILE = join(
    dirname(__file__), 'filetime.yaml')

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
          f'Unable to parse FILETIME value with error: {exception!s}')

    if filetime == 0:
      return dfdatetime_semantic_time.NotSet()

    try:
      return dfdatetime_filetime.Filetime(timestamp=filetime)
    except ValueError:
      raise errors.ParseError(f'Invalid FILETIME value: 0x{filetime:08x}')

  def ExtractEvents(self, parser_mediator, registry_key, **kwargs):
    """Extracts events from a Windows Registry key.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
    """
    for subkey in registry_key.GetSubkeys():
      event_data = WindowsRegistryDiagnosedApplicationsEventData()

      event_data.process_name = subkey.name
      event_data.last_detection_time = self._ParseFiletime(
        subkey.GetValueByName(
          "LastDetectionTime"
        ).data
      )
      event_data.key_path = subkey.path
      event_data.last_written_time = subkey.last_written_time
      parser_mediator.ProduceEventData(event_data)


winreg_parser.WinRegistryParser.RegisterPlugin(DiagnosedApplicationsPlugin)
