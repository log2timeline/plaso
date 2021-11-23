# -*- coding: utf-8 -*-
"""Analysis plugin related functions and classes for testing."""

from plaso.analysis import mediator as analysis_mediator
from plaso.containers import artifacts
from plaso.containers import events
from plaso.containers import sessions
from plaso.engine import knowledge_base
from plaso.parsers import interface as parsers_interface
from plaso.parsers import mediator as parsers_mediator
from plaso.storage.fake import writer as fake_writer

from tests import test_lib as shared_test_lib
from tests.containers import test_lib as containers_test_lib


class AnalysisPluginTestCase(shared_test_lib.BaseTestCase):
  """The unit test case for an analysis plugin."""

  def _AnalyzeEvents(
      self, event_values_list, plugin, knowledge_base_values=None):
    """Analyzes events using the analysis plugin.

    Args:
      event_values_list (list[dict[str, object]]): list of event values.
      plugin (AnalysisPlugin): plugin.
      knowledge_base_values (Optional[dict[str, str]]): knowledge base values.

    Returns:
      FakeStorageWriter: storage writer.
    """
    knowledge_base_object = self._SetUpKnowledgeBase(
        knowledge_base_values=knowledge_base_values)

    session = sessions.Session()
    storage_writer = fake_writer.FakeStorageWriter()
    storage_writer.Open()

    test_events = []
    for event, event_data, event_data_stream in (
        containers_test_lib.CreateEventsFromValues(event_values_list)):
      storage_writer.AddAttributeContainer(event_data_stream)

      event_data.SetEventDataStreamIdentifier(event_data_stream.GetIdentifier())
      storage_writer.AddAttributeContainer(event_data)

      event.SetEventDataIdentifier(event_data.GetIdentifier())
      storage_writer.AddAttributeContainer(event)

      test_events.append((event, event_data, event_data_stream))

    mediator = analysis_mediator.AnalysisMediator(
        session, knowledge_base_object)
    mediator.SetStorageWriter(storage_writer)

    for event, event_data, event_data_stream in test_events:
      plugin.ExamineEvent(mediator, event, event_data, event_data_stream)

    analysis_report = plugin.CompileReport(mediator)
    storage_writer.AddAttributeContainer(analysis_report)

    return storage_writer

  def _ParseAndAnalyzeFile(
      self, path_segments, parser, plugin, knowledge_base_values=None):
    """Parses and analyzes a file using the parser and analysis plugin.

    Args:
      path_segments (list[str]): path segments inside the test data directory.
      parser (BaseParser): parser.
      plugin (AnalysisPlugin): plugin.
      knowledge_base_values (Optional[dict[str, str]]): knowledge base values.

    Returns:
      FakeStorageWriter: storage writer.

    Raises:
      SkipTest: if the path inside the test data directory does not exist and
          the test should be skipped.
    """
    session = sessions.Session()

    knowledge_base_object = self._SetUpKnowledgeBase(
        knowledge_base_values=knowledge_base_values)

    storage_writer = self._ParseFile(
        path_segments, parser, knowledge_base_object)

    mediator = analysis_mediator.AnalysisMediator(
        session, knowledge_base_object)
    mediator.SetStorageWriter(storage_writer)

    for event in storage_writer.GetSortedEvents():
      event_data = None
      event_data_identifier = event.GetEventDataIdentifier()
      if event_data_identifier:
        event_data = storage_writer.GetAttributeContainerByIdentifier(
            events.EventData.CONTAINER_TYPE, event_data_identifier)

      event_data_stream = None
      if event_data:
        event_data_stream_identifier = event_data.GetEventDataStreamIdentifier()
        if event_data_stream_identifier:
          event_data_stream = storage_writer.GetAttributeContainerByIdentifier(
              events.EventDataStream.CONTAINER_TYPE,
              event_data_stream_identifier)

      plugin.ExamineEvent(mediator, event, event_data, event_data_stream)

    analysis_report = plugin.CompileReport(mediator)
    storage_writer.AddAttributeContainer(analysis_report)

    return storage_writer

  def _ParseFile(self, path_segments, parser, knowledge_base_object):
    """Parses a file using the parser.

    Args:
      path_segments (list[str]): path segments inside the test data directory.
      parser (BaseParser): parser.
      knowledge_base_object (KnowledgeBase): knowledge base.

    Returns:
      FakeStorageWriter: storage writer.

    Raises:
      SkipTest: if the path inside the test data directory does not exist and
          the test should be skipped.
    """
    parser_mediator = parsers_mediator.ParserMediator(knowledge_base_object)

    storage_writer = fake_writer.FakeStorageWriter()
    storage_writer.Open()
    parser_mediator.SetStorageWriter(storage_writer)

    file_entry = self._GetTestFileEntry(path_segments)
    parser_mediator.SetFileEntry(file_entry)

    event_data_stream = events.EventDataStream()
    parser_mediator.ProduceEventDataStream(event_data_stream)

    if isinstance(parser, parsers_interface.FileEntryParser):
      parser.Parse(parser_mediator)

    elif isinstance(parser, parsers_interface.FileObjectParser):
      file_object = file_entry.GetFileObject()
      parser.Parse(parser_mediator, file_object)

    else:
      self.fail('Got unexpected parser type: {0!s}'.format(type(parser)))

    return storage_writer

  def _SetUpKnowledgeBase(self, knowledge_base_values=None):
    """Sets up a knowledge base.

    Args:
      knowledge_base_values (Optional[dict[str, str]]): knowledge base values.

    Returns:
      KnowledgeBase: knowledge base.
    """
    knowledge_base_object = knowledge_base.KnowledgeBase()
    if knowledge_base_values:
      for identifier, value in knowledge_base_values.items():
        if identifier == 'users':
          self._SetUserAccounts(knowledge_base_object, value)
        else:
          knowledge_base_object.SetValue(identifier, value)

    return knowledge_base_object

  def _SetUserAccounts(self, knowledge_base_object, users):
    """Sets the user accounts in the knowledge base.

    Args:
      knowledge_base_object (KnowledgeBase): used to store information about
          users.
      users (list[dict[str, str])): users, for example [{'name': 'me',
        'sid': 'S-1', 'uid': '1'}]
    """
    for user in users:
      identifier = user.get('sid', user.get('uid', None))
      if not identifier:
        continue

      user_account_artifact = artifacts.UserAccountArtifact(
          identifier=identifier, user_directory=user.get('path', None),
          username=user.get('name', None))

      knowledge_base_object.AddUserAccount(user_account_artifact)
