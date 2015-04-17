#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the psort front-end."""

import os
import unittest

from plaso.cli import test_lib as cli_test_lib
from plaso.formatters import interface as formatters_interface
from plaso.formatters import manager as formatters_manager
from plaso.formatters import mediator as formatters_mediator
from plaso.frontend import psort
from plaso.frontend import test_lib
from plaso.lib import event
from plaso.lib import pfilter
from plaso.lib import storage
from plaso.lib import timelib
from plaso.output import interface as output_interface
from plaso.output import mediator as output_mediator


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


class TestOutputModule(output_interface.LinearOutputModule):
  """Test output module."""

  _HEADER = (
      u'date,time,timezone,MACB,source,sourcetype,type,user,host,'
      u'short,desc,version,filename,inode,notes,format,extra\n')

  def WriteEventBody(self, event_object):
    """Writes the body of an event object to the output.

    Args:
      event_object: the event object (instance of EventObject).
    """
    message, _ = self._output_mediator.GetFormattedMessages(event_object)
    source_short, source_long = self._output_mediator.GetFormattedSources(
        event_object)
    self._WriteLine(u'{0:s}/{1:s} {2:s}\n'.format(
        source_short, source_long, message))

  def WriteHeader(self):
    """Writes the header to the output."""
    self._WriteLine(self._HEADER)


class TestEventBuffer(output_interface.EventBuffer):
  """A test event buffer."""

  def __init__(self, output_module, check_dedups=True, store=None):
    """Initialize the EventBuffer.

    This class is used for buffering up events for duplicate removals
    and for other post-processing/analysis of events before being presented
    by the appropriate output module.

    Args:
      output_module: The output module (instance of OutputModule).
      check_dedups: Optional boolean value indicating whether or not the buffer
                    should check and merge duplicate entries or not.
      store: Optional storage file object (instance of StorageFile) that defines
             the storage.
    """
    super(TestEventBuffer, self).__init__(
        output_module, check_dedups=check_dedups)
    self.record_count = 0
    self.store = store

  def Append(self, event_object):
    self._buffer_dict[event_object.EqualityString()] = event_object
    self.record_count += 1

  def Flush(self):
    for event_object_key in self._buffer_dict:
      self._output_module.WriteEventBody(self._buffer_dict[event_object_key])
    self._buffer_dict = {}

  def End(self):
    pass


class PsortFrontendTest(test_lib.FrontendTestCase):
  """Tests for the psort front-end."""

  def setUp(self):
    """Setup sets parameters that will be reused throughout this test."""
    self._formatter_mediator = formatters_mediator.FormatterMediator()
    self._front_end = psort.PsortFrontend()

    # TODO: have sample output generated from the test.
    self._test_file = os.path.join(self._TEST_DATA_PATH, u'psort_test.out')
    self.first = timelib.Timestamp.CopyFromString(u'2012-07-24 21:45:24')
    self.last = timelib.Timestamp.CopyFromString(u'2016-11-18 01:15:43')

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

    self.assertEqual(len(timestamp_list), 8)
    self.assertTrue(
        timestamp_list[0] >= self.first and timestamp_list[-1] <= self.last)

    storage_file.Close()

  def testOutput(self):
    """Testing if psort can output data."""
    formatters_manager.FormattersManager.RegisterFormatter(
        PsortTestEventFormatter)

    events = []
    events.append(PsortTestEvent(5134324321))
    events.append(PsortTestEvent(2134324321))
    events.append(PsortTestEvent(9134324321))
    events.append(PsortTestEvent(15134324321))
    events.append(PsortTestEvent(5134324322))
    events.append(PsortTestEvent(5134024321))

    output_writer = cli_test_lib.TestOutputWriter()

    with test_lib.TempDirectory() as dirname:
      temp_file = os.path.join(dirname, u'plaso.db')

      storage_file = storage.StorageFile(temp_file, read_only=False)
      pfilter.TimeRangeCache.ResetTimeConstraints()
      storage_file.SetStoreLimit()
      storage_file.AddEventObjects(events)
      storage_file.Close()

      with storage.StorageFile(temp_file) as storage_file:
        storage_file.store_range = [1]
        output_mediator_object = output_mediator.OutputMediator(
            self._formatter_mediator, storage_file)
        output_module = TestOutputModule(
            output_mediator_object, output_writer=output_writer)
        event_buffer = TestEventBuffer(
            output_module, check_dedups=False, store=storage_file)

        self._front_end.ProcessOutput(storage_file, event_buffer)

    event_buffer.Flush()
    lines = []
    output = output_writer.ReadOutput()
    for line in output.split(b'\n'):
      if line == b'.':
        continue
      if line:
        lines.append(line)

    # One more line than events (header row).
    self.assertEqual(len(lines), 7)
    self.assertTrue(b'My text goes along: My text dude. lines' in lines[2])
    self.assertTrue(b'LOG/' in lines[2])
    self.assertTrue(b'None in Particular' in lines[2])
    self.assertEqual(lines[0], (
        b'date,time,timezone,MACB,source,sourcetype,type,user,host,short,desc,'
        b'version,filename,inode,notes,format,extra'))

    formatters_manager.FormattersManager.DeregisterFormatter(
        PsortTestEventFormatter)

  # TODO: add bogus data location test.


if __name__ == '__main__':
  unittest.main()
