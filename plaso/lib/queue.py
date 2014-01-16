#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2012 The Plaso Project Authors.
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

from plaso.lib import event
from plaso.lib import errors
from plaso.serializer import protobuf_serializer


class QueueEndOfInput(object):
  """Class that implements a queue end of input."""


class Queue(object):
  """Class that implements the queue interface."""

  @abc.abstractmethod
  def __len__(self):
    """Return the estimated number of entries inside the queue."""

  @abc.abstractmethod
  def IsEmpty(self):
    """Determines if the queue is empty."""

  @abc.abstractmethod
  def PushItem(self, item):
    """Pushes an item onto the queue."""

  @abc.abstractmethod
  def PopItem(self):
    """Pops an item off the queue."""

  def SignalEndOfInput(self):
    """Signals the queue no input remains."""
    self.PushItem(QueueEndOfInput())


class MultiThreadedQueue(Queue):
  """Multi threaded queue."""

  def __init__(self):
    """Initializes the multi threaded queue."""
    super(MultiThreadedQueue, self).__init__()
    self._queue = multiprocessing.Queue()

  def __len__(self):
    """Return the total number of events stored inside the queue."""
    size = 0
    try:
      size = self._queue.qsize()
    except NotImplementedError:
      logging.warning(
          u'Returning queue length does not work on Mac OS X because of broken'
          u'sem_getvalue()')
      raise

    return size

  def IsEmpty(self):
    """Determines if the queue is empty."""
    return self._queue.empty()

  def PushItem(self, item):
    """Pushes an item onto the queue."""
    self._queue.put(item)

  def PopItem(self):
    """Pops an item off the queue."""
    try:
      return self._queue.get()
    except KeyboardInterrupt:
      raise errors.QueueEmpty


class SingleThreadedQueue(Queue):
  """Single threaded queue."""

  def __init__(self):
    """Initializes a single threaded queue."""
    super(SingleThreadedQueue, self).__init__()
    self._queue = collections.deque()

  def __len__(self):
    """Return the number of items inside the queue."""
    return len(self._queue)

  def IsEmpty(self):
    """Determines if the queue is empty."""
    return len(self._queue)

  def PushItem(self, item):
    """Pushes an item onto the queue."""
    self._queue.append(item)

  def PopItem(self):
    """Pops an item off the queue."""
    try:
      # Using popleft to have FIFO behavior.
      return self._queue.popleft()
    except IndexError:
      raise errors.QueueEmpty


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
    self._queue = queue_object

  @abc.abstractmethod
  def _ConsumeItem(self, item):
    """Consumes an item callback for ConsumeItems."""

  def ConsumeItems(self):
    """Consumes the items that are pushed on the queue."""
    while True:
      try:
        item = self._queue.PopItem()
      except errors.QueueEmpty:
        break

      if isinstance(item, QueueEndOfInput):
        # Push the item back onto the queue to make sure all
        # queue consumers are stopped.
        self._queue.PushItem(item)
        break

      self._ConsumeItem(item)


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
    self._queue = queue_object

  def SignalEndOfInput(self):
    """Signals the queue no input remains."""
    self._queue.SignalEndOfInput()


class AnalysisReportQueueConsumer(QueueConsumer):
  """Class that implements the analysis report queue consumer.

     The consumer subscribes to updates on the queue.
  """

  @abc.abstractmethod
  def _ConsumeAnalysisReport(self, analysis_report):
    """Consumes an analysis report callback for ConsumeAnalysisReports."""

  def ConsumeAnalysisReports(self):
    """Consumes the analysis reports that are pushed on the queue.

    Raises:
      RuntimeError: when there is an unsupported object type on the queue.
    """
    while True:
      try:
        item = self._queue.PopItem()
      except errors.QueueEmpty:
        break

      if isinstance(item, QueueEndOfInput):
        # Push the item back onto the queue to make sure all
        # queue consumers are stopped.
        self._queue.PushItem(item)
        break

      if not isinstance(item, event.AnalysisReport):
        raise RuntimeError(u'Unsupported item type on queue.')

      self._ConsumeAnalysisReport(item)


