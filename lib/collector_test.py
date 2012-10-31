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
"""This file contains the unit tests for the collection mechanism of Plaso."""
import os
import shutil
import tempfile
import unittest

from plaso.lib import collector
from plaso.proto import transmission_pb2


class TempDirectory(object):
  """A self cleaning temporary directory."""

  def __enter__(self):
    self.name = tempfile.mkdtemp()

    return self.name

  def __exit__(self, exc_type, exc_value, traceback):
    shutil.rmtree(self.name, True)


class PlasoCollectorUnitTest(unittest.TestCase):
  """The unit test for plaso storage."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self.base_path = os.path.join('plaso/test_data')

  def GetEvents(self, collector_queue):
    events = []
    for evt in collector_queue.PopItems():
      proto = transmission_pb2.PathSpec()
      proto.ParseFromString(evt)
      events.append(proto)

    return events

  def testTskCollector(self):
    """Test collection from a simple raw image device.

    This images has two files:
      + logs/hidden.zip
      + logs/sys.tgz

    The hidden.zip file contains one file, syslog, which is the
    same for sys.tgz.

    The end results should therefore be:
      + logs/hidden.zip (unchanged)
      + logs/hidden.zip:syslog (the text file extracted out)
      + logs/sys.tgz (unchanged)
      + logs/sys.tgz (read as a GZIP file, so not compressed)
      + logs/sys.tgz:syslog.gz (A GZIP file from the TAR container)
      + logs/sys.tgz:syslog.gz:syslog (the extracted syslog file)

    This means that the collection script should collect 6 files in total.
    """
    path = os.path.join(self.base_path, 'syslog_image.dd')

    # Start with a collector without opening files.
    my_collect = collector.SimpleImageCollector(path, 0)
    my_collect.Run()
    events = self.GetEvents(my_collect)

    self.assertEquals(len(events), 2)

  def testFileCollector(self):
    """Test collection from a simple file."""
    files = []
    files.append(os.path.join(self.base_path, 'syslog.tgz'))
    files.append(os.path.join(self.base_path, 'syslog.zip'))
    files.append(os.path.join(self.base_path, 'syslog.bz2'))
    files.append(os.path.join(self.base_path, 'wtmp.1'))

    with TempDirectory() as dirname:
      for a_file in files:
        shutil.copy(a_file, dirname)

      my_collect = collector.SimpleFileCollector(dirname)
      my_collect.Run()
      events = self.GetEvents(my_collect)

      self.assertEquals(len(events), 4)


if __name__ == '__main__':
  unittest.main()
