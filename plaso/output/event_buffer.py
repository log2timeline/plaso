# -*- coding: utf-8 -*-
"""This file contains the event buffer class."""

import heapq
import logging

from plaso.lib import errors
from plaso.lib import utils


class _EventsHeap(object):
  """Class that defines the event objects heap."""

  def __init__(self):
    """Initializes an event objects heap."""
    super(_EventsHeap, self).__init__()
    self._heap = []

  @property
  def number_of_events(self):
    """The number of serialized event objects on the heap."""
    return len(self._heap)

  def PopEvent(self):
    """Pops an event object from the heap.

    Returns:
      An event object (instance of EventObject).
    """
    try:
      _, _, event_object = heapq.heappop(self._heap)
      return event_object

    except IndexError:
      return None

  def PushEvent(self, event_object):
    """Pushes an event object onto the heap.

    Args:
      event_object: an event object (instance of EventObject).
    """
    heap_values = (
        event_object.timestamp, event_object.timestamp_desc, event_object)
    heapq.heappush(self._heap, heap_values)

  def PushEvents(self, event_objects):
    """Pushes event objects onto the heap.

    Args:
      event_objects: a list of event objects (instances of EventObject).
    """
    for event_object in event_objects:
      self.PushEvent(event_object)


# TODO: rename class and fix docstrings.
class EventBuffer(object):
  """Buffer class for event object output processing.

  The event buffer is used to deduplicate event objects and make sure
  they are sorted before output.

  Attributes:
    check_dedups: boolean value indicating whether or not the buffer
                  should check and merge duplicate entries or not.
    duplicate_counter: integer that contains the number of duplicates.
  """

  _MERGE_ATTRIBUTES = frozenset([u'inode', u'filename', u'display_name'])

  def __init__(self, output_module, check_dedups=True):
    """Initializes an event buffer object.

    This class is used for buffering up events for duplicate removals
    and for other post-processing/analysis of events before being presented
    by the appropriate output module.

    Args:
      output_module: an output module object (instance of OutputModule).
      check_dedups: optional boolean value indicating whether or not the buffer
                    should check and merge duplicate entries or not.
    """
    self._current_timestamp = 0
    self._events_per_key = {}
    self._output_module = output_module
    self._output_module.Open()
    self._output_module.WriteHeader()

    self.check_dedups = check_dedups
    self.duplicate_counter = 0

  def __enter__(self):
    """Make usable with "with" statement."""
    return self

  def __exit__(self, unused_type, unused_value, unused_traceback):
    """Make usable with "with" statement."""
    self.End()

  def Append(self, event_object):
    """Appends an event object.

    Args:
      event_object: an event object (instance of EventObject).
    """
    if not self.check_dedups:
      self._output_module.WriteEvent(event_object)
      return

    if event_object.timestamp != self._current_timestamp:
      self._current_timestamp = event_object.timestamp
      self.Flush()

    key = event_object.EqualityString()
    if key in self._events_per_key:
      duplicate_event_object = self._events_per_key.pop(key)
      self.JoinEvents(event_object, duplicate_event_object)

    self._events_per_key[key] = event_object

  def End(self):
    """Closes the buffer.

    Buffered event objects are written using the output module, an optional
    footer is written and the output is closed.
    """
    self.Flush()

    if self._output_module:
      self._output_module.WriteFooter()
      self._output_module.Close()

  def Flush(self):
    """Flushes the buffer.

    Buffered event objects are written using the output module.
    """
    if not self._events_per_key:
      return

    # The heap is used to make sure the events are sorted in
    # a deterministic way.
    events_heap = _EventsHeap()
    events_heap.PushEvents(self._events_per_key.values())
    self._events_per_key = {}

    event_object = events_heap.PopEvent()
    while event_object:
      try:
        self._output_module.WriteEvent(event_object)
      except errors.WrongFormatter as exception:
        # TODO: store errors and report them at the end of psort.
        logging.error(
            u'Unable to write event with error: {0:s}'.format(exception))

      event_object = events_heap.PopEvent()

  def JoinEvents(self, first_event, second_event):
    """Joins two event objects.

    Args:
      first_event: the first event object (instance of EventObject).
      second_event: the second event object (instance of EventObject).
    """
    self.duplicate_counter += 1
    # TODO: Currently we are using the first event pathspec, perhaps that
    # is not the best approach. There is no need to have all the pathspecs
    # inside the combined event, however which one should be chosen is
    # perhaps something that can be evaluated here (regular TSK in favor of
    # an event stored deep inside a VSS for instance).
    for attr in self._MERGE_ATTRIBUTES:
      # TODO: remove need for GetUnicodeString.
      first_value = set(utils.GetUnicodeString(
          getattr(first_event, attr, u'')).split(u';'))
      second_value = set(utils.GetUnicodeString(
          getattr(second_event, attr, u'')).split(u';'))
      values_list = list(first_value | second_value)
      values_list.sort() # keeping this consistent across runs helps with diffs
      setattr(first_event, attr, u';'.join(values_list))

    # Special instance if this is a filestat entry we need to combine the
    # description field.
    if getattr(first_event, u'parser', u'') == u'filestat':
      first_description = set(
          getattr(first_event, u'timestamp_desc', u'').split(u';'))
      second_description = set(
          getattr(second_event, u'timestamp_desc', u'').split(u';'))
      descriptions = list(first_description | second_description)
      descriptions.sort()
      if second_event.timestamp_desc not in first_event.timestamp_desc:
        setattr(first_event, u'timestamp_desc', u';'.join(descriptions))