class AnalysisReportQueueProducer(QueueProducer):
  """Class that implements the analysis report queue producer.

     The producer generates updates on the queue.
  """

  def ProduceAnalysisReport(self, analysis_report):
    """Produces a analysis report onto the queue.

    Args:
      analysis_report: the analysis report object (instance of
                       EventAnalysisReport).
    """
    self._queue.PushItem(analysis_report)


class EventObjectQueueConsumer(QueueConsumer):
  """Class that implements the event object queue consumer.

     The consumer subscribes to updates on the queue.
  """

  def __init__(self, queue_object):
    """Initializes the queue consumer.

    Args:
      queue_object: the queue object (instance of Queue).
    """
    super(EventObjectQueueConsumer, self).__init__(queue_object)
    self._serializer = protobuf_serializer.ProtobufEventObjectSerializer

  @abc.abstractmethod
  def _ConsumeEventObject(self, event_object):
    """Consumes an event object callback for ConsumeEventObjects."""

  def ConsumeEventObjects(self):
    """Consumes the event object that are pushed on the queue.

    Raises:
      RuntimeError: when there is an unsupported object type on the queue.
    """
    while True:
      try:
        item = self._queue.PopItem()
      except errors.QueueEmpty:
        break

      if isinstance(item, QueueEndOfInput):
        # Push the item back onto the queue to make sure all
        # queue consumers are stopped.
        self._queue.PushItem(item)
        break

      # TODO: the event object cannot be correctly serialized by the queue
      # hence a manual serialization is done as a work around but the root
      # cause should be fixed.
      item = self._serializer.ReadSerialized(item)
      if not isinstance(item, event.EventObject):
        raise RuntimeError(u'Unsupported item type on queue.')

      self._ConsumeEventObject(item)


class EventObjectQueueProducer(QueueProducer):
  """Class that implements the event object queue producer.

     The producer generates updates on the queue.
  """

  def __init__(self, queue_object):
    """Initializes the queue producer.

    Args:
      queue_object: the queue object (instance of Queue).
    """
    super(EventObjectQueueProducer, self).__init__(queue_object)
    self._serializer = protobuf_serializer.ProtobufEventObjectSerializer

  # TODO: implement this function and have the AsEventObjects function
  # flatten the container into objects.
  # def ProduceEventContainer(self, event_container):
  #   """Produces an event container onto the queue.
  #
  #   The event container is split up in event objects.
  #
  #   Args:
  #     event_container: the event container (instance of EventContainer).
  #   """
  #   for event_object in event_container.AsEventObjects():
  #     self.ProduceEventObject(event_object)

  def ProduceEventObject(self, event_object):
    """Produces an event object onto the queue.

    Args:
      event_object: the event object (instance of EventObject).
    """
    # TODO: the event object cannot be correctly serialized by the queue
    # hence a manual serialization is done as a work around but the root
    # cause should be fixed.
    event_object = self._serializer.WriteSerialized(event_object)
    self._queue.PushItem(event_object)

  def ProduceEventObjects(self, event_objects):
    """Produces event objects onto the queue.

    Args:
      event_objects: a generator of event objects (instances of EventObject).
    """
    for event_object in event_objects:
      self.ProduceEventObject(event_object)


class PathSpecQueueConsumer(QueueConsumer):
  """Class that implements the path specification queue consumer.

     The consumer subscribes to updates on the queue.
  """

  @abc.abstractmethod
  def _ConsumePathSpec(self, path_spec):
    """Consumes a path specification callback for ConsumePathSpecs."""

  def ConsumePathSpecs(self):
    """Consumes the path specifications that are pushed on the queue.

    Raises:
      RuntimeError: when there is an unsupported object type on the queue.
    """
    while True:
      try:
        item = self._queue.PopItem()
      except errors.QueueEmpty:
        break

      if isinstance(item, QueueEndOfInput):
        # Push the item back onto the queue to make sure all
        # queue consumers are stopped.
        self._queue.PushItem(item)
        break

      if not isinstance(item, event.EventPathSpec):
        raise RuntimeError(u'Unsupported item type on queue.')

      self._ConsumePathSpec(item)


class PathSpecQueueProducer(QueueProducer):
  """Class that implements the path specification queue producer.

     The producer generates updates on the queue.
  """

  def ProducePathSpec(self, path_spec):
    """Produces a path specification onto the queue.

    Args:
      path_spec: the path specification object (instance of EventPathSpec).
    """
    self._queue.PushItem(path_spec)
