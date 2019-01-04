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
    test_definition = presets.ParserPresetDefinition()
    self.assertIsNotNone(test_definition)


class ParserPresetsTest(shared_test_lib.BaseTestCase):
  """Tests for the parser and parser pluging presets."""

  def testGetNames(self):
    """Tests the GetNames function."""
    test_parser_presets = presets.ParserPresets()

    test_names = list(test_parser_presets.GetNames())
    self.assertNotEqual(len(test_names), 0)

  def testGetPresetByName(self):
    """Tests the GetPresetByName function."""
    test_parser_presets = presets.ParserPresets()

    test_preset = test_parser_presets.GetPresetByName('linux')
    self.assertIsNotNone(test_preset)
    self.assertEqual(test_preset.name, 'linux')

    test_preset = test_parser_presets.GetPresetByName('bogus')
    self.assertIsNone(test_preset)

  def testGetPresets(self):
    """Tests the GetPresets function."""
    test_parser_presets = presets.ParserPresets()

    test_presets = list(test_parser_presets.GetPresets())
    self.assertNotEqual(len(test_presets), 0)


if __name__ == '__main__':
  unittest.main()
