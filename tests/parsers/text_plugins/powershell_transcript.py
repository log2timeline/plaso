#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for PowerShell transcript log text parser plugin."""

import unittest

from plaso.parsers.text_plugins import powershell_transcript

from tests.parsers.text_plugins import test_lib


class PowerShellTranscriptLogTextPluginTest(test_lib.TextPluginTestCase):
  """Tests for PowerShell transcript log text parser plugin."""

  def testProcess(self):
    """Tests the Process function ."""
    plugin = powershell_transcript.PowerShellTranscriptLogTextPlugin()
    storage_writer = self._ParseTextFileWithPlugin(
        ['powershell_transcript.txt'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 1)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'build_version': '10.0.17763.1852',
        'clr_version': '4.0.30319.42000',
        'commands': 'PS C:\\Windows\\system32> whoami; msedgewin10\\ieuser',
        'compatible_versions': '1.0, 2.0, 3.0, 4.0, 5.0, 5.1.17763.1852',
        'data_type': 'powershell:transcript_log:entry',
        'edition': 'Desktop',
        'host_application':
            'C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe',
        'machine': 'MSEDGEWIN10 (Microsoft Windows NT 10.0.17763.0)',
        'process_identifier': '6456',
        'remoting_protocol_version': '2.3',
        'runas_user': 'MSEDGEWIN10\\IEUser',
        'serialization_version': '1.1.0.1',
        'start_time': '2022-07-21T02:37:49',
        'username': 'MSEDGEWIN10\\IEUser',
        'version': '5.1.17763.1852',
        'ws_man_stack_version': '3.0'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)

  def testProcessGerman(self):
    """Tests the Process function on a file with German locale."""
    plugin = powershell_transcript.PowerShellTranscriptLogTextPlugin()
    storage_writer = self._ParseTextFileWithPlugin(
        ['powershell_transcript_ger.txt'], plugin)

    # actually 3 Events, but as per l.297 (powershell_transcript.py)
    # currently only the first 2 will be parsed correctly

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 2)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'build_version': '10.0.19041.1682',
        'clr_version': '4.0.30319.42000',
        'commands': (
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
            '.\\myfile.txt; VERBOSE: Simple Test'),
        'compatible_versions': '1.0, 2.0, 3.0, 4.0, 5.0, 5.1.19041.1682',
        'data_type': 'powershell:transcript_log:entry',
        'edition': 'Desktop',
        'host_application':
            'C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe',
        'machine': 'MySystem (Microsoft Windows NT 10.0.19044.0)',
        'process_identifier': '18716',
        'remoting_protocol_version': '2.3',
        'runas_user': 'DE\\User',
        'serialization_version': '1.1.0.1',
        'start_time': '2022-08-24T12:21:11',
        'username': 'DE\\User',
        'version': '5.1.19041.1682',
        'ws_man_stack_version': '3.0'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)

    expected_event_values = {
        'build_version': '10.0.19041.1682',
        'clr_version': '4.0.30319.42000',
        'commands': (
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
            '= 1ms, Mittelwert = 0ms'),
        'compatible_versions': '1.0, 2.0, 3.0, 4.0, 5.0, 5.1.19041.1682',
        'data_type': 'powershell:transcript_log:entry',
        'edition': 'Desktop',
        'host_application':
            'C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe',
        'machine': 'MySystem (Microsoft Windows NT 10.0.19044.0)',
        'process_identifier': '18716',
        'remoting_protocol_version': '2.3',
        'runas_user': 'DE\\User',
        'serialization_version': '1.1.0.1',
        'start_time': '2022-08-24T12:31:14',
        'username': 'DE\\User',
        'version': '5.1.19041.1682',
        'ws_man_stack_version': '3.0'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 1)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
