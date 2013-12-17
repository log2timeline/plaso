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
"""This file contains the unit tests for the collection mechanism of Plaso."""

import logging
import os
import shutil
import tempfile
import unittest

from plaso.collector import factory
from plaso.collector import os_collector
from plaso.lib import event
from plaso.lib import preprocess
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


class OsCollectorUnitTest(unittest.TestCase):
  """The unit test for the OS collector."""

  def GetEvents(self, collector_queue):
    """Return all events."""
    events = []
    for evt in collector_queue.PopItems():
      pathspec = event.EventPathSpec()
      pathspec.FromProtoString(evt)
      events.append(pathspec)

    return events

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
      my_store = queue.SingleThreadedQueue()
      with os_collector.OSCollector(
          my_queue, my_store, dirname) as my_collector:
        my_collector.Collect()
      events = self.GetEvents(my_queue)

      self.assertEquals(len(events), 4)


class TargetedDirectoryTest(unittest.TestCase):
  """Test targeted recursive directory check."""

  def testDirectoryTarget(self):
    """Run the tests."""
    filter_name = ''
    with tempfile.NamedTemporaryFile(delete=False) as fh:
      filter_name = fh.name
      fh.write('/test_data/testdir/filter_.+.txt\n')
      fh.write('/test_data/.+evtx\n')
      fh.write('/AUTHORS\n')
      fh.write('/does_not_exist/some_file_[0-9]+txt\n')

    pre_obj = preprocess.PlasoPreprocess()
    my_queue = queue.SingleThreadedQueue()
    my_store = queue.SingleThreadedQueue()
    my_collector = factory.GetFileSystemCollectorWithFilter(
      my_queue, my_store, pre_obj, './', filter_name)

    my_collector.Run()
    pathspecs = []
    for serialized_pathspec in my_queue.PopItems():
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


if __name__ == '__main__':
  unittest.main()
