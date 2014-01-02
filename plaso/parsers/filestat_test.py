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
"""This file contains the unit tests for the filestat parsing in Plaso."""

import os
import unittest

# pylint: disable-msg=unused-import
from plaso.formatters import filestat as filestat_formatter
from plaso.lib import event
from plaso.lib import preprocess
from plaso.parsers import filestat
from plaso.parsers import test_lib
from plaso.pvfs import pvfs


class FileStatTest(test_lib.ParserTestCase):
  """The unit test for filestat parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    pre_obj = preprocess.PlasoPreprocess()
    self._parser = filestat.PfileStatParser(pre_obj)
    self._fscache = pvfs.FilesystemCache()

  def testTSKFile(self):
    """Read a file within an image file and make few tests."""
    path = event.EventPathSpec()
    path.type = 'TSK'
    path.container_path = os.path.join('test_data', 'image.dd')
    path.image_offset = 0
    path.image_inode = 15
    path.file_path = 'passwords.txt'

    events = self._ParseFileByPathSpec(
        self._parser, path, fscache=self._fscache)
    event_container = self._GetEventContainer(events)

    # The TSK file entry has 3 timestamps.
    self.assertEquals(len(event_container.events), 3)

  def testZipFile(self):
    """Test a ZIP file."""
    path = event.EventPathSpec()
    path.type = 'ZIP'
    path.container_path = os.path.join('test_data', 'syslog.zip')
    path.file_path = 'syslog'

    events = self._ParseFileByPathSpec(
        self._parser, path, fscache=self._fscache)
    event_container = self._GetEventContainer(events)

    # The ZIP file has 1 timestamp.
    self.assertEquals(len(event_container.events), 1)

  def testGzipFile(self):
    """Test a GZIP file."""
    path = event.EventPathSpec()
    path.type = 'GZIP'
    path.file_path = os.path.join('test_data', 'syslog.gz')

    events = self._ParseFileByPathSpec(
        self._parser, path, fscache=self._fscache)

    self.assertEquals(len(events), 0)

  def testTarFile(self):
    """Test a TAR file."""
    path = event.EventPathSpec()
    path.type = 'TAR'
    path.container_path = os.path.join('test_data', 'syslog.tar')
    path.file_path = 'syslog'

    events = self._ParseFileByPathSpec(
        self._parser, path, fscache=self._fscache)

    self.assertEquals(len(events), 0)

  def testNestedFile(self):
    """Test a nested file."""
    path = event.EventPathSpec()
    path.type = 'GZIP'
    path.file_path = os.path.join('test_data', 'syslog.tgz')

    host_file = event.EventPathSpec()
    host_file.type = 'TAR'
    host_file.file_path = 'syslog'

    path.nested_pathspec = host_file

    events = self._ParseFileByPathSpec(
        self._parser, path, fscache=self._fscache)

    # No stat available from a GZIP file.
    self.assertEquals(len(events), 0)

    path = event.EventPathSpec()
    path.type = 'OS'
    path.file_path = os.path.join('test_data', 'syslog.gz')

    gzip = event.EventPathSpec()
    gzip.type = 'GZIP'
    gzip.file_path = os.path.join('test_data', 'syslog.gz')

    path.nested_pathspec = gzip

    events = self._ParseFileByPathSpec(
        self._parser, path, fscache=self._fscache)

    # No stat available from a GZIP file.
    self.assertEquals(len(events), 0)

  def testNestedTSK(self):
    """Test a nested TSK file."""
    path = event.EventPathSpec()
    path.type = 'TSK'
    path.container_path = os.path.join('test_data', 'syslog_image.dd')
    path.image_offset = 0
    path.image_inode = 11
    path.file_path = 'logs/hidden.zip'

    host_path = event.EventPathSpec()
    host_path.type = 'ZIP'
    host_path.file_path = 'syslog'

    path.nested_pathspec = host_path

    events = self._ParseFileByPathSpec(
        self._parser, path, fscache=self._fscache)
    event_container = self._GetEventContainer(events)

    # The ZIP file has 1 timestamp.
    self.assertEquals(len(event_container.events), 1)


if __name__ == '__main__':
  unittest.main()
