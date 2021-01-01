#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for parser and parser plugin presets."""

import unittest

from plaso.parsers import presets
from plaso.parsers import manager as parsers_manager
from plaso.filters import parser_filter

from tests import test_lib as shared_test_lib


class PresetsDataTest(shared_test_lib.BaseTestCase):
  """Tests the presets.yaml file."""

  def testParsersAndPresets(self):
    """Tests that all parsers/plugins in presets.yaml are valid."""
    presets_file_path = self._GetDataFilePath(['presets.yaml'])

    preset_manager = presets.ParserPresetsManager()
    preset_manager.ReadFromFile(presets_file_path)
    filter_helper = parser_filter.ParserFilterExpressionHelper()

    for name in preset_manager.GetNames():
      expanded_preset = filter_helper.ExpandPresets(preset_manager, name)
      _, invalid_parser_elements = (
          parsers_manager.ParsersManager.CheckFilterExpression(expanded_preset))

      error_message = 'Invalid parser/plugin name(s) in preset: {0:s}'.format(
          name)
      self.assertFalse(invalid_parser_elements, msg=error_message)


if __name__ == '__main__':
  unittest.main()
