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
  def PushItem(self, item):
    """Pushes an item onto the queue.

    Raises:
      QueueFull: when the next call to PushItem would exceed the limit of items
                 in the queue.
    """

  @abc.abstractmethod
  def PopItem(self):
    """Pops an item off the queue.

    Raises:
      QueueEmpty: when the queue is empty.
    """

  @abc.abstractmethod
  def Close(self):
    """Closes the queue."""

  @abc.abstractmethod
  def Open(self):
    """Opens the queue, ready to enqueue or dequeue items."""
