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
"""This file contains a unit test for the TSKFile (sleuthkit)."""
import os

import pytsk3
import unittest

from plaso.lib import sleuthkit

__pychecker__ = 'no-funcdoc'


class SleuthkitUnitTest(unittest.TestCase):
  """The unit test for TSK integration into plaso."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    test_file = os.path.join('test_data', 'image.dd')
    self.img = pytsk3.Img_Info(test_file)
    self.fs = pytsk3.FS_Info(self.img, offset=0)

  def testReadFileName(self):
    f = sleuthkit.Open(self.fs, 15, '/passwords.txt')

    self.assertEquals(f.name, '/passwords.txt')
    f.close()

  def testReadFileContent(self):
    f = sleuthkit.Open(self.fs, 15, '/')
    buf = []
    for l in f:
      buf.append(l)

    self.assertEquals(''.join(buf), ('place,user,password\n'
                                     'bank,joesmith,superrich\n'
                                     'alarm system,-,1234\n'
                                     'treasure chest,-,1111\n'
                                     'uber secret laire,admin,admin\n'))

    f.close()

  def testReadLine(self):
    f = sleuthkit.Open(self.fs, 16, '/a_directory/another_file')
    self.assertEquals(f.readline(), 'This is another file.\n')

    f.seek(0)
    self.assertEquals(f.readline(5), 'This ')
    f.close()

  def testSeekAndTell(self):
    f = sleuthkit.Open(self.fs, 16, '/a_directory/another_file')
    f.seek(10)
    self.assertEquals(f.read(5), 'other')
    self.assertEquals(f.tell(), 15)

    f.seek(-10, 2)
    self.assertEquals(f.read(5), 'her f')

    f.seek(2, 1)
    self.assertEquals(f.read(2), 'e.')

    f.seek(300)
    self.assertEquals(f.read(2), '')

    f.seek(0)
    _ = f.readline()
    self.assertEquals(f.tell(), 22)
    f.close()

  def testReadLines(self):
    f = sleuthkit.Open(self.fs, 15, '/passwords.txt')
    lines = []

    # I'm trying to test readlines specifically, hence not using the
    # default iterator.
    for line in f.readlines():
      lines.append(line)

    self.assertEquals(len(lines), 5)

    self.assertEquals(lines[3], 'treasure chest,-,1111\n')
    f.close()

  def testIter(self):
    f = sleuthkit.Open(self.fs, 15, '/passwords.txt')

    lines = []
    for l in f:
      lines.append(l)

    self.assertEquals(lines[0], 'place,user,password\n')
    self.assertEquals(lines[1], 'bank,joesmith,superrich\n')
    self.assertEquals(lines[2], 'alarm system,-,1234\n')
    self.assertEquals(lines[3], 'treasure chest,-,1111\n')
    self.assertEquals(lines[4], 'uber secret laire,admin,admin\n')

  def testCtime(self):
    f = sleuthkit.Open(self.fs, 15, '/passwords.txt')

    self.assertEquals(f.ctime, 1337961663)


if __name__ == '__main__':
  unittest.main()
