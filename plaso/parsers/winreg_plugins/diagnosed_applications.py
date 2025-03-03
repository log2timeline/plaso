# -*- coding: utf-8 -*-
"""Plug-in to collect evidence of execution from RADAR 
HeapLeakDetection Diagnosed Applications."""

from plaso.containers import events
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
    super(WindowsRegistryMotherboardInfoEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.process_name = None
    self.last_detection_time = None
    self.key_path = None
    self.last_written_time = None


class DiagnosedApplicationsPlugin(interface.WindowsRegistryPlugin):
  """Plug-in to collect information about the Motherboard and BIOS."""

  NAME = 'diagnosed_applications'
  DATA_FORMAT = 'Diagnosed Applications Registry data'

  FILTERS = frozenset([
    interface.WindowsRegistryKeyPathFilter(
      'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\RADAR\\HeapLeakDetection\\'
      'DiagnosedApplications')])

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
      print(subkey.GetValueByName('LastDetectionTime'))
      
      try:
        event_data.last_detection_time = self._ParseFiletime(
          subkey.GetValueByName('LastDetectionTime')
        )
      except errors.ParseError as exception:
        warning = f'unable to parse LastDetectionTime: {exception!s}'
        parser_mediator.ProduceExtractionWarning(warning)
      
      event_data.key_path = subkey.path
      event_data.last_written_time = subkey.last_written_time
  
      parser_mediator.ProduceEventData(event_data)


winreg_parser.WinRegistryParser.RegisterPlugin(DiagnosedApplicationsPlugin)
