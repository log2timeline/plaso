# -*- coding: utf-8 -*-
"""Analysis plugin related functions and classes for testing."""

from dfvfs.lib import definitions
from dfvfs.path import factory as path_spec_factory
from dfvfs.resolver import resolver as path_spec_resolver

from plaso.analysis import mediator
from plaso.containers import artifacts
from plaso.containers import reports
from plaso.containers import sessions
from plaso.engine import knowledge_base
from plaso.engine import plaso_queue
from plaso.engine import single_process
from plaso.parsers import interface as parsers_interface
from plaso.parsers import mediator as parsers_mediator
from plaso.storage import fake_storage

from tests import test_lib as shared_test_lib


class TestAnalysisReportQueueConsumer(plaso_queue.ItemQueueConsumer):
  """Class that implements a test analysis report queue consumer."""

  def __init__(self, queue_object):
    """Initializes the queue consumer.

    Args:
      queue_object (Queue): queue object.
    """
    super(TestAnalysisReportQueueConsumer, self).__init__(queue_object)
    self.analysis_reports = []

  def _ConsumeItem(self, analysis_report, **unused_kwargs):
    """Consumes an item callback for ConsumeItems.

    Args:
      analysis_report (AnalysisReport): analysis report.
    """
    self.analysis_reports.append(analysis_report)

  @property
  def number_of_analysis_reports(self):
    """The number of analysis reports."""
    return len(self.analysis_reports)


class TestEventObjectProducer(plaso_queue.ItemQueueProducer):
  """Class that implements an event object producer."""

  def __init__(self, queue_object, storage_writer):
    """Initializes the queue producer object.

    Args:
      queue_object (Queue): queue.
      storage_writer (FakeStorageWriter): storage writer.
    """
    super(TestEventObjectProducer, self).__init__(queue_object)
    self._storage_writer = storage_writer

  def Run(self):
    """Produces event object onto the queue."""
    for event_object in self._storage_writer.events:
      self.ProduceItem(event_object)


class AnalysisPluginTestCase(shared_test_lib.BaseTestCase):
  """The unit test case for an analysis plugin."""

  def _GetAnalysisReportsFromQueue(self, analysis_report_queue_consumer):
    """Retrieves the analysis reports from the queue consumer.

    Args:
      analysis_report_queue_consumer (TestAnalysisReportQueueConsumer):
          analysis report queue consumer.

    Returns:
      list[AnalysisReport]: analysis reports.
    """
    analysis_report_queue_consumer.ConsumeItems()

    analysis_reports = []
    for analysis_report in analysis_report_queue_consumer.analysis_reports:
      self.assertIsInstance(analysis_report, reports.AnalysisReport)
      analysis_reports.append(analysis_report)

    return analysis_reports

  def _ParseFile(self, path_segments, parser, knowledge_base_object):
    """Parses a file using the parser object.

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

    parser_mediator = parsers_mediator.ParserMediator(
        storage_writer, knowledge_base_object)

    path = self._GetTestFilePath(path_segments)
    path_spec = path_spec_factory.Factory.NewPathSpec(
        definitions.TYPE_INDICATOR_OS, location=path)

    file_entry = path_spec_resolver.Resolver.OpenFileEntry(path_spec)
    parser_mediator.SetFileEntry(file_entry)

    if isinstance(parser, parsers_interface.FileEntryParser):
      parser.Parse(parser_mediator)

    elif isinstance(parser, parsers_interface.FileObjectParser):
      file_object = file_entry.GetFileObject()
      try:
        parser.Parse(parser_mediator, file_object)
      finally:
        file_object.close()

    else:
      self.fail(
          u'Got unexpected parser type: {0:s}'.format(type(parser)))

    return storage_writer

  def _RunAnalysisPlugin(self, analysis_plugin, knowledge_base_object):
    """Analyzes an event object queue using the plugin object.

    Args:
      analysis_plugin (AnalysisPlugin): analysis plugin.
      knowledge_base_object (KnowledgeBase): knowledge base.

    Returns:
      TestAnalysisReportQueueConsumer: analysis report queue consumer.
    """
    analysis_report_queue = single_process.SingleProcessQueue()
    analysis_report_queue_consumer = TestAnalysisReportQueueConsumer(
        analysis_report_queue)
    analysis_report_queue_producer = plaso_queue.ItemQueueProducer(
        analysis_report_queue)

    analysis_mediator = mediator.AnalysisMediator(
        analysis_report_queue_producer, knowledge_base_object)

    analysis_plugin.RunPlugin(analysis_mediator)

    return analysis_report_queue_consumer

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

      # TODO: refactor the use of store number.
      user_account_artifact.store_number = 0
      knowledge_base_object.SetUserAccount(user_account_artifact)
