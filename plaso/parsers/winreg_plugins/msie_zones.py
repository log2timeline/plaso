# -*- coding: utf-8 -*-
"""This file contains the MSIE zone settings plugin."""

from plaso.containers import time_events
from plaso.containers import windows_events
from plaso.lib import definitions
from plaso.parsers import winreg
from plaso.parsers.winreg_plugins import interface


__author__ = 'Elizabeth Schweinsberg (beth@bethlogic.net)'


class MsieZoneSettingsPlugin(interface.WindowsRegistryPlugin):
  """Windows Registry plugin for parsing the MSIE Zones settings.

    The MSIE Feature controls are stored in the Zone specific subkeys in:
      Internet Settings\\Zones key
      Internet Settings\\Lockdown_Zones key
  """

  NAME = u'msie_zone'
  DESCRIPTION = u'Parser for Internet Explorer zone settings Registry data.'

  FILTERS = frozenset([
      interface.WindowsRegistryKeyPathFilter(
          u'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\'
          u'Internet Settings\\Lockdown_Zones'),
      interface.WindowsRegistryKeyPathFilter(
          u'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\'
          u'Internet Settings\\Zones'),
      interface.WindowsRegistryKeyPathFilter(
          u'HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows\\CurrentVersion\\'
          u'Internet Settings\\Lockdown_Zones'),
      interface.WindowsRegistryKeyPathFilter(
          u'HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows\\CurrentVersion\\'
          u'Internet Settings\\Zones')])

  URLS = [u'http://support.microsoft.com/kb/182569']

  _ZONE_NAMES = {
      u'0': u'0 (My Computer)',
      u'1': u'1 (Local Intranet Zone)',
      u'2': u'2 (Trusted sites Zone)',
      u'3': u'3 (Internet Zone)',
      u'4': u'4 (Restricted Sites Zone)',
      u'5': u'5 (Custom)'
  }

  _KNOWN_PERMISSIONS_VALUE_NAMES = [
      u'1001', u'1004', u'1200', u'1201', u'1400', u'1402', u'1405', u'1406',
      u'1407', u'1601', u'1604', u'1606', u'1607', u'1608', u'1609', u'1800',
      u'1802', u'1803', u'1804', u'1809', u'1A04', u'2000', u'2001', u'2004',
      u'2100', u'2101', u'2102', u'2200', u'2201', u'2300']

  _CONTROL_VALUES_PERMISSIONS = {
      0x00000000: u'0 (Allow)',
      0x00000001: u'1 (Prompt User)',
      0x00000003: u'3 (Not Allowed)',
      0x00010000: u'0x00010000 (Administrator approved)'
  }

  _CONTROL_VALUES_SAFETY = {
      0x00010000: u'0x00010000 (High safety)',
      0x00020000: u'0x00020000 (Medium safety)',
      0x00030000: u'0x00030000 (Low safety)'
  }

  _CONTROL_VALUES_1A00 = {
      0x00000000: (
          u'0x00000000 (Automatic logon with current user name and password)'),
      0x00010000: u'0x00010000 (Prompt for user name and password)',
      0x00020000: u'0x00020000 (Automatic logon only in Intranet zone)',
      0x00030000: u'0x00030000 (Anonymous logon)'
  }

  _CONTROL_VALUES_1C00 = {
      0x00000000: u'0x00000000 (Disable Java)',
      0x00010000: u'0x00010000 (High safety)',
      0x00020000: u'0x00020000 (Medium safety)',
      0x00030000: u'0x00030000 (Low safety)',
      0x00800000: u'0x00800000 (Custom)'
  }

  _FEATURE_CONTROLS = {
      u'1200': u'Run ActiveX controls and plug-ins',
      u'1400': u'Active scripting',
      u'1001': u'Download signed ActiveX controls',
      u'1004': u'Download unsigned ActiveX controls',
      u'1201': u'Initialize and script ActiveX controls not marked as safe',
      u'1206': u'Allow scripting of IE Web browser control',
      u'1207': u'Reserved',
      u'1208': (
          u'Allow previously unused ActiveX controls to run without prompt'),
      u'1209': u'Allow Scriptlets',
      u'120A': u'Override Per-Site (domain-based) ActiveX restrictions',
      u'120B': u'Override Per-Site (domain-based) ActiveX restrictions',
      u'1402': u'Scripting of Java applets',
      u'1405': u'Script ActiveX controls marked as safe for scripting',
      u'1406': u'Access data sources across domains',
      u'1407': u'Allow Programmatic clipboard access',
      u'1408': u'Reserved',
      u'1601': u'Submit non-encrypted form data',
      u'1604': u'Font download',
      u'1605': u'Run Java',
      u'1606': u'Userdata persistence',
      u'1607': u'Navigate sub-frames across different domains',
      u'1608': u'Allow META REFRESH',
      u'1609': u'Display mixed content',
      u'160A': u'Include local directory path when uploading files to a server',
      u'1800': u'Installation of desktop items',
      u'1802': u'Drag and drop or copy and paste files',
      u'1803': u'File Download',
      u'1804': u'Launching programs and files in an IFRAME',
      u'1805': u'Launching programs and files in webview',
      u'1806': u'Launching applications and unsafe files',
      u'1807': u'Reserved',
      u'1808': u'Reserved',
      u'1809': u'Use Pop-up Blocker',
      u'180A': u'Reserved',
      u'180B': u'Reserved',
      u'180C': u'Reserved',
      u'180D': u'Reserved',
      u'1A00': u'User Authentication: Logon',
      u'1A02': u'Allow persistent cookies that are stored on your computer',
      u'1A03': u'Allow per-session cookies (not stored)',
      u'1A04': u'Don\'t prompt for client cert selection when no certs exists',
      u'1A05': u'Allow 3rd party persistent cookies',
      u'1A06': u'Allow 3rd party session cookies',
      u'1A10': u'Privacy Settings',
      u'1C00': u'Java permissions',
      u'1E05': u'Software channel permissions',
      u'1F00': u'Reserved',
      u'2000': u'Binary and script behaviors',
      u'2001': u'.NET: Run components signed with Authenticode',
      u'2004': u'.NET: Run components not signed with Authenticode',
      u'2100': u'Open files based on content, not file extension',
      u'2101': u'Web sites in less privileged zone can navigate into this zone',
      u'2102': (
          u'Allow script initiated windows without size/position constraints'),
      u'2103': u'Allow status bar updates via script',
      u'2104': u'Allow websites to open windows without address or status bars',
      u'2105': (
          u'Allow websites to prompt for information using scripted windows'),
      u'2200': u'Automatic prompting for file downloads',
      u'2201': u'Automatic prompting for ActiveX controls',
      u'2300': (
          u'Allow web pages to use restricted protocols for active content'),
      u'2301': u'Use Phishing Filter',
      u'2400': u'.NET: XAML browser applications',
      u'2401': u'.NET: XPS documents',
      u'2402': u'.NET: Loose XAML',
      u'2500': u'Turn on Protected Mode',
      u'2600': u'Enable .NET Framework setup',
      u'{AEBA21FA-782A-4A90-978D-B72164C80120}': u'First Party Cookie',
      u'{A8A88C49-5EB2-4990-A1A2-0876022C854F}': u'Third Party Cookie'
  }

  def ExtractEvents(self, parser_mediator, registry_key, **kwargs):
    """Extracts events from a Windows Registry key.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
    """
    values_dict = {}

    if registry_key.number_of_values > 0:
      for registry_value in registry_key.GetValues():
        value_name = registry_value.name or u'(default)'

        if registry_value.DataIsString():
          value_string = u'[{0:s}] {1:s}'.format(
              registry_value.data_type_string, registry_value.GetDataAsObject())

        elif registry_value.DataIsInteger():
          value_string = u'[{0:s}] {1:d}'.format(
              registry_value.data_type_string, registry_value.GetDataAsObject())

        elif registry_value.DataIsMultiString():
          value_string = u'[{0:s}] {1:s}'.format(
              registry_value.data_type_string, u''.join(
                  registry_value.GetDataAsObject()))

        else:
          value_string = u'[{0:s}]'.format(registry_value.data_type_string)

        values_dict[value_name] = value_string

    # Generate at least one event object for the key.
    event_data = windows_events.WindowsRegistryEventData()
    event_data.key_path = registry_key.path
    event_data.offset = registry_key.offset
    event_data.regvalue = values_dict
    event_data.urls = self.URLS

    event = time_events.DateTimeValuesEvent(
        registry_key.last_written_time, definitions.TIME_DESCRIPTION_WRITTEN)
    parser_mediator.ProduceEventWithEventData(event, event_data)

    if registry_key.number_of_subkeys == 0:
      error_string = u'Key: {0:s} missing subkeys.'.format(registry_key.path)
      parser_mediator.ProduceExtractionError(error_string)
      return

    for zone_key in registry_key.GetSubkeys():
      # TODO: these values are stored in the Description value of the
      # zone key. This solution will break on zone values that are larger
      # than 5.
      path = u'{0:s}\\{1:s}'.format(
          registry_key.path, self._ZONE_NAMES[zone_key.name])

      values_dict = {}

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
                value_integer, u'UNKNOWN')
          elif value.name == u'1A00':
            value_string = self._CONTROL_VALUES_1A00.get(
                value_integer, u'UNKNOWN')
          elif value.name == u'1C00':
            value_string = self._CONTROL_VALUES_1C00.get(
                value_integer, u'UNKNOWN')
          elif value.name == u'1E05':
            value_string = self._CONTROL_VALUES_SAFETY.get(
                value_integer, u'UNKNOWN')
          else:
            value_string = u'{0:d}'.format(value_integer)

        else:
          value_string = u'[{0:s}]'.format(value.data_type_string)

        if len(value.name) == 4 and value.name != u'Icon':
          value_description = self._FEATURE_CONTROLS.get(value.name, u'UNKNOWN')
        else:
          value_description = self._FEATURE_CONTROLS.get(value.name, u'')

        if value_description:
          feature_control = u'[{0:s}] {1:s}'.format(
              value.name, value_description)
        else:
          feature_control = u'[{0:s}]'.format(value.name)

        values_dict[feature_control] = value_string

      event_data = windows_events.WindowsRegistryEventData()
      event_data.key_path = path
      event_data.offset = zone_key.offset
      event_data.regvalue = values_dict
      event_data.urls = self.URLS

      event = time_events.DateTimeValuesEvent(
          zone_key.last_written_time, definitions.TIME_DESCRIPTION_WRITTEN)
      parser_mediator.ProduceEventWithEventData(event, event_data)


winreg.WinRegistryParser.RegisterPlugin(MsieZoneSettingsPlugin)
