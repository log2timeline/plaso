#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the output and formatting multi-processing engine."""

import io
import os
import unittest

from plaso.engine import configurations
from plaso.lib import definitions
from plaso.multi_process import output_engine
from plaso.output import dynamic
from plaso.output import interface as output_interface
from plaso.output import mediator as output_mediator
from plaso.storage import factory as storage_factory

from tests import test_lib as shared_test_lib
from tests.containers import test_lib as containers_test_lib
from tests.multi_process import test_lib


class TestOutputModule(output_interface.OutputModule):
  """Output module for testing.

  Attributes:
    events (list[tuple[EventObject, EventData]]): event written to the output.
    macb_groups (list[list[tuple[EventObject, EventData]]]): MACB groups of
        events written to the output.
  """

  # pylint: disable=arguments-renamed,unused-argument

  NAME = 'psort_test'

  def __init__(self):
    """Initializes an output module."""
    super(TestOutputModule, self).__init__()
    self.events = []
    self.macb_groups = []

  def _GetFieldValues(
      self, output_mediator_object, event, event_data, event_data_stream,
      event_tag):
    """Retrieves the output field values.

    Args:
      output_mediator_object (OutputMediator): mediates interactions between
          output modules and other components, such as storage and dfVFS.
      event (EventObject): event.
      event_data (EventData): event data.
      event_data_stream (EventDataStream): event data stream.
      event_tag (EventTag): event tag.

    Returns:
      dict[str, str]: output field values per name.
    """
    return {}

  def _WriteFieldValues(self, output_mediator_object, field_values):
    """Writes field values to the output.

    Args:
      output_mediator_object (OutputMediator): mediates interactions between
          output modules and other components, such as storage and dfVFS.
      field_values (dict[str, str]): output field values per name.
    """
    self.events.append(field_values)

  def WriteFieldValuesOfMACBGroup(self, output_mediator_object, macb_group):
    """Writes field values of a MACB group to the output.

    Args:
      output_mediator_object (OutputMediator): mediates interactions between
          output modules and other components, such as storage and dfVFS.
      macb_group (list[dict[str, str]]): group of output field values per name
          with identical timestamps, attributes and values.
    """
    self.events.extend(macb_group)
    self.macb_groups.append(macb_group)

  def WriteHeader(self, output_mediator_object):
    """Writes the header to the output.

    Args:
      output_mediator_object (OutputMediator): mediates interactions between
          output modules and other components, such as storage and dfVFS.
    """
    return


class PsortEventHeapTest(test_lib.MultiProcessingTestCase):
  """Tests for the psort events heap."""

  # pylint: disable=protected-access

  _TEST_EVENTS = [
      {'data_type': 'test:event',
       'timestamp': 5134324321,
       'timestamp_desc': definitions.TIME_DESCRIPTION_METADATA_MODIFICATION},
      {'_parser_chain': 'test_parser',
       'data_type': 'test:event',
       'display_name': '/dev/none',
       'filename': '/dev/none',
       'text': 'text',
       'timestamp': 2345871286,
       'timestamp_desc': definitions.TIME_DESCRIPTION_METADATA_MODIFICATION,
       'var': 'Issue: False, Closed: True'}]

  def testNumberOfEvents(self):
    """Tests the number_of_events property."""
    event_heap = output_engine.PsortEventHeap()
    self.assertEqual(event_heap.number_of_events, 0)

  def testPopEvent(self):
    """Tests the PopEvent function."""
    event_heap = output_engine.PsortEventHeap()

    self.assertEqual(len(event_heap._heap), 0)

    test_event = event_heap.PopEvent()
    self.assertIsNone(test_event)

    for event, event_data, event_data_stream in (
        containers_test_lib.CreateEventsFromValues(self._TEST_EVENTS)):
      event_heap.PushEvent(event, event_data, event_data_stream)

    self.assertEqual(len(event_heap._heap), 2)

    test_event = event_heap.PopEvent()
    self.assertIsNotNone(test_event)

    self.assertEqual(len(event_heap._heap), 1)

  def testPopEvents(self):
    """Tests the PopEvents function."""
    event_heap = output_engine.PsortEventHeap()

    self.assertEqual(len(event_heap._heap), 0)

    test_events = list(event_heap.PopEvents())
    self.assertEqual(len(test_events), 0)

    for event, event_data, event_data_stream in (
        containers_test_lib.CreateEventsFromValues(self._TEST_EVENTS)):
      event_heap.PushEvent(event, event_data, event_data_stream)

    self.assertEqual(len(event_heap._heap), 2)

    test_events = list(event_heap.PopEvents())
    self.assertEqual(len(test_events), 2)

    self.assertEqual(len(event_heap._heap), 0)

  def testPushEvent(self):
    """Tests the PushEvent function."""
    event_heap = output_engine.PsortEventHeap()

    self.assertEqual(len(event_heap._heap), 0)

    event, event_data, event_data_stream = (
        containers_test_lib.CreateEventFromValues(self._TEST_EVENTS[0]))
    event_heap.PushEvent(event, event_data, event_data_stream)

    self.assertEqual(len(event_heap._heap), 1)


