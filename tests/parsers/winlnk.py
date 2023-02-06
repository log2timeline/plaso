#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Windows Shortcut (LNK) parser."""

import unittest

from plaso.parsers import winlnk

from tests.parsers import test_lib


class WinLnkParserTest(test_lib.ParserTestCase):
  """Tests for the Windows Shortcut (LNK) parser."""

  def testParse(self):
    """Tests the Parse function."""
    parser = winlnk.WinLnkParser()
    storage_writer = self._ParseFile(['example.lnk'], parser)

    # Link information:
    #   Creation time                  : Jul 13, 2009 23:29:02.849131000 UTC
    #   Modification time              : Jul 14, 2009 01:39:18.220000000 UTC
    #   Access time                    : Jul 13, 2009 23:29:02.849131000 UTC
    #   Description                    : @%windir%\system32\migwiz\wet.dll,-590
    #   Relative path                  : .\migwiz\migwiz.exe
    #   Working directory              : %windir%\system32\migwiz
    #   Icon location                  : %windir%\system32\migwiz\migwiz.exe
    #   Environment variables location : %windir%\system32\migwiz\migwiz.exe

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 3)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    # Test shortcut event data.
    expected_event_values = {
        'access_time': '2009-07-13T23:29:02.8491310+00:00',
        'data_type': 'windows:lnk:link',
        'description': '@%windir%\\system32\\migwiz\\wet.dll,-590',
        'creation_time': '2009-07-13T23:29:02.8491310+00:00',
        'env_var_location': '%windir%\\system32\\migwiz\\migwiz.exe',
        'file_attribute_flags': 0x00000020,
        'file_size': 544768,
        'icon_location': '%windir%\\system32\\migwiz\\migwiz.exe',
        'modification_time': '2009-07-14T01:39:18.2200000+00:00',
        'relative_path': '.\\migwiz\\migwiz.exe',
        'working_directory': '%windir%\\system32\\migwiz'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)

    # Test distributed link tracking event data.
    expected_event_values = {
        'creation_time': '2009-07-14T05:45:20.5000123+00:00',
        'data_type': 'windows:distributed_link_tracking:creation',
        'mac_address': '00:1d:09:fa:5a:1c',
        'uuid': '846ee3bb-7039-11de-9d20-001d09fa5a1c'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 1)
    self.CheckEventData(event_data, expected_event_values)

  def testParseLinkTargetIdentifier(self):
    """Tests the Parse function on an LNK with a link target identifier."""
    parser = winlnk.WinLnkParser()
    storage_writer = self._ParseFile(['NeroInfoTool.lnk'], parser)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 8)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    # Test shortcut event data.
    expected_event_values = {
        'creation_time': '2009-06-05T20:13:20.0000000+00:00',
        'data_type': 'windows:lnk:link',
        'description': (
            'Nero InfoTool provides you with information about the most '
            'important features of installed drives, inserted discs, installed '
            'software and much more. With Nero InfoTool you can find out all '
            'about your drive and your system configuration.'),
        'drive_serial_number': 0x70ecfa33,
        'drive_type': 3,
        'file_attribute_flags': 0x00000020,
        'file_size': 4635160,
        'icon_location': (
            'C:\\Program Files (x86)\\Nero\\Nero 9\\Nero InfoTool\\'
            'InfoTool.exe'),
        'local_path': (
            'C:\\Program Files (x86)\\Nero\\Nero 9\\Nero InfoTool\\'
            'InfoTool.exe'),
        'relative_path': (
            '..\\..\\..\\..\\..\\..\\..\\..\\Program Files (x86)\\'
            'Nero\\Nero 9\\Nero InfoTool\\InfoTool.exe'),
        'volume_label': 'OS',
        'working_directory': (
            'C:\\Program Files (x86)\\Nero\\Nero 9\\Nero InfoTool')}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 5)
    self.CheckEventData(event_data, expected_event_values)

    # Test shell item event data.
    expected_event_values = {
        'access_time': '2010-01-29T21:30:12+00:00',
        'creation_time': '2009-06-05T20:13:20+00:00',
        'data_type': 'windows:shell_item:file_entry',
        'file_reference': '81349-1',
        'long_name': 'InfoTool.exe',
        'modification_time': '2009-06-05T20:13:20+00:00',
        'name': 'InfoTool.exe',
        'origin': 'NeroInfoTool.lnk',
        'shell_item_path': (
            '<My Computer> C:\\Program Files (x86)\\Nero\\Nero 9\\'
            'Nero InfoTool\\InfoTool.exe')}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 4)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
