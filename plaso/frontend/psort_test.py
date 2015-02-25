#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the psort front-end."""

import os
import StringIO
import unittest

from plaso.formatters import interface as formatters_interface
from plaso.formatters import manager as formatters_manager
from plaso.frontend import psort
from plaso.frontend import test_lib
from plaso.lib import event
from plaso.lib import pfilter
from plaso.lib import storage
from plaso.lib import timelib_test
from plaso.output import interface as output_interface


class PsortTestEvent(event.EventObject):
  DATA_TYPE = 'test:event:psort'

  def __init__(self, timestamp):
    super(PsortTestEvent, self).__init__()
    self.timestamp = timestamp
    self.timestamp_desc = u'Last Written'

    self.parser = u'TestEvent'

    self.display_name = u'/dev/none'
    self.filename = u'/dev/none'
    self.some = u'My text dude.'
    self.var = {u'Issue': False, u'Closed': True}


class PsortTestEventFormatter(formatters_interface.EventFormatter):
  DATA_TYPE = 'test:event:psort'

  FORMAT_STRING = u'My text goes along: {some} lines'

  SOURCE_SHORT = u'LOG'
  SOURCE_LONG = u'None in Particular'


formatters_manager.FormattersManager.RegisterFormatter(PsortTestEventFormatter)


class TestFormatter(output_interface.LogOutputFormatter):
  """Dummy formatter."""

  def Start(self):
    self.filehandle.write((
        u'date,time,timezone,MACB,source,sourcetype,type,user,host,'
        u'short,desc,version,filename,inode,notes,format,extra\n'))

  def EventBody(self, event_object):
    """Writes the event body.

    Args:
      event_object: The event object (instance of EventObject).
    """
    event_formatter = formatters_manager.FormattersManager.GetFormatterObject(
        event_object.data_type)
    msg, _ = event_formatter.GetMessages(event_object)
    source_short, source_long = event_formatter.GetSources(event_object)
    self.filehandle.write(u'{0:s}/{1:s} {2:s}\n'.format(
        source_short, source_long, msg))


class TestEventBuffer(output_interface.EventBuffer):
  """A test event buffer."""

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


class PsortFrontendTest(test_lib.FrontendTestCase):
  """Tests for the psort front-end."""

  def setUp(self):
    """Setup sets parameters that will be reused throughout this test."""
    self._front_end = psort.PsortFrontend()

    # TODO: have sample output generated from the test.
    self._test_file = os.path.join(self._TEST_DATA_PATH, u'psort_test.out')
    self.first = timelib_test.CopyStringToTimestamp(u'2012-07-24 21:45:24')
    self.last = timelib_test.CopyStringToTimestamp(u'2016-11-18 01:15:43')

  def testReadEntries(self):
    """Ensure returned EventObjects from the storage are within timebounds."""
    timestamp_list = []
    pfilter.TimeRangeCache.ResetTimeConstraints()
    pfilter.TimeRangeCache.SetUpperTimestamp(self.last)
    pfilter.TimeRangeCache.SetLowerTimestamp(self.first)

    storage_file = storage.StorageFile(self._test_file, read_only=True)
    storage_file.SetStoreLimit()

    event_object = storage_file.GetSortedEntry()
    while event_object:
      timestamp_list.append(event_object.timestamp)
      event_object = storage_file.GetSortedEntry()

    self.assertEquals(len(timestamp_list), 8)
    self.assertTrue(
        timestamp_list[0] >= self.first and timestamp_list[-1] <= self.last)

    storage_file.Close()

  def testOutput(self):
    """Testing if psort can output data."""
    events = []
    events.append(PsortTestEvent(5134324321))
    events.append(PsortTestEvent(2134324321))
    events.append(PsortTestEvent(9134324321))
    events.append(PsortTestEvent(15134324321))
    events.append(PsortTestEvent(5134324322))
    events.append(PsortTestEvent(5134024321))

    output_fd = StringIO.StringIO()

    with test_lib.TempDirectory() as dirname:
      temp_file = os.path.join(dirname, u'plaso.db')

      storage_file = storage.StorageFile(temp_file, read_only=False)
      pfilter.TimeRangeCache.ResetTimeConstraints()
      storage_file.SetStoreLimit()
      storage_file.AddEventObjects(events)
      storage_file.Close()

      with storage.StorageFile(temp_file) as storage_file:
        storage_file.store_range = [1]
        formatter = TestFormatter(storage_file, output_fd)
        event_buffer = TestEventBuffer(storage_file, formatter)

        self._front_end.ProcessOutput(storage_file, event_buffer)

    event_buffer.Flush()
    lines = []
    for line in output_fd.getvalue().split(u'\n'):
      if line == u'.':
        continue
      if line:
        lines.append(line)

    # One more line than events (header row).
    self.assertEquals(len(lines), 7)
    self.assertTrue(u'My text goes along: My text dude. lines' in lines[2])
    self.assertTrue(u'LOG/' in lines[2])
    self.assertTrue(u'None in Particular' in lines[2])
    self.assertEquals(lines[0], (
        u'date,time,timezone,MACB,source,sourcetype,type,user,host,short,desc,'
        u'version,filename,inode,notes,format,extra'))


if __name__ == '__main__':
  unittest.main()
