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

from plaso.collector import collector
from plaso.lib import event
from plaso.lib import queue


class TempDirectory(object):
  """A self cleaning temporary directory."""

  def __init__(self):
    """Initializes the temporary directory."""
    super(TempDirectory, self).__init__()
    self.name = u''

  def __enter__(self):
    """Make this work with the 'with' statement."""
    self.name = tempfile.mkdtemp()
    return self.name

  def __exit__(self, unused_type, unused_value, unused_traceback):
    """Make this work with the 'with' statement."""
    shutil.rmtree(self.name, True)


class TestCollectorQueueConsumer(queue.PathSpecQueueConsumer):
  """Class that implements a test collector queue consumer."""

  def __init__(self, queue_object):
    """Initializes the queue consumer.

    Args:
      queue_object: the queue object (instance of Queue).
    """
    super(TestCollectorQueueConsumer, self).__init__(queue_object)
    self.path_specs = []

  def _ConsumePathSpec(self, path_spec):
    """Consumes a path specification callback for ConsumePathSpecs."""
    self.path_specs.append(path_spec)

  @property
  def number_of_path_specs(self):
    """The number of path specifications."""
    return len(self.path_specs)

  def GetFilePaths(self):
    """Retrieves a list of file paths from the path specifications."""
    return [path_spec.file_path for path_spec in self.path_specs]


class CollectorTest(unittest.TestCase):
  """The unit test for the OS collector."""

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

      test_collection_queue = queue.SingleThreadedQueue()
      test_store = queue.SingleThreadedQueue()
      test_collector = collector.Collector(
          test_collection_queue, test_store, dirname)
      test_collector.Collect()

      test_collector_queue_consumer = TestCollectorQueueConsumer(
          test_collection_queue)
      test_collector_queue_consumer.ConsumePathSpecs()

      self.assertEquals(test_collector_queue_consumer.number_of_path_specs, 4)

  def testFileSystemWithFilterCollection(self):
    """Test collection on the file system with a filter."""
    filter_name = ''
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
      filter_name = temp_file.name
      temp_file.write('/test_data/testdir/filter_.+.txt\n')
      temp_file.write('/test_data/.+evtx\n')
      temp_file.write('/AUTHORS\n')
      temp_file.write('/does_not_exist/some_file_[0-9]+txt\n')

    pre_obj = event.PreprocessObject()
    test_collection_queue = queue.SingleThreadedQueue()
    test_store = queue.SingleThreadedQueue()
    test_collector = collector.Collector(
          test_collection_queue, test_store, './')
    test_collector.SetFilter(filter_name, pre_obj)
    test_collector.Collect()

    test_collector_queue_consumer = TestCollectorQueueConsumer(
          test_collection_queue)
    test_collector_queue_consumer.ConsumePathSpecs()

    try:
      os.remove(filter_name)
    except (OSError, IOError) as e:
      logging.warning((
          u'Unable to remove temporary file: {0:s} due to: {1:s}').format(
              filter_name, e))

    # Two files with test_data/testdir/filter_*.txt, AUTHORS
    # and test_data/System.evtx.
    self.assertEquals(test_collector_queue_consumer.number_of_path_specs, 4)

    paths = test_collector_queue_consumer.GetFilePaths()
    self.assertTrue(u'./test_data/testdir/filter_1.txt' in paths)
    self.assertFalse(u'./test_data/testdir/filter2.txt' in paths)
    self.assertTrue(u'./test_data/testdir/filter_3.txt' in paths)
    self.assertTrue(u'./AUTHORS' in paths)

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

    test_collection_queue = queue.SingleThreadedQueue()
    test_storage_queue = queue.SingleThreadedQueue()
    test_storage_queue_producer = queue.EventObjectQueueProducer(
        test_storage_queue)
    test_collector = collector.Collector(
          test_collection_queue, test_storage_queue_producer, test_file)
    test_collector.SetImageInformation(byte_offset=0)
    test_collector.Collect()

    test_collector_queue_consumer = TestCollectorQueueConsumer(
          test_collection_queue)
    test_collector_queue_consumer.ConsumePathSpecs()

    self.assertEquals(test_collector_queue_consumer.number_of_path_specs, 2)

  def testImageWithFilterCollection(self):
    """Test collection on a storage media image file with a filter."""
    test_file = os.path.join('test_data', 'image.dd')

    filter_name = ''
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
      filter_name = temp_file.name
      temp_file.write('/a_directory/.+zip\n')
      temp_file.write('/a_directory/another.+\n')
      temp_file.write('/passwords.txt\n')

    pre_obj = event.PreprocessObject()
    test_collection_queue = queue.SingleThreadedQueue()
    test_storage_queue = queue.SingleThreadedQueue()
    test_storage_queue_producer = queue.EventObjectQueueProducer(
        test_storage_queue)
    test_collector = collector.Collector(
          test_collection_queue, test_storage_queue_producer, test_file)
    test_collector.SetImageInformation(byte_offset=0)
    test_collector.SetFilter(filter_name, pre_obj)
    test_collector.Collect()

    test_collector_queue_consumer = TestCollectorQueueConsumer(
          test_collection_queue)
    test_collector_queue_consumer.ConsumePathSpecs()

    try:
      os.remove(filter_name)
    except (OSError, IOError) as e:
      logging.warning((
          u'Unable to remove temporary file: {0:s} due to: {1:s}').format(
              filter_name, e))

    self.assertEquals(test_collector_queue_consumer.number_of_path_specs, 2)

    paths = test_collector_queue_consumer.GetFilePaths()

    # path_specs[0]
    # type: TSK
    # file_path: '/a_directory/another_file'
    # container_path: 'test_data/image.dd'
    # image_offset: 0
    self.assertEquals(paths[0], u'/a_directory/another_file')

    # path_specs[1]
    # type: TSK
    # file_path: '/passwords.txt'
    # container_path: 'test_data/image.dd'
    # image_offset: 0
    self.assertEquals(paths[1], u'/passwords.txt')


if __name__ == '__main__':
  unittest.main()
