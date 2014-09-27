#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2013 The Plaso Project Authors.
# Please see the AUTHORS file for details on individual authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
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
