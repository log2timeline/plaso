#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for PowerShell transcript parser"""

import unittest

from plaso.lib import errors
from plaso.parsers import powershell_transcript

from tests.parsers import test_lib


class PowerShellTranscriptParserTest(test_lib.ParserTestCase):
  """Tests for the PowerShell Transcript parser"""

  def testParseEng(self):
    """Tests the parse function on an example file with english locale."""
    parser = powershell_transcript.PowerShellTranscriptParser()
    storage_writer = self._ParseFile(
        ['powershell_transcript.txt'], parser)

    number_of_events = storage_writer.GetNumberOfAttributeContainers(
        'event')
    self.assertEqual(number_of_events, 1)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetSortedEvents())

    expected_event_values = {
        'build_version': '10.0.17763.1852',
        'clr_version': '4.0.30319.42000',
        'command': 'PS C:\\Windows\\system32> whoami; msedgewin10\\ieuser; ',
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

  def testParseGer(self):
    """Tests the parse function on an example file with german locale."""
    parser_ger = powershell_transcript.PowerShellTranscriptParser()
    storage_writer_ger = self._ParseFile(
        ['powershell_transcript_ger.txt'], parser_ger)

    number_of_events = storage_writer_ger.GetNumberOfAttributeContainers(
        'event')
    # actually 3 Events, but as per l.297 (powershell_transcript.py)
    # currently only the first 2 will be parsed correctly
    self.assertEqual(number_of_events, 2)

    number_of_warnings = storage_writer_ger.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer_ger.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events_ger = list(storage_writer_ger.GetSortedEvents())
    expected_event_values_ger_0 = {
        'build_version': '10.0.19041.1682',
        'clr_version': '4.0.30319.42000',
        'command': (
            'Die Aufzeichnung wurde gestartet. '
            'Die Ausgabedatei ist "C:\\Users\\User\\'
            'Documents\\PowerShell_transcript.MySystem.'
            'rvARGulQ.20220824122111.txt".; PS C:\\Users\\User> whoami; '
            'de\\User; PS C:\\Users\\User> echo $null >> filename; '
            'PS C:\\Users\\User> ping 8.8.8.8; Ping wird ausgeführt für '
            '8.8.8.8 mit 32 Bytes Daten:; Zeitüberschreitung der '
            'Anforderung.; Ping-Statistik für 8.8.8.8:; Pakete: '
            'Gesendet = 1, Empfangen = 0, Verloren = 1; (100% Verlust),'
            '; STRG-C; PS C:\\Users\\User> TerminatingError(): "Die '
            'Pipeline wurde beendet."; >> TerminatingError(): "Die '
            'Pipeline wurde beendet."; PS C:\\Users\\User> Get-Content '
            '.\\myfile.txt; VERBOSE: Simple Test; '
        ),
        'compatible_versions': '1.0, 2.0, 3.0, 4.0, 5.0, 5.1.19041.1682',
        'date_time': '2022-08-24 12:21:11',
        'data_type': 'powershell:transcript:event',
        'edition': 'Desktop',
        'host_application':
            'C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe',
        'machine': 'MySystem (Microsoft Windows NT 10.0.19044.0)',
        'process_id': '18716',
        'remoting_protocol_version': '2.3',
        'runas_user': 'DE\\User',
        'serialization_version': '1.1.0.1',
        'username': 'DE\\User',
        'version': '5.1.19041.1682',
        'ws_man_stack_version': '3.0'}

    self.CheckEventValues(
        storage_writer_ger, events_ger[0], expected_event_values_ger_0)

    expected_event_values_ger_1 = {
        'build_version': '10.0.19041.1682',
        'clr_version': '4.0.30319.42000',
        'command': (
            'PS C:\\Users\\User\\Documents> '
            'ping 127.0.0.1 -n 5; Ping wird ausgeführt '
            'für 127.0.0.1 mit 32 Bytes Daten:; Antwort '
            'von 127.0.0.1: Bytes=32 Zeit<1ms TTL=128; '
            'Antwort von 127.0.0.1: Bytes=32 Zeit<1ms TTL=128; '
            'Antwort von 127.0.0.1: Bytes=32 Zeit<1ms TTL=128; '
            'Antwort von 127.0.0.1: Bytes=32 Zeit=1ms TTL=128; '
            'Antwort von 127.0.0.1: Bytes=32 Zeit<1ms TTL=128; '
            'Ping-Statistik für 127.0.0.1:; Pakete: Gesendet = 5, '
            'Empfangen = 5, Verloren = 0; (0% Verlust),; Ca. '
            'Zeitangaben in Millisek.:; Minimum = 0ms, Maximum '
            '= 1ms, Mittelwert = 0ms; '
        ),
        'compatible_versions': '1.0, 2.0, 3.0, 4.0, 5.0, 5.1.19041.1682',
        'date_time': '2022-08-24 12:31:14',
        'data_type': 'powershell:transcript:event',
        'edition': 'Desktop',
        'host_application':
            'C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe',
        'machine': 'MySystem (Microsoft Windows NT 10.0.19044.0)',
        'process_id': '18716',
        'remoting_protocol_version': '2.3',
        'runas_user': 'DE\\User',
        'serialization_version': '1.1.0.1',
        'username': 'DE\\User',
        'version': '5.1.19041.1682',
        'ws_man_stack_version': '3.0'}

    self.CheckEventValues(
        storage_writer_ger, events_ger[1], expected_event_values_ger_1)

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
