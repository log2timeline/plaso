#!/usr/bin/python
# -*- coding: utf-8 -*-
#
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
"""This file contains the tests for the Windows Registry library."""

import os
import unittest

from plaso.pvfs import pfile
from plaso.winreg import winregistry


class RegistryUnitTest(unittest.TestCase):
  """Tests for the Windows Registry library."""

  def testMountFile(self):
    """Tests mounting REGF files in the Registry."""
    registry = winregistry.WinRegistry(
        winregistry.WinRegistry.BACKEND_PYREGF)

    test_file = os.path.join('test_data', 'SOFTWARE')
    path_spec = pfile.PFileResolver.CopyPathToPathSpec('OS', test_file)
    file_entry = pfile.PFileResolver.OpenFileEntry(path_spec)
    winreg_file = registry.OpenFile(file_entry, codepage='cp1252')

    registry.MountFile(winreg_file, u'HKEY_LOCAL_MACHINE\\Software')

    test_file = os.path.join('test_data', 'NTUSER-WIN7.DAT')
    path_spec = pfile.PFileResolver.CopyPathToPathSpec('OS', test_file)
    file_entry = pfile.PFileResolver.OpenFileEntry(path_spec)
    winreg_file = registry.OpenFile(file_entry, codepage='cp1252')

    with self.assertRaises(KeyError):
      registry.MountFile(winreg_file, u'HKEY_LOCAL_MACHINE\\Software')

    registry.MountFile(winreg_file, u'HKEY_CURRENT_USER')


if __name__ == '__main__':
  unittest.main()
