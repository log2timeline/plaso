#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2014 The Plaso Project Authors.
# Please see the AUTHORS file for details on individual authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Analysis plugin related functions and classes for testing."""

import os
import unittest

from dfvfs.lib import definitions
from dfvfs.path import factory as path_spec_factory
from dfvfs.resolver import resolver as path_spec_resolver

from plaso.analysis import context
from plaso.artifacts import knowledge_base
from plaso.lib import event
from plaso.lib import queue
from plaso.parsers import context as parsers_context


class TestAnalysisReportQueueConsumer(queue.AnalysisReportQueueConsumer):
  """Class that implements a test analysis report queue consumer."""

  def __init__(self, queue_object):
    """Initializes the queue consumer.

    Args:
      queue_object: the queue object (instance of Queue).
    """
    super(TestAnalysisReportQueueConsumer, self).__init__(queue_object)
    self.analysis_reports = []

  def _ConsumeAnalysisReport(self, analysis_report):
    """Consumes an analysis report callback for ConsumeAnalysisReports."""
    self.analysis_reports.append(analysis_report)

  @property
  def number_of_analysis_reports(self):
    """The number of analysis reports."""
    return len(self.analysis_reports)


class AnalysisPluginTestCase(unittest.TestCase):
  """The unit test case for an analysis plugin."""

  _TEST_DATA_PATH = os.path.join(os.getcwd(), 'test_data')

  # Show full diff results, part of TestCase so does not follow our naming
  # conventions.
  maxDiff = None

  def _GetAnalysisReportsFromQueue(self, analysis_report_queue_consumer):
    """Retrieves the analysis reports from the queue consumer.

    Args:
      analysis_report_queue_consumer: the analysis report queue consumer
                                      object (instance of
                                      TestAnalysisReportQueueConsumer).

    Returns:
      A list of analysis reports (instances of AnalysisReport).
    """
    analysis_report_queue_consumer.ConsumeAnalysisReports()

    analysis_reports = []
    for analysis_report in analysis_report_queue_consumer.analysis_reports:
      self.assertIsInstance(analysis_report, event.AnalysisReport)
      analysis_reports.append(analysis_report)

    return analysis_reports

  def _GetTestFilePath(self, path_segments):
    """Retrieves the path of a test file relative to the test data directory.

    Args:
      path_segments: the path segments inside the test data directory.

    Returns:
      A path of the test file.
    """
    # Note that we need to pass the individual path segments to os.path.join
    # and not a list.
    return os.path.join(self._TEST_DATA_PATH, *path_segments)

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
    event_queue = queue.SingleThreadedQueue()
    event_queue_producer = queue.EventObjectQueueProducer(event_queue)

    parser_context = parsers_context.ParserContext(
        event_queue_producer, knowledge_base_object)
    path_spec = path_spec_factory.Factory.NewPathSpec(
        definitions.TYPE_INDICATOR_OS, location=path)
    file_entry = path_spec_resolver.Resolver.OpenFileEntry(path_spec)

    parser_object.Parse(parser_context, file_entry)
    event_queue.SignalEndOfInput()

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
    analysis_report_queue = queue.SingleThreadedQueue()
    analysis_report_queue_consumer = TestAnalysisReportQueueConsumer(
        analysis_report_queue)
    analysis_report_queue_producer = queue.AnalysisReportQueueProducer(
        analysis_report_queue)

    analysis_context = context.AnalysisContext(
        analysis_report_queue_producer, knowledge_base_object)

    analysis_plugin.RunPlugin(analysis_context)
    analysis_report_queue.SignalEndOfInput()

    return analysis_report_queue_consumer

  def _SetUpKnowledgeBase(self, knowledge_base_values=None):
    """Sets up a knowledge base.

    Args:
      knowledge_base_values: optional dict containing the knowledge base
                             values. The default is None.

    Returns:
      An knowledge base object (instance of KnowledgeBase).
    """
    knowledge_base_object = knowledge_base.KnowledgeBase()
    if knowledge_base_values:
      for identifier, value in knowledge_base_values.iteritems():
        knowledge_base_object.SetValue(identifier, value)

    return knowledge_base_object
