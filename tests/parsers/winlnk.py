#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Windows Shortcut (LNK) parser."""

import unittest

from plaso.lib import definitions
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

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 5)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetEvents())

    # A shortcut last accessed event.
    expected_event_values = {
        'date_time': '2009-07-13 23:29:02.8491310',
        'data_type': 'windows:lnk:link',
        'description': '@%windir%\\system32\\migwiz\\wet.dll,-590',
        'env_var_location': '%windir%\\system32\\migwiz\\migwiz.exe',
        'file_attribute_flags': 0x00000020,
        'file_size': 544768,
        'icon_location': '%windir%\\system32\\migwiz\\migwiz.exe',
        'relative_path': '.\\migwiz\\migwiz.exe',
        'timestamp_desc': definitions.TIME_DESCRIPTION_LAST_ACCESS,
        'working_directory': '%windir%\\system32\\migwiz'}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    # A shortcut creation event.
    expected_event_values = {
        'date_time': '2009-07-13 23:29:02.8491310',
        'data_type': 'windows:lnk:link',
        'timestamp_desc': definitions.TIME_DESCRIPTION_CREATION}

    self.CheckEventValues(storage_writer, events[1], expected_event_values)

    # A shortcut last modification event.
    expected_event_values = {
        'date_time': '2009-07-14 01:39:18.2200000',
        'data_type': 'windows:lnk:link',
        'description': '@%windir%\\system32\\migwiz\\wet.dll,-590',
        'env_var_location': '%windir%\\system32\\migwiz\\migwiz.exe',
        'file_attribute_flags': 0x00000020,
        'file_size': 544768,
        'icon_location': '%windir%\\system32\\migwiz\\migwiz.exe',
        'relative_path': '.\\migwiz\\migwiz.exe',
        'timestamp_desc': definitions.TIME_DESCRIPTION_MODIFICATION,
        'working_directory': '%windir%\\system32\\migwiz'}

    self.CheckEventValues(storage_writer, events[2], expected_event_values)

    # A distributed link tracking creation event.
    expected_event_values = {
        'date_time': '2009-07-14 05:45:20.5000123',
        'data_type': 'windows:distributed_link_tracking:creation',
        'mac_address': '00:1d:09:fa:5a:1c',
        'timestamp_desc': definitions.TIME_DESCRIPTION_CREATION,
        'uuid': '846ee3bb-7039-11de-9d20-001d09fa5a1c'}

    self.CheckEventValues(storage_writer, events[4], expected_event_values)

  def testParseLinkTargetIdentifier(self):
    """Tests the Parse function on an LNK with a link target identifier."""
    parser = winlnk.WinLnkParser()
    storage_writer = self._ParseFile(['NeroInfoTool.lnk'], parser)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 20)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetEvents())

    # A shortcut creation event.
    expected_event_values = {
        'date_time': '2009-06-05 20:13:20.0000000',
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
            '%ProgramFiles%\\Nero\\Nero 9\\Nero InfoTool\\InfoTool.exe'),
        'local_path': (
            'C:\\Program Files (x86)\\Nero\\Nero 9\\Nero InfoTool\\'
            'InfoTool.exe'),
        'relative_path': (
            '..\\..\\..\\..\\..\\..\\..\\..\\Program Files (x86)\\'
            'Nero\\Nero 9\\Nero InfoTool\\InfoTool.exe'),
        'timestamp_desc': definitions.TIME_DESCRIPTION_CREATION,
        'volume_label': 'OS',
        'working_directory': (
            'C:\\Program Files (x86)\\Nero\\Nero 9\\Nero InfoTool')}

    self.CheckEventValues(storage_writer, events[16], expected_event_values)

    # A shell item event.
    expected_event_values = {
        'date_time': '2009-06-05 20:13:20',
        'data_type': 'windows:shell_item:file_entry',
        'file_reference': '81349-1',
        'long_name': 'InfoTool.exe',
        'name': 'InfoTool.exe',
        'origin': 'NeroInfoTool.lnk',
        'shell_item_path': (
            '<My Computer> C:\\Program Files (x86)\\Nero\\Nero 9\\'
            'Nero InfoTool\\InfoTool.exe'),
        'timestamp_desc': definitions.TIME_DESCRIPTION_CREATION}

    self.CheckEventValues(storage_writer, events[12], expected_event_values)


if __name__ == '__main__':
  unittest.main()
