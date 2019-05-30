#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the psort multi-processing engine."""

from __future__ import unicode_literals

import codecs
import os
import shutil
import unittest

from plaso.analysis import interface as analysis_interface
from plaso.analysis import tagging
from plaso.containers import sessions
from plaso.engine import configurations
from plaso.engine import knowledge_base
from plaso.formatters import interface as formatters_interface
from plaso.formatters import manager as formatters_manager
from plaso.formatters import mediator as formatters_mediator
from plaso.lib import definitions
from plaso.multi_processing import psort
from plaso.output import dynamic
from plaso.output import interface as output_interface
from plaso.output import mediator as output_mediator
from plaso.output import null
from plaso.storage import factory as storage_factory

from tests import test_lib as shared_test_lib
from tests.cli import test_lib as cli_test_lib
from tests.containers import test_lib as containers_test_lib
from tests.filters import test_lib as filters_test_lib
from tests.multi_processing import test_lib


class TestAnalysisPlugin(analysis_interface.AnalysisPlugin):
  """Analysis plugin for testing."""

  # pylint: disable=redundant-returns-doc
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

  def ExamineEvent(self, mediator, event, event_data):
    """Analyzes an event object.

    Args:
      mediator (AnalysisMediator): mediates interactions between
          analysis plugins and other components, such as storage and dfvfs.
      event (EventObject): event.
      event_data (EventData): event data.
    """
    return


class TestEventFormatter(formatters_interface.EventFormatter):
  """Event formatter for testing."""

  DATA_TYPE = 'test:event:psort'

  FORMAT_STRING = 'My text goes along: {text} lines'

  SOURCE_SHORT = 'LOG'
  SOURCE_LONG = 'None in Particular'


class TestOutputModule(output_interface.LinearOutputModule):
  """Output module for testing.

  Attributes:
    events (list[tuple[EventObject, EventData]]): event written to the output.
    macb_groups (list[list[tuple[EventObject, EventData]]]): MACB groups of
        events written to the output.
  """

  NAME = 'psort_test'

  def __init__(self, output_mediator_object):
    """Initializes an output module.

    Args:
      output_mediator_object (OutputMediator): mediates interactions between
          output modules and other components, such as storage and dfvfs.

    Raises:
      ValueError: when there are unused keyword arguments.
    """
    super(TestOutputModule, self).__init__(output_mediator_object)
    self.events = []
    self.macb_groups = []

  def WriteEventBody(self, event, event_data, event_tag):
    """Writes the body of an event object to the output.

    Args:
      event (EventObject): event.
      event_data (EventData): event data.
      event_tag (EventTag): event tag.
    """
    self.events.append((event, event_data, event_tag))

  def WriteHeader(self):
    """Writes the header to the output."""
    return

  def WriteEventMACBGroup(self, event_macb_group):
    """Writes an event MACB group to the output.

    An event MACB group is a group of events that have the same timestamp and
    event data (attributes and values), where the timestamp description (or
    usage) is one or more of MACB (modification, access, change, birth).

    This function is called if the psort engine detected an event MACB group
    so that the output module, if supported, can represent the group as
    such. If not overridden this function will output every event individually.

    Args:
      event_macb_group (list[EventObject]): group of events with identical
          timestamps, attributes and values.
    """
    self.events.extend(event_macb_group)
    self.macb_groups.append(event_macb_group)


