#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the SQLite database parser."""

import unittest

from plaso.parsers import sqlite
from plaso.parsers import test_lib
# Register plugins.
from plaso.parsers import sqlite_plugins  # pylint: disable=unused-import


class SQLiteParserTest(test_lib.ParserTestCase):
  """Tests for the SQLite database parser."""

  def testGetPluginNames(self):
    """Tests the GetPluginNames function."""
    all_plugin_names = sqlite.SQLiteParser.GetPluginNames()

    self.assertNotEqual(all_plugin_names, [])

    self.assertTrue('skype' in all_plugin_names)
    self.assertTrue('chrome_history' in all_plugin_names)
    self.assertTrue('firefox_history' in all_plugin_names)

    # Change the calculations of the parsers.
    parser_filter_string = 'chrome_history, firefox_history, -skype'
    plugin_names = sqlite.SQLiteParser.GetPluginNames(
        parser_filter_string=parser_filter_string)

    self.assertEqual(len(plugin_names), 2)
    self.assertFalse('skype' in plugin_names)
    self.assertTrue('chrome_history' in plugin_names)
    self.assertTrue('firefox_history' in plugin_names)

    # Test with a different plugin selection.
    parser_filter_string = 'sqlite, -skype'
    plugin_names = sqlite.SQLiteParser.GetPluginNames(
        parser_filter_string=parser_filter_string)

    # This should result in all plugins EXCEPT the skype one.
    self.assertEqual(len(plugin_names), len(all_plugin_names) - 1)
    self.assertFalse('skype' in plugin_names)
    self.assertTrue('chrome_history' in plugin_names)
    self.assertTrue('firefox_history' in plugin_names)

  def testFileParserChainMaintenance(self):
    """Tests that the parser chain is correctly maintained by the parser."""
    parser = sqlite.SQLiteParser()
    test_file = self._GetTestFilePath([u'contacts2.db'])

    event_queue_consumer = self._ParseFile(parser, test_file)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)
    for event in event_objects:
      chain = event.parser
      self.assertEqual(1, chain.count(u'/'))


if __name__ == '__main__':
  unittest.main()
