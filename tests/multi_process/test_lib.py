# -*- coding: utf-8 -*-
"""Multi-processing related functions and classes for testing."""

from plaso.engine import knowledge_base
from plaso.parsers import mediator as parsers_mediator
from plaso.storage.fake import writer as fake_writer

from tests import test_lib as shared_test_lib


class MultiProcessingTestCase(shared_test_lib.BaseTestCase):
  """Multi-processing test case."""

  def _CreateKnowledgeBase(self, knowledge_base_values=None, timezone='UTC'):
    """Creates a knowledge base.

    Args:
      knowledge_base_values (Optional[dict]): knowledge base values.
      timezone (str): timezone.

    Returns:
      KnowledgeBase: knowledge base.
    """
    knowledge_base_object = knowledge_base.KnowledgeBase()
    if knowledge_base_values:
      for identifier, value in knowledge_base_values.items():
        knowledge_base_object.SetValue(identifier, value)

    knowledge_base_object.SetTimeZone(timezone)

    return knowledge_base_object

  def _CreateParserMediator(
      self, storage_writer, knowledge_base_object, file_entry=None,
      parser_chain=None):
    """Creates a parser mediator.

    Args:
      storage_writer (StorageWriter): storage writer.
      knowledge_base_object (KnowledgeBase): knowledge base.
      file_entry (Optional[dfvfs.FileEntry]): file entry object being parsed.
      parser_chain (Optional[str]): parsing chain up to this point.

    Returns:
      ParserMediator: parser mediator.
    """
    parser_mediator = parsers_mediator.ParserMediator(knowledge_base_object)
    parser_mediator.SetStorageWriter(storage_writer)

    if file_entry:
      parser_mediator.SetFileEntry(file_entry)

    if parser_chain:
      parser_mediator.parser_chain = parser_chain

    return parser_mediator

  def _CreateStorageWriter(self):
    """Creates a storage writer object.

    Returns:
      FakeStorageWriter: storage writer.
    """
    storage_writer = fake_writer.FakeStorageWriter()
    storage_writer.Open()
    return storage_writer
