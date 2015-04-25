# -*- coding: utf-8 -*-
"""Queue management implementation for Plaso.

This file contains an implementation of a queue used by plaso for
queue management.

The queue has been abstracted in order to provide support for different
implementations of the queueing mechanism, to support multi processing and
scalability.
"""

import abc

from plaso.lib import errors


class QueueEndOfInput(object):
  """Class that implements a queue end of input."""


class Queue(object):
  """Class that implements the queue interface."""

  @abc.abstractmethod
  def IsEmpty(self):
    """Determines if the queue is empty."""

  @abc.abstractmethod
  def PushItem(self, item):
    """Pushes an item onto the queue."""

  @abc.abstractmethod
  def PopItem(self):
    """Pops an item off the queue or None on timeout."""

  def SignalEndOfInput(self):
    """Signals the queue no input remains."""
    self.PushItem(QueueEndOfInput())


class QueueConsumer(object):
  """Class that implements the queue consumer interface.

     The consumer subscribes to updates on the queue.
  """

  def __init__(self, queue_object):
    """Initializes the queue consumer.

    Args:
      queue_object: the queue object (instance of Queue).
    """
    super(QueueConsumer, self).__init__()
    self._abort = False
    self._queue = queue_object

  def SignalAbort(self):
    """Signals the consumer to abort."""
    self._abort = True


class QueueProducer(object):
  """Class that implements the queue producer interface.

     The producer generates updates on the queue.
  """

  def __init__(self, queue_object):
    """Initializes the queue producer.

    Args:
      queue_object: the queue object (instance of Queue).
    """
    super(QueueProducer, self).__init__()
    self._abort = False
    self._queue = queue_object

  def SignalAbort(self):
    """Signals the producer to abort."""
    self._abort = True

  def SignalEndOfInput(self):
    """Signals the queue no input remains."""
    self._queue.SignalEndOfInput()


class EventObjectQueueConsumer(QueueConsumer):
  """Class that implements the event object queue consumer.

     The consumer subscribes to updates on the queue.
  """

  @abc.abstractmethod
  def _ConsumeEventObject(self, event_object, **kwargs):
    """Consumes an event object callback for ConsumeEventObjects."""

  def ConsumeEventObjects(self, **kwargs):
    """Consumes the event object that are pushed on the queue.

       This function will issue a callback to _ConsumeEventObject for every
       event object (instance of EventObject) consumed from the queue.

    Args:
      kwargs: keyword arguments to pass to the _ConsumeEventObject callback.
    """
    while not self._abort:
      try:
        item = self._queue.PopItem()
      except errors.QueueEmpty:
        break

      if isinstance(item, QueueEndOfInput):
        # Check if this is the last item in the queue.
        try:
          next_item = self._queue.PopItem()
        except errors.QueueEmpty:
          # Push the item back onto the queue to make sure all
          # queue consumers are stopped.
          self._queue.PushItem(item)

          break

        self._queue.PushItem(item)
        item = next_item

      # Ignore empty items this can happen when the call to PopItem times out.
      if item:
        self._ConsumeEventObject(item, **kwargs)

    self._abort = False


class ItemQueueConsumer(QueueConsumer):
  """Class that implements an item queue consumer.

     The consumer subscribes to updates on the queue.
  """

  @abc.abstractmethod
  def _ConsumeItem(self, item):
    """Consumes an item callback for ConsumeItems.

    Args:
      item: the item object.
    """

  def ConsumeItems(self):
    """Consumes the items that are pushed on the queue."""
    while not self._abort:
      try:
        item = self._queue.PopItem()
      except errors.QueueEmpty:
        break

      if isinstance(item, QueueEndOfInput):
        # Check if this is the last item in the queue.
        try:
          next_item = self._queue.PopItem()
        except errors.QueueEmpty:
          # Push the item back onto the queue to make sure all
          # queue consumers are stopped.
          self._queue.PushItem(item)

          break

        self._queue.PushItem(item)
        item = next_item

      # Ignore empty items this can happen when the call to PopItem times out.
      if item:
        self._ConsumeItem(item)

    self._abort = False


class ItemQueueProducer(QueueProducer):
  """Class that implements an item queue producer.

     The producer generates updates on the queue.
  """

  def _FlushQueue(self):
    """Flushes the queue callback for the QueueFull exception."""
    return

  def ProduceItem(self, item):
    """Produces an item onto the queue.

    Args:
      item: the item object.
    """
    try:
      self._queue.PushItem(item)
    except errors.QueueFull:
      self._FlushQueue()

  def ProduceItems(self, items):
    """Produces items onto the queue.

    Args:
      items: a list or generator of item objects.
    """
    for item in items:
      self.ProduceItem(item)
