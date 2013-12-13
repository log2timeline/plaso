#!/usr/bin/python
# -*- coding: utf-8 -*-
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
"""Tests for the Windows Shortcut (LNK) parser."""
import unittest

from plaso.lib import preprocess
from plaso.parsers import sqlite


class Configuration(object):
  """Config object."""

  def __init__(self):
    """Initialize."""
    self.parsers = ''

class SQLiteParserTest(unittest.TestCase):
  """Tests for the SQLite parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    pre_obj = preprocess.PlasoPreprocess()
    self.config = Configuration()
    self.test_parser = sqlite.SQLiteParser(pre_obj, self.config)
    # Show full diff results, part of TestCase so does not follow our naming
    # conventions.
    self.maxDiff = None

  def testPluginList(self):
    """Test the plugin list returns the right values."""
    # pylint: disable-msg=protected-access
    all_plugins = self.test_parser._GetPlugins()
    self.assertGreaterEqual(len(all_plugins), 10)

    all_plugin_names = [x.plugin_name for x in all_plugins]

    self.assertTrue('skype' in all_plugin_names)
    self.assertTrue('chrome_history' in all_plugin_names)
    self.assertTrue('firefox_history' in all_plugin_names)

    # Change the calculations of the parsers.
    self.config.parsers = 'chrome_history, firefox_history, -skype'
    plugins = self.test_parser._GetPlugins()

    self.assertEquals(len(plugins), 2)

    # Test with a different plugin selection.
    self.config.parsers = 'sqlite, -skype'
    plugins = self.test_parser._GetPlugins()

    # This should result in all plugins EXCEPT the skype one.
    self.assertEquals(len(plugins), len(all_plugins) - 1)


if __name__ == '__main__':
  unittest.main()
