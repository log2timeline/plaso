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
"""This file contains a unit test for TSKFile (sleuthkit)."""

import os
import unittest

from plaso.lib import event
from plaso.pvfs import pfile_entry
from plaso.pvfs import pvfs


class SleuthkitUnitTest(unittest.TestCase):
  """The unit test for TSK integration into plaso."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._test_file = os.path.join('test_data', 'image.dd')
    self._fscache = pvfs.FilesystemCache()

    self._path_spec1 = event.EventPathSpec()
    self._path_spec1.type = 'TSK'
    self._path_spec1.container_path = self._test_file
    self._path_spec1.image_offset = 0
    self._path_spec1.image_inode = 15
    self._path_spec1.file_path = '/passwords.txt'

    self._path_spec2 = event.EventPathSpec()
    self._path_spec2.type = 'TSK'
    self._path_spec2.container_path = self._test_file
    self._path_spec2.image_offset = 0
    self._path_spec2.image_inode = 16
    self._path_spec2.file_path = '/a_directory/another_file'

  def testReadFileName(self):
    file_entry = pfile_entry.TSKFileEntry(
        self._path_spec1, fscache=self._fscache)
    # Need to open before file entry name is set.
    _ = file_entry.Open()

    self.assertEquals(file_entry.name, '/passwords.txt')

  def testReadFileContent(self):
    file_entry = pfile_entry.TSKFileEntry(
        self._path_spec1, fscache=self._fscache)
    file_object = file_entry.Open()

    buf = []
    for l in file_object:
      buf.append(l)

    expected_string = (
        'place,user,password\n'
        'bank,joesmith,superrich\n'
        'alarm system,-,1234\n'
        'treasure chest,-,1111\n'
        'uber secret laire,admin,admin\n')

    self.assertEquals(''.join(buf), expected_string)

    file_object.close()

  def testReadLine(self):
    file_entry = pfile_entry.TSKFileEntry(
        self._path_spec2, fscache=self._fscache)
    file_object = file_entry.Open()

    self.assertEquals(file_object.readline(), 'This is another file.\n')

    file_object.seek(0)
    self.assertEquals(file_object.readline(5), 'This ')
    file_object.close()

  def testSeekAndTell(self):
    file_entry = pfile_entry.TSKFileEntry(
        self._path_spec2, fscache=self._fscache)
    file_object = file_entry.Open()

    file_object.seek(10)
    self.assertEquals(file_object.read(5), 'other')
    self.assertEquals(file_object.tell(), 15)

    file_object.seek(-10, 2)
    self.assertEquals(file_object.read(5), 'her f')

    file_object.seek(2, 1)
    self.assertEquals(file_object.read(2), 'e.')

    file_object.seek(300)
    self.assertEquals(file_object.read(2), '')

    file_object.seek(0)
    _ = file_object.readline()
    self.assertEquals(file_object.tell(), 22)

    file_object.seek(10)
    self.assertEquals(file_object.read(5), 'other')
    self.assertEquals(file_object.tell(), 15)
    file_object.close()

  def testReadLines(self):
    file_entry = pfile_entry.TSKFileEntry(
        self._path_spec1, fscache=self._fscache)
    file_object = file_entry.Open()

    lines = []

    # I'm trying to test readlines specifically, hence not using the
    # default iterator.
    for line in file_object.readlines():
      lines.append(line)

    self.assertEquals(len(lines), 5)

    self.assertEquals(lines[3], 'treasure chest,-,1111\n')
    file_object.close()

  def testIter(self):
    file_entry = pfile_entry.TSKFileEntry(
        self._path_spec1, fscache=self._fscache)
    file_object = file_entry.Open()

    lines = []
    for l in file_object:
      lines.append(l)

    self.assertEquals(lines[0], 'place,user,password\n')
    self.assertEquals(lines[1], 'bank,joesmith,superrich\n')
    self.assertEquals(lines[2], 'alarm system,-,1234\n')
    self.assertEquals(lines[3], 'treasure chest,-,1111\n')
    self.assertEquals(lines[4], 'uber secret laire,admin,admin\n')

  def testCtime(self):
    file_entry = pfile_entry.TSKFileEntry(
        self._path_spec1, fscache=self._fscache)
    # Need to open before Stat() can be used.
    _ = file_entry.Open()

    stat_object = file_entry.Stat()

    self.assertEquals(stat_object.ctime, 1337961663)


if __name__ == '__main__':
  unittest.main()
