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
"""Tests for plaso.frontend.psort."""

import os
import StringIO
import tempfile

import unittest

from plaso.frontend import psort
from plaso.lib import event
from plaso.lib import output
from plaso.lib import eventdata
from plaso.lib import pfilter
from plaso.lib import storage


class TestEvent1(event.EventObject):
  DATA_TYPE = 'test:psort:1'

  def __init__(self):
    super(TestEvent1, self).__init__()
    self.timestamp = 123456


class TestEvent2(event.EventObject):
  DATA_TYPE = 'test:psort:2'

  def __init__(self, timestamp):
    super(TestEvent2, self).__init__()
    self.timestamp = timestamp
    self.timestamp_desc = 'Last Written'

    self.parser = 'TestEvent'

    self.display_name = '/dev/none'
    self.filename = '/dev/none'
    self.some = u'My text dude.'
    self.var = {'Issue': False, 'Closed': True}


class TestEvent2Formatter(eventdata.EventFormatter):
  DATA_TYPE = 'test:psort:2'

  FORMAT_STRING = 'My text goes along: {some} lines'

  SOURCE_SHORT = 'LOG'
  SOURCE_LONG = 'None in Particular'


class TestFormatter(output.LogOutputFormatter):
  """Dummy formatter."""

  def FetchEntry(self, store_number=-1, store_index=-1):
    return self.store.GetSortedEntry()

  def Start(self):
    self.filehandle.write((
        'date,time,timezone,MACB,source,sourcetype,type,user,host,'
        'short,desc,version,filename,inode,notes,format,extra\n'))

  def EventBody(self, event_object):
    event_formatter = eventdata.EventFormatterManager.GetFormatter(event_object)
    msg, _ = event_formatter.GetMessages(event_object)
    source_short, source_long = event_formatter.GetSources(event_object)
    self.filehandle.write(u'{}/{} {}\n'.format(
        source_short, source_long, msg))


class TestEventBuffer(output.EventBuffer):
  """A dummy output buffer."""

  def __init__(self, store, formatter=None):
    self.record_count = 0
    self.store = store
    if not formatter:
      formatter = TestFormatter(store)
    super(TestEventBuffer, self).__init__(formatter, False)

  def Append(self, event_object):
    self._buffer_dict[event_object.EqualityString()] = event_object
    self.record_count += 1

  def Flush(self):
    for event_object_key in self._buffer_dict:
      self.formatter.EventBody(self._buffer_dict[event_object_key])
    self._buffer_dict = {}

  def End(self):
    pass


class PsortTest(unittest.TestCase):
  """Test the plaso psort front-end."""

  def setUp(self):
    """Setup sets parameters that will be reused throughout this test."""
    # TODO: have sample output generated from the test.
    self.test_file = os.path.join('test_data', 'psort_test.out')
    self.first = 1342799054000000  # Fri, 20 Jul 2012 15:44:14 GMT
    self.last = 1342824552000000  # Fri, 20 Jul 2012 22:49:12 GMT

  def testSetupStorage(self):
    storage_cls = psort.SetupStorage(self.test_file)
    self.assertEquals(type(storage_cls), storage.PlasoStorage)

  def testReadEntries(self):
    """Ensure returned EventObjects from the storage are within timebounds."""
    store = storage.PlasoStorage(self.test_file, read_only=True)
    timestamp_list = []
    pfilter.TimeRangeCache.ResetTimeConstraints()
    pfilter.TimeRangeCache.SetUpperTimestamp(self.last)
    pfilter.TimeRangeCache.SetLowerTimestamp(self.first)
    store.SetStoreLimit()

    event_object = store.GetSortedEntry()
    while event_object:
      timestamp_list.append(event_object.timestamp)
      event_object = store.GetSortedEntry()

    self.assertEquals(len(timestamp_list), 10)
    self.assertTrue(timestamp_list[0] >= self.first and
                    timestamp_list[-1] <= self.last)

  def testOutput(self):
    """Testing if psort can output data."""
    events = []
    events.append(TestEvent2(5134324321))
    events.append(TestEvent2(2134324321))
    events.append(TestEvent2(9134324321))
    events.append(TestEvent2(15134324321))
    events.append(TestEvent2(5134324322))
    events.append(TestEvent2(5134024321))

    output_fd = StringIO.StringIO()

    with tempfile.NamedTemporaryFile() as fh:
      store = storage.PlasoStorage(fh)
      pfilter.TimeRangeCache.ResetTimeConstraints()
      store.SetStoreLimit()

      for my_event in events:
        store.AddEntry(my_event.ToProtoString())
      store.CloseStorage()

      with psort.SetupStorage(fh.name) as store:
        store.store_range = [1]
        formatter = TestFormatter(store, output_fd)
        event_buffer = TestEventBuffer(store, formatter)

        psort.ProcessOutput(event_buffer, formatter, None)

    event_buffer.Flush()
    lines = []
    for line in output_fd.getvalue().split('\n'):
      if line == '.':
        continue
      if line:
        lines.append(line)

    # One more line than events (header row).
    self.assertEquals(len(lines), 7)
    self.assertTrue('My text goes along: My text dude. lines' in lines[2])
    self.assertTrue('LOG/' in lines[2])
    self.assertTrue('None in Particular' in lines[2])
    self.assertEquals(
        lines[0], ('date,time,timezone,MACB,source,sourcetype,type,user,host,'
                   'short,desc,version,filename,inode,notes,format,extra'))


if __name__ == '__main__':
  unittest.main()
