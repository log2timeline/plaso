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
"""This file contains tests for the pyregf Windows Registry back-end."""
import os
import unittest

from plaso.lib import putils
from plaso.winreg import winpyregf


class RegistryUnitTest(unittest.TestCase):
  """An unit test for the plaso winpyregf library."""

  def setUp(self):
    self.base_path = 'test_data'

  def testListKeys(self):
    test_file = os.path.join(self.base_path, 'NTUSER.DAT')
    file_object = putils.OpenOSFile(test_file)
    reg = winpyregf.WinRegistry(file_object)
    keys = list(reg)

    # Count the number of registry keys in the hive.
    self.assertEquals(len(keys), 1126)

  def testWinPyregf(self):
    test_file = os.path.join(self.base_path, 'NTUSER.DAT')
    file_object = putils.OpenOSFile(test_file)
    reg = winpyregf.WinPyregfFile()
    reg.Open(file_object)

    self._KeyPathCompare(reg, '\\')
    self._KeyPathCompare(reg, '\\Printers')
    self._KeyPathCompare(reg, '\\Printers\\Connections')
    self._KeyPathCompare(reg, '\\Software')

  def _KeyPathCompare(self, reg, path):
    """Get a key, compare it's path to the path requested."""
    key = reg.GetKeyByPath(path)
    self.assertEquals(key.path, path)


if __name__ == '__main__':
  unittest.main()
