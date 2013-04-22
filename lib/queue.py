#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2012 Google Inc. All Rights Reserved.
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
"""Queue management implementation for Plaso.

This file contains an implementation of a queue used by plaso for
queue management.

The queue has been abstracted in order to provide support for different
implementations of the queueing mechanism, to support multi processing and
scalability.
"""
import abc
import collections
import logging
import multiprocessing


class QueueInterface(object):
  """Abstract class that represents the interface of a queue."""
  __abstract = True

  @abc.abstractmethod
  def PopItems(self):
    """A generator that returns items from the queue."""
    raise NotImplementedError

  @abc.abstractmethod
  def Close(self):
    """Send a stop or end of processing signal to the queue."""
    raise NotImplementedError

  @abc.abstractmethod
  def Queue(self, item):
    """Add item to the queue."""
    raise NotImplementedError

  @abc.abstractmethod
  def __len__(self):
    """Return the estimated number of entries inside the queue."""
    raise NotImplementedError


class MultiThreadedQueue(QueueInterface):
  """Multi threaded queue."""

  def __init__(self):
    """Initializes a multi threaded queue."""
    self._queue = multiprocessing.Queue()
    super(MultiThreadedQueue, self).__init__()
    self.closed = False

  def PopItems(self):
    """Yield items from the queue."""
    while 1:
      try:
        item = self._queue.get()
      except KeyboardInterrupt:
        break

      if item == 'STOP':
        self.Close()
        break
      yield item

  def Close(self):
    """Send a stop or end of processing signal to queue."""
    self.closed = True
    self._queue.put('STOP')

  def Queue(self, item):
    """Add an item to the queue."""
    if not self.closed:
      self._queue.put(item)

  def __len__(self):
    """Return the total number of events stored inside the queue."""
    size = 0
    try:
      size = self._queue.qsize()
    except NotImplementedError:
      logging.warning(
          ('Returning queue length does not work on Mac OS X because of broken'
           'sem_getvalue()'))
      raise

    return size


class SingleThreadedQueue(QueueInterface):
  """Single threaded queue."""

  def __init__(self):
    """Initializes a single threaded queue."""
    super(SingleThreadedQueue, self).__init__()
    self._queue = collections.deque()
    self.closed = False

  def PopItems(self):
    """Return a generator that gets items of the queue."""
    try:
      while 1:
        yield self._queue.pop()
    except IndexError:
      pass

  def Close(self):
    """Indicate that the queue has been closed."""
    self.closed = True

  def __len__(self):
    """Return the number of items inside the queue."""
    return len(self._queue)

  def Queue(self, item):
    """Add an even to the queue."""
    if not self.closed:
      self._queue.append(item)
    else:
      logging.debug('Unable to add item to queue, since it is closed.')

  def AddEvent(self, item):
    """Add an event to the queue."""
    self.Queue(item)
