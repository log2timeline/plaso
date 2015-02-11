#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2015 The Plaso Project Authors.
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
"""Tests the worker."""

import unittest

from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory
from dfvfs.resolver import context

from plaso.artifacts import knowledge_base
from plaso.engine import single_process
from plaso.engine import test_lib
from plaso.engine import worker
from plaso.parsers import mediator as parsers_mediator


class BaseEventExtractionWorkerTest(test_lib.EngineTestCase):
  """Tests for the worker object."""

  def testExtractionWorker(self):
    """Tests the extraction worker functionality."""
    collection_queue = single_process.SingleProcessQueue()
    storage_queue = single_process.SingleProcessQueue()
    parse_error_queue = single_process.SingleProcessQueue()

    event_queue_producer = single_process.SingleProcessItemQueueProducer(
        storage_queue)
    parse_error_queue_producer = single_process.SingleProcessItemQueueProducer(
        parse_error_queue)

    knowledge_base_object = knowledge_base.KnowledgeBase()

    parser_mediator = parsers_mediator.ParserMediator(
        event_queue_producer, parse_error_queue_producer,
        knowledge_base_object)

    resolver_context = context.Context()

    extraction_worker = worker.BaseEventExtractionWorker(
        0, collection_queue, event_queue_producer, parse_error_queue_producer,
        parser_mediator, resolver_context=resolver_context)

    self.assertNotEquals(extraction_worker, None)

    extraction_worker.InitializeParserObjects()

    # Process a file.
    source_path = self._GetTestFilePath([u'syslog'])
    path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=source_path)

    collection_queue.PushItem(path_spec)
    extraction_worker.Run()

    test_queue_consumer = test_lib.TestQueueConsumer(storage_queue)
    test_queue_consumer.ConsumeItems()

    self.assertEquals(test_queue_consumer.number_of_items, 16)

    # Process a compressed file.
    source_path = self._GetTestFilePath([u'syslog.gz'])
    path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=source_path)

    collection_queue.PushItem(path_spec)
    extraction_worker.Run()

    test_queue_consumer = test_lib.TestQueueConsumer(storage_queue)
    test_queue_consumer.ConsumeItems()

    self.assertEquals(test_queue_consumer.number_of_items, 16)

    source_path = self._GetTestFilePath([u'syslog.bz2'])
    path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=source_path)

    collection_queue.PushItem(path_spec)
    extraction_worker.Run()

    test_queue_consumer = test_lib.TestQueueConsumer(storage_queue)
    test_queue_consumer.ConsumeItems()

    self.assertEquals(test_queue_consumer.number_of_items, 15)

    # Process a file in an archive.
    source_path = self._GetTestFilePath([u'syslog.tar'])
    path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=source_path)
    path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TAR, location=u'/syslog',
        parent=path_spec)

    collection_queue.PushItem(path_spec)
    extraction_worker.Run()

    test_queue_consumer = test_lib.TestQueueConsumer(storage_queue)
    test_queue_consumer.ConsumeItems()

    self.assertEquals(test_queue_consumer.number_of_items, 13)

    # Process an archive file without "process archive files" mode.
    extraction_worker.SetProcessArchiveFiles(False)

    source_path = self._GetTestFilePath([u'syslog.tar'])
    path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=source_path)

    collection_queue.PushItem(path_spec)
    extraction_worker.Run()

    test_queue_consumer = test_lib.TestQueueConsumer(storage_queue)
    test_queue_consumer.ConsumeItems()

    self.assertEquals(test_queue_consumer.number_of_items, 3)

    # Process an archive file with "process archive files" mode.
    extraction_worker.SetProcessArchiveFiles(True)

    source_path = self._GetTestFilePath([u'syslog.tar'])
    path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=source_path)

    collection_queue.PushItem(path_spec)
    extraction_worker.Run()

    test_queue_consumer = test_lib.TestQueueConsumer(storage_queue)
    test_queue_consumer.ConsumeItems()

    self.assertEquals(test_queue_consumer.number_of_items, 16)

    # Process a file in a compressed archive.
    source_path = self._GetTestFilePath([u'syslog.tgz'])
    path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=source_path)
    path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_GZIP, parent=path_spec)
    path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TAR, location=u'/syslog',
        parent=path_spec)

    collection_queue.PushItem(path_spec)
    extraction_worker.Run()

    test_queue_consumer = test_lib.TestQueueConsumer(storage_queue)
    test_queue_consumer.ConsumeItems()

    self.assertEquals(test_queue_consumer.number_of_items, 13)

    # Process an archive file with "process archive files" mode.
    extraction_worker.SetProcessArchiveFiles(True)

    source_path = self._GetTestFilePath([u'syslog.tgz'])
    path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=source_path)

    collection_queue.PushItem(path_spec)
    extraction_worker.Run()

    test_queue_consumer = test_lib.TestQueueConsumer(storage_queue)
    test_queue_consumer.ConsumeItems()

    self.assertEquals(test_queue_consumer.number_of_items, 17)


if __name__ == '__main__':
  unittest.main()
