# -*- coding: utf-8 -*-
"""Analysis plugin related functions and classes for testing."""

from plaso.analysis import mediator as analysis_mediator
from plaso.containers import artifacts
from plaso.containers import events
from plaso.containers import sessions
from plaso.engine import knowledge_base
from plaso.parsers import interface as parsers_interface
from plaso.parsers import mediator as parsers_mediator
from plaso.storage import fake_storage

from tests import test_lib as shared_test_lib


class AnalysisPluginTestCase(shared_test_lib.BaseTestCase):
  """The unit test case for an analysis plugin."""

  def _AnalyzeEvents(
      self, event_objects, plugin, knowledge_base_values=None):
    """Analyzes events using the analysis plugin.

    Args:
      event_objects (list[EventObject]]): events to analyze.
      plugin (AnalysisPlugin): plugin.
      knowledge_base_values (Optional[dict[str,str]]): knowledge base values.

    Returns:
      FakeStorageWriter: storage writer.
    """
    knowledge_base_object = self._SetUpKnowledgeBase(
        knowledge_base_values=knowledge_base_values)

    session = sessions.Session()
    storage_writer = fake_storage.FakeStorageWriter(session)
    storage_writer.Open()

    mediator = analysis_mediator.AnalysisMediator(
        storage_writer, knowledge_base_object)

    for event in event_objects:
      plugin.ExamineEvent(mediator, event)

    analysis_report = plugin.CompileReport(mediator)
    storage_writer.AddAnalysisReport(analysis_report)

    return storage_writer

  def _CreateTestEventObject(self, event_dictionary):
    """Create a test event with a set of attributes.

    Args:
      event_dictionary (dict[str, str]): contains attributes of an event.

    Returns:
      EventObject: event with the appropriate attributes for testing.
    """
    event = events.EventObject()
    for attribute_name, attribute_value in event_dictionary.items():
      setattr(event, attribute_name, attribute_value)

    return event

  def _ParseAndAnalyzeFile(
      self, path_segments, parser, plugin, knowledge_base_values=None):
    """Parses and analyzes a file using the parser and analysis plugin.

    Args:
      path_segments (list[str]): path segments inside the test data directory.
      parser (BaseParser): parser.
      plugin (AnalysisPlugin): plugin.
      knowledge_base_values (Optional[dict[str,str]]): knowledge base values.

    Returns:
      FakeStorageWriter: storage writer.
    """
    knowledge_base_object = self._SetUpKnowledgeBase(
        knowledge_base_values=knowledge_base_values)

    storage_writer = self._ParseFile(
        path_segments, parser, knowledge_base_object)

    mediator = analysis_mediator.AnalysisMediator(
        storage_writer, knowledge_base_object)

    for event in storage_writer.events:
      plugin.ExamineEvent(mediator, event)

    analysis_report = plugin.CompileReport(mediator)
    storage_writer.AddAnalysisReport(analysis_report)

    return storage_writer

  def _ParseFile(self, path_segments, parser, knowledge_base_object):
    """Parses a file using the parser.

    Args:
      path_segments (list[str]): path segments inside the test data directory.
      parser (BaseParser): parser.
      knowledge_base_object (KnowledgeBase): knowledge base.

    Returns:
      FakeStorageWriter: storage writer.
    """
    session = sessions.Session()
    storage_writer = fake_storage.FakeStorageWriter(session)
    storage_writer.Open()

    mediator = parsers_mediator.ParserMediator(
        storage_writer, knowledge_base_object)

    file_entry = self._GetTestFileEntry(path_segments)
    mediator.SetFileEntry(file_entry)

    if isinstance(parser, parsers_interface.FileEntryParser):
      parser.Parse(mediator)

    elif isinstance(parser, parsers_interface.FileObjectParser):
      file_object = file_entry.GetFileObject()
      try:
        parser.Parse(mediator, file_object)
      finally:
        file_object.close()

    else:
      self.fail(
          u'Got unexpected parser type: {0:s}'.format(type(parser)))

    return storage_writer

  def _SetUpKnowledgeBase(self, knowledge_base_values=None):
    """Sets up a knowledge base.

    Args:
      knowledge_base_values (Optional[dict[str,str]]): knowledge base values.

    Returns:
      KnowledgeBase: knowledge base.
    """
    knowledge_base_object = knowledge_base.KnowledgeBase()
    if knowledge_base_values:
      for identifier, value in iter(knowledge_base_values.items()):
        if identifier == u'users':
          self._SetUserAccounts(knowledge_base_object, value)
        else:
          knowledge_base_object.SetValue(identifier, value)

    return knowledge_base_object

  def _SetUserAccounts(self, knowledge_base_object, users):
    """Sets the user accounts in the knowledge base.

    Args:
      knowledge_base_object (KnowledgeBase): used to store information about
          users.
      users (list[dict[str,str])): users, for example [{'name': 'me',
        'sid': 'S-1', 'uid': '1'}]
    """
    for user in users:
      identifier = user.get(u'sid', user.get(u'uid', None))
      if not identifier:
        continue

      user_account_artifact = artifacts.UserAccountArtifact(
          identifier=identifier, user_directory=user.get(u'path', None),
          username=user.get(u'name', None))

      knowledge_base_object.AddUserAccount(user_account_artifact)
