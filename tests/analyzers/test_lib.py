# -*- coding: utf-8 -*-
"""Analyzer related functions and classes for testing."""

from dfvfs.lib import definitions
from dfvfs.path import factory as path_spec_factory
from dfvfs.resolver import resolver as path_spec_resolver

from plaso.containers import sessions
from plaso.engine import knowledge_base
from plaso.parsers import mediator
from plaso.storage import fake_storage

from tests import test_lib as shared_test_lib


class AnalyzerTestCase(shared_test_lib.BaseTestCase):
  """Parent test case for a analyzer."""

  def _GetTestFileEntry(self, path_segments):
    """Creates a file_entry that references a file in the test dir.

    Args:
      path_segments (list[str]): the path segments inside the test data
          directory.

    Returns:
      dfvfs.FileEntry: file_entry object.
    """
    path = self._GetTestFilePath(path_segments)
    path_spec = path_spec_factory.Factory.NewPathSpec(
        definitions.TYPE_INDICATOR_OS, location=path)
    return path_spec_resolver.Resolver.OpenFileEntry(path_spec)

  def _CreateMediator(self):
    """Creates a parser mediator."""
    session = sessions.Session()
    storage_writer = fake_storage.FakeStorageWriter(session)
    storage_writer.Open()
    knowledge_base_object = knowledge_base.KnowledgeBase()
    parser_mediator = mediator.ParserMediator(
        storage_writer, knowledge_base_object)
    return parser_mediator
