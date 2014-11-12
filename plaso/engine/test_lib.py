#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2014 The Plaso Project Authors.
# Please see the AUTHORS file for details on individual authors.
#
# Licensed under the Apache License, Version 2.0 (the 'License');
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
"""Engine related functions and classes for testing."""

import os
import unittest

from plaso.engine import queue


class TestQueueConsumer(queue.ItemQueueConsumer):
  """Class that implements the test queue consumer.

     The queue consumer subscribes to updates on the queue.
  """

  def __init__(self, test_queue):
    """Initializes the queue consumer.

    Args:
      test_queue: the test queue (instance of Queue).
    """
    super(TestQueueConsumer, self).__init__(test_queue)
    self.items = []

  def _ConsumeItem(self, item):
    """Consumes an item callback for ConsumeItems."""
    self.items.append(item)

  @property
  def number_of_items(self):
    """The number of items."""
    return len(self.items)


class EngineTestCase(unittest.TestCase):
  """The unit test case for a front-end."""

  _TEST_DATA_PATH = os.path.join(os.getcwd(), 'test_data')

  # Show full diff results, part of TestCase so does not follow our naming
  # conventions.
  maxDiff = None

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
