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
import os
import logging
import tempfile
import unittest

from plaso.lib import event
from plaso.lib import preprocess
from plaso.lib import queue
from plaso.lib import tsk_collector


class TskCollectorUnitTest(unittest.TestCase):
  """The unit test for the TSK collector."""

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
    my_storage = queue.SingleThreadedQueue()
    my_collect = tsk_collector.SimpleImageCollector(
        my_queue, my_storage, path, 0)
    my_collect.Run()
    events = self.GetEvents(my_queue)

    self.assertEquals(len(events), 2)


class TargetedImageTest(unittest.TestCase):
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
    my_queue = queue.SingleThreadedQueue()
    my_store = queue.SingleThreadedQueue()
    my_collector = tsk_collector.TargetedImageCollector(
        my_queue, my_store, image_path, filter_name, pre_obj, sector_offset=0,
        byte_offset=0, parse_vss=False)

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
    # TODO: Remove this unnecessary buildup of slashes in front.
    self.assertEquals(pathspecs[0].file_path, '///passwords.txt')


if __name__ == '__main__':
  unittest.main()
