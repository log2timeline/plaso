#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the psort front-end."""

import os
import unittest

from plaso.formatters import interface as formatters_interface
from plaso.formatters import manager as formatters_manager
from plaso.formatters import mediator as formatters_mediator
from plaso.frontend import psort
from plaso.lib import event
from plaso.lib import timelib
from plaso.output import event_buffer as output_event_buffer
from plaso.output import interface as output_interface
from plaso.output import mediator as output_mediator
from plaso.storage import time_range as storage_time_range
from plaso.storage import zip_file as storage_zip_file

from tests import test_lib as shared_test_lib
from tests.cli import test_lib as cli_test_lib
from tests.frontend import test_lib


class PsortTestEvent(event.EventObject):
  DATA_TYPE = u'test:event:psort'

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
  DATA_TYPE = u'test:event:psort'

  FORMAT_STRING = u'My text goes along: {some} lines'

  SOURCE_SHORT = u'LOG'
  SOURCE_LONG = u'None in Particular'


class TestOutputModule(output_interface.LinearOutputModule):
  """Test output module."""

  NAME = u'psort_test'

  _HEADER = (
      u'date,time,timezone,MACB,source,sourcetype,type,user,host,'
      u'short,desc,version,filename,inode,notes,format,extra\n')

  def WriteEventBody(self, event_object):
    """Writes the body of an event object to the output.

    Args:
      event_object: an event object (instance of EventObject).
    """
    message, _ = self._output_mediator.GetFormattedMessages(event_object)
    source_short, source_long = self._output_mediator.GetFormattedSources(
        event_object)
    self._WriteLine(u'{0:s}/{1:s} {2:s}\n'.format(
        source_short, source_long, message))

  def WriteHeader(self):
    """Writes the header to the output."""
    self._WriteLine(self._HEADER)


class TestEventBuffer(output_event_buffer.EventBuffer):
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
    """Makes preparations before running an individual test."""
    self._formatter_mediator = formatters_mediator.FormatterMediator()
    self._front_end = psort.PsortFrontend()

    # TODO: have sample output generated from the test.

    self._start_timestamp = timelib.Timestamp.CopyFromString(
        u'2012-07-24 21:45:24')
    self._end_timestamp = timelib.Timestamp.CopyFromString(
        u'2016-11-18 01:15:43')

  def testReadEntries(self):
    """Ensure returned EventObjects from the storage are within time bounds."""
    storage_file_path = self._GetTestFilePath([u'psort_test.proto.plaso'])
    storage_file = storage_zip_file.StorageFile(
        storage_file_path, read_only=True)
    time_range = storage_time_range.TimeRange(
        self._start_timestamp, self._end_timestamp)

    timestamp_list = []
    # TODO: refactor to use StorageReader.
    for event_object in storage_file.GetSortedEntries(time_range=time_range):
      timestamp_list.append(event_object.timestamp)

    self.assertEqual(len(timestamp_list), 15)
    self.assertEqual(timestamp_list[0], self._start_timestamp)
    self.assertEqual(timestamp_list[-1], self._end_timestamp)

    storage_file.Close()

  def testProcessStorage(self):
    """Test the ProcessStorage function."""
    test_front_end = psort.PsortFrontend()
    test_front_end.SetOutputFormat(u'dynamic')
    test_front_end.SetPreferredLanguageIdentifier(u'en-US')
    test_front_end.SetQuietMode(True)

    storage_file_path = self._GetTestFilePath([u'psort_test.proto.plaso'])
    storage_file = test_front_end.OpenStorage(storage_file_path, read_only=True)

    output_writer = test_lib.StringIOOutputWriter()
    output_module = test_front_end.GetOutputModule(storage_file)
    output_module.SetOutputWriter(output_writer)

    counter = test_front_end.ProcessStorage(
        output_module, storage_file, storage_file_path, [], [])
    self.assertEqual(counter[u'Stored Events'], 15)

    output_writer.SeekToBeginning()
    lines = []
    line = output_writer.GetLine()
    while line:
      lines.append(line)
      line = output_writer.GetLine()

    self.assertEqual(len(lines), 16)

    expected_line = (
        u'2015-12-31T17:54:32+00:00,Entry Written,LOG,Log File,[anacron  '
        u'pid: 1234] : Another one just like this (124 job run),syslog,'
        u'OS:syslog,-\n')
    self.assertEquals(lines[13], expected_line)

  def testOutput(self):
    """Testing if psort can output data."""
    formatters_manager.FormattersManager.RegisterFormatter(
        PsortTestEventFormatter)

    events = [
        PsortTestEvent(5134324321),
        PsortTestEvent(2134324321),
        PsortTestEvent(9134324321),
        PsortTestEvent(15134324321),
        PsortTestEvent(5134324322),
        PsortTestEvent(5134024321)]

    output_writer = cli_test_lib.TestOutputWriter()

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, u'plaso.db')

      storage_file = storage_zip_file.StorageFile(temp_file)
      storage_file.AddEventObjects(events)
      storage_file.Close()

      with storage_zip_file.StorageFile(
          temp_file, read_only=True) as storage_file:
        output_mediator_object = output_mediator.OutputMediator(
            self._formatter_mediator)
        output_mediator_object.SetStorageFile(storage_file)

        output_module = TestOutputModule(output_mediator_object)
        output_module.SetOutputWriter(output_writer)
        event_buffer = TestEventBuffer(
            output_module, check_dedups=False, store=storage_file)

        self._front_end.ProcessEventsFromStorage(storage_file, event_buffer)

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

  def testGetLastGoodPreprocess(self):
    """Tests the last good preprocess method."""
    test_front_end = psort.PsortFrontend()
    storage_file_path = self._GetTestFilePath([u'psort_test.json.plaso'])
    storage_file = test_front_end.OpenStorage(storage_file_path, read_only=True)
    preprocessor_object = test_front_end._GetLastGoodPreprocess(storage_file)
    self.assertIsNotNone(preprocessor_object)
    timezone = getattr(preprocessor_object, u'zone')
    self.assertEqual(timezone.zone, u'Iceland')

  def testSetAnalysisPluginProcessInformation(self):
    """Test the _SetAnalysisPluginProcessInformation method."""
    test_front_end = psort.PsortFrontend()
    analysis_plugins = [test_lib.TestAnalysisPlugin(None)]

    preprocess_object = event.PreprocessObject()
    preprocess_object.SetCollectionInformationValues({})
    test_front_end._SetAnalysisPluginProcessInformation(
        u'', analysis_plugins, preprocess_object)
    self.assertIsNotNone(preprocess_object)
    plugin_names = preprocess_object.collection_information[u'plugins']
    time_of_run = preprocess_object.collection_information[u'time_of_run']
    method = preprocess_object.collection_information[u'method']

    for analysis_plugin in analysis_plugins:
      self.assertIn(analysis_plugin.NAME, plugin_names)
    self.assertAlmostEqual(timelib.Timestamp.GetNow(), time_of_run, 2000000)
    self.assertIsNotNone(method)

  # TODO: add bogus data location test.


if __name__ == '__main__':
  unittest.main()
