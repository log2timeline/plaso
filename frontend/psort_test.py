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
"""Tests for plaso.frontend.psort."""
import os

import pytz
import unittest

from plaso.frontend import psort
from plaso.lib import storage


class PsortTest(unittest.TestCase):
  """Test the plaso psort tool."""

  def setUp(self):
    """Setup sets parameters that will be reused throughout this test."""
    self.base_path = os.path.join('plaso/test_data')
    self.path = os.path.join(self.base_path, 'sample_output')
    self.first = 1349893007000000  # Wed, 10 Oct 2012 18:16:47 UTC+0
    self.last = 1349893565000000  # Wed, 10 Oct 2012 18:26:05 UTC+0

  def testGetMicroseconds(self):
    """Tests GetMicroseconds returns the correct timestamp."""
    date_str = '2012-10-10 16:18:56'  # Naive date string
    source_timezone = pytz.timezone('US/Eastern')  # UTC-4
    rtn = psort.GetMicroseconds(date_str, source_timezone)
    self.assertEquals(rtn, 1349900336000000)  # Wed, 10 Oct 2012 20:18:56 UTC+0

  class MockStore(object):
    """A simple mock of the storage object."""

    def GetProtoNumbers(self):
      yield 3
      yield 10

    def ReadMeta(self, number):
      if number == 3:
        return {'range': (1349893007000000, 1349893565000000)}
      if number == 10:
        return {'range': (1350820458000000, 1355914295000000)}

  def testReadMeta(self):
    """ReadMeta should read metas and return containers only within bounds."""
    store = self.MockStore()
    expected_result = (3)  # Mock has 3&10; only 3 in range
    for value in psort.ReadMeta(store, self.first, self.last):
      self.assertEquals(value, expected_result)

  def testReadPbCheckTime(self):
    """Ensure returned protobufs from a container are within the timebounds."""
    store = storage.PlasoStorage(self.path, read_only=True)
    success = False
    timestamp_list = []
    number = 4
    while not success:
      returned_timestamp, _ = psort.ReadPbCheckTime(store, number, self.first,
                                                   self.last)
      if returned_timestamp:
        timestamp_list.append(returned_timestamp)
      else:
        success = 1
    timestamp_list = sorted(timestamp_list)
    self.assertTrue(timestamp_list[0] >= self.first and timestamp_list[-1] <=
                    self.last)

  def testMergeSort(self):
    """This test ensures that items read and output are in the correct order.

    This method by design outputs data as it runs.  In order to test this a
    a modified OutputRenderer in is inserted here with flush removed.

    The test will be to read the OutputRenderer storage and check to see if it
    matches the known good sort order.
    """

    class OutputRenderer(object):
      def __init__(self):
        self.buffer_list = []
        self.record_count = 0

      def Append(self, item):
        self.buffer_list.append(item)
        self.record_count += 1

      def Flush(self):
        pass

      def End(self):
        pass

    def MockReadMetaOutput():
      yield 5
      yield 4

    test_object = OutputRenderer()
    store = storage.PlasoStorage(self.path, read_only=True)
    psort.MergeSort(store, MockReadMetaOutput(), self.first,
                    self.last, test_object)
    returned_list = []
    for item in test_object.buffer_list:
      returned_list.append(item.timestamp)

    correct_order = [1349893007000000L,
                     1349893007000000L,
                     1349893007000000L,
                     1349893007000000L,
                     1349893007000000L,
                     1349893449000000L,
                     1349893564000000L,
                     1349893564000000L,
                     1349893564000000L,
                     1349893564000000L,
                     1349893564000000L,
                     1349893564000000L,
                     1349893564000000L,
                     1349893565000000L,
                     1349893565000000L,
                     1349893565000000L]

    self.assertEquals(returned_list, correct_order)

  def testOutputRenderer_Flush(self):
    """Test to ensure we empty our buffers and sends to output properly."""

    class Fakepb(object):
      timestamp = 123456

    options = {}
    options['output_fd'] = open(os.devnull, 'a')
    options['Format'] = 'Raw'
    my_test_ob = psort.OutputRenderer(**options)
    my_test_ob.Append(Fakepb)
    #my_test_ob.Append((1340821021, Fakepb, 'test_filename'))
    my_test_ob.Flush()
    self.assertEquals(len(my_test_ob.buffer_list), 0)

if __name__ == '__main__':
  unittest.main()
