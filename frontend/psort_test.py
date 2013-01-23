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
import re
import StringIO
import tempfile

import pytz
import unittest

from plaso.frontend import psort
from plaso.lib import event
from plaso.lib import eventdata
from plaso.lib import storage

__pychecker__ = 'no-funcdoc'


class MyFormatter(eventdata.EventFormatter):
  """A simple test event formatter."""
  ID_RE = re.compile('FakeEvt', re.DOTALL)

  FORMAT_STRING = 'My text goes along: {some} lines'


class TestOutputRenderer(object):
  """A dummy renderer."""
  def __init__(self, store):
    self.buffer_list = []
    self.record_count = 0
    self.store = store

  def Append(self, item):
    __pychecker__ = 'missingattrs=buffer_list,record_count'
    self.buffer_list.append(item)
    self.record_count += 1

  def FetchEntry(self, store_index):
    """Fake a fetch entry."""
    return self.store.GetEntry(store_index)

  def Flush(self):
    pass

  def End(self):
    pass


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
      returned_timestamp, _ = psort.ReadPbCheckTime(
          number, self.first, self.last, TestOutputRenderer(store))
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

    def MockReadMetaOutput():
      yield 5
      yield 4

    store = storage.PlasoStorage(self.path, read_only=True)
    test_object = TestOutputRenderer(store)
    psort.MergeSort(MockReadMetaOutput(), self.first,
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

    class FakeEvt(event.EventObject):
      """A "fake" EventObject, or a dummy one used for this test."""

      def __init__(self):
        super(FakeEvt, self).__init__()
        self.timestamp = 123456
        self.source_short = 'LOG'
        self.source_long = 'NoSource'

    options = {}
    options['file_descriptor'] = open(os.devnull, 'a')
    options['out_format'] = 'Raw'
    options['store'] = None
    my_test_ob = psort.OutputRenderer(**options)
    my_test_ob.Append(FakeEvt())
    my_test_ob.Flush()
    self.assertEquals(len(my_test_ob.buffer_list), 0)

  def testOutput(self):
    """Testing if psort can output data."""
    class FakeEvt(event.EventObject):
      """Simple EventObject."""

      def __init__(self, timestamp):
        """Build it up."""
        super(FakeEvt, self).__init__()
        self.source_short = 'LOG'
        self.source_long = 'None in Particular'
        self.some = u'My text dude.'
        self.var = {'Issue': False, 'Closed': True}
        self.timestamp_desc = 'Last Written'
        self.timestamp = timestamp
        self.filename = '/dev/none'
        self.display_name = '/dev/none'
        self.parser = 'FakeEvt'

    events = []
    events.append(FakeEvt(5134324321))
    events.append(FakeEvt(2134324321))
    events.append(FakeEvt(9134324321))
    events.append(FakeEvt(15134324321))
    events.append(FakeEvt(5134324322))
    events.append(FakeEvt(5134024321))

    output_fd = StringIO.StringIO()

    with tempfile.NamedTemporaryFile() as fh:
      store = storage.PlasoStorage(fh)

      for my_event in events:
        store.AddEntry(my_event.ToProtoString())
      store.CloseStorage()

      with psort.SetupStorage(fh.name) as store:
        psort.MergeSort(
            (1,), 0, 90000000000,
            psort.OutputRenderer(store, file_descriptor=output_fd))

    lines = []
    for line in output_fd.getvalue().split('\n'):
      if line:
        lines.append(line)

    # One more line than events (header row).
    self.assertEquals(len(lines), 7)
    self.assertTrue('My text goes along: My text dude. lines' in lines[2])
    self.assertTrue(',LOG,' in lines[2])
    self.assertTrue(',None in Particular,' in lines[2])
    self.assertEquals(
        lines[0], ('date,time,timezone,MACB,source,sourcetype,type,user,host,'
                   'short,desc,version,filename,inode,notes,format,extra'))


if __name__ == '__main__':
  unittest.main()
