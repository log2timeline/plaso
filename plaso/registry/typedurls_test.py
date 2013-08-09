#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2012 The Plaso Project Authors.
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
"""This file contains a test for typed URLs plugin in Plaso."""

import os
import unittest

from plaso.formatters import winreg   # pylint: disable-msg=W0611
from plaso.lib import eventdata
from plaso.parsers import winreg
from plaso.registry import typedurls
from plaso.winreg import winregistry

__author__ = 'David Nides (david.nides@gmail.com)'


class RegistryTypedURLsTest(unittest.TestCase):
  """The unit test for typed URLs plugin."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    registry = winregistry.WinRegistry(
        winregistry.WinRegistry.BACKEND_PYREGF)

    test_file = os.path.join('test_data', 'NTUSER-WIN7.DAT')
    file_object = open(test_file, 'rb')
    self.winreg_file = registry.OpenFile(file_object, codepage='cp1252')

  def testMsieTypedURLs(self):
    """Test the MISE Typed URLs plugin."""
    key = self.winreg_file.GetKeyByPath(
        '\\Software\\Microsoft\\Internet Explorer\\TypedURLs')
    plugin = typedurls.MsieTypedURLsPlugin(None, None, None)
    entries = list(plugin.Process(key))

    self.assertEquals(len(entries), 13)

    self.assertEquals(entries[0].timestamp, 1331587433307749)
    self.assertTrue(u'url1' in entries[0].regvalue)

    expected_value_data = u'http://cnn.com/'

    self.assertEquals(entries[0].regvalue[u'url1'], expected_value_data)

    expected_string = (
        u'[\\Software\\Microsoft\\Internet Explorer\\TypedURLs] '
        u'url1: http://cnn.com/')

    msg, _ = eventdata.EventFormatterManager.GetMessageStrings(entries[0])
    self.assertEquals(msg, expected_string)

  def testTypedPaths(self):
    """Test the Typed Paths plugin."""
    key = self.winreg_file.GetKeyByPath(
        '\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer'
        '\\TypedPaths')
    plugin = typedurls.TypedPathsPlugin(None, None, None)
    entries = list(plugin.Process(key))

    self.assertEquals(len(entries), 1)

    self.assertEquals(entries[0].timestamp, 1289375895811625)
    self.assertTrue(u'url1' in entries[0].regvalue)

    expected_value_data = u'\\\\controller'

    self.assertEquals(entries[0].regvalue[u'url1'], expected_value_data)

    expected_string = (
        u'[\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\'
        u'TypedPaths] url1: \\\\controller')

    msg, _ = eventdata.EventFormatterManager.GetMessageStrings(entries[0])
    self.assertEquals(msg, expected_string)


if __name__ == '__main__':
  unittest.main()
