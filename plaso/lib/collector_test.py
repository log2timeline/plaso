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
from plaso.lib import event
from plaso.lib import preprocess
from plaso.lib import sleuthkit
from plaso.lib import queue


class TempDirectory(object):
  """A self cleaning temporary directory."""

  def __enter__(self):
    """Make this work with the 'with' statement."""
    self.name = tempfile.mkdtemp()

    return self.name

  def __exit__(self, exc_type, exc_value, traceback):
    """Make this work with the 'with' statement."""
    _ = exc_type
    _ = exc_value
    _ = traceback
    shutil.rmtree(self.name, True)


class PlasoCollectorUnitTest(unittest.TestCase):
  """The unit test for plaso storage."""

  def GetEvents(self, collector_queue):
    """Return all events."""
    events = []
    for evt in collector_queue.PopItems():
      pathspec = event.EventPathSpec()
      pathspec.FromProtoString(evt)
      events.append(pathspec)

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
    path = os.path.join('test_data', 'syslog_image.dd')

    # Start with a collector without opening files.
    my_queue = queue.SingleThreadedQueue()
    my_collect = collector.PCollector(my_queue)
    my_collect.CollectFromImage(path, 0)
    events = self.GetEvents(my_queue)

    self.assertEquals(len(events), 2)

  def testFileCollector(self):
    """Test collection from a simple file."""
    files = []
    files.append(os.path.join('test_data', 'syslog.tgz'))
    files.append(os.path.join('test_data', 'syslog.zip'))
    files.append(os.path.join('test_data', 'syslog.bz2'))
    files.append(os.path.join('test_data', 'wtmp.1'))

    with TempDirectory() as dirname:
      for a_file in files:
        shutil.copy(a_file, dirname)

      my_queue = queue.SingleThreadedQueue()
      my_collect = collector.PCollector(my_queue)
      my_collect.CollectFromDir(dirname)
      events = self.GetEvents(my_queue)

      self.assertEquals(len(events), 4)


class PlasoTargetedImageTest(unittest.TestCase):
  """Test targeted collection from an image."""

  def testImageCollection(self):
    """Test the image collection."""
    image_path = os.path.join('test_data', 'image.dd')
    filter_name = ''
    with tempfile.NamedTemporaryFile(delete=False) as fh:
      filter_name = fh.name
      fh.write('/a_directory/.+zip\n')
      fh.write('/a_directory/another.+\n')
      fh.write('/passwords.txt\n')

    pre_obj = preprocess.PlasoPreprocess()
    my_collector = collector.TargetedImageCollector(
        image_path, filter_name, pre_obj, sector_offset=0, byte_offset=0,
        parse_vss=False)

    my_collector.Run()

    pathspecs = []
    for serialized_pathspec in my_collector.PopItems():
      pathspec = event.EventPathSpec()
      pathspec.FromProtoString(serialized_pathspec)
      pathspecs.append(pathspec)

    try:
      os.remove(filter_name)
    except (OSError, IOError) as e:
      logging.warning(
          u'Unable to remove temporary file: %s due to: %s', filter_name, e)

    self.assertEquals(len(pathspecs), 2)
    # pathspecs[0]
    # type: TSK
    # file_path: '//a_directory/another_file'
    # container_path: 'test_data/image.dd'
    # image_offset: 0
    self.assertEquals(pathspecs[0].file_path, '//a_directory/another_file')

    # pathspecs[1]
    # type: TSK
    # file_path: '///passwords.txt'
    # container_path: 'test_data/image.dd'
    # image_offset: 0
    # TODO: Remove this unnecessary buildup of slashes in front.
    self.assertEquals(pathspecs[1].file_path, '///passwords.txt')


class PlasoTargetedDirectory(unittest.TestCase):
  """Test targeted recursive directory check."""

  def testDirectoryTarget(self):
    """Run the tests."""
    filter_name = ''
    with tempfile.NamedTemporaryFile(delete=False) as fh:
      filter_name = fh.name
      fh.write('/plaso/lib/collector_.+.py\n')
      fh.write('/test_data/.+evtx\n')
      fh.write('/AUTHORS\n')
      fh.write('/does_not_exist/some_file_[0-9]+txt\n')

    pre_obj = preprocess.PlasoPreprocess()
    my_collector = collector.TargetedFileSystemCollector(
      pre_obj, './', filter_name)

    my_collector.Run()
    pathspecs = []
    for serialized_pathspec in my_collector.PopItems():
      pathspec = event.EventPathSpec()
      pathspec.FromProtoString(serialized_pathspec)
      pathspecs.append(pathspec)

    try:
      os.remove(filter_name)
    except (OSError, IOError) as e:
      logging.warning(
          u'Unable to remove temporary file: %s due to: %s', filter_name, e)

    # Three files with lib/collector_, AUTHORS and test_data/System.evtx.
    self.assertEquals(len(pathspecs), 5)

    paths = []
    for pathspec in pathspecs:
      paths.append(pathspec.file_path)

    self.assertTrue('./plaso/lib/collector_filter.py' in paths)
    self.assertTrue('./plaso/lib/collector_filter_test.py' in paths)
    self.assertTrue('././AUTHORS' in paths)


if __name__ == '__main__':
  unittest.main()
