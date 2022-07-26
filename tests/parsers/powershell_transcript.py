#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for PowerShell transcript parser"""

import unittest

from plaso.lib import errors
from plaso.parsers import powershell_transcript

from tests.parsers import test_lib


class PowerShellTranscriptParserTest(test_lib.ParserTestCase):
  """Tests for the PowerShell Transcript parser"""

  def testParse(self):
    """Tests the parse function on an example file."""
    parser = powershell_transcript.PowerShellTranscriptParser()
    storage_writer = self._ParseFile(
        ['powershell_transcript.txt'], parser)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 2)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 3)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetSortedEvents())

    # Test a regular event.
    expected_event_values = {
        'build_version': '10.0.17763.1852',
        'clr_version': '4.0.30319.42000',
        'command': 'PS C:\\Windows\\system32> whoami; msedgewin10\\ieuser',
        'compatible_versions': '1.0, 2.0, 3.0, 4.0, 5.0, 5.1.17763.1852',
        'date_time': '2022-07-21 02:37:49',
        'data_type': 'powershell:transcript:event',
        'edition': 'Desktop',
        'host_application':
          'C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe',
        'machine': 'MSEDGEWIN10 (Microsoft Windows NT 10.0.17763.0)',
        'process_id': '6456',
        'remoting_protocol_version': '2.3',
        'runas_user': 'MSEDGEWIN10\\IEUser',
        'serialization_version': '1.1.0.1',
        'username': 'MSEDGEWIN10\\IEUser',
        'version': '5.1.17763.1852',
        'ws_man_stack_version': '3.0'}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

  def testRaisesUnableToParseForInvalidFiles(self):
    """Test that attempting to parse an invalid file should raise an error."""
    parser = powershell_transcript.PowerShellTranscriptParser()

    invalid_file_name = 'access.log'
    invalid_file_path = self._GetTestFilePath([invalid_file_name])
    self._SkipIfPathNotExists(invalid_file_path)

    with self.assertRaises(errors.WrongParser):
      self._ParseFile(
          [invalid_file_name], parser)


if __name__ == '__main__':
  unittest.main()
