#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for parser and parser plugin presets."""

import unittest

from plaso.containers import artifacts
from plaso.parsers import presets

from tests import test_lib as shared_test_lib


class ParserPresetTest(shared_test_lib.BaseTestCase):
  """Tests for the parser and parser plugin preset."""

  def testInitialize(self):
    """Tests the __init__ function."""
    test_definition = presets.ParserPreset('test', ['parser1', 'parser2'])
    self.assertIsNotNone(test_definition)


class ParserPresetsManagerTest(shared_test_lib.BaseTestCase):
  """Tests for the parser and parser plugin presets manager."""

  _LINUX_PARSERS = [
      'bash_history',
      'bencode',
      'czip/oxml',
      'dockerjson',
      'dpkg',
      'filestat',
      'gdrive_synclog',
      'olecf',
      'pls_recall',
      'popularity_contest',
      'selinux',
      'sqlite/google_drive',
      'sqlite/skype',
      'sqlite/zeitgeist',
      'syslog',
      'systemd_journal',
      'utmp',
      'vsftpd',
      'webhist',
      'xchatlog',
      'xchatscrollback',
      'zsh_extended_history']

  _MACOS_PARSERS = [
      'asl_log',
      'bash_history',
      'bencode',
      'bsm_log',
      'cups_ipp',
      'czip/oxml',
      'filestat',
      'fseventsd',
      'gdrive_synclog',
      'mac_appfirewall_log',
      'mac_keychain',
      'mac_securityd',
      'macwifi',
      'olecf',
      'plist',
      'sqlite/appusage',
      'sqlite/google_drive',
      'sqlite/imessage',
      'sqlite/ls_quarantine',
      'sqlite/mac_document_versions',
      'sqlite/mackeeper_cache',
      'sqlite/skype',
      'syslog',
      'utmpx',
      'webhist',
      'zsh_extended_history']

  # TODO add tests for _ReadPresetDefinitionValues
  # TODO add tests for _ReadPresetsFromFileObject

  def testGetNames(self):
    """Tests the GetNames function."""
    test_file_path = self._GetTestFilePath(['presets.yaml'])
    self._SkipIfPathNotExists(test_file_path)

    test_manager = presets.ParserPresetsManager()
    test_manager.ReadFromFile(test_file_path)

    test_names = list(test_manager.GetNames())
    self.assertEqual(len(test_names), 7)

    expected_names = sorted([
        'android', 'linux', 'macos', 'webhist', 'win7', 'win_gen', 'winxp'])
    self.assertEqual(test_names, expected_names)

  def testGetParsersByPreset(self):
    """Tests the GetParsersByPreset function."""
    test_file_path = self._GetTestFilePath(['presets.yaml'])
    self._SkipIfPathNotExists(test_file_path)

    test_manager = presets.ParserPresetsManager()
    test_manager.ReadFromFile(test_file_path)

    parser_names = test_manager.GetParsersByPreset('linux')
    self.assertEqual(parser_names, self._LINUX_PARSERS)

    with self.assertRaises(KeyError):
      test_manager.GetParsersByPreset('bogus')

  def testGetPresetByName(self):
    """Tests the GetPresetByName function."""
    test_file_path = self._GetTestFilePath(['presets.yaml'])
    self._SkipIfPathNotExists(test_file_path)

    test_manager = presets.ParserPresetsManager()
    test_manager.ReadFromFile(test_file_path)

    test_preset = test_manager.GetPresetByName('linux')
    self.assertIsNotNone(test_preset)
    self.assertEqual(test_preset.name, 'linux')

    self.assertEqual(test_preset.parsers, self._LINUX_PARSERS)

    test_preset = test_manager.GetPresetByName('bogus')
    self.assertIsNone(test_preset)

  def testGetPresetsByOperatingSystem(self):
    """Tests the GetPresetsByOperatingSystem function."""
    test_file_path = self._GetTestFilePath(['presets.yaml'])
    self._SkipIfPathNotExists(test_file_path)

    test_manager = presets.ParserPresetsManager()
    test_manager.ReadFromFile(test_file_path)

    operating_system = artifacts.OperatingSystemArtifact(family='MacOS')

    test_presets = test_manager.GetPresetsByOperatingSystem(operating_system)
    self.assertEqual(len(test_presets), 1)
    self.assertEqual(test_presets[0].name, 'macos')

    self.assertEqual(test_presets[0].parsers, self._MACOS_PARSERS)

    operating_system = artifacts.OperatingSystemArtifact(family='bogus')

    test_presets = test_manager.GetPresetsByOperatingSystem(operating_system)
    self.assertEqual(len(test_presets), 0)

  def testGetPresetsInformation(self):
    """Tests the GetPresetsInformation function."""
    test_file_path = self._GetTestFilePath(['presets.yaml'])
    self._SkipIfPathNotExists(test_file_path)

    test_manager = presets.ParserPresetsManager()
    test_manager.ReadFromFile(test_file_path)

    parser_presets_information = test_manager.GetPresetsInformation()
    self.assertGreaterEqual(len(parser_presets_information), 1)

    available_parser_names = [name for name, _ in parser_presets_information]
    self.assertIn('linux', available_parser_names)

  # TODO add tests for ReadFromFile


if __name__ == '__main__':
  unittest.main()
