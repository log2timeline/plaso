#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the SQLite database parser."""

import unittest

from plaso.parsers import sqlite
# Register all plugins.
from plaso.parsers import sqlite_plugins  # pylint: disable=unused-import

from tests.parsers import test_lib


class SQLiteParserTest(test_lib.ParserTestCase):
  """Tests for the SQLite database parser."""

  # pylint: disable=protected-access

  def testInitialize(self):
    """Tests the initialization."""
    parser_object = sqlite.SQLiteParser([u'chrome_history'])

    self.assertIsNotNone(parser_object)
    self.assertIsNone(parser_object._default_plugin)
    self.assertNotEqual(parser_object._plugin_objects, [])
    self.assertEqual(len(parser_object._plugin_objects), 1)

  def testFileParserChainMaintenance(self):
    """Tests that the parser chain is correctly maintained by the parser."""
    parser_object = sqlite.SQLiteParser()
    test_file = self._GetTestFilePath([u'contacts2.db'])

    event_queue_consumer = self._ParseFile(parser_object, test_file)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)
    for event in event_objects:
      chain = event.parser
      self.assertEqual(1, chain.count(u'/'))


if __name__ == '__main__':
  unittest.main()
