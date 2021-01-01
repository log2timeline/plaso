# -*- coding: utf-8 -*-
"""Queue management implementation for Plaso.

This file contains an implementation of a queue used by plaso for
queue management.

The queue has been abstracted in order to provide support for different
implementations of the queueing mechanism, to support multi processing and
scalability.
"""

import abc


class QueueAbort(object):
  """Class that implements a queue abort."""


class Queue(object):
  """Class that implements the queue interface."""

  @abc.abstractmethod
  def IsEmpty(self):
    """Determines if the queue is empty."""

  @abc.abstractmethod
  def PushItem(self, item, block=True):
    """Pushes an item onto the queue.

    Args:
      item (object): item to add.
      block (bool): whether to block if the queue is full.

    Raises:
      QueueFull: if the queue is full, and the item could not be added.
    """

  @abc.abstractmethod
  def PopItem(self):
    """Pops an item off the queue.

    Raises:
      QueueEmpty: when the queue is empty.
    """

  @abc.abstractmethod
  def Close(self, abort=False):
    """Closes the queue.

    Args:
      abort (Optional[bool]): whether the Close is the result of an abort
          condition. If True, queue contents may be lost.
    """

  @abc.abstractmethod
  def Open(self):
    """Opens the queue, ready to enqueue or dequeue items."""
