#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the task-based multi-process processing analysis engine."""

import os
import shutil
import unittest

from plaso.analysis import tagging
from plaso.containers import sessions
from plaso.engine import configurations
from plaso.engine import knowledge_base
from plaso.lib import definitions
from plaso.multi_process import analysis_engine
from plaso.storage import factory as storage_factory

from tests import test_lib as shared_test_lib
from tests.filters import test_lib as filters_test_lib
from tests.multi_process import test_lib


class AnalysisEngineMultiProcessEngineTest(test_lib.MultiProcessingTestCase):
  """Tests for the task-based multi-process processing analysis engine."""

  # pylint: disable=protected-access

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
      knowledge_base_object.SetActiveSession(session.identifier)
      for source_configuration in session.source_configurations or []:
        knowledge_base_object.ReadSystemConfigurationArtifact(
            source_configuration.system_configuration)

  def testInternalAnalyzeEvents(self):
    """Tests the _AnalyzeEvents function."""
    test_file_path = self._GetTestFilePath(['psort_test.plaso'])
    self._SkipIfPathNotExists(test_file_path)

    test_tagging_file_path = self._GetTestFilePath([
        'tagging_file', 'valid.txt'])
    self._SkipIfPathNotExists(test_tagging_file_path)

    session = sessions.Session()
    knowledge_base_object = knowledge_base.KnowledgeBase()

    analysis_plugin = tagging.TaggingAnalysisPlugin()
    analysis_plugin.SetAndLoadTagFile(test_tagging_file_path)

    analysis_plugins = {'tagging': analysis_plugin}

    configuration = configurations.ProcessingConfiguration()
    test_engine = analysis_engine.AnalysisMultiProcessEngine()

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, 'storage.plaso')
      shutil.copyfile(test_file_path, temp_file)

      self._ReadSessionConfiguration(temp_file, knowledge_base_object)

      storage_writer = storage_factory.StorageFactory.CreateStorageWriter(
          definitions.DEFAULT_STORAGE_FORMAT)

      test_engine._processing_configuration = configuration
      test_engine._session = session

      test_engine._storage_file_path = temp_directory
      test_engine._StartTaskStorage(definitions.STORAGE_FORMAT_SQLITE)

      test_engine._StartAnalysisProcesses(analysis_plugins)

      storage_writer.Open(path=temp_file)

      try:
        events_counter = test_engine._AnalyzeEvents(
            storage_writer, analysis_plugins)
      finally:
        storage_writer.Close()

      test_engine._StopAnalysisProcesses()

    self.assertIsNotNone(events_counter)
    self.assertEqual(events_counter['Events filtered'], 0)
    self.assertEqual(events_counter['Events processed'], 38)

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
          definitions.DEFAULT_STORAGE_FORMAT)

      storage_writer.Open(path=temp_file)

      try:
        number_of_reports = storage_writer.GetNumberOfAttributeContainers(
            'analysis_report')
        self.assertEqual(number_of_reports, 2)

        test_engine.AnalyzeEvents(
            session, knowledge_base_object, storage_writer, data_location,
            analysis_plugins, configuration, storage_file_path=temp_directory)

        number_of_reports = storage_writer.GetNumberOfAttributeContainers(
            'analysis_report')
        self.assertEqual(number_of_reports, 3)

      finally:
        storage_writer.Close()

  def testAnalyzeEventsWithEventFilter(self):
    """Tests the AnalyzeEvents function with an event filter."""
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
    test_filter = filters_test_lib.TestEventFilter()

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, 'storage.plaso')
      shutil.copyfile(test_file_path, temp_file)

      storage_writer = storage_factory.StorageFactory.CreateStorageWriter(
          definitions.DEFAULT_STORAGE_FORMAT)

      storage_writer.Open(path=temp_file)

      try:
        number_of_reports = storage_writer.GetNumberOfAttributeContainers(
            'analysis_report')
        self.assertEqual(number_of_reports, 2)

        test_engine.AnalyzeEvents(
            session, knowledge_base_object, storage_writer, data_location,
            analysis_plugins, configuration, event_filter=test_filter,
            storage_file_path=temp_directory)

        number_of_reports = storage_writer.GetNumberOfAttributeContainers(
            'analysis_report')
        self.assertEqual(number_of_reports, 3)

      finally:
        storage_writer.Close()

  # TODO: add bogus data location test.


if __name__ == '__main__':
  unittest.main()
