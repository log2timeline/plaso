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


class QueueAbort(object):
  """Class that implements a queue abort."""


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
    """Pops an item off the queue or None on timeout.

    Raises:
      QueueEmpty: when the queue is empty.
    """

  @abc.abstractmethod
  def Close(self):
    """Closes the queue."""


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


class ItemQueueConsumer(QueueConsumer):
  """Class that implements an item queue consumer.

     The consumer subscribes to updates on the queue.
  """

  def __init__(self, queue_object):
    """Initializes the item queue consumer.

    Args:
      queue_object: the queue object (instance of Queue).
    """
    super(ItemQueueConsumer, self).__init__(queue_object)
    self._number_of_consumed_items = 0

  @property
  def number_of_consumed_items(self):
    """The number of consumed items."""
    return self._number_of_consumed_items

  @abc.abstractmethod
  def _ConsumeItem(self, item, **kwargs):
    """Consumes an item callback for ConsumeItems.

    Args:
      item: the item object.
      kwargs: keyword arguments to pass to the _ConsumeItem callback.
    """

  def ConsumeItems(self, **kwargs):
    """Consumes the items that are pushed on the queue.

    Args:
      kwargs: keyword arguments to pass to the _ConsumeItem callback.
    """
    while not self._abort:
      try:
        item = self._queue.PopItem()
      except (errors.QueueClose, errors.QueueEmpty):
        break

      if isinstance(item, QueueAbort):
        break

      self._number_of_consumed_items += 1
      self._ConsumeItem(item, **kwargs)


class ItemQueueProducer(QueueProducer):
  """Class that implements an item queue producer.

     The producer generates updates on the queue.
  """

  def __init__(self, queue_object):
    """Initializes the item queue producer.

    Args:
      queue_object: the queue object (instance of Queue).
    """
    super(ItemQueueProducer, self).__init__(queue_object)
    self._number_of_produced_items = 0

  @property
  def number_of_produced_items(self):
    """The number of produced items."""
    return self._number_of_produced_items

  def _FlushQueue(self):
    """Flushes the queue callback for the QueueFull exception."""
    return

  def ProduceItem(self, item):
    """Produces an item onto the queue.

    Args:
      item: the item object.
    """
    try:
      self._number_of_produced_items += 1
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

  def Close(self):
    """Closes the queue backing this producer.

    The closing of the queue indicates the produce will not produce any more
    items."""
    self._queue.Close()
