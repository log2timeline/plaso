#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import shutil
import tempfile
import unittest

from plaso.engine import queue
from plaso.frontend import plasm
from plaso.frontend import test_lib
from plaso.lib import event
from plaso.lib import pfilter
from plaso.lib import storage
from plaso.multi_processing import multi_process


class TestEvent(event.EventObject):
  DATA_TYPE = 'test:plasm:1'

  def __init__(self, timestamp, filename='/dev/null', stuff='bar'):
    super(TestEvent, self).__init__()
    self.timestamp = timestamp
    self.filename = filename
    self.timestamp_desc = 'Last Written'
    self.parser = 'TestEvent'
    self.display_name = 'fake:{}'.format(filename)
    self.stuff = stuff


class PlasmTest(test_lib.FrontendTestCase):
  """Tests for the plasm front-end."""

  def setUp(self):
    """Sets up the objects used throughout the test."""
    self._temp_directory = tempfile.mkdtemp()
    self._storage_filename = os.path.join(self._temp_directory, 'plaso.db')
    self._tag_input_filename = os.path.join(self._temp_directory, 'input1.tag')

    tag_input_file = open(self._tag_input_filename, 'wb')
    tag_input_file.write('\n'.join([
        'Test Tag',
        '  filename contains \'/tmp/whoaaaa\'',
        '  parser is \'TestEvent\' and stuff is \'dude\'']))
    tag_input_file.close()

    pfilter.TimeRangeCache.ResetTimeConstraints()

    # TODO: add upper queue limit.
    # We need to specify a timeout here to prevent the multi process queue
    # blocking if the queue is empty.
    test_queue = multi_process.MultiProcessingQueue(timeout=0.1)
    test_queue_producer = queue.ItemQueueProducer(test_queue)
    test_queue_producer.ProduceItems([
        TestEvent(0),
        TestEvent(1000),
        TestEvent(2000000, '/tmp/whoaaaaa'),
        TestEvent(2500000, '/tmp/whoaaaaa'),
        TestEvent(5000000, '/tmp/whoaaaaa', 'dude')])

    storage_writer = storage.FileStorageWriter(
        test_queue, self._storage_filename)
    storage_writer.WriteEventObjects()

    self._storage_file = storage.StorageFile(self._storage_filename)
    self._storage_file.SetStoreLimit()

  def tearDown(self):
    """Cleans up the objects used throughout the test."""
    shutil.rmtree(self._temp_directory, True)

  def testTagParsing(self):
    """Test if plasm can parse Tagging Input files."""
    tags = plasm.ParseTaggingFile(self._tag_input_filename)
    self.assertEqual(len(tags), 1)
    self.assertTrue('Test Tag' in tags)
    self.assertEqual(len(tags['Test Tag']), 2)

  def testInvalidTagParsing(self):
    """Test what happens when Tagging Input files contain invalid conditions."""
    tag_input_filename = os.path.join(self._temp_directory, 'input2.tag')

    tag_input_file = open(tag_input_filename, 'wb')
    tag_input_file.write('\n'.join([
        'Invalid Tag', '  my hovercraft is full of eels']))
    tag_input_file.close()

    tags = plasm.ParseTaggingFile(tag_input_filename)
    self.assertEqual(len(tags), 1)
    self.assertTrue('Invalid Tag' in tags)
    self.assertEqual(len(tags['Invalid Tag']), 0)

  def testMixedValidityTagParsing(self):
    """Tagging Input file contains a mix of valid and invalid conditions."""
    tag_input_filename = os.path.join(self._temp_directory, 'input3.tag')

    tag_input_file = open(tag_input_filename, 'wb')
    tag_input_file.write('\n'.join([
        'Semivalid Tag', '  filename contains \'/tmp/whoaaaa\'',
        '  Yandelavasa grldenwi stravenka']))
    tag_input_file.close()

    tags = plasm.ParseTaggingFile(tag_input_filename)
    self.assertEqual(len(tags), 1)
    self.assertTrue('Semivalid Tag' in tags)
    self.assertEqual(len(tags['Semivalid Tag']), 1)

  def testIteratingOverPlasoStore(self):
    """Tests the plaso storage iterator"""
    counter = 0
    for _ in plasm.EventObjectGenerator(self._storage_file, quiet=True):
      counter += 1
    self.assertEqual(counter, 5)

    self._storage_file.Close()

    pfilter.TimeRangeCache.ResetTimeConstraints()
    self._storage_file = storage.StorageFile(self._storage_filename)
    self._storage_file.SetStoreLimit()

    counter = 0
    for _ in plasm.EventObjectGenerator(self._storage_file, quiet=False):
      counter += 1
    self.assertEqual(counter, 5)

  def testTaggingEngine(self):
    """Tests the Tagging engine's functionality."""
    self.assertFalse(self._storage_file.HasTagging())
    tagging_engine = plasm.TaggingEngine(
        self._storage_filename, self._tag_input_filename, quiet=True)
    tagging_engine.Run()
    test = storage.StorageFile(self._storage_filename)
    self.assertTrue(test.HasTagging())
    tagging = test.GetTagging()
    count = 0
    for tag_event in tagging:
      count += 1
      self.assertEqual(tag_event.tags, ['Test Tag'])
    self.assertEqual(count, 3)

  def testGroupingEngineUntagged(self):
    """Grouping engine should do nothing if dealing with untagged storage."""
    storage_file = storage.StorageFile(self._storage_filename, read_only=False)
    grouping_engine = plasm.GroupingEngine()
    grouping_engine.Run(storage_file, quiet=True)
    storage_file.Close()

    storage_file = storage.StorageFile(self._storage_filename, read_only=True)

    self.assertFalse(storage_file.HasGrouping())

    storage_file.Close()

  def testGroupingEngine(self):
    """Tests the Grouping engine's functionality."""
    pfilter.TimeRangeCache.ResetTimeConstraints()
    tagging_engine = plasm.TaggingEngine(
        self._storage_filename, self._tag_input_filename, quiet=True)
    tagging_engine.Run()

    storage_file = storage.StorageFile(self._storage_filename, read_only=False)
    grouping_engine = plasm.GroupingEngine()
    grouping_engine.Run(storage_file, quiet=True)
    storage_file.Close()

    storage_file = storage.StorageFile(self._storage_filename, read_only=True)

    storage_file.SetStoreLimit()
    self.assertTrue(storage_file.HasGrouping())
    groups = storage_file.GetGrouping()
    count = 0
    for group_event in groups:
      count += 1
      self.assertEqual(group_event.category, 'Test Tag')
    self.assertEqual(count, 2)

    storage_file.Close()


if __name__ == '__main__':
  unittest.main()
