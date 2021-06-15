#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the task-based multi-process processing analysis engine."""

import os
import shutil
import unittest

from plaso.analysis import interface as analysis_interface
from plaso.analysis import tagging
from plaso.containers import sessions
from plaso.engine import configurations
from plaso.engine import knowledge_base
from plaso.lib import definitions
from plaso.multi_processing import analysis_engine
from plaso.storage import factory as storage_factory

from tests import test_lib as shared_test_lib
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

  def ExamineEvent(self, mediator, event, event_data, event_data_stream):
    """Analyzes an event object.

    Args:
      mediator (AnalysisMediator): mediates interactions between
          analysis plugins and other components, such as storage and dfvfs.
      event (EventObject): event.
      event_data (EventData): event data.
      event_data_stream (EventDataStream): event data stream.
    """
    return


class AnalysisEngineMultiProcessEngineTest(test_lib.MultiProcessingTestCase):
  """Tests for the task-based multi-process processing analysis engine."""

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

    for event, event_data, event_data_stream in (
        containers_test_lib.CreateEventsFromValues(self._TEST_EVENTS)):
      storage_file.AddEventDataStream(event_data_stream)

      event_data.SetEventDataStreamIdentifier(event_data_stream.GetIdentifier())
      storage_file.AddEventData(event_data)

      event.SetEventDataIdentifier(event_data.GetIdentifier())
      storage_file.AddEvent(event)

    storage_file.Close()

  def _ReadSessionConfiguration(self, path, knowledge_base_object):
    """Reads session configuration information.

    The session configuration contains the system configuration, which contains
    information about various system specific configuration data, for example
    the user accounts.

    Args:
      path (str): path.
      knowledge_base_object (KnowledgeBase): is used to store the system
          configuration.
    """
    storage_reader = storage_factory.StorageFactory.CreateStorageReaderForFile(
        path)

    for session in storage_reader.GetSessions():
      if not session.source_configurations:
        storage_reader.ReadSystemConfiguration(knowledge_base_object)
      else:
        for source_configuration in session.source_configurations:
          knowledge_base_object.ReadSystemConfigurationArtifact(
              source_configuration.system_configuration,
              session_identifier=session.identifier)

  def testInternalAnalyzeEvents(self):
    """Tests the _AnalyzeEvents function."""
    session = sessions.Session()
    knowledge_base_object = knowledge_base.KnowledgeBase()

    test_engine = analysis_engine.AnalysisMultiProcessEngine()

    test_plugin = TestAnalysisPlugin()

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, 'storage.plaso')
      self._CreateTestStorageFile(temp_file)
      self._ReadSessionConfiguration(temp_file, knowledge_base_object)

      storage_writer = storage_factory.StorageFactory.CreateStorageWriter(
          definitions.DEFAULT_STORAGE_FORMAT, session, temp_file)

      storage_writer.Open()

      # TODO: implement, this currently loops infinite.
      # test_engine._AnalyzeEvents(
      # storage_writer, [test_plugin], storage_file_path=temp_directory)
      storage_writer.Close()

    test_filter = filters_test_lib.TestEventFilter()

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, 'storage.plaso')
      self._CreateTestStorageFile(temp_file)
      self._ReadSessionConfiguration(temp_file, knowledge_base_object)

      storage_writer = storage_factory.StorageFactory.CreateStorageWriter(
          definitions.DEFAULT_STORAGE_FORMAT, session, temp_file)

      storage_writer.Open()

      # TODO: implement, this currently loops infinite.
      _ = test_engine
      _ = test_plugin
      _ = test_filter
      # test_engine._AnalyzeEvents(
      #    storage_writer, [test_plugin], event_filter=test_filter,
      #    storage_file_path=temp_directory)
      storage_writer.Close()

  # TODO: add test for _CheckStatusAnalysisProcess.
  # TODO: add test for _StartAnalysisProcesses.
  # TODO: add test for _StatusUpdateThreadMain.
  # TODO: add test for _StopAnalysisProcesses.
  # TODO: add test for _UpdateProcessingStatus.

  def testAnalyzeEvents(self):
    """Tests the AnalyzeEvents function."""
    test_file_path = self._GetTestFilePath(['psort_test.plaso'])
    self._SkipIfPathNotExists(test_file_path)

    test_tagging_file_path = self._GetTestFilePath([
        'tagging_file', 'valid.txt'])
    self._SkipIfPathNotExists(test_tagging_file_path)

    session = sessions.Session()
    knowledge_base_object = knowledge_base.KnowledgeBase()

    data_location = ''

    analysis_plugin = tagging.TaggingAnalysisPlugin()
    analysis_plugin.SetAndLoadTagFile(test_tagging_file_path)

    analysis_plugins = {'tagging': analysis_plugin}

    configuration = configurations.ProcessingConfiguration()
    test_engine = analysis_engine.AnalysisMultiProcessEngine()

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, 'storage.plaso')
      shutil.copyfile(test_file_path, temp_file)

      storage_writer = storage_factory.StorageFactory.CreateStorageWriter(
          definitions.DEFAULT_STORAGE_FORMAT, session, temp_file)

      counter = test_engine.AnalyzeEvents(
          session, knowledge_base_object, storage_writer, data_location,
          analysis_plugins, configuration, storage_file_path=temp_directory)

    # TODO: assert if tests were successful.
    _ = counter

    test_engine = analysis_engine.AnalysisMultiProcessEngine()
    test_filter = filters_test_lib.TestEventFilter()

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, 'storage.plaso')
      shutil.copyfile(test_file_path, temp_file)

      storage_writer = storage_factory.StorageFactory.CreateStorageWriter(
          definitions.DEFAULT_STORAGE_FORMAT, session, temp_file)

      counter = test_engine.AnalyzeEvents(
          session, knowledge_base_object, storage_writer, data_location,
          analysis_plugins, configuration, event_filter=test_filter,
          storage_file_path=temp_directory)

    # TODO: assert if tests were successful.
    _ = counter

    # TODO: add bogus data location test.


if __name__ == '__main__':
  unittest.main()
