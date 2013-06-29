#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2013 The Plaso Project Authors.
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
"""Tests for plaso.frontend.plasm."""

import tempfile

import unittest

from plaso.frontend import plasm
from plaso.lib import event
from plaso.lib import pfilter
from plaso.lib import storage

__pychecker__ = 'no-funcdoc'


class TestEvent(event.EventObject):
  DATA_TYPE = 'test:plasm:1'

  def __init__(self, timestamp, filename='/dev/null'):
    super(TestEvent, self).__init__()
    self.timestamp = timestamp
    self.filename = filename
    self.timestamp_desc = 'Last Written'
    self.parser = 'TestEvent'
    self.display_name = 'fake:{}'.format(filename)


class TestArgs(object):
  DATA_TYPE = 'test:plasm:2'

  def __init__(self, storagefile, tag_input):
    super(TestArgs, self).__init__()
    self.storagefile = storagefile
    self.tag_input = tag_input
    self.quiet = True


class PlasmTest(unittest.TestCase):

  def setUp(self):
    """Setup creates a Plaso Store to play with, as well as a basic filter."""
    self.storage_file = tempfile.NamedTemporaryFile()
    self.storage_name = self.storage_file.name
    self.tag_input_file = tempfile.NamedTemporaryFile()
    self.tag_input_name = self.tag_input_file.name

    self.tag_input_file.write('Test Tag\n')
    self.tag_input_file.write('  filename contains \'/tmp/whoaaaa\'\n')
    self.tag_input_file.flush()

    dumper = storage.SimpleStorageDumper(self.storage_file)
    dumper.AddEvent(TestEvent(0).ToProtoString())
    dumper.AddEvent(TestEvent(1000).ToProtoString())
    dumper.AddEvent(TestEvent(2000000, '/tmp/whoaaaaa').ToProtoString())
    dumper.AddEvent(TestEvent(2500000, '/tmp/whoaaaaa').ToProtoString())
    dumper.AddEvent(TestEvent(5000000, '/tmp/whoaaaaa').ToProtoString())
    dumper.Close()
    dumper.Run()

    self.my_args = TestArgs(self.storage_name, self.tag_input_name)
    self.storage = storage.PlasoStorage(self.storage_file)
    pfilter.TimeRangeCache.ResetTimeConstraints()
    self.storage.SetStoreLimit()

  def tearDown(self):
    self.storage_file.close()
    self.tag_input_file.close()

  def testTagParsing(self):
    """Test if plasm can parse Tagging Input files."""
    tags = plasm.ParseTaggingFile(self.tag_input_name)
    self.assertEquals(len(tags), 1)
    self.assertTrue('Test Tag' in tags)
    self.assertEquals(len(tags['Test Tag']), 1)

  def testInvalidTagParsing(self):
    """Test what happens when Tagging Input files contain invalid conditions."""
    with tempfile.NamedTemporaryFile() as tag_input:
      tag_input.write('Invalid Tag\n')
      tag_input.write('  my hovercraft is full of eels\n')
      tag_input.flush()

      tags = plasm.ParseTaggingFile(tag_input.name)
      self.assertEquals(len(tags), 1)
      self.assertTrue('Invalid Tag' in tags)
      self.assertEquals(len(tags['Invalid Tag']), 0)

  def testMixedValidityTagParsing(self):
    """Tagging Input file contains a mix of valid and invalid conditions."""
    with tempfile.NamedTemporaryFile() as tag_input:
      tag_input.write('Semivalid Tag\n')
      tag_input.write('  filename contains \'/tmp/whoaaaa\'\n')
      tag_input.write('  Yandelavasa grldenwi stravenka\n')
      tag_input.flush()

      tags = plasm.ParseTaggingFile(tag_input.name)
      self.assertEquals(len(tags), 1)
      self.assertTrue('Semivalid Tag' in tags)
      self.assertEquals(len(tags['Semivalid Tag']), 1)

  def testIteratingOverPlasoStore(self):
    """Tests the plaso storage iterator"""
    counter = 0
    for event_object in plasm.EventObjectGenerator(self.storage, quiet=True):
      counter += 1
    self.assertEquals(counter, 5)
    self.storage = storage.PlasoStorage(self.storage_file)
    pfilter.TimeRangeCache.ResetTimeConstraints()
    self.storage.SetStoreLimit()
    counter = 0
    for event_object in plasm.EventObjectGenerator(self.storage, quiet=False):
      counter += 1
    self.assertEquals(counter, 5)

  def testTaggingEngine(self):
    """Tests the Tagging engine's functionality."""
    self.assertFalse(self.storage.HasTagging())
    plasm.TaggingEngine(self.my_args)
    test = storage.PlasoStorage(self.storage_name)
    self.assertTrue(test.HasTagging())
    tagging = test.GetTagging()
    count = 0
    for tag_event in tagging:
      count += 1
      self.assertEquals(tag_event.tags, ['Test Tag'])
    self.assertEquals(count, 3)

  def testGroupingEngineUntagged(self):
    """Grouping engine should do nothing if dealing with untagged storage."""
    plasm.GroupingEngine(self.my_args)
    self.assertFalse(self.storage.HasGrouping())

  def testGroupingEngine(self):
    """Tests the Grouping engine's functionality."""
    plasm.TaggingEngine(self.my_args)
    plasm.GroupingEngine(self.my_args)
    test = storage.PlasoStorage(self.storage_name)
    pfilter.TimeRangeCache.ResetTimeConstraints()
    test.SetStoreLimit()
    self.assertTrue(test.HasGrouping())
    groups = test.GetGrouping()
    count = 0
    for group_event in groups:
      count += 1
      self.assertEquals(group_event.category, 'Test Tag')
    self.assertEquals(count, 2)

if __name__ == '__main__':
  unittest.main()
