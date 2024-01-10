#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the CSV parser."""

import unittest

from plaso.parsers import csv_parser
from plaso.parsers import csv_plugins  # pylint: disable=unused-import

from tests.parsers import test_lib

class CSVTest(test_lib.ParserTestCase):
  """Tests for the CSV parser."""

  # pylint: disable=protected-access

  def testEnablePlugins(self):
    """Tests the EnablePlugins function."""
    parser = csv_parser.CSVFileParser()

    number_of_plugins = len(parser._plugin_classes)

    parser.EnablePlugins([])
    self.assertEqual(len(parser._plugins_per_name), 0)

    parser.EnablePlugins(parser.ALL_PLUGINS)
    self.assertEqual(len(parser._plugins_per_name), number_of_plugins)

    parser.EnablePlugins(['m365_activitylog'])
    self.assertEqual(len(parser._plugins_per_name), 1)

if __name__ == '__main__':
  unittest.main()
