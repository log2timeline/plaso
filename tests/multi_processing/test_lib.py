# -*- coding: utf-8 -*-
"""Multi-processing related functions and classes for testing."""

from __future__ import unicode_literals

from plaso.containers import events
from plaso.engine import knowledge_base
from plaso.parsers import mediator as parsers_mediator
from plaso.storage.fake import writer as fake_writer

from tests import test_lib as shared_test_lib


class MultiProcessingTestCase(shared_test_lib.BaseTestCase):
  """Multi-processing test case."""

  def _CreateTestEvent(self, event_values):
    """Create a test event and event data.

    Args:
      event_values (dict[str, str]): event values.

    Returns:
      tuple[EventObject, WindowsRegistryServiceEventData]: event and event
          data for testing.
    """
    copy_of_event_values = dict(event_values)

    timestamp = copy_of_event_values.get('timestamp', None)
    if 'timestamp' in copy_of_event_values:
      del copy_of_event_values['timestamp']

    timestamp_desc = copy_of_event_values.get('timestamp_desc', None)
    if 'timestamp_desc' in copy_of_event_values:
      del copy_of_event_values['timestamp_desc']

    event = events.EventObject()
    event.timestamp = timestamp
    event.timestamp_desc = timestamp_desc

    event_data = events.EventData()
    event_data.CopyFromDict(copy_of_event_values)

    return event, event_data

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
      for identifier, value in iter(knowledge_base_values.items()):
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
    parser_mediator = parsers_mediator.ParserMediator(
        storage_writer, knowledge_base_object)

    if file_entry:
      parser_mediator.SetFileEntry(file_entry)

    if parser_chain:
      parser_mediator.parser_chain = parser_chain

    return parser_mediator

  def _CreateStorageWriter(self, session):
    """Creates a storage writer object.

    Args:
      session (Session): session.

    Returns:
      FakeStorageWriter: storage writer.
    """
    storage_writer = fake_writer.FakeStorageWriter(session)
    storage_writer.Open()
    return storage_writer
