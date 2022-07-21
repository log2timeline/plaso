#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Windows Defender History parser."""

import unittest

from plaso.parsers import windefenderhistory

from tests.parsers import test_lib


class WinDefenderHistoryUnitTest(test_lib.ParserTestCase):
  """Tests for the Windows Defender History parser."""

  def testWebFileDetection(self):
    """Tests parsing a webfile Detection History file."""
    parser = windefenderhistory.WinDefenderHistoryParser()
    storage_writer = self._ParseFile([
      'defender/'
      'f34a0f70391bc24ecd465f713c6b068cc24dd05d71994924abbb438ba9eecf62'
    ], parser)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    for event in storage_writer.GetEvents():
      event_data = self._GetEventDataOfEvent(storage_writer, event)
      self.assertEqual(
          'C:\\Users\\Luqman\\Downloads\\Ransomware.Jigsaw.zip',
          event_data.filename)
      self.assertEqual(
          'C:\\Users\\Luqman\\Downloads\\Ransomware.Jigsaw.zip|http://10.1.20.13:8000/Ransomware.Jigsaw.zip|pid:1020,ProcessStart:132525829301711007', # pylint: disable=line-too-long
          event_data.web_filename)
      self.assertEqual(
          '86a391fe7a237f4f17846c53d71e45820411d1a9a6e0c16f22a11ebc491ff9ff',
          event_data.sha256)
      self.assertEqual('Trojan:Win32/Vigorf.A', event_data.threatname)
      self.assertEqual('DESKTOP-38RB3EF\\Luqman',
                        event_data.host_and_user)
      self.assertEqual('Unknown', event_data.process)
      self.assertEqual('2020-12-16 09:02:12',
                        event.date_time.CopyToDateTimeString())

  def testContainerDetection(self):
    """Tests parsing a containerfile Detection History file."""
    parser = windefenderhistory.WinDefenderHistoryParser()
    storage_writer = self._ParseFile([
        'defender/'
        '5f747e1ce825ffb36d0cbd7e9348886e79a71f7f317b1c0afe11f6baafa35015'
    ], parser)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    for event in storage_writer.GetEvents():
      event_data = self._GetEventDataOfEvent(storage_writer, event)
      self.assertEqual(
          'C:\\Users\\bkara\\AppData\\Local\\Mozilla\\Firefox\\Profiles\\2k4x3nr9.default-release\\cache2\\entries\\32F0AE83BF7D7CFE8D5B679DE93E8E189345BB6C->(GZip)->(SCRIPT0001)', # pylint: disable=line-too-long
          event_data.filename)
      self.assertEqual(
          '82e242b2951403ef2d288fb97f428b830900530f85f1b4689a6130b328aa4c45',
          event_data.sha256)
      self.assertEqual('Trojan:HTML/Phish.VS!MSR', event_data.threatname)
      self.assertEqual(
          'C:\\Users\\bkara\\AppData\\Local\\Mozilla\\Firefox\\Profiles\\2k4x3nr9.default-release\\cache2\\entries\\32F0AE83BF7D7CFE8D5B679DE93E8E189345BB6C', # pylint: disable=line-too-long
          event_data.container_filename)
      self.assertEqual('DESKTOP-E9T3V5E\\bkara',
                        event_data.host_and_user)
      self.assertEqual('Unknown', event_data.process)

  def testRegistryBasedDetection(self):
    """Tests parsing a regkey Detection History file."""
    parser = windefenderhistory.WinDefenderHistoryParser()
    storage_writer = self._ParseFile([
        'defender/'
        '233c51b726822b2223142d8d05976509936ce28323006f7f8a89ca1e8b7f14b6'
    ], parser)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    for event in storage_writer.GetEvents():
      event_data = self._GetEventDataOfEvent(storage_writer, event)
      self.assertEqual('VirTool:Win32/DefenderTamperingRestore',
                        event_data.threatname)
      self.assertEqual('UNKNOWN', event_data.filename)
      self.assertEqual('UNKNOWN', event_data.sha256)
      self.assertEqual(
          'hklm\\software\\microsoft\\windows defender\\\\DisableAntiSpyware',
          event_data.extra)
      self.assertEqual('NT AUTHORITY\\SYSTEM', event_data.host_and_user)
      self.assertEqual('Unknown', event_data.process)

  def testProcessBasedDetection(self):
    """Tests parsing a process:// Detection History file."""
    parser = windefenderhistory.WinDefenderHistoryParser()
    storage_writer = self._ParseFile([
        'defender/'
        '535d641be9356b67a4fa15fafd516187fa6c2e585e16be6813b56f47ead81c83'
    ], parser)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    for event in storage_writer.GetEvents():
      event_data = self._GetEventDataOfEvent(storage_writer, event)
      self.assertEqual('Trojan:Win32/Delf.BB', event_data.threatname)
      self.assertEqual(
          'process://C:\\Program Files (x86)\\DesktopCentral_Agent\\dcconfig.exe,pid:53668,ProcessStart:133004481826348874', # pylint: disable=line-too-long
          event_data.filename)
      self.assertEqual(
          '4219fd3fd695a020bf5d300d7b9cf80806af2aa626c59713587d7f6c650e58bb',
          event_data.sha256)
      self.assertEqual('pid:53668,ProcessStart:133004481826348874',
                        event_data.extra)
      self.assertEqual('NT AUTHORITY\\SYSTEM', event_data.host_and_user)
      self.assertEqual(
          'C:\\Program Files (x86)\\DesktopCentral_Agent\\dcconfig.exe',
          event_data.process)

  def testNoFilenameFrenchSystem(self):
    """Tests parsing a french Detection History file with a ThreatData key."""
    parser = windefenderhistory.WinDefenderHistoryParser()
    storage_writer = self._ParseFile([
        'defender/'
        'b7c5b9dc8388a709849bbf6c7a03b3a55ae8a1edaa87c16779bf01668ebce299'
    ], parser)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    for event in storage_writer.GetEvents():
      event_data = self._GetEventDataOfEvent(storage_writer, event)
      self.assertEqual('VirTool:Win32/ExcludeProc.D',
                        event_data.threatname)
      self.assertEqual('UNKNOWN', event_data.filename)
      self.assertEqual('UNKNOWN', event_data.sha256)
      self.assertEqual(
          'C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe -EncodedCommand QQBkAGQALQBNAHAAUAByAGUAZgBlAHIAZQBuAGMAZQAgAC0ARQB4AGMAbAB1AHMAaQBvAG4ARQB4AHQAZQBuAHMAaQBvAG4AIABAACgAJwBlAHgAZQAnACwAJwBkAGwAbAAnACkAIAAtAEYAbwByAGMAZQA=, C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe -EncodedCommand QQBkAGQALQBNAHAAUAByAGUAZgBlAHIAZQBuAGMAZQAgAC0ARQB4AGMAbAB1AHMAaQBvAG4AUABhAHQAaAAgAEAAKAAkAGUAbgB2ADoAVQBzAGUAcgBQAHIAbwBmAGkAbABlACwAJABlAG4AdgA6AFMAeQBzAHQAZQBtAEQAcgBpAHYAZQApACAALQBGAG8AcgBjAGUA, i AQAAAIkSBYAAAAAAAAAAAGchilvXwQAAoQYaJ1g0xpRzihIDOX+yDaJMTaBWaXJUb29sOldpbjMyL0V4Y2x1ZGVQcm9jLkQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA== 57 10 C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe powershell -EncodedCommand QQBkAGQALQBNAHAAUAByAGUAZgBlAHIAZQBuAGMAZQAgAC0ARQB4AGMAbAB1AHMAaQBvAG4ARQB4AHQAZQBuAHMAaQBvAG4AIABAACgAJwBlAHgAZQAnACwAJwBkAGwAbAAnACkAIAAtAEYAbwByAGMAZQA=, i AQAAAIkSBYAAAAAAAAAAAGchilvXwQAAoQYaJ1g0xpRzihIDOX+yDaJMTaBWaXJUb29sOldpbjMyL0V4Y2x1ZGVQcm9jLkQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA== 57 10 C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe powershell -EncodedCommand QQBkAGQALQBNAHAAUAByAGUAZgBlAHIAZQBuAGMAZQAgAC0ARQB4AGMAbAB1AHMAaQBvAG4AUABhAHQAaAAgAEAAKAAkAGUAbgB2ADoAVQBzAGUAcgBQAHIAbwBmAGkAbABlACwAJABlAG4AdgA6AFMAeQBzAHQAZQBtAEQAcgBpAHYAZQApACAALQBGAG8AcgBjAGUA', # pylint: disable=line-too-long
          event_data.extra)
      self.assertEqual('AUTORITE NT\\Système', event_data.host_and_user)
      self.assertEqual('Unknown', event_data.process)


if __name__ == '__main__':
  unittest.main()
