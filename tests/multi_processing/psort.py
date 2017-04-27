#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the psort multi-processing engine."""

import os
import shutil
import unittest

from plaso.analysis import interface as analysis_interface
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
from tests.filters import test_lib as filters_test_lib


class TestAnalysisPlugin(analysis_interface.AnalysisPlugin):
  """Class that defines an analysis plugin for testing."""

  def CompileReport(self, mediator):
    """Compiles a report of the analysis.

    After the plugin has received every copy of an event to
    analyze this function will be called so that the report
    can be assembled.

    Args:
      mediator (AnalysisMediator): mediates interactions between
          analysis plugins and other components, such as storage and dfvfs.

    Returns:
      AnalysisReport: report, which will be None for testing.
    """
    return

  def ExamineEvent(self, mediator, event):
    """Analyzes an event object.

    Args:
      mediator (AnalysisMediator): mediates interactions between
          analysis plugins and other components, such as storage and dfvfs.
      event (EventObject): event.
    """
    pass


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
    event_identifier = event.GetIdentifier()
    lookup_key = event_identifier.CopyToString()
    self._events_per_key[lookup_key] = event
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

  def _CreateTestStorageFile(self, path):
    """Creates a storage file for testing.

    Args:
      path (str): path.
    """
    storage_file = storage_zip_file.ZIPStorageFile()
    storage_file.Open(path=path, read_only=False)

    # TODO: add preprocessing information.

    storage_file.AddEvent(TestEvent(5134324321))
    storage_file.AddEvent(TestEvent(2134324321))
    storage_file.AddEvent(TestEvent(9134324321))
    storage_file.AddEvent(TestEvent(15134324321))
    storage_file.AddEvent(TestEvent(5134324322))
    storage_file.AddEvent(TestEvent(5134024321))

    storage_file.Close()

  def testInternalAnalyzeEvents(self):
    """Tests the _AnalyzeEvents function."""
    session = sessions.Session()
    knowledge_base_object = knowledge_base.KnowledgeBase()

    test_engine = psort.PsortMultiProcessEngine()

    test_plugin = TestAnalysisPlugin()

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, u'storage.plaso')
      self._CreateTestStorageFile(temp_file)

      storage_writer = storage_zip_file.ZIPStorageFileWriter(
          session, temp_file)

      storage_writer.StartTaskStorage()

      storage_writer.Open()
      storage_writer.ReadPreprocessingInformation(knowledge_base_object)

      # TODO: implement, this currently loops infinite.
      # test_engine._AnalyzeEvents(storage_writer, [test_plugin])
      storage_writer.Close()

    test_filter = filters_test_lib.TestEventFilter()

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, u'storage.plaso')
      self._CreateTestStorageFile(temp_file)

      storage_writer = storage_zip_file.ZIPStorageFileWriter(
          session, temp_file)

      storage_writer.StartTaskStorage()

      storage_writer.Open()
      storage_writer.ReadPreprocessingInformation(knowledge_base_object)

      # TODO: implement, this currently loops infinite.
      _ = test_engine
      _ = test_plugin
      _ = test_filter
      # test_engine._AnalyzeEvents(
      #    storage_writer, [test_plugin], event_filter=test_filter)
      storage_writer.Close()

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

    formatters_manager.FormattersManager.RegisterFormatter(TestEventFormatter)

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, u'storage.plaso')
      self._CreateTestStorageFile(temp_file)

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

  @shared_test_lib.skipUnlessHasTestFile([u'psort_test.json.plaso'])
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
    analysis_plugin = tagging.TaggingAnalysisPlugin()
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

    test_filter = filters_test_lib.TestEventFilter()

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, u'storage.plaso')
      shutil.copyfile(storage_file_path, temp_file)

      storage_writer = storage_zip_file.ZIPStorageFileWriter(
          session, temp_file)

      counter = test_engine.AnalyzeEvents(
          knowledge_base_object, storage_writer, data_location,
          [analysis_plugin], event_filter=test_filter)

    # TODO: assert if tests were successful.
    _ = counter

    # TODO: add bogus data location test.

  @shared_test_lib.skipUnlessHasTestFile([u'psort_test.json.plaso'])
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

    self.assertEqual(counter[u'Stored Events'], 0)

    lines = []
    output = output_writer.ReadOutput()
    for line in output.split(b'\n'):
      lines.append(line)

    self.assertEqual(len(lines), 22)

    expected_line = (
        u'2014-11-18T01:15:43+00:00,'
        u'Content Modification Time,'
        u'LOG,'
        u'Log File,'
        u'[---] last message repeated 5 times ---,'
        u'syslog,'
        u'OS:/tmp/test/test_data/syslog,'
        u'repeated')
    self.assertEqual(lines[14], expected_line)


if __name__ == '__main__':
  unittest.main()
