#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the psort multi-processing engine."""

import os
import shutil
import unittest

from plaso.analysis import tagging
from plaso.containers import events
from plaso.containers import sessions
from plaso.engine import knowledge_base
from plaso.formatters import interface as formatters_interface
from plaso.formatters import manager as formatters_manager
from plaso.formatters import mediator as formatters_mediator
from plaso.multi_processing import psort
from plaso.output import dynamic
from plaso.output import event_buffer as output_event_buffer
from plaso.output import interface as output_interface
from plaso.output import mediator as output_mediator
from plaso.output import null
from plaso.storage import zip_file as storage_zip_file

from tests import test_lib as shared_test_lib
from tests.cli import test_lib as cli_test_lib


class TestEvent(events.EventObject):
  """Class that defines an event for testing."""

  DATA_TYPE = u'test:event:psort'

  def __init__(self, timestamp):
    """Initializes an event."""
    super(TestEvent, self).__init__()
    self.timestamp = timestamp
    self.timestamp_desc = u'Last Written'

    self.parser = u'TestEvent'

    self.display_name = u'/dev/none'
    self.filename = u'/dev/none'
    self.some = u'My text dude.'
    self.var = {u'Issue': False, u'Closed': True}


class TestEventFormatter(formatters_interface.EventFormatter):
  """Class that defines an event formatter for testing."""

  DATA_TYPE = u'test:event:psort'

  FORMAT_STRING = u'My text goes along: {some} lines'

  SOURCE_SHORT = u'LOG'
  SOURCE_LONG = u'None in Particular'


class TestOutputModule(output_interface.LinearOutputModule):
  """Class that defines an output module for testing."""

  NAME = u'psort_test'

  _HEADER = (
      u'date,time,timezone,MACB,source,sourcetype,type,user,host,'
      u'short,desc,version,filename,inode,notes,format,extra\n')

  def WriteEventBody(self, event):
    """Writes the body of an event object to the output.

    Args:
      event (EventObject): event.
    """
    message, _ = self._output_mediator.GetFormattedMessages(event)
    source_short, source_long = self._output_mediator.GetFormattedSources(event)
    self._WriteLine(u'{0:s}/{1:s} {2:s}\n'.format(
        source_short, source_long, message))

  def WriteHeader(self):
    """Writes the header to the output."""
    self._WriteLine(self._HEADER)


class TestEventBuffer(output_event_buffer.EventBuffer):
  """Class that defines an event buffer for testing.

  This class is used for buffering up events for duplicate removals
  and for other post-processing/analysis of events before being presented
  by the appropriate output module.

  Attributes:
    record_count (int): number of records.
  """

  def __init__(self, output_module, check_dedups=True):
    """Initialize an event buffer.

    Args:
      output_module (OutputModule): output module.
      check_dedups (Optional[bool]): True if the event buffer should check for
          and merge duplicate entries.
    """
    super(TestEventBuffer, self).__init__(
        output_module, check_dedups=check_dedups)
    self.record_count = 0

  def Append(self, event):
    """Appends an event.

    Args:
      event (EventObject): event.
    """
    key = event.EqualityString()
    self._events_per_key[key] = event
    self.record_count += 1

  def End(self):
    """Closes the buffer.

    Buffered event objects are written using the output module, an optional
    footer is written and the output is closed.
    """
    pass

  def Flush(self):
    """Flushes the buffer.

    Buffered event objects are written using the output module.
    """
    for key in iter(self._events_per_key.keys()):
      self._output_module.WriteEventBody(self._events_per_key[key])
    self._events_per_key = {}


