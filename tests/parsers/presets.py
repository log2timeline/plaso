#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for parser and parser plugin presets."""

from __future__ import unicode_literals

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


@shared_test_lib.skipUnlessHasTestFile(['presets.yaml'])
class ParserPresetsManagerTest(shared_test_lib.BaseTestCase):
  """Tests for the parser and parser plugin presets manager."""

  # TODO add tests for _ReadPresetDefinitionValues
  # TODO add tests for _ReadPresetsFromFileObject

  def testGetNames(self):
    """Tests the GetNames function."""
    test_manager = presets.ParserPresetsManager()

    test_path = self._GetTestFilePath(['presets.yaml'])
    test_manager.ReadFromFile(test_path)

    test_names = list(test_manager.GetNames())
    self.assertEqual(len(test_names), 7)

    expected_names = sorted([
        'android', 'linux', 'macos', 'webhist', 'win7', 'win_gen', 'winxp'])
    self.assertEqual(test_names, expected_names)

  def testGetPresetByName(self):
    """Tests the GetPresetByName function."""
    test_manager = presets.ParserPresetsManager()

    test_path = self._GetTestFilePath(['presets.yaml'])
    test_manager.ReadFromFile(test_path)

    test_preset = test_manager.GetPresetByName('linux')
    self.assertIsNotNone(test_preset)
    self.assertEqual(test_preset.name, 'linux')

    expected_parsers = [
        'bash_history',
        'bencode',
        'czip/oxml',
        'dockerjson',
        'dpkg',
        'filestat',
        'gdrive_synclog',
        'java_idx',
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
        'webhist',
        'xchatlog',
        'xchatscrollback',
        'zsh_extended_history']

    self.assertEqual(test_preset.parsers, expected_parsers)

    test_preset = test_manager.GetPresetByName('bogus')
    self.assertIsNone(test_preset)

  def testGetPresetsByOperatingSystem(self):
    """Tests the GetPresetsByOperatingSystem function."""
    test_manager = presets.ParserPresetsManager()

    test_path = self._GetTestFilePath(['presets.yaml'])
    test_manager.ReadFromFile(test_path)

    operating_system = artifacts.OperatingSystemArtifact(family='MacOS')

    test_presets = test_manager.GetPresetsByOperatingSystem(operating_system)
    self.assertEqual(len(test_presets), 1)
    self.assertEqual(test_presets[0].name, 'macos')

    expected_parsers = [
        'asl_log',
        'bash_history',
        'bencode',
        'bsm_log',
        'cups_ipp',
        'czip/oxml',
        'filestat',
        'fseventsd',
        'gdrive_synclog',
        'java_idx',
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

    self.assertEqual(test_presets[0].parsers, expected_parsers)

    operating_system = artifacts.OperatingSystemArtifact(family='bogus')

    test_presets = test_manager.GetPresetsByOperatingSystem(operating_system)
    self.assertEqual(len(test_presets), 0)

  def testGetPresets(self):
    """Tests the GetPresets function."""
    test_manager = presets.ParserPresetsManager()

    test_path = self._GetTestFilePath(['presets.yaml'])
    test_manager.ReadFromFile(test_path)

    test_presets = list(test_manager.GetPresets())
    self.assertEqual(len(test_presets), 7)

  # TODO add tests for ReadFromFile


if __name__ == '__main__':
  unittest.main()