class PsortEventHeapTest(test_lib.MultiProcessingTestCase):
  """Tests for the psort events heap."""

  # pylint: disable=protected-access

  _TEST_EVENTS = [
      {'data_type': 'test:event',
       'timestamp': 5134324321,
       'timestamp_desc': definitions.TIME_DESCRIPTION_CHANGE},
      {'data_type': 'test:event:psort',
       'display_name': '/dev/none',
       'filename': '/dev/none',
       'parser': 'TestEvent',
       'text': 'text',
       'timestamp': 2345871286,
       'timestamp_desc': definitions.TIME_DESCRIPTION_CHANGE,
       'var': {'Issue': False, 'Closed': True}}]

  def testNumberOfEvents(self):
    """Tests the number_of_events property."""
    event_heap = psort.PsortEventHeap()
    self.assertEqual(event_heap.number_of_events, 0)

  def testGetEventIdentifiers(self):
    """Tests the _GetEventIdentifiers function."""
    event_heap = psort.PsortEventHeap()

    event, event_data = containers_test_lib.CreateEventFromValues(
        self._TEST_EVENTS[0])
    macb_group_identifier, content_identifier = (
        event_heap._GetEventIdentifiers(event, event_data))

    expected_identifier = 'data_type: test:event'
    self.assertEqual(macb_group_identifier, expected_identifier)

    expected_identifier = 'Metadata Modification Time, data_type: test:event'
    self.assertEqual(content_identifier, expected_identifier)

  def testPopEvent(self):
    """Tests the PopEvent function."""
    event_heap = psort.PsortEventHeap()

    self.assertEqual(len(event_heap._heap), 0)

    test_event = event_heap.PopEvent()
    self.assertIsNone(test_event)

    for event, event_data in containers_test_lib.CreateEventsFromValues(
        self._TEST_EVENTS):
      event_heap.PushEvent(event, event_data)

    self.assertEqual(len(event_heap._heap), 2)

    test_event = event_heap.PopEvent()
    self.assertIsNotNone(test_event)

    self.assertEqual(len(event_heap._heap), 1)

  def testPopEvents(self):
    """Tests the PopEvents function."""
    event_heap = psort.PsortEventHeap()

    self.assertEqual(len(event_heap._heap), 0)

    test_events = list(event_heap.PopEvents())
    self.assertEqual(len(test_events), 0)

    for event, event_data in containers_test_lib.CreateEventsFromValues(
        self._TEST_EVENTS):
      event_heap.PushEvent(event, event_data)

    self.assertEqual(len(event_heap._heap), 2)

    test_events = list(event_heap.PopEvents())
    self.assertEqual(len(test_events), 2)

    self.assertEqual(len(event_heap._heap), 0)

  def testPushEvent(self):
    """Tests the PushEvent function."""
    event_heap = psort.PsortEventHeap()

    self.assertEqual(len(event_heap._heap), 0)

    event, event_data = containers_test_lib.CreateEventFromValues(
        self._TEST_EVENTS[0])
    event_heap.PushEvent(event, event_data)

    self.assertEqual(len(event_heap._heap), 1)


