# -*- coding: utf-8 -*-
"""The pprof front-end."""

import collections

from plaso.engine import queue


# TODO: Remove this after the dfVFS integration.
# TODO: Make sure we don't need to implement the method _ConsumeItem, or
# to have that not as an abstract method.
# pylint: disable=abstract-method
class PprofEventObjectQueueConsumer(queue.EventObjectQueueConsumer):
  """Class that implements an event object queue consumer for pprof."""

  def __init__(self, queue_object):
    """Initializes the queue consumer.

    Args:
      queue_object: the queue object (instance of Queue).
    """
    super(PprofEventObjectQueueConsumer, self).__init__(queue_object)
    self.counter = collections.Counter()
    self.parsers = []
    self.plugins = []

  def _ConsumeEventObject(self, event_object, **unused_kwargs):
    """Consumes an event object callback for ConsumeEventObject."""
    parser = getattr(event_object, 'parser', u'N/A')
    if parser not in self.parsers:
      self.parsers.append(parser)

    plugin = getattr(event_object, 'plugin', u'N/A')
    if plugin not in self.plugins:
      self.plugins.append(plugin)

    self.counter[parser] += 1
    if plugin != u'N/A':
      self.counter[u'[Plugin] {}'.format(plugin)] += 1
    self.counter['Total'] += 1
