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
"""This file contains a test for Typed Paths plugin in Plaso."""


import os
import re
import unittest

from plaso.lib import eventdata
from plaso.lib import win_registry
from plaso.parsers import winreg
from plaso.registry import test_lib
from plaso.registry import typedpaths

__author__ = 'David Nides (david.nides@gmail.com)'


class RegistryTypedPathsTest(unittest.TestCase):
  """The unit test for the Typed Paths plugin."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    test_file = os.path.join('test_data', 'NTUSER-WIN7.DAT')
    file_object = open(test_file, 'rb')
    self.registry = win_registry.WinRegistry(file_object)

  def testTypedPathst(self):
    """Test the Typed Paths plugin."""
    key = self.registry.GetKey(
        '\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer'
        '\\TypedPaths')
    plugin = typedpaths.TypedPathsPlugin(None, None)
    entries = list(plugin.Process(key))

    self.assertEquals(entries[0].timestamp, 1289375895811625)
    self.assertTrue(
        u'url1' in entries[0].regvalue)
    
    self.assertEquals(entries[0].regvalue[u'url1'],
                      u'\\\\controller')
    msg, _ = eventdata.EventFormatterManager.GetMessageStrings(entries[0])
    self.assertEquals(
        msg, u'[\Software\Microsoft\Windows\CurrentVersion\Explorer\TypedPaths] url1: '
        '\\\\controller')


if __name__ == '__main__':
  unittest.main()
