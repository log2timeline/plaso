# -*- coding: utf-8 -*-
"""This file contains the MSIE zone settings plugin."""

from plaso.containers import events
from plaso.parsers import winreg_parser
from plaso.parsers.winreg_plugins import interface


class MSIEZoneSettingsEventData(events.EventData):
  """MSIE zone settings event data attribute container.

  Attributes:
    key_path (str): Windows Registry key path.
    last_written_time (dfdatetime.DateTimeValues): entry last written date and
        time.
    settings (str): MSIE zone settings.
  """

  DATA_TYPE = 'windows:registry:msie_zone_settings'

  def __init__(self):
    """Initializes event data."""
    super(MSIEZoneSettingsEventData, self).__init__(data_type=self.DATA_TYPE)
    self.key_path = None
    self.last_written_time = None
    self.settings = None


class MSIEZoneSettingsPlugin(interface.WindowsRegistryPlugin):
  """Windows Registry plugin for parsing the MSIE zone settings.

  The MSIE Feature controls are stored in the Zone specific subkeys in:
    Internet Settings\\Zones key
    Internet Settings\\Lockdown_Zones key
  """

  NAME = 'msie_zone'
  DATA_FORMAT = 'Microsoft Internet Explorer zone settings Registry data'

  FILTERS = frozenset([
      interface.WindowsRegistryKeyPathFilter(
          'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\'
          'Internet Settings\\Lockdown_Zones'),
      interface.WindowsRegistryKeyPathFilter(
          'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\'
          'Internet Settings\\Zones'),
      interface.WindowsRegistryKeyPathFilter(
          'HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows\\CurrentVersion\\'
          'Internet Settings\\Lockdown_Zones'),
      interface.WindowsRegistryKeyPathFilter(
          'HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows\\CurrentVersion\\'
          'Internet Settings\\Zones')])

  _ZONE_NAMES = {
      '0': '0 (My Computer)',
      '1': '1 (Local Intranet Zone)',
      '2': '2 (Trusted sites Zone)',
      '3': '3 (Internet Zone)',
      '4': '4 (Restricted Sites Zone)',
      '5': '5 (Custom)'
  }

  _KNOWN_PERMISSIONS_VALUE_NAMES = [
      '1001', '1004', '1200', '1201', '1400', '1402', '1405', '1406',
      '1407', '1601', '1604', '1606', '1607', '1608', '1609', '1800',
      '1802', '1803', '1804', '1809', '1A04', '2000', '2001', '2004',
      '2100', '2101', '2102', '2200', '2201', '2300']

  _CONTROL_VALUES_PERMISSIONS = {
      0x00000000: '0 (Allow)',
      0x00000001: '1 (Prompt User)',
      0x00000003: '3 (Not Allowed)',
      0x00010000: '0x00010000 (Administrator approved)'
  }

  _CONTROL_VALUES_SAFETY = {
      0x00010000: '0x00010000 (High safety)',
      0x00020000: '0x00020000 (Medium safety)',
      0x00030000: '0x00030000 (Low safety)'
  }

  _CONTROL_VALUES_1A00 = {
      0x00000000: (
          '0x00000000 (Automatic logon with current user name and password)'),
      0x00010000: '0x00010000 (Prompt for user name and password)',
      0x00020000: '0x00020000 (Automatic logon only in Intranet zone)',
      0x00030000: '0x00030000 (Anonymous logon)'
  }

  _CONTROL_VALUES_1C00 = {
      0x00000000: '0x00000000 (Disable Java)',
      0x00010000: '0x00010000 (High safety)',
      0x00020000: '0x00020000 (Medium safety)',
      0x00030000: '0x00030000 (Low safety)',
      0x00800000: '0x00800000 (Custom)'
  }

  _FEATURE_CONTROLS = {
      '1200': 'Run ActiveX controls and plug-ins',
      '1400': 'Active scripting',
      '1001': 'Download signed ActiveX controls',
      '1004': 'Download unsigned ActiveX controls',
      '1201': 'Initialize and script ActiveX controls not marked as safe',
      '1206': 'Allow scripting of IE Web browser control',
      '1207': 'Reserved',
      '1208': (
          'Allow previously unused ActiveX controls to run without prompt'),
      '1209': 'Allow Scriptlets',
      '120A': 'Override Per-Site (domain-based) ActiveX restrictions',
      '120B': 'Override Per-Site (domain-based) ActiveX restrictions',
      '1402': 'Scripting of Java applets',
      '1405': 'Script ActiveX controls marked as safe for scripting',
      '1406': 'Access data sources across domains',
      '1407': 'Allow Programmatic clipboard access',
      '1408': 'Reserved',
      '1601': 'Submit non-encrypted form data',
      '1604': 'Font download',
      '1605': 'Run Java',
      '1606': 'Userdata persistence',
      '1607': 'Navigate sub-frames across different domains',
      '1608': 'Allow META REFRESH',
      '1609': 'Display mixed content',
      '160A': 'Include local directory path when uploading files to a server',
      '1800': 'Installation of desktop items',
      '1802': 'Drag and drop or copy and paste files',
      '1803': 'File Download',
      '1804': 'Launching programs and files in an IFRAME',
      '1805': 'Launching programs and files in webview',
      '1806': 'Launching applications and unsafe files',
      '1807': 'Reserved',
      '1808': 'Reserved',
      '1809': 'Use Pop-up Blocker',
      '180A': 'Reserved',
      '180B': 'Reserved',
      '180C': 'Reserved',
      '180D': 'Reserved',
      '1A00': 'User Authentication: Logon',
      '1A02': 'Allow persistent cookies that are stored on your computer',
      '1A03': 'Allow per-session cookies (not stored)',
      '1A04': 'Don\'t prompt for client cert selection when no certs exists',
      '1A05': 'Allow 3rd party persistent cookies',
      '1A06': 'Allow 3rd party session cookies',
      '1A10': 'Privacy Settings',
      '1C00': 'Java permissions',
      '1E05': 'Software channel permissions',
      '1F00': 'Reserved',
      '2000': 'Binary and script behaviors',
      '2001': '.NET: Run components signed with Authenticode',
      '2004': '.NET: Run components not signed with Authenticode',
      '2100': 'Open files based on content, not file extension',
      '2101': 'Web sites in less privileged zone can navigate into this zone',
      '2102': (
          'Allow script initiated windows without size/position constraints'),
      '2103': 'Allow status bar updates via script',
      '2104': 'Allow websites to open windows without address or status bars',
      '2105': (
          'Allow websites to prompt for information using scripted windows'),
      '2200': 'Automatic prompting for file downloads',
      '2201': 'Automatic prompting for ActiveX controls',
      '2300': (
          'Allow web pages to use restricted protocols for active content'),
      '2301': 'Use Phishing Filter',
      '2400': '.NET: XAML browser applications',
      '2401': '.NET: XPS documents',
      '2402': '.NET: Loose XAML',
      '2500': 'Turn on Protected Mode',
      '2600': 'Enable .NET Framework setup',
      '{AEBA21FA-782A-4A90-978D-B72164C80120}': 'First Party Cookie',
      '{A8A88C49-5EB2-4990-A1A2-0876022C854F}': 'Third Party Cookie'
  }

  def ExtractEvents(self, parser_mediator, registry_key, **kwargs):
    """Extracts events from a Windows Registry key.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
    """
    self._ProduceDefaultWindowsRegistryEvent(parser_mediator, registry_key)

    if registry_key.number_of_subkeys == 0:
      error_string = 'Key: {0:s} missing subkeys.'.format(registry_key.path)
      parser_mediator.ProduceExtractionWarning(error_string)
      return

    for zone_key in registry_key.GetSubkeys():
      # TODO: these values are stored in the Description value of the
      # zone key. This solution will break on zone values that are larger
      # than 5.
      path = '{0:s}\\{1:s}'.format(
          registry_key.path, self._ZONE_NAMES[zone_key.name])

      settings = []

      # TODO: this plugin currently just dumps the values and does not
      # distinguish between what is a feature control or not.
      for value in zone_key.GetValues():
        # Ignore the default value.
        if not value.name:
          continue

        if value.DataIsString():
          value_string = value.GetDataAsObject()

        elif value.DataIsInteger():
          value_integer = value.GetDataAsObject()
          if value.name in self._KNOWN_PERMISSIONS_VALUE_NAMES:
            value_string = self._CONTROL_VALUES_PERMISSIONS.get(
                value_integer, 'UNKNOWN')
          elif value.name == '1A00':
            value_string = self._CONTROL_VALUES_1A00.get(
                value_integer, 'UNKNOWN')
          elif value.name == '1C00':
            value_string = self._CONTROL_VALUES_1C00.get(
                value_integer, 'UNKNOWN')
          elif value.name == '1E05':
            value_string = self._CONTROL_VALUES_SAFETY.get(
                value_integer, 'UNKNOWN')
          else:
            value_string = '{0:d}'.format(value_integer)

        else:
          value_string = '[{0:s}]'.format(value.data_type_string)

        if len(value.name) == 4 and value.name != 'Icon':
          value_description = self._FEATURE_CONTROLS.get(value.name, 'UNKNOWN')
        else:
          value_description = self._FEATURE_CONTROLS.get(value.name, '')

        if value_description:
          feature_control = '[{0:s}] {1:s}: {2:s}'.format(
              value.name, value_description, value_string)
        else:
          feature_control = '[{0:s}]: {1:s}'.format(value.name, value_string)

        settings.append(feature_control)

      event_data = MSIEZoneSettingsEventData()
      event_data.key_path = path
      event_data.last_written_time = zone_key.last_written_time
      event_data.settings = ' '.join(sorted(settings))

      parser_mediator.ProduceEventData(event_data)


winreg_parser.WinRegistryParser.RegisterPlugin(MSIEZoneSettingsPlugin)
