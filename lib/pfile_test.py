#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2012 Google Inc. All Rights Reserved.
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
"""This file contains the unit tests for the PFile implementation in Plaso."""
import os
import unittest

from plaso.lib import errors
from plaso.lib import pfile
from plaso.proto import transmission_pb2


class PlasoPFileTest(unittest.TestCase):
  """The unit test for PFile implementation."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self.base_path = os.path.join('plaso/test_data')

  def PerformSyslogTests(self, fh):
    """Perform a series of tests against a known syslog file.

    In order to evaluate different drivers the same syslog file is compressed
    and presented using several different mechanism, yet it needs to pass the
    same tests, since it is the same file, however the storage mechanism is
    implemented.

    Args:
      fh: A PFile object that can be used as a file-like object.
    """
    # Read lines.
    self.assertEquals(fh.readline(), ('Jan 22 07:52:33 myhostname.myhost.com '
                                      'client[30840]: INFO No new content.\n'))
    self.assertEquals(fh.readline(), ('Jan 22 07:52:33 myhostname.myhost.com '
                                      'client[30840]: INFO No change in [/etc/'
                                      'netgroup]. Done\n'))
    self.assertEquals(fh.readline(42), ('Jan 22 07:53:01 myhostname.myhost.com '
                                        'CRON'))

    # Read operations.
    text = fh.read(5)
    self.assertEquals(text, '[3105')
    self.assertEquals(fh.tell(), 214)

    fh.seek(0)
    text = fh.read(5)
    self.assertEquals(text, 'Jan 2')
    self.assertEquals(fh.tell(), 5)

    fh.seek(11)
    text = fh.read(10)
    self.assertEquals(text, '2:33 myhos')
    self.assertEquals(fh.tell(), 21)

    fh.seek(10, 1)
    self.assertEquals(fh.tell(), 31)
    text = fh.read(10)
    self.assertEquals(text, 'st.com cli')
    self.assertEquals(fh.tell(), 41)

    fh.seek(-10, 2)
    self.assertEquals(fh.tell(), 1237)
    text = fh.read(5)
    self.assertEquals(text, 'times')
    self.assertEquals(fh.tell(), 1242)

  def RunTest(self, pfile_class, path):
    """Open up a file and run syslog tests against it."""
    with pfile_class(path) as fh:
      fh.Open()
      self.PerformSyslogTests(fh)

  def testTSKFile(self):
    """Read a file within an image file and make few tests."""
    image_path = os.path.join(self.base_path, 'image.dd')

    path = transmission_pb2.PathSpec()
    path.type = transmission_pb2.PathSpec.TSK
    path.container_path = image_path
    path.image_offset = 0
    path.image_inode = 15
    path.file_path = 'passwords.txt'

    fh = pfile.TskFile(path)
    fh.Open()

    # Test fs cache.
    fs_hash = u'%s:0:-1' % image_path
    self.assertTrue(fs_hash in pfile.FilesystemCache.cached_filesystems)

    # Read lines.
    self.assertEquals(fh.readline(), 'place,user,password\n')
    self.assertEquals(fh.readline(), 'bank,joesmith,superrich\n')
    self.assertEquals(fh.readline(), 'alarm system,-,1234\n')
    self.assertEquals(fh.readline(), 'treasure chest,-,1111\n')
    self.assertEquals(fh.readline(), 'uber secret laire,admin,admin\n')

    # Seek and read
    fh.seek(0)
    text = fh.read(5)
    self.assertEquals(fh.tell(), 5)
    self.assertEquals(text, 'place')

    fh.seek(3, 1)
    text = fh.read(4)
    self.assertEquals(text, 'er,p')
    self.assertEquals(fh.tell(), 12)

    fh.seek(15)
    text = fh.read(6)
    self.assertEquals(text, 'word\nb')
    self.assertEquals(fh.tell(), 21)

    fh.seek(-10, 2)
    text = fh.read(5)
    self.assertEquals(text, 'min,a')
    self.assertEquals(fh.tell(), 111)

    # Test Stat
    stat = fh.Stat()
    self.assertEquals(stat.ctime, 1337961663)
    self.assertEquals(stat.mtime, 1337961653)
    self.assertEquals(stat.mtime_nano, 0)
    self.assertEquals(stat.size, 116)
    self.assertEquals(stat.ino, 15)

  def testZipFile(self):
    image_path = os.path.join(self.base_path, 'syslog.zip')

    path = transmission_pb2.PathSpec()
    path.type = transmission_pb2.PathSpec.ZIP
    path.container_path = image_path
    path.file_path = 'syslog'

    self.RunTest(pfile.ZipFile, path)

  def testGzipFile(self):
    file_path = os.path.join(self.base_path, 'syslog.gz')

    path = transmission_pb2.PathSpec()
    path.type = transmission_pb2.PathSpec.GZIP
    path.file_path = file_path

    self.RunTest(pfile.GzipFile, path)

  def testTarFile(self):
    image_path = os.path.join(self.base_path, 'syslog.tar')

    path = transmission_pb2.PathSpec()
    path.type = transmission_pb2.PathSpec.TAR
    path.container_path = image_path
    path.file_path = 'syslog'

    self.RunTest(pfile.TarFile, path)

  def testOsFile(self):
    file_path = os.path.join(self.base_path, 'syslog')

    path = transmission_pb2.PathSpec()
    path.type = transmission_pb2.PathSpec.OS
    path.file_path = file_path

    self.RunTest(pfile.OsFile, path)

  def testBz2File(self):
    file_path = os.path.join(self.base_path, 'syslog.bz2')

    path = transmission_pb2.PathSpec()
    path.type = transmission_pb2.PathSpec.BZ2
    path.file_path = file_path

    self.RunTest(pfile.Bz2File, path)

  def testFaultyFile(self):
    file_path = os.path.join(self.base_path, 'syslog.bz2')

    path = transmission_pb2.PathSpec()
    path.type = transmission_pb2.PathSpec.TSK
    path.file_path = file_path

    self.assertRaises(errors.UnableToOpenFile, pfile.Bz2File, path)

  def testNestedFile(self):
    file_path = os.path.join(self.base_path, 'syslog.tgz')

    path = transmission_pb2.PathSpec()
    path.type = transmission_pb2.PathSpec.GZIP
    path.file_path = file_path

    host_file = transmission_pb2.PathSpec()
    host_file.type = transmission_pb2.PathSpec.TAR
    host_file.file_path = 'syslog'

    path.nested_pathspec.MergeFrom(host_file)

    with pfile.OpenPFile(path) as fh:
      self.PerformSyslogTests(fh)

    file_path = os.path.join(self.base_path, 'syslog.gz')

    path = transmission_pb2.PathSpec()
    path.type = transmission_pb2.PathSpec.OS
    path.file_path = file_path

    gzip = transmission_pb2.PathSpec()
    gzip.type = transmission_pb2.PathSpec.GZIP
    gzip.file_path = file_path

    path.nested_pathspec.MergeFrom(gzip)

    with pfile.OpenPFile(path) as fh:
      self.PerformSyslogTests(fh)

  def testNestedTSK(self):
    image_path = os.path.join(self.base_path, 'syslog_image.dd')

    path = transmission_pb2.PathSpec()
    path.type = transmission_pb2.PathSpec.TSK
    path.container_path = image_path
    path.image_offset = 0
    path.image_inode = 11
    path.file_path = 'logs/hidden.zip'

    host_path = transmission_pb2.PathSpec()
    host_path.type = transmission_pb2.PathSpec.ZIP
    host_path.file_path = 'syslog'

    path.nested_pathspec.MergeFrom(host_path)

    with pfile.OpenPFile(path) as fh:
      self.PerformSyslogTests(fh)

  def testTarReadline(self):
    image_path = os.path.join(self.base_path, 'syslog.tar')

    path = transmission_pb2.PathSpec()
    path.type = transmission_pb2.PathSpec.TAR
    path.container_path = image_path
    path.file_path = 'syslog'

    # First line is 74 chars, second is 93.
    with pfile.TarFile(path) as fh:
      fh.Open()
      line1 = fh.readline()
      line2 = fh.readline()
      self.assertEqual(len(line1), 74)
      self.assertEqual(len(line2), 93)

    with pfile.TarFile(path) as fh:
      fh.Open()
      self.assertEqual(fh.readline(150), line1)
      self.assertEqual(fh.readline(), line2)

    with pfile.TarFile(path) as fh:
      fh.Open()
      self.assertEqual(fh.readline(10), line1[:10])
      self.assertEqual(fh.readline(), line1[10:])
      self.assertEqual(fh.readline(), line2)

    # Now test what happens if there is a buffer.
    with pfile.TarFile(path) as fh:
      fh.Open()
      fh.buffer += fh.read(10)
      self.assertEqual(fh.readline(), line1)
      self.assertEqual(fh.readline(), line2)

    with pfile.TarFile(path) as fh:
      fh.Open()
      fh.buffer += fh.read(150)
      self.assertEqual(fh.readline(), line1)
      self.assertEqual(fh.readline(), line2)

    with pfile.TarFile(path) as fh:
      fh.Open()
      fh.buffer += fh.read(150)
      self.assertEqual(fh.readline(140), line1)
      self.assertEqual(fh.readline(), line2)

    with pfile.TarFile(path) as fh:
      fh.Open()
      fh.buffer += fh.read(150)
      self.assertEqual(fh.readline(200), line1)
      self.assertEqual(fh.readline(200), line2)

    with pfile.TarFile(path) as fh:
      fh.Open()
      fh.buffer += fh.read(60)
      self.assertEqual(fh.readline(20), line1[:20])
      self.assertEqual(fh.readline(20), line1[20:40])
      self.assertEqual(fh.readline(40), line1[40:])
      self.assertEqual(fh.readline(40), line2[:40])


if __name__ == '__main__':
  unittest.main()
