# -*- coding: utf-8 -*-
"""Analysis plugin related functions and classes for testing."""

from dfvfs.lib import definitions
from dfvfs.path import factory as path_spec_factory
from dfvfs.resolver import resolver as path_spec_resolver

from plaso.analysis import mediator
from plaso.containers import reports
from plaso.engine import knowledge_base
from plaso.engine import plaso_queue
from plaso.engine import single_process
from plaso.parsers import interface as parsers_interface
from plaso.parsers import mediator as parsers_mediator

from tests import test_lib as shared_test_lib


class TestAnalysisReportQueueConsumer(plaso_queue.ItemQueueConsumer):
  """Class that implements a test analysis report queue consumer."""

  def __init__(self, queue_object):
    """Initializes the queue consumer.

    Args:
      queue_object: the queue object (instance of Queue).
    """
    super(TestAnalysisReportQueueConsumer, self).__init__(queue_object)
    self.analysis_reports = []

  def _ConsumeItem(self, analysis_report, **unused_kwargs):
    """Consumes an item callback for ConsumeItems.

    Args:
      analysis_report: the analysis report (instance of AnalysisReport).
    """
    self.analysis_reports.append(analysis_report)

  @property
  def number_of_analysis_reports(self):
    """The number of analysis reports."""
    return len(self.analysis_reports)


class AnalysisPluginTestCase(shared_test_lib.BaseTestCase):
  """The unit test case for an analysis plugin."""

  def _GetAnalysisReportsFromQueue(self, analysis_report_queue_consumer):
    """Retrieves the analysis reports from the queue consumer.

    Args:
      analysis_report_queue_consumer: the analysis report queue consumer
                                      object (instance of
                                      TestAnalysisReportQueueConsumer).

    Returns:
      A list of analysis reports (instances of AnalysisReport).
    """
    analysis_report_queue_consumer.ConsumeItems()

    analysis_reports = []
    for analysis_report in analysis_report_queue_consumer.analysis_reports:
      self.assertIsInstance(analysis_report, reports.AnalysisReport)
      analysis_reports.append(analysis_report)

    return analysis_reports

  def _ParseFile(self, parser_object, path, knowledge_base_object):
    """Parses a file using the parser object.

    Args:
      parser_object: the parser object.
      path: the path of the file to parse.
      knowledge_base_object: the knowledge base object (instance of
                             KnowledgeBase).

    Returns:
      An event object queue object (instance of Queue).
    """
    event_queue = single_process.SingleProcessQueue()
    event_queue_producer = plaso_queue.ItemQueueProducer(event_queue)

    parse_error_queue = single_process.SingleProcessQueue()

    parser_mediator = parsers_mediator.ParserMediator(
        event_queue_producer, parse_error_queue, knowledge_base_object)
    path_spec = path_spec_factory.Factory.NewPathSpec(
        definitions.TYPE_INDICATOR_OS, location=path)
    file_entry = path_spec_resolver.Resolver.OpenFileEntry(path_spec)
    parser_mediator.SetFileEntry(file_entry)

    if isinstance(parser_object, parsers_interface.FileEntryParser):
      parser_object.Parse(parser_mediator)

    elif isinstance(parser_object, parsers_interface.FileObjectParser):
      file_object = file_entry.GetFileObject()
      try:
        parser_object.Parse(parser_mediator, file_object)
      finally:
        file_object.close()

    else:
      self.fail(
          u'Got unexpected parser type: {0:s}'.format(type(parser_object)))

    return event_queue

  def _RunAnalysisPlugin(self, analysis_plugin, knowledge_base_object):
    """Analyzes an event object queue using the plugin object.

    Args:
      analysis_plugin: the analysis plugin object (instance of AnalysisPlugin).
      knowledge_base_object: the knowledge base object (instance of
                             KnowledgeBase).

    Returns:
      An event object queue object (instance of Queue).
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
      knowledge_base_values: optional dict containing the knowledge base
                             values.

    Returns:
      An knowledge base object (instance of KnowledgeBase).
    """
    knowledge_base_object = knowledge_base.KnowledgeBase()
    if knowledge_base_values:
      for identifier, value in iter(knowledge_base_values.items()):
        knowledge_base_object.SetValue(identifier, value)

    return knowledge_base_object
