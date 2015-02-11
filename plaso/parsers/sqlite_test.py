#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the SQLite database parser."""

import unittest

from plaso.parsers import sqlite
# Register plugins.
from plaso.parsers import sqlite_plugins  # pylint: disable=unused-import


class SQLiteParserTest(unittest.TestCase):
  """Tests for the SQLite database parser."""

  def testGetPluginNames(self):
    """Tests the GetPluginNames function."""
    all_plugin_names = sqlite.SQLiteParser.GetPluginNames()

    self.assertNotEquals(all_plugin_names, [])

    self.assertTrue('skype' in all_plugin_names)
    self.assertTrue('chrome_history' in all_plugin_names)
    self.assertTrue('firefox_history' in all_plugin_names)

    # Change the calculations of the parsers.
    parser_filter_string = 'chrome_history, firefox_history, -skype'
    plugin_names = sqlite.SQLiteParser.GetPluginNames(
        parser_filter_string=parser_filter_string)

    self.assertEquals(len(plugin_names), 2)
    self.assertFalse('skype' in plugin_names)
    self.assertTrue('chrome_history' in plugin_names)
    self.assertTrue('firefox_history' in plugin_names)

    # Test with a different plugin selection.
    parser_filter_string = 'sqlite, -skype'
    plugin_names = sqlite.SQLiteParser.GetPluginNames(
        parser_filter_string=parser_filter_string)

    # This should result in all plugins EXCEPT the skype one.
    self.assertEquals(len(plugin_names), len(all_plugin_names) - 1)
    self.assertFalse('skype' in plugin_names)
    self.assertTrue('chrome_history' in plugin_names)
    self.assertTrue('firefox_history' in plugin_names)


if __name__ == '__main__':
  unittest.main()
