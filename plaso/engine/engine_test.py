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
"""Tests for the engine."""

import os
import unittest

from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.helpers import file_system_searcher
from dfvfs.path import factory as path_spec_factory
from dfvfs.resolver import context

from plaso.engine import collector
from plaso.engine import engine
from plaso.engine import worker
from plaso.lib import queue


class EngineTest(unittest.TestCase):
  """Tests for the engine object."""

  _TEST_DATA_PATH = os.path.join(os.getcwd(), u'test_data')

  def testEngine(self):
    """Test the engine functionality."""
    collection_queue = queue.SingleThreadedQueue()
    storage_queue = queue.SingleThreadedQueue()
    parse_error_queue = queue.SingleThreadedQueue()

    resolver_context = context.Context()
    test_engine = engine.Engine(
        collection_queue, storage_queue, parse_error_queue)

    self.assertNotEquals(test_engine, None)

    source_path = os.path.join(self._TEST_DATA_PATH, u'image.dd')
    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=source_path)
    source_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK, location=u'/',
        parent=os_path_spec)

    test_engine.SetSource(source_path_spec, resolver_context=resolver_context)

    self.assertFalse(test_engine.SourceIsDirectory())
    self.assertFalse(test_engine.SourceIsFile())
    self.assertTrue(test_engine.SourceIsStorageMediaImage())

    test_searcher = test_engine.GetSourceFileSystemSearcher(
        resolver_context=resolver_context)
    self.assertNotEquals(test_searcher, None)
    self.assertIsInstance(
        test_searcher, file_system_searcher.FileSystemSearcher)

    test_engine.PreprocessSource('Windows')

    test_collector = test_engine.CreateCollector(
        False, vss_stores=None, filter_find_specs=None,
        resolver_context=resolver_context)
    self.assertNotEquals(test_collector, None)
    self.assertIsInstance(test_collector, collector.Collector)

    test_extraction_worker = test_engine.CreateExtractionWorker(0, None)
    self.assertNotEquals(test_extraction_worker, None)
    self.assertIsInstance(test_extraction_worker, worker.EventExtractionWorker)


if __name__ == '__main__':
  unittest.main()
