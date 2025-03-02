# -*- coding: utf-8 -*-
"""Plug-in to collect information about the Motherboard and BIOS."""

from plaso.containers import events
from plaso.parsers import winreg_parser
from plaso.parsers.winreg_plugins import interface


class WindowsRegistryMotherboardInfoEventData(events.EventData):
  """Windows Motherboard Info event data attribute container.

  Attributes:
    bios_release_date (str): Date of release of the installed BIOS.
    bios_version (str): Version of installed BIOS.
    key_path (str): Windows Registry key path.
    last_written_time (dfdatetime.DateTimeValues): entry last written date
        and time.
    motherboard_manufacturer (str): Motherboard manafacturer name.
    motherboard_model (str): Name of the specific motherboard model.
  """

  DATA_TYPE = 'windows:registry:motherboard_info'

  def __init__(self):
    """Initializes event data."""
    super(WindowsRegistryMotherboardInfoEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.bios_release_date = None
    self.bios_version = None
    self.key_path = None
    self.last_written_time = None
    self.motherboard_manufacturer = None
    self.motherboard_model = None


class MotherboardInfoPlugin(interface.WindowsRegistryPlugin):
  """Plug-in to collect information about the Motherboard and BIOS."""

  NAME = 'motherboard_info'
  DATA_FORMAT = 'Motherboard Info Registry data'

  FILTERS = frozenset([
    interface.WindowsRegistryKeyPathFilter(
      'HKEY_LOCAL_MACHINE\\System\\CurrentControlSet\\Control\\'
      'SystemInformation')])

  def ExtractEvents(self, parser_mediator, registry_key, **kwargs):
    """Extracts events from a Windows Registry key.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
    """
    event_data = WindowsRegistryMotherboardInfoEventData()
    event_data.motherboard_manufacturer = self._GetValueFromKey(
      registry_key, 'SystemManufacturer')
    event_data.motherboard_model = self._GetValueFromKey(
      registry_key, 'SystemProductName')
    event_data.bios_release_date = self._GetValueFromKey(
      registry_key, 'BIOSReleaseDate')
    event_data.bios_version = self._GetValueFromKey(
      registry_key, 'BIOSVersion')
    event_data.key_path = registry_key.path
    event_data.last_written_time = registry_key.last_written_time

    parser_mediator.ProduceEventData(event_data)


winreg_parser.WinRegistryParser.RegisterPlugin(MotherboardInfoPlugin)
