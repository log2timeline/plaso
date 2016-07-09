#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests the worker."""

import unittest

from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory
from dfvfs.resolver import context

from plaso.containers import sessions
from plaso.engine import knowledge_base
from plaso.engine import worker
from plaso.parsers import mediator as parsers_mediator
from plaso.storage import fake_storage

from tests import test_lib as shared_test_lib


class EventExtractionWorkerTest(shared_test_lib.BaseTestCase):
  """Tests for the worker object."""

  # pylint: disable=protected-access

  def _GetTestFilePathSpec(self, path_segments):
    """Retrieves a path specification of a test file in the test data directory.

    Args:
      path_segments: a list of strings containing the path segments inside
                     the test data directory.

    Returns:
      A path specification (instance of dfvfs.PathSpec).
    """
    source_path = self._GetTestFilePath(path_segments)
    return path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=source_path)

  def _TestProcessPathSpec(
      self, storage_writer, path_spec, process_archive_files=False):
    """Tests processing a path specification.

    Args:
      storage_writer: a storage writer object (instance of StorageWriter).
      path_spec: a path specification (dfvfs.PathSpec).
      process_archive_files: optional boolean value to indicate if archive
                             files should be processed.
    """
    knowledge_base_object = knowledge_base.KnowledgeBase()
    resolver_context = context.Context()

    parser_mediator = parsers_mediator.ParserMediator(
        storage_writer, knowledge_base_object)

    extraction_worker = worker.EventExtractionWorker(
        resolver_context, process_archive_files=process_archive_files)

    storage_writer.Open()
    storage_writer.WriteSessionStart()

    extraction_worker.ProcessPathSpec(parser_mediator, path_spec)

    new_event_sources = True
    while new_event_sources:
      new_event_sources = False
      event_source = storage_writer.GetNextEventSource()
      while event_source:
        new_event_sources = True

        extraction_worker.ProcessPathSpec(
            parser_mediator, event_source.path_spec)
        event_source = storage_writer.GetNextEventSource()

    storage_writer.WriteSessionCompletion()
    storage_writer.Close()

  def testProcessPathSpec(self):
    """Tests the ProcessPathSpec function."""
    session = sessions.Session()

    # Process a file.
    path_spec = self._GetTestFilePathSpec([u'syslog'])
    storage_writer = fake_storage.FakeStorageWriter(session)
    self._TestProcessPathSpec(storage_writer, path_spec)

    self.assertEqual(storage_writer.number_of_events, 16)

    # Process a compressed file.
    path_spec = self._GetTestFilePathSpec([u'syslog.gz'])
    storage_writer = fake_storage.FakeStorageWriter(session)
    self._TestProcessPathSpec(storage_writer, path_spec)

    self.assertEqual(storage_writer.number_of_events, 16)

    path_spec = self._GetTestFilePathSpec([u'syslog.bz2'])
    storage_writer = fake_storage.FakeStorageWriter(session)
    self._TestProcessPathSpec(storage_writer, path_spec)

    self.assertEqual(storage_writer.number_of_events, 15)

    # Process a file in an archive.
    source_path = self._GetTestFilePath([u'syslog.tar'])
    path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=source_path)
    path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TAR, location=u'/syslog',
        parent=path_spec)

    storage_writer = fake_storage.FakeStorageWriter(session)
    self._TestProcessPathSpec(storage_writer, path_spec)

    self.assertEqual(storage_writer.number_of_events, 13)

    # Process an archive file without "process archive files" mode.
    path_spec = self._GetTestFilePathSpec([u'syslog.tar'])
    storage_writer = fake_storage.FakeStorageWriter(session)
    self._TestProcessPathSpec(storage_writer, path_spec)

    self.assertEqual(storage_writer.number_of_events, 3)

    # Process an archive file with "process archive files" mode.
    path_spec = self._GetTestFilePathSpec([u'syslog.tar'])
    storage_writer = fake_storage.FakeStorageWriter(session)
    self._TestProcessPathSpec(
        storage_writer, path_spec, process_archive_files=True)

    self.assertEqual(storage_writer.number_of_events, 16)

    # Process a file in a compressed archive.
    source_path = self._GetTestFilePath([u'syslog.tgz'])
    path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=source_path)
    path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_GZIP, parent=path_spec)
    path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TAR, location=u'/syslog',
        parent=path_spec)

    storage_writer = fake_storage.FakeStorageWriter(session)
    self._TestProcessPathSpec(storage_writer, path_spec)

    self.assertEqual(storage_writer.number_of_events, 13)

    # Process an archive file with "process archive files" mode.
    path_spec = self._GetTestFilePathSpec([u'syslog.tgz'])
    storage_writer = fake_storage.FakeStorageWriter(session)
    self._TestProcessPathSpec(
        storage_writer, path_spec, process_archive_files=True)

    self.assertEqual(storage_writer.number_of_events, 17)

    # Process a storage media image with a symbolic link.
    source_path = self._GetTestFilePath([u'image.vmdk'])
    path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=source_path)
    path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_VMDK, parent=path_spec)
    path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK, location=u'/',
        parent=path_spec)
    storage_writer = fake_storage.FakeStorageWriter(session)
    self._TestProcessPathSpec(storage_writer, path_spec)

    self.assertEqual(storage_writer.number_of_events, 18)

  def testExtractionWorkerHashing(self):
    """Test that the worker sets up and runs hashing code correctly."""
    resolver_context = context.Context()
    extraction_worker = worker.EventExtractionWorker(resolver_context)

    extraction_worker.SetHashers(hasher_names_string=u'md5')
    self.assertEqual(1, len(extraction_worker._hasher_names))

    # TODO: test hashing results.


if __name__ == '__main__':
  unittest.main()
