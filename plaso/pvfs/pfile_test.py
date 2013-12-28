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
"""This file contains the tests for PFile."""

import os
import unittest

from plaso.lib import errors
from plaso.lib import event
from plaso.pvfs import pfile
from plaso.pvfs import pfile_entry
from plaso.pvfs import pvfs


class PlasoPFileTest(unittest.TestCase):
  """The unit test for PFile implementation."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._fscache = pvfs.FilesystemCache()

  def PerformSyslogTests(self, file_object):
    """Perform a series of tests against a known syslog file.

    In order to evaluate different drivers the same syslog file is compressed
    and presented using several different mechanism, yet it needs to pass the
    same tests, since it is the same file, however the storage mechanism is
    implemented.

    Args:
      file_object: A file-like object to read from.
    """
    # Read lines.
    expected_line = (
        'Jan 22 07:52:33 myhostname.myhost.com client[30840]: INFO No new '
        'content.\n')

    self.assertEquals(file_object.readline(), expected_line)

    expected_line = (
        'Jan 22 07:52:33 myhostname.myhost.com client[30840]: INFO No change '
        'in [/etc/netgroup]. Done\n')

    self.assertEquals(file_object.readline(), expected_line)

    expected_line = 'Jan 22 07:53:01 myhostname.myhost.com CRON'

    self.assertEquals(file_object.readline(42), expected_line)

    # Read operations.
    text = file_object.read(5)
    self.assertEquals(text, '[3105')
    self.assertEquals(file_object.tell(), 214)

    file_object.seek(0)
    text = file_object.read(5)
    self.assertEquals(text, 'Jan 2')
    self.assertEquals(file_object.tell(), 5)

    file_object.seek(11)
    text = file_object.read(10)
    self.assertEquals(text, '2:33 myhos')
    self.assertEquals(file_object.tell(), 21)

    file_object.seek(10, 1)
    self.assertEquals(file_object.tell(), 31)
    text = file_object.read(10)
    self.assertEquals(text, 'st.com cli')
    self.assertEquals(file_object.tell(), 41)

    file_object.seek(-10, 2)
    self.assertEquals(file_object.tell(), 1237)
    text = file_object.read(5)
    self.assertEquals(text, 'times')
    self.assertEquals(file_object.tell(), 1242)

  def RunTest(self, pfile_class, path):
    """Open up a file and run syslog tests against it."""
    file_entry = pfile_class(path)
    file_object = file_entry.Open()
    self.PerformSyslogTests(file_object)

  def testTSKFileEntry(self):
    """Read a file within an image file and make few tests."""
    test_file = os.path.join('test_data', 'image.dd')

    path = event.EventPathSpec()
    path.type = 'TSK'
    path.container_path = test_file
    path.image_offset = 0
    path.image_inode = 15
    path.file_path = 'passwords.txt'

    file_entry = pfile_entry.TSKFileEntry(path, fscache=self._fscache)
    file_object = file_entry.Open()

    # Test fs cache.
    fs_hash = u'%s:0:-1' % test_file
    self.assertTrue(fs_hash in self._fscache.cached_filesystems)

    # Read lines.
    self.assertEquals(file_object.readline(), 'place,user,password\n')
    self.assertEquals(file_object.readline(), 'bank,joesmith,superrich\n')
    self.assertEquals(file_object.readline(), 'alarm system,-,1234\n')
    self.assertEquals(file_object.readline(), 'treasure chest,-,1111\n')
    self.assertEquals(file_object.readline(), 'uber secret laire,admin,admin\n')

    # Seek and read
    file_object.seek(0)
    text = file_object.read(5)
    self.assertEquals(file_object.tell(), 5)
    self.assertEquals(text, 'place')

    file_object.seek(3, 1)
    text = file_object.read(4)
    self.assertEquals(text, 'er,p')
    self.assertEquals(file_object.tell(), 12)

    file_object.seek(15)
    text = file_object.read(6)
    self.assertEquals(text, 'word\nb')
    self.assertEquals(file_object.tell(), 21)

    file_object.seek(-10, 2)
    text = file_object.read(5)
    self.assertEquals(text, 'min,a')
    self.assertEquals(file_object.tell(), 111)

    # Test Stat
    stat = file_entry.Stat()
    self.assertEquals(stat.ctime, 1337961663)
    self.assertEquals(stat.mtime, 1337961653)
    self.assertEquals(stat.mtime_nano, 0)
    self.assertEquals(stat.size, 116)
    self.assertEquals(stat.ino, 15)

  def testZipFileEntry(self):
    test_file = os.path.join('test_data', 'syslog.zip')

    path = event.EventPathSpec()
    path.type = 'ZIP'
    path.container_path = test_file
    path.file_path = 'syslog'

    self.RunTest(pfile_entry.ZipFileEntry, path)

  def testGzipFileEntry(self):
    test_file = os.path.join('test_data', 'syslog.gz')

    path = event.EventPathSpec()
    path.type = 'GZIP'
    path.file_path = test_file

    self.RunTest(pfile_entry.GzipFileEntry, path)

  def testTarFileEntry(self):
    test_file = os.path.join('test_data', 'syslog.tar')

    path = event.EventPathSpec()
    path.type = 'TAR'
    path.container_path = test_file
    path.file_path = 'syslog'

    self.RunTest(pfile_entry.TarFileEntry, path)

  def testOsFileEntry(self):
    test_file = os.path.join('test_data', 'syslog_copy')

    path = event.EventPathSpec()
    path.type = 'OS'
    path.file_path = test_file

    self.RunTest(pfile_entry.OsFileEntry, path)

  def testBz2FileEntry(self):
    test_file = os.path.join('test_data', 'syslog.bz2')

    path = event.EventPathSpec()
    path.type = 'BZ2'
    path.file_path = test_file

    self.RunTest(pfile_entry.Bz2FileEntry, path)

  def testFaultyFileEntry(self):
    test_file = os.path.join('test_data', 'syslog.bz2')

    path = event.EventPathSpec()
    path.type = 'TSK'
    path.file_path = test_file

    self.assertRaises(errors.UnableToOpenFile, pfile_entry.Bz2FileEntry, path)

  def testNestedFileEntry(self):
    test_file = os.path.join('test_data', 'syslog.tgz')

    path = event.EventPathSpec()
    path.type = 'GZIP'
    path.file_path = test_file

    host_file = event.EventPathSpec()
    host_file.type = 'TAR'
    host_file.file_path = 'syslog'

    path.nested_pathspec = host_file

    with pfile.OpenPFileEntry(path) as file_entry:
      self.PerformSyslogTests(file_entry.file_object)

    test_file = os.path.join('test_data', 'syslog.gz')

    path = event.EventPathSpec()
    path.type = 'OS'
    path.file_path = test_file

    gzip = event.EventPathSpec()
    gzip.type = 'GZIP'
    gzip.file_path = test_file

    path.nested_pathspec = gzip

    with pfile.OpenPFileEntry(path) as file_entry:
      self.PerformSyslogTests(file_entry.file_object)

  def testNestedTSK(self):
    test_file = os.path.join('test_data', 'syslog_image.dd')

    path = event.EventPathSpec()
    path.type = 'TSK'
    path.container_path = test_file
    path.image_offset = 0
    path.image_inode = 11
    path.file_path = 'logs/hidden.zip'

    host_path = event.EventPathSpec()
    host_path.type = 'ZIP'
    host_path.file_path = 'syslog'

    path.nested_pathspec = host_path

    with pfile.OpenPFileEntry(path, fscache=self._fscache) as file_entry:
      self.PerformSyslogTests(file_entry.file_object)

  def testTarReadline(self):
    test_file = os.path.join('test_data', 'syslog.tar')

    path = event.EventPathSpec()
    path.type = 'TAR'
    path.container_path = test_file
    path.file_path = 'syslog'

    # First line is 74 chars, second is 93.
    with pfile_entry.TarFileEntry(path) as file_entry:
      file_object = file_entry.Open()
      line1 = file_object.readline()
      line2 = file_object.readline()
      self.assertEqual(len(line1), 74)
      self.assertEqual(len(line2), 93)

    with pfile_entry.TarFileEntry(path) as file_entry:
      file_object = file_entry.Open()
      self.assertEqual(file_object.readline(150), line1)
      self.assertEqual(file_object.readline(), line2)

    with pfile_entry.TarFileEntry(path) as file_entry:
      file_object = file_entry.Open()
      self.assertEqual(file_object.readline(10), line1[:10])
      self.assertEqual(file_object.readline(), line1[10:])
      self.assertEqual(file_object.readline(), line2)

    # Now test what happens if there is a buffer.
    with pfile_entry.TarFileEntry(path) as file_entry:
      file_object = file_entry.Open()
      file_object.buffer += file_object.read(10)
      self.assertEqual(file_object.readline(), line1)
      self.assertEqual(file_object.readline(), line2)

    with pfile_entry.TarFileEntry(path) as file_entry:
      file_object = file_entry.Open()
      file_object.buffer += file_object.read(150)
      self.assertEqual(file_object.readline(), line1)
      self.assertEqual(file_object.readline(), line2)

    with pfile_entry.TarFileEntry(path) as file_entry:
      file_object = file_entry.Open()
      file_object.buffer += file_object.read(150)
      self.assertEqual(file_object.readline(140), line1)
      self.assertEqual(file_object.readline(), line2)

    with pfile_entry.TarFileEntry(path) as file_entry:
      file_object = file_entry.Open()
      file_object.buffer += file_object.read(150)
      self.assertEqual(file_object.readline(200), line1)
      self.assertEqual(file_object.readline(200), line2)

    with pfile_entry.TarFileEntry(path) as file_entry:
      file_object = file_entry.Open()
      file_object.buffer += file_object.read(60)
      self.assertEqual(file_object.readline(20), line1[:20])
      self.assertEqual(file_object.readline(20), line1[20:40])
      self.assertEqual(file_object.readline(40), line1[40:])
      self.assertEqual(file_object.readline(40), line2[:40])


if __name__ == '__main__':
  unittest.main()
