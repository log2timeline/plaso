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
"""Tests for the Windows Registry objects cache."""

import unittest

from plaso.winreg import cache
from plaso.winreg import test_lib
from plaso.winreg import winregistry


class CacheTest(test_lib.WinRegTestCase):
  """Tests for the Windows Registry objects cache."""

  def testBuildCache(self):
    """Tests creating a Windows Registry objects cache."""
    registry = winregistry.WinRegistry(
        winregistry.WinRegistry.BACKEND_PYREGF)

    test_file = self._GetTestFilePath(['SYSTEM'])
    file_entry = self._GetTestFileEntry(test_file)
    winreg_file = registry.OpenFile(file_entry, codepage='cp1252')

    winreg_cache = cache.WinRegistryCache()

    # Test if this function does not raise an exception.
    winreg_cache.BuildCache(winreg_file, 'SYSTEM')

    self.assertEqual(
       winreg_cache.attributes['current_control_set'], 'ControlSet001')


if __name__ == '__main__':
  unittest.main()
