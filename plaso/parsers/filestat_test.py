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
"""This file contains the unit tests for the filestat parsing in Plaso."""
import os
import unittest

from plaso.formatters import filestat
from plaso.lib import event
from plaso.lib import preprocess
from plaso.parsers import filestat
from plaso.pvfs import pfile
from plaso.pvfs import pvfs


class FileStatTest(unittest.TestCase):
  """The unit test for filestat parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    pre_obj = preprocess.PlasoPreprocess()
    self.parser = filestat.PfileStatParser(pre_obj)
    self.fscache = pvfs.FilesystemCache()

  def testTSKFile(self):
    """Read a file within an image file and make few tests."""
    test_file = os.path.join('test_data', 'image.dd')

    path = event.EventPathSpec()
    path.type = 'TSK'
    path.container_path = test_file
    path.image_offset = 0
    path.image_inode = 15
    path.file_path = 'passwords.txt'

    file_object = pfile.TskFile(path, fscache=self.fscache)
    file_object.Open()

    events = list(self.parser.Parse(file_object))
    # The TSK file entry has 3 timestamps.
    self.assertEquals(len(events), 3)

  def testZipFile(self):
    """Test a ZIP file."""
    test_file = os.path.join('test_data', 'syslog.zip')

    path = event.EventPathSpec()
    path.type = 'ZIP'
    path.container_path = test_file
    path.file_path = 'syslog'

    file_object = pfile.OpenPFile(path)
    events = list(self.parser.Parse(file_object))
    # The ZIP file has 1 timestamp.
    self.assertEquals(len(events), 1)

  def testGzipFile(self):
    """Test a GZIP file."""
    test_file = os.path.join('test_data', 'syslog.gz')

    path = event.EventPathSpec()
    path.type = 'GZIP'
    path.file_path = test_file

    file_object = pfile.OpenPFile(path)
    events = list(self.parser.Parse(file_object))
    # There are no timestamps associated to uncompressed GZIP files (yet).
    self.assertEquals(len(events), 0)

  def testTarFile(self):
    """Test a TAR file."""
    test_file = os.path.join('test_data', 'syslog.tar')

    path = event.EventPathSpec()
    path.type = 'TAR'
    path.container_path = test_file
    path.file_path = 'syslog'

    file_object = pfile.OpenPFile(path)
    events = list(self.parser.Parse(file_object))
    # Nothing extracted from tar files yet.
    self.assertEquals(len(events), 0)

  def testNestedFile(self):
    """Test a nested file."""
    test_file = os.path.join('test_data', 'syslog.tgz')

    path = event.EventPathSpec()
    path.type = 'GZIP'
    path.file_path = test_file

    host_file = event.EventPathSpec()
    host_file.type = 'TAR'
    host_file.file_path = 'syslog'

    path.nested_pathspec = host_file

    file_object = pfile.OpenPFile(path)
    # No stat available from a GZIP file.
    events = list(self.parser.Parse(file_object))
    self.assertEquals(len(events), 0)

    test_file = os.path.join('test_data', 'syslog.gz')

    path = event.EventPathSpec()
    path.type = 'OS'
    path.file_path = test_file

    gzip = event.EventPathSpec()
    gzip.type = 'GZIP'
    gzip.file_path = test_file

    path.nested_pathspec = gzip

    file_object = pfile.OpenPFile(path)
    events = list(self.parser.Parse(file_object))
    self.assertEquals(len(events), 0)

  def testNestedTSK(self):
    """Test a nested TSK file."""
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

    file_object = pfile.OpenPFile(path, fscache=self.fscache)
    events = list(self.parser.Parse(file_object))
    # The ZIP file has 1 timestamp.
    self.assertEquals(len(events), 1)


if __name__ == '__main__':
  unittest.main()
