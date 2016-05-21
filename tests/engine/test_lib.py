# -*- coding: utf-8 -*-
"""Engine related functions and classes for testing."""

import os
import unittest

from plaso.engine import plaso_queue
from plaso.storage import interface as storage_interface


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


class TestQueueConsumer(plaso_queue.ItemQueueConsumer):
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


class TestStorageWriter(storage_interface.StorageWriter):
  """Class that implements a test storage writer object.

  Attributes:
    event_objects: a list of event objects (instances of EventObject).
    event_sources: a list of event sources (instances of EventSource).
  """

  def __init__(self):
    """Initializes a storage writer object."""
    super(TestStorageWriter, self).__init__()
    self.event_objects = []
    self.event_sources = []

  def AddEvent(self, event_object):
    """Adds an event object to the storage.

    Args:
      event_object: an event object (instance of EventObject).
    """
    self.event_objects.append(event_object)

  def AddEventSource(self, event_source):
    """Adds an event source to the storage.

    Args:
      event_source: an event source object (instance of EventSource).
    """
    self.event_sources.append(event_source)

  def Close(self):
    """Closes the storage writer."""
    return

  # TODO: remove during phased processing refactor.
  def ForceClose(self):
    """Forces the storage writer to close."""
    return

  # TODO: remove during phased processing refactor.
  def ForceFlush(self):
    """Forces the storage writer to flush."""
    return

  def GetEventSources(self):
    """Retrieves the event sources.

    Yields:
      An event source object (instance of EventSource).
    """
    for event_source in self.event_sources:
      yield event_source

  def Open(self):
    """Opens the storage writer."""
    return

  def WriteSessionCompletion(self):
    """Writes session completion information."""
    return

  def WriteSessionStart(self, session_start):
    """Writes session start information.

    Args:
      session_start: the session start information (instance of SessionStart).
    """
    return