class OutputAndFormattingMultiProcessEngineTest(
    test_lib.MultiProcessingTestCase):
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
       'timestamp_desc': definitions.TIME_DESCRIPTION_METADATA_MODIFICATION},
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
       'timestamp_desc': definitions.TIME_DESCRIPTION_METADATA_MODIFICATION},
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
       'timestamp_desc': definitions.TIME_DESCRIPTION_METADATA_MODIFICATION},
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

    for event, event_data, event_data_stream in (
        containers_test_lib.CreateEventsFromValues(self._TEST_EVENTS)):
      storage_file.AddAttributeContainer(event_data_stream)

      event_data.SetEventDataStreamIdentifier(event_data_stream.GetIdentifier())
      storage_file.AddAttributeContainer(event_data)

      event.SetEventDataIdentifier(event_data.GetIdentifier())
      storage_file.AddAttributeContainer(event)

    storage_file.Close()

  # TODO: add test for _ExportEvent.

  def testInternalExportEvents(self):
    """Tests the _ExportEvents function."""
    formatters_directory_path = self._GetDataFilePath(['formatters'])

    output_module = TestOutputModule()

    test_engine = output_engine.OutputAndFormattingMultiProcessEngine()

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, 'storage.plaso')
      self._CreateTestStorageFile(temp_file)

      storage_reader = (
          storage_factory.StorageFactory.CreateStorageReaderForFile(temp_file))

      output_mediator_object = output_mediator.OutputMediator(
          storage_reader, data_location=shared_test_lib.TEST_DATA_PATH)
      output_mediator_object.ReadMessageFormattersFromDirectory(
          formatters_directory_path)

      test_engine._ExportEvents(
          storage_reader, output_module, deduplicate_events=False)

    self.assertEqual(len(output_module.events), 17)
    self.assertEqual(len(output_module.macb_groups), 3)

  def testInternalExportEventsDeduplicate(self):
    """Tests the _ExportEvents function with deduplication."""
    formatters_directory_path = self._GetDataFilePath(['formatters'])

    output_module = TestOutputModule()

    test_engine = output_engine.OutputAndFormattingMultiProcessEngine()

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, 'storage.plaso')
      self._CreateTestStorageFile(temp_file)

      storage_reader = (
          storage_factory.StorageFactory.CreateStorageReaderForFile(temp_file))

      output_mediator_object = output_mediator.OutputMediator(
          storage_reader, data_location=shared_test_lib.TEST_DATA_PATH)

      output_mediator_object.ReadMessageFormattersFromDirectory(
          formatters_directory_path)

      test_engine._ExportEvents(storage_reader, output_module)

    self.assertEqual(len(output_module.events), 15)
    self.assertEqual(len(output_module.macb_groups), 3)

  # TODO: add test for _FlushExportBuffer.

  def testExportEvents(self):
    """Tests the ExportEvents function."""
    test_file_path = self._GetTestFilePath(['psort_test.plaso'])
    self._SkipIfPathNotExists(test_file_path)

    test_file_object = io.StringIO()

    storage_reader = storage_factory.StorageFactory.CreateStorageReaderForFile(
        test_file_path)

    output_module = dynamic.DynamicOutputModule()
    output_module._file_object = test_file_object

    configuration = configurations.ProcessingConfiguration()
    configuration.data_location = shared_test_lib.DATA_PATH
    configuration.preferred_language = 'en-US'

    test_engine = output_engine.OutputAndFormattingMultiProcessEngine()

    test_engine.ExportEvents(storage_reader, output_module, configuration)

    output = test_file_object.getvalue()
    lines = output.split('\n')

    self.assertEqual(len(lines), 22)

    expected_line = (
        '2014-11-18T01:15:43.000000+00:00,'
        'Content Modification Time,'
        'LOG,'
        'Log File,'
        '[---] last message repeated 5 times ---,'
        'text/syslog_traditional,'
        'OS:/tmp/test/test_data/syslog,'
        'repeated')
    self.assertEqual(lines[14], expected_line)


if __name__ == '__main__':
  unittest.main()
