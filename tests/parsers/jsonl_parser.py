#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the line-based JSON (JSON-L) log format parser."""

import unittest

from plaso.parsers import jsonl_parser
from plaso.parsers import jsonl_plugins  # pylint: disable=unused-import

from tests.parsers import test_lib


class JSONLParserTest(test_lib.ParserTestCase):
  """Tests for the line-based JSON (JSON-L) log format parser."""

  # pylint: disable=protected-access

  def testEnablePlugins(self):
    """Tests the EnablePlugins function."""
    parser = jsonl_parser.JSONLParser()

    number_of_plugins = len(parser._plugin_classes)

    parser.EnablePlugins([])
    self.assertEqual(len(parser._plugins_per_name), 0)

    parser.EnablePlugins(parser.ALL_PLUGINS)
    self.assertEqual(len(parser._plugins_per_name), number_of_plugins)

    parser.EnablePlugins(['gcp_log'])
    self.assertEqual(len(parser._plugins_per_name), 1)

  def testParse(self):
    """Tests the Parse function."""
    parser = jsonl_parser.JSONLParser()
    storage_writer = self._ParseFile(['gcp_logging.jsonl'], parser)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 9)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)


if __name__ == '__main__':
  unittest.main()
