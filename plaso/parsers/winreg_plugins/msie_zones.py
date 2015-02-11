# -*- coding: utf-8 -*-
"""This file contains the MSIE zone settings plugin."""

from plaso.events import windows_events
from plaso.parsers import winreg
from plaso.parsers.winreg_plugins import interface


__author__ = 'Elizabeth Schweinsberg (beth@bethlogic.net)'


class MsieZoneSettingsPlugin(interface.KeyPlugin):
  """Windows Registry plugin for parsing the MSIE Zones settings."""

  NAME = 'winreg_msie_zone'
  DESCRIPTION = u'Parser for Internet Explorer zone settings Registry data.'

  REG_TYPE = 'NTUSER'

  REG_KEYS = [
      (u'\\Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings'
       u'\\Zones'),
      (u'\\Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings'
       u'\\Lockdown_Zones')]

  URLS = ['http://support.microsoft.com/kb/182569']

  ZONE_NAMES = {
      '0': '0 (My Computer)',
      '1': '1 (Local Intranet Zone)',
      '2': '2 (Trusted sites Zone)',
      '3': '3 (Internet Zone)',
      '4': '4 (Restricted Sites Zone)',
      '5': '5 (Custom)'
  }

  KNOWN_PERMISSIONS_VALUE_NAMES = [
      '1001', '1004', '1200', '1201', '1400', '1402', '1405', '1406', '1407',
      '1601', '1604', '1606', '1607', '1608', '1609', '1800', '1802', '1803',
      '1804', '1809', '1A04', '2000', '2001', '2004', '2100', '2101', '2102',
      '2200', '2201', '2300']

  CONTROL_VALUES_PERMISSIONS = {
      0x00000000: '0 (Allow)',
      0x00000001: '1 (Prompt User)',
      0x00000003: '3 (Not Allowed)',
      0x00010000: '0x00010000 (Administrator approved)'
  }

  CONTROL_VALUES_SAFETY = {
      0x00010000: '0x00010000 (High safety)',
      0x00020000: '0x00020000 (Medium safety)',
      0x00030000: '0x00030000 (Low safety)'
  }

  CONTROL_VALUES_1A00 = {
      0x00000000: ('0x00000000 (Automatic logon with current user name and '
                   'password)'),
      0x00010000: '0x00010000 (Prompt for user name and password)',
      0x00020000: '0x00020000 (Automatic logon only in Intranet zone)',
      0x00030000: '0x00030000 (Anonymous logon)'
  }

  CONTROL_VALUES_1C00 = {
      0x00000000: '0x00000000 (Disable Java)',
      0x00010000: '0x00010000 (High safety)',
      0x00020000: '0x00020000 (Medium safety)',
      0x00030000: '0x00030000 (Low safety)',
      0x00800000: '0x00800000 (Custom)'
  }

  FEATURE_CONTROLS = {
      '1200': 'Run ActiveX controls and plug-ins',
      '1400': 'Active scripting',
      '1001': 'Download signed ActiveX controls',
      '1004': 'Download unsigned ActiveX controls',
      '1201': 'Initialize and script ActiveX controls not marked as safe',
      '1206': 'Allow scripting of IE Web browser control',
      '1207': 'Reserved',
      '1208': 'Allow previously unused ActiveX controls to run without prompt',
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
      '2102': ('Allow script initiated windows without size/position '
               'constraints'),
      '2103': 'Allow status bar updates via script',
      '2104': 'Allow websites to open windows without address or status bars',
      '2105': 'Allow websites to prompt for information using scripted windows',
      '2200': 'Automatic prompting for file downloads',
      '2201': 'Automatic prompting for ActiveX controls',
      '2300': 'Allow web pages to use restricted protocols for active content',
      '2301': 'Use Phishing Filter',
      '2400': '.NET: XAML browser applications',
      '2401': '.NET: XPS documents',
      '2402': '.NET: Loose XAML',
      '2500': 'Turn on Protected Mode',
      '2600': 'Enable .NET Framework setup',
      '{AEBA21FA-782A-4A90-978D-B72164C80120}': 'First Party Cookie',
      '{A8A88C49-5EB2-4990-A1A2-0876022C854F}': 'Third Party Cookie'
  }

  def GetEntries(
      self, parser_mediator, key=None, registry_type=None, codepage='cp1252',
      **unused_kwargs):
    """Retrieves information of the Internet Settings Zones values.

    The MSIE Feature controls are stored in the Zone specific subkeys in:
      Internet Settings\\Zones key
      Internet Settings\\Lockdown_Zones key

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      file_entry: optional file entry object (instance of dfvfs.FileEntry).
                  The default is None.
      key: Optional Registry key (instance of winreg.WinRegKey).
           The default is None.
      registry_type: Optional Registry type string. The default is None.
    """
    text_dict = {}

    if key.number_of_values == 0:
      error_string = u'Key: {0:s} missing values.'.format(key.path)
      parser_mediator.ProduceParseError(self.NAME, error_string)

    else:
      for value in key.GetValues():
        if not value.name:
          value_name = '(default)'
        else:
          value_name = u'{0:s}'.format(value.name)

        if value.DataIsString():
          value_string = u'[{0:s}] {1:s}'.format(
              value.data_type_string, value.data)
        elif value.DataIsInteger():
          value_string = u'[{0:s}] {1:d}'.format(
              value.data_type_string, value.data)
        elif value.DataIsMultiString():
          value_string = u'[{0:s}] {1:s}'.format(
              value.data_type_string, u''.join(value.data))
        else:
          value_string = u'[{0:s}]'.format(value.data_type_string)

        text_dict[value_name] = value_string

    # Generate at least one event object for the key.
    event_object = windows_events.WindowsRegistryEvent(
        key.last_written_timestamp, key.path, text_dict, offset=key.offset,
        registry_type=registry_type, urls=self.URLS)
    parser_mediator.ProduceEvent(event_object)

    if key.number_of_subkeys == 0:
      error_string = u'Key: {0:s} missing subkeys.'.format(key.path)
      parser_mediator.ProduceParseError(self.NAME, error_string)
      return

    for zone_key in key.GetSubkeys():
      # TODO: these values are stored in the Description value of the
      # zone key. This solution will break on zone values that are larger
      # than 5.
      path = u'{0:s}\\{1:s}'.format(key.path, self.ZONE_NAMES[zone_key.name])

      text_dict = {}

      # TODO: this plugin currently just dumps the values and does not
      # distinguish between what is a feature control or not.
      for value in zone_key.GetValues():
        # Ignore the default value.
        if not value.name:
          continue

        if value.DataIsString():
          value_string = value.data

        elif value.DataIsInteger():
          if value.name in self.KNOWN_PERMISSIONS_VALUE_NAMES:
            value_string = self.CONTROL_VALUES_PERMISSIONS.get(
                value.data, u'UNKNOWN')
          elif value.name == '1A00':
            value_string = self.CONTROL_VALUES_1A00.get(value.data, u'UNKNOWN')
          elif value.name == '1C00':
            value_string = self.CONTROL_VALUES_1C00.get(value.data, u'UNKNOWN')
          elif value.name == '1E05':
            value_string = self.CONTROL_VALUES_SAFETY.get(
                value.data, u'UNKNOWN')
          else:
            value_string = u'{0:d}'.format(value.data)

        else:
          value_string = u'[{0:s}]'.format(value.data_type_string)

        if len(value.name) == 4 and value.name != 'Icon':
          value_description = self.FEATURE_CONTROLS.get(value.name, 'UNKNOWN')
        else:
          value_description = self.FEATURE_CONTROLS.get(value.name, '')

        if value_description:
          feature_control = u'[{0:s}] {1:s}'.format(
              value.name, value_description)
        else:
          feature_control = u'[{0:s}]'.format(value.name)

        text_dict[feature_control] = value_string

      event_object = windows_events.WindowsRegistryEvent(
          zone_key.last_written_timestamp, path, text_dict,
          offset=zone_key.offset, registry_type=registry_type,
          urls=self.URLS)
      parser_mediator.ProduceEvent(event_object)


class MsieZoneSettingsSoftwareZonesPlugin(MsieZoneSettingsPlugin):
  """Parses the Zones key in the Software hive."""

  NAME = 'winreg_msie_zone_software'

  REG_TYPE = 'SOFTWARE'
  REG_KEYS = [
      u'\\Microsoft\\Windows\\CurrentVersion\\Internet Settings\\Zones',
      (u'\\Microsoft\\Windows\\CurrentVersion\\Internet Settings'
       u'\\Lockdown_Zones'),
      (u'\\Wow6432Node\\Microsoft\\Windows\\CurrentVersion\\Internet Settings'
       u'\\Zones'),
      (u'\\Wow6432Node\\Microsoft\\Windows\\CurrentVersion\\Internet Settings'
       u'\\Lockdown_Zones')]


winreg.WinRegistryParser.RegisterPlugins([
    MsieZoneSettingsPlugin, MsieZoneSettingsSoftwareZonesPlugin])
