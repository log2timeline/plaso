# -*- coding: utf-8 -*-
"""Engine related functions and classes for testing."""

import os
import unittest

from plaso.engine import queue
from plaso.storage import writer as storage_writer


class EngineTestCase(unittest.TestCase):
  """The unit test case for a front-end."""

  _TEST_DATA_PATH = os.path.join(os.getcwd(), u'test_data')

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

  def _ConsumeItem(self, item, **unused_kwargs):
    """Consumes an item callback for ConsumeItems."""
    self.items.append(item)

  @property
  def number_of_items(self):
    """The number of items."""
    return len(self.items)


class TestStorageWriter(storage_writer.StorageWriter):
  """Class that implements a test storage writer object."""

  def __init__(self, event_object_queue):
    """Initializes a storage writer object.

    Args:
      event_object_queue: the event object queue (instance of Queue).
    """
    super(TestStorageWriter, self).__init__(event_object_queue)
    self.event_objects = []

  def _ConsumeItem(self, event_object, **unused_kwargs):
    """Consumes an item callback for ConsumeItems."""
    self.event_objects.append(event_object)