class PsortMultiProcessEngineTest(shared_test_lib.BaseTestCase):
  """Tests for the multi-processing engine."""

  # pylint: disable=protected-access

  # TODO: add test for _AnalyzeEvent.
  # TODO: add test for _AnalyzeEvents.
  # TODO: add test for _CheckStatusAnalysisProcess.

  def testInternalExportEvents(self):
    """Tests the _ExportEvents function."""
    knowledge_base_object = knowledge_base.KnowledgeBase()
    output_writer = cli_test_lib.TestOutputWriter()

    formatter_mediator = formatters_mediator.FormatterMediator()

    output_mediator_object = output_mediator.OutputMediator(
        knowledge_base_object, formatter_mediator)

    output_module = TestOutputModule(output_mediator_object)
    output_module.SetOutputWriter(output_writer)

    test_engine = psort.PsortMultiProcessEngine()

    event_objects = [
        TestEvent(5134324321),
        TestEvent(2134324321),
        TestEvent(9134324321),
        TestEvent(15134324321),
        TestEvent(5134324322),
        TestEvent(5134024321)]

    formatters_manager.FormattersManager.RegisterFormatter(TestEventFormatter)

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, u'storage.plaso')

      storage_file = storage_zip_file.ZIPStorageFile()
      storage_file.Open(path=temp_file, read_only=False)
      # TODO: add preprocessing information.
      for event in event_objects:
        storage_file.AddEvent(event)
      storage_file.Close()

      storage_reader = storage_zip_file.ZIPStorageFileReader(temp_file)
      storage_reader.ReadPreprocessingInformation(knowledge_base_object)

      event_buffer = TestEventBuffer(output_module, check_dedups=False)

      test_engine._ExportEvents(storage_reader, event_buffer)

    event_buffer.Flush()

    formatters_manager.FormattersManager.DeregisterFormatter(TestEventFormatter)

    lines = []
    output = output_writer.ReadOutput()
    for line in output.split(b'\n'):
      lines.append(line)

    self.assertEqual(len(lines), 8)

    self.assertTrue(b'My text goes along: My text dude. lines' in lines[2])
    self.assertTrue(b'LOG/' in lines[2])
    self.assertTrue(b'None in Particular' in lines[2])
    self.assertEqual(lines[0], (
        b'date,time,timezone,MACB,source,sourcetype,type,user,host,short,desc,'
        b'version,filename,inode,notes,format,extra'))

  # TODO: add test for _StartAnalysisProcesses.
  # TODO: add test for _StatusUpdateThreadMain.
  # TODO: add test for _StopAnalysisProcesses.
  # TODO: add test for _UpdateProcessingStatus.

  def testAnalyzeEvents(self):
    """Tests the AnalyzeEvents function."""
    storage_file_path = self._GetTestFilePath([u'psort_test.json.plaso'])

    session = sessions.Session()
    knowledge_base_object = knowledge_base.KnowledgeBase()

    formatter_mediator = formatters_mediator.FormatterMediator()
    formatter_mediator.SetPreferredLanguageIdentifier(u'en-US')

    output_mediator_object = output_mediator.OutputMediator(
        knowledge_base_object, formatter_mediator)

    output_module = null.NullOutputModule(output_mediator_object)

    data_location = u''
    analysis_plugin = tagging.TaggingPlugin()
    # TODO: set tag file.

    test_engine = psort.PsortMultiProcessEngine()

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, u'storage.plaso')
      shutil.copyfile(storage_file_path, temp_file)

      storage_writer = storage_zip_file.ZIPStorageFileWriter(
          session, temp_file)

      counter = test_engine.AnalyzeEvents(
          knowledge_base_object, storage_writer, output_module, data_location,
          [analysis_plugin])

    # TODO: assert if tests were successful.
    _ = counter

    # TODO: add bogus data location test.

  def testExportEvents(self):
    """Tests the ExportEvents function."""
    storage_file_path = self._GetTestFilePath([u'psort_test.json.plaso'])

    knowledge_base_object = knowledge_base.KnowledgeBase()
    output_writer = cli_test_lib.TestOutputWriter()

    formatter_mediator = formatters_mediator.FormatterMediator()
    formatter_mediator.SetPreferredLanguageIdentifier(u'en-US')

    output_mediator_object = output_mediator.OutputMediator(
        knowledge_base_object, formatter_mediator)

    output_module = dynamic.DynamicOutputModule(output_mediator_object)
    output_module.SetOutputWriter(output_writer)

    storage_reader = storage_zip_file.ZIPStorageFileReader(storage_file_path)

    test_engine = psort.PsortMultiProcessEngine()
    counter = test_engine.ExportEvents(
        knowledge_base_object, storage_reader, output_module)

    # TODO: refactor preprocessing object.
    self.assertEqual(counter[u'Stored Events'], 0)

    lines = []
    output = output_writer.ReadOutput()
    for line in output.split(b'\n'):
      lines.append(line)

    self.assertEqual(len(lines), 21)

    expected_line = (
        u'2016-07-18T05:37:35+00:00,'
        u'mtime,'
        u'FILE,'
        u'OS mtime,'
        u'OS:/tmp/test/test_data/syslog Type: file,'
        u'filestat,'
        u'OS:/tmp/test/test_data/syslog,-')
    self.assertEquals(lines[14], expected_line)


if __name__ == '__main__':
  unittest.main()