class PsortMultiProcessEngineTest(test_lib.MultiProcessingTestCase):
  """Tests for the multi-processing engine."""

  # pylint: disable=protected-access

  _TEST_EVENTS = [
      {'data_type': 'test:event',
       'timestamp': 5134324321,
       'timestamp_desc': definitions.TIME_DESCRIPTION_WRITTEN},
      {'data_type': 'test:event',
       'timestamp': 5134324321,
       'timestamp_desc': definitions.TIME_DESCRIPTION_LAST_ACCESS},
      {'data_type': 'test:event',
       'timestamp': 2134324321,
       'timestamp_desc': definitions.TIME_DESCRIPTION_UNKNOWN},
      {'data_type': 'test:event',
       'timestamp': 9134324321,
       'timestamp_desc': definitions.TIME_DESCRIPTION_UNKNOWN},
      {'data_type': 'test:event',
       'timestamp': 5134324321,
       'timestamp_desc': definitions.TIME_DESCRIPTION_CHANGE},
      {'data_type': 'test:event',
       'timestamp': 5134324321,
       'timestamp_desc': definitions.TIME_DESCRIPTION_CREATION},
      {'data_type': 'test:event',
       'timestamp': 15134324321,
       'timestamp_desc': definitions.TIME_DESCRIPTION_UNKNOWN},
      {'data_type': 'test:event',
       'timestamp': 5134324322,
       'timestamp_desc': definitions.TIME_DESCRIPTION_CREATION},
      {'data_type': 'test:event',
       'timestamp': 5134324322,
       'timestamp_desc': definitions.TIME_DESCRIPTION_LAST_ACCESS},
      {'data_type': 'test:event',
       'timestamp': 5134324322,
       'timestamp_desc': definitions.TIME_DESCRIPTION_CHANGE},
      {'data_type': 'test:event',
       'timestamp': 5134324322,
       'timestamp_desc': definitions.TIME_DESCRIPTION_WRITTEN},
      {'data_type': 'test:event',
       'timestamp': 5134324322,
       'timestamp_desc': definitions.TIME_DESCRIPTION_WRITTEN},
      {'data_type': 'test:event',
       'timestamp': 5134324322,
       'text': 'Another text',
       'timestamp_desc': definitions.TIME_DESCRIPTION_LAST_ACCESS},
      {'data_type': 'test:event',
       'timestamp': 5134324322,
       'text': 'Another text',
       'timestamp_desc': definitions.TIME_DESCRIPTION_CHANGE},
      {'data_type': 'test:event',
       'text': 'Another text',
       'timestamp': 5134324322,
       'timestamp_desc': definitions.TIME_DESCRIPTION_WRITTEN},
      {'data_type': 'test:event',
       'timestamp': 5134024321,
       'timestamp_desc': definitions.TIME_DESCRIPTION_UNKNOWN},
      {'data_type': 'test:event',
       'timestamp': 5134024321,
       'timestamp_desc': definitions.TIME_DESCRIPTION_UNKNOWN}]

  def _CreateTestStorageFile(self, path):
    """Creates a storage file for testing.

    Args:
      path (str): path.
    """
    storage_file = storage_factory.StorageFactory.CreateStorageFile(
        definitions.DEFAULT_STORAGE_FORMAT)
    storage_file.Open(path=path, read_only=False)

    # TODO: add preprocessing information.

    for event, event_data in containers_test_lib.CreateEventsFromValues(
        self._TEST_EVENTS):
      storage_file.AddEventData(event_data)

      event.SetEventDataIdentifier(event_data.GetIdentifier())
      storage_file.AddEvent(event)

    storage_file.Close()

  def testInternalAnalyzeEvents(self):
    """Tests the _AnalyzeEvents function."""
    session = sessions.Session()
    knowledge_base_object = knowledge_base.KnowledgeBase()

    test_engine = psort.PsortMultiProcessEngine()

    test_plugin = TestAnalysisPlugin()

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, 'storage.plaso')
      self._CreateTestStorageFile(temp_file)

      storage_writer = storage_factory.StorageFactory.CreateStorageWriter(
          definitions.DEFAULT_STORAGE_FORMAT, session, temp_file)

      storage_writer.StartTaskStorage()

      storage_writer.Open()
      storage_writer.ReadPreprocessingInformation(knowledge_base_object)

      # TODO: implement, this currently loops infinite.
      # test_engine._AnalyzeEvents(storage_writer, [test_plugin])
      storage_writer.Close()

    test_filter = filters_test_lib.TestEventFilter()

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, 'storage.plaso')
      self._CreateTestStorageFile(temp_file)

      storage_writer = storage_factory.StorageFactory.CreateStorageWriter(
          definitions.DEFAULT_STORAGE_FORMAT, session, temp_file)

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
  # TODO: add test for _ExportEvent.

  def testInternalExportEvents(self):
    """Tests the _ExportEvents function."""
    knowledge_base_object = knowledge_base.KnowledgeBase()
    output_writer = cli_test_lib.TestBinaryOutputWriter()

    formatter_mediator = formatters_mediator.FormatterMediator()

    output_mediator_object = output_mediator.OutputMediator(
        knowledge_base_object, formatter_mediator)

    output_module = TestOutputModule(output_mediator_object)
    output_module.SetOutputWriter(output_writer)

    test_engine = psort.PsortMultiProcessEngine()

    formatters_manager.FormattersManager.RegisterFormatter(TestEventFormatter)

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, 'storage.plaso')
      self._CreateTestStorageFile(temp_file)

      storage_reader = (
          storage_factory.StorageFactory.CreateStorageReaderForFile(temp_file))
      storage_reader.ReadPreprocessingInformation(knowledge_base_object)

      test_engine._ExportEvents(
          storage_reader, output_module, deduplicate_events=False)

    formatters_manager.FormattersManager.DeregisterFormatter(TestEventFormatter)

    self.assertEqual(len(output_module.events), 17)
    self.assertEqual(len(output_module.macb_groups), 3)

  def testInternalExportEventsDeduplicate(self):
    """Tests the _ExportEvents function with deduplication."""
    knowledge_base_object = knowledge_base.KnowledgeBase()
    output_writer = cli_test_lib.TestBinaryOutputWriter()

    formatter_mediator = formatters_mediator.FormatterMediator()

    output_mediator_object = output_mediator.OutputMediator(
        knowledge_base_object, formatter_mediator)

    output_module = TestOutputModule(output_mediator_object)
    output_module.SetOutputWriter(output_writer)

    test_engine = psort.PsortMultiProcessEngine()

    formatters_manager.FormattersManager.RegisterFormatter(TestEventFormatter)

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, 'storage.plaso')
      self._CreateTestStorageFile(temp_file)

      storage_reader = (
          storage_factory.StorageFactory.CreateStorageReaderForFile(temp_file))
      storage_reader.ReadPreprocessingInformation(knowledge_base_object)

      test_engine._ExportEvents(storage_reader, output_module)

    formatters_manager.FormattersManager.DeregisterFormatter(TestEventFormatter)

    lines = []
    output = output_writer.ReadOutput()
    for line in output.split(b'\n'):
      lines.append(line)

    self.assertEqual(len(output_module.events), 15)
    self.assertEqual(len(output_module.macb_groups), 3)

  # TODO: add test for _FlushExportBuffer.
  # TODO: add test for _StartAnalysisProcesses.
  # TODO: add test for _StatusUpdateThreadMain.
  # TODO: add test for _StopAnalysisProcesses.
  # TODO: add test for _UpdateProcessingStatus.

  def testAnalyzeEvents(self):
    """Tests the AnalyzeEvents function."""
    test_file_path = self._GetTestFilePath(['psort_test.plaso'])
    self._SkipIfPathNotExists(test_file_path)

    session = sessions.Session()
    knowledge_base_object = knowledge_base.KnowledgeBase()

    formatter_mediator = formatters_mediator.FormatterMediator()
    formatter_mediator.SetPreferredLanguageIdentifier('en-US')

    output_mediator_object = output_mediator.OutputMediator(
        knowledge_base_object, formatter_mediator)

    output_module = null.NullOutputModule(output_mediator_object)

    data_location = ''
    analysis_plugin = tagging.TaggingAnalysisPlugin()
    analysis_plugins = {'tagging': analysis_plugin}
    # TODO: set tag file.

    configuration = configurations.ProcessingConfiguration()

    test_engine = psort.PsortMultiProcessEngine()

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, 'storage.plaso')
      shutil.copyfile(test_file_path, temp_file)

      storage_writer = storage_factory.StorageFactory.CreateStorageWriter(
          definitions.DEFAULT_STORAGE_FORMAT, session, temp_file)

      counter = test_engine.AnalyzeEvents(
          knowledge_base_object, storage_writer, output_module, data_location,
          analysis_plugins, configuration)

    # TODO: assert if tests were successful.
    _ = counter

    test_filter = filters_test_lib.TestEventFilter()

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, 'storage.plaso')
      shutil.copyfile(test_file_path, temp_file)

      storage_writer = storage_factory.StorageFactory.CreateStorageWriter(
          definitions.DEFAULT_STORAGE_FORMAT, session, temp_file)

      counter = test_engine.AnalyzeEvents(
          knowledge_base_object, storage_writer, data_location,
          analysis_plugins, configuration, event_filter=test_filter)

    # TODO: assert if tests were successful.
    _ = counter

    # TODO: add bogus data location test.

  def testExportEvents(self):
    """Tests the ExportEvents function."""
    test_file_path = self._GetTestFilePath(['psort_test.plaso'])
    self._SkipIfPathNotExists(test_file_path)

    knowledge_base_object = knowledge_base.KnowledgeBase()
    output_writer = cli_test_lib.TestBinaryOutputWriter()

    formatter_mediator = formatters_mediator.FormatterMediator()
    formatter_mediator.SetPreferredLanguageIdentifier('en-US')

    output_mediator_object = output_mediator.OutputMediator(
        knowledge_base_object, formatter_mediator)

    output_module = dynamic.DynamicOutputModule(output_mediator_object)
    output_module.SetOutputWriter(output_writer)

    configuration = configurations.ProcessingConfiguration()

    storage_reader = storage_factory.StorageFactory.CreateStorageReaderForFile(
        test_file_path)

    test_engine = psort.PsortMultiProcessEngine()
    test_engine.ExportEvents(
        knowledge_base_object, storage_reader, output_module, configuration)

    lines = []
    output = output_writer.ReadOutput()
    # TODO: add test output writer that produces strings also see:
    # https://github.com/log2timeline/plaso/issues/1963
    output = codecs.decode(output, 'utf-8')
    for line in output.split('\n'):
      lines.append(line)

    self.assertEqual(len(lines), 22)

    expected_line = (
        '2014-11-18T01:15:43+00:00,'
        'Content Modification Time,'
        'LOG,'
        'Log File,'
        '[---] last message repeated 5 times ---,'
        'syslog,'
        'OS:/tmp/test/test_data/syslog,'
        'repeated')
    self.assertEqual(lines[14], expected_line)


if __name__ == '__main__':
  unittest.main()
