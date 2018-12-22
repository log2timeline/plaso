#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for parser and parser pluging presets."""

from __future__ import unicode_literals

import unittest

from plaso.parsers import presets

from tests import test_lib as shared_test_lib


class ParserPresetDefinitionTest(shared_test_lib.BaseTestCase):
  """Tests for the parser and parser pluging preset definition."""

  def testInitialize(self):
    """Tests the __init__ function."""
    test_definition = presets.ParserPresetDefinition(
        'test', ['parser1', 'parser2'])
    self.assertIsNotNone(test_definition)


@shared_test_lib.skipUnlessHasTestFile(['presets.yaml'])
class ParserPresetsTest(shared_test_lib.BaseTestCase):
  """Tests for the parser and parser pluging presets."""

  def testGetNames(self):
    """Tests the GetNames function."""
    test_parser_presets = presets.ParserPresets()

    test_path = self._GetTestFilePath(['presets.yaml'])
    test_parser_presets.ReadFromFile(test_path)

    test_names = list(test_parser_presets.GetNames())
    self.assertEqual(len(test_names), 7)

  def testGetPresetByName(self):
    """Tests the GetPresetByName function."""
    test_parser_presets = presets.ParserPresets()

    test_path = self._GetTestFilePath(['presets.yaml'])
    test_parser_presets.ReadFromFile(test_path)

    test_preset = test_parser_presets.GetPresetByName('linux')
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

    test_preset = test_parser_presets.GetPresetByName('bogus')
    self.assertIsNone(test_preset)

  def testGetPresets(self):
    """Tests the GetPresets function."""
    test_parser_presets = presets.ParserPresets()

    test_path = self._GetTestFilePath(['presets.yaml'])
    test_parser_presets.ReadFromFile(test_path)

    test_presets = list(test_parser_presets.GetPresets())
    self.assertEqual(len(test_presets), 7)


if __name__ == '__main__':
  unittest.main()
