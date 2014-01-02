#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2013 The Plaso Project Authors.
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
"""The unit tests for the generic collector object."""

import logging
import os
import shutil
import tempfile
import unittest

from plaso.collector import generic_collector
from plaso.lib import event
from plaso.lib import preprocess
from plaso.lib import queue


class TempDirectory(object):
  """A self cleaning temporary directory."""

  def __enter__(self):
    """Make this work with the 'with' statement."""
    self.name = tempfile.mkdtemp()

    return self.name

  def __exit__(self, dummy_type, dummy_value, dummy_traceback):
    """Make this work with the 'with' statement."""
    shutil.rmtree(self.name, True)


class GenericCollectorUnitTest(unittest.TestCase):
  """The unit test for the OS collector."""

  def GetEvents(self, collector_queue):
    """Return all events."""
    events = []
    for evt in collector_queue.PopItems():
      pathspec = event.EventPathSpec()
      pathspec.FromProtoString(evt)
      events.append(pathspec)

    return events

  def testFileSystemCollection(self):
    """Test collection on the file system."""
    test_files = [
        os.path.join('test_data', 'syslog.tgz'),
        os.path.join('test_data', 'syslog.zip'),
        os.path.join('test_data', 'syslog.bz2'),
        os.path.join('test_data', 'wtmp.1')]

    with TempDirectory() as dirname:
      for a_file in test_files:
        shutil.copy(a_file, dirname)

      test_queue = queue.SingleThreadedQueue()
      test_store = queue.SingleThreadedQueue()
      test_collector = generic_collector.GenericCollector(
          test_queue, test_store, dirname)
      test_collector.Run()

      events = self.GetEvents(test_queue)
      self.assertEquals(len(events), 4)

  def testFileSystemWithFilterCollection(self):
    """Test collection on the file system with a filter."""
    filter_name = ''
    with tempfile.NamedTemporaryFile(delete=False) as fh:
      filter_name = fh.name
      fh.write('/test_data/testdir/filter_.+.txt\n')
      fh.write('/test_data/.+evtx\n')
      fh.write('/AUTHORS\n')
      fh.write('/does_not_exist/some_file_[0-9]+txt\n')

    pre_obj = preprocess.PlasoPreprocess()
    test_queue = queue.SingleThreadedQueue()
    test_store = queue.SingleThreadedQueue()
    test_collector = generic_collector.GenericCollector(
        test_queue, test_store, './')
    test_collector.SetFilter(filter_name, pre_obj)
    test_collector.Run()

    pathspecs = []
    for serialized_pathspec in test_queue.PopItems():
      pathspec = event.EventPathSpec()
      pathspec.FromProtoString(serialized_pathspec)
      pathspecs.append(pathspec)

    try:
      os.remove(filter_name)
    except (OSError, IOError) as e:
      logging.warning(
          u'Unable to remove temporary file: %s due to: %s', filter_name, e)

    # Two files with test_data/testdir/filter_*.txt, AUTHORS
    # and test_data/System.evtx.
    self.assertEquals(len(pathspecs), 4)

    paths = []
    for pathspec in pathspecs:
      paths.append(pathspec.file_path)

    self.assertTrue('./test_data/testdir/filter_1.txt' in paths)
    self.assertFalse('./test_data/testdir/filter2.txt' in paths)
    self.assertTrue('./test_data/testdir/filter_3.txt' in paths)
    self.assertTrue('././AUTHORS' in paths)

  def testImageCollection(self):
    """Test collection on a storage media image file.

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
    test_file = os.path.join('test_data', 'syslog_image.dd')

    test_queue = queue.SingleThreadedQueue()
    test_storage = queue.SingleThreadedQueue()
    test_collector = generic_collector.GenericCollector(
        test_queue, test_storage, test_file)
    test_collector.SetImageInformation(byte_offset=0)
    test_collector.Run()

    events = self.GetEvents(test_queue)
    self.assertEquals(len(events), 2)

  def testImageWithFilterCollection(self):
    """Test collection on a storage media image file with a filter."""
    test_file = os.path.join('test_data', 'image.dd')
    filter_name = ''
    with tempfile.NamedTemporaryFile(delete=False) as fh:
      filter_name = fh.name
      fh.write('/a_directory/.+zip\n')
      fh.write('/a_directory/another.+\n')
      fh.write('/passwords.txt\n')

    pre_obj = preprocess.PlasoPreprocess()
    test_queue = queue.SingleThreadedQueue()
    test_storage = queue.SingleThreadedQueue()
    test_collector = generic_collector.GenericCollector(
        test_queue, test_storage, test_file)
    test_collector.SetImageInformation(byte_offset=0)
    test_collector.SetFilter(filter_name, pre_obj)
    test_collector.Run()

    pathspecs = []
    for serialized_pathspec in test_queue.PopItems():
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
    self.assertEquals(pathspecs[1].file_path, '//a_directory/another_file')

    # pathspecs[1]
    # type: TSK
    # file_path: '///passwords.txt'
    # container_path: 'test_data/image.dd'
    # image_offset: 0
    self.assertEquals(pathspecs[0].file_path, '///passwords.txt')


if __name__ == '__main__':
  unittest.main()
