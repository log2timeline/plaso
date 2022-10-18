# -*- coding: utf-8 -*-
"""MountPoints2 Windows Registry parser plugin."""

from plaso.containers import events
from plaso.parsers import winreg_parser
from plaso.parsers.winreg_plugins import interface


class MountPoints2EventData(events.EventData):
  """Windows MountPoints2 event data attribute container.

  Attributes:
    key_path (str): Windows Registry key path.
    label (str): mount point label.
    last_written_time (dfdatetime.DateTimeValues): entry last written date and
        time.
    name (str): name of the mount point source.
    server_name (str): name of the remote drive server or None if not set.
    share_name (str): name of the remote drive share or None if not set.
    type (str): type of the mount point source, which can be "Drive",
        "Remove Drive" or "Volume".
  """

  DATA_TYPE = 'windows:registry:mount_points2'

  def __init__(self):
    """Initializes event data."""
    super(MountPoints2EventData, self).__init__(data_type=self.DATA_TYPE)
    self.key_path = None
    self.last_written_time = None
    self.label = None
    self.name = None
    self.server_name = None
    self.share_name = None
    self.type = None


class MountPoints2Plugin(interface.WindowsRegistryPlugin):
  """Windows Registry plugin for parsing the MountPoints2 key."""

  NAME = 'explorer_mountpoints2'
  DATA_FORMAT = 'Windows Explorer mount points Registry data'

  FILTERS = frozenset([
      interface.WindowsRegistryKeyPathFilter(
          'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\'
          'Explorer\\MountPoints2')])

  def ExtractEvents(self, parser_mediator, registry_key, **kwargs):
    """Extracts events from a Windows Registry key.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
    """
    for subkey in registry_key.GetSubkeys():
      name = subkey.name
      if not name:
        continue

      server_name = 'Drive'
      share_name = None
      source_type = None

      if name.startswith('{'):
        source_type = 'Volume'

      # Check if the name is formatted as: "##Server_Name#Share_Name".
      elif name.startswith('##'):
        source_type = 'Remote Drive'
        server_name, _, share_name = name[2:].partition('#')
        share_name = '\\{0:s}'.format(share_name.replace('#', '\\'))

      label_value = subkey.GetValueByName('_LabelFromReg')
      if label_value:
        label = label_value.GetDataAsObject()
      else:
        label = None

      event_data = MountPoints2EventData()
      event_data.key_path = registry_key.path
      event_data.label = label
      event_data.last_written_time = subkey.last_written_time
      event_data.name = name
      event_data.server_name = server_name
      event_data.share_name = share_name
      event_data.type = source_type

      parser_mediator.ProduceEventData(event_data)


winreg_parser.WinRegistryParser.RegisterPlugin(MountPoints2Plugin)
