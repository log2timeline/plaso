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
"""This file contains the unit tests for the filestat parsing in Plaso."""
import os
import unittest

from plaso.lib import pfile
from plaso.parsers import filestat
from plaso.proto import transmission_pb2


class EmptyObject(object):
  """Empty object used to store pre-processing information."""


class FileStatTest(unittest.TestCase):
  """The unit test for filestat parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self.base_path = os.path.join('plaso/test_data')
    self.parser_obj = filestat.ParsePfileStat(EmptyObject())

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

    evts = list(self.parser_obj.Parse(fh))
    self.assertEquals(len(evts), 5)

  def testZipFile(self):
    image_path = os.path.join(self.base_path, 'syslog.zip')

    path = transmission_pb2.PathSpec()
    path.type = transmission_pb2.PathSpec.ZIP
    path.container_path = image_path
    path.file_path = 'syslog'

    fh = pfile.OpenPFile(path)
    evts = list(self.parser_obj.Parse(fh))
    # Only one timestamp from ZIP files.
    self.assertEquals(len(evts), 1)

  def testGzipFile(self):
    file_path = os.path.join(self.base_path, 'syslog.gz')

    path = transmission_pb2.PathSpec()
    path.type = transmission_pb2.PathSpec.GZIP
    path.file_path = file_path

    fh = pfile.OpenPFile(path)
    evts = list(self.parser_obj.Parse(fh))
    # There are no timestamps associated to uncompressed GZIP files (yet).
    self.assertEquals(len(evts), 0)

  def testTarFile(self):
    image_path = os.path.join(self.base_path, 'syslog.tar')

    path = transmission_pb2.PathSpec()
    path.type = transmission_pb2.PathSpec.TAR
    path.container_path = image_path
    path.file_path = 'syslog'

    fh = pfile.OpenPFile(path)
    evts = list(self.parser_obj.Parse(fh))
    # Nothing extracted from tar files yet.
    self.assertEquals(len(evts), 0)

  def testNestedFile(self):
    file_path = os.path.join(self.base_path, 'syslog.tgz')

    path = transmission_pb2.PathSpec()
    path.type = transmission_pb2.PathSpec.GZIP
    path.file_path = file_path

    host_file = transmission_pb2.PathSpec()
    host_file.type = transmission_pb2.PathSpec.TAR
    host_file.file_path = 'syslog'

    path.nested_pathspec.MergeFrom(host_file)

    fh = pfile.OpenPFile(path)
    # No stat available from a GZIP file.
    evts = list(self.parser_obj.Parse(fh))
    self.assertEquals(len(evts), 0)

    file_path = os.path.join(self.base_path, 'syslog.gz')

    path = transmission_pb2.PathSpec()
    path.type = transmission_pb2.PathSpec.OS
    path.file_path = file_path

    gzip = transmission_pb2.PathSpec()
    gzip.type = transmission_pb2.PathSpec.GZIP
    gzip.file_path = file_path

    path.nested_pathspec.MergeFrom(gzip)

    fh = pfile.OpenPFile(path)
    evts = list(self.parser_obj.Parse(fh))
    self.assertEquals(len(evts), 0)

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

    fh = pfile.OpenPFile(path)
    evts = list(self.parser_obj.Parse(fh))
    # Zip only contains a single timestamp.
    self.assertEquals(len(evts), 1)


if __name__ == '__main__':
  unittest.main()
