# -*- coding: utf-8 -*-
"""This file contains the event buffer class."""

import heapq
import logging

from plaso.lib import errors
from plaso.lib import py2to3


class _EventsHeap(object):
  """Class that defines the events heap."""

  def __init__(self):
    """Initializes an events heap."""
    super(_EventsHeap, self).__init__()
    self._heap = []

  @property
  def number_of_events(self):
    """int: number of serialized events on the heap."""
    return len(self._heap)

  def PopEvent(self):
    """Pops an event from the heap.

    Returns:
      EventObject: event.
    """
    try:
      _, _, _, event = heapq.heappop(self._heap)
      return event

    except IndexError:
      return None

  def PushEvent(self, event):
    """Pushes an event onto the heap.

    Args:
      event (EventObject): event.
    """
    event_identifier = event.GetIdentifier()
    event_identifier_string = event_identifier.CopyToString()
    heap_values = (
        event.timestamp, event.timestamp_desc, event_identifier_string, event)
    heapq.heappush(self._heap, heap_values)

  def PushEvents(self, events):
    """Pushes events onto the heap.

    Args:
      events list[EventObject]: events.
    """
    for event in events:
      self.PushEvent(event)


# TODO: rename class and fix docstrings.
class EventBuffer(object):
  """Buffer class for event output processing.

  The event buffer is used to deduplicate events and make sure they are sorted
  before output.

  Attributes:
    check_dedups (bool): True if the event buffer should check and merge
        duplicate events.
    duplicate_counter (int): number of duplicate events.
  """

  _JOIN_ATTRIBUTES = frozenset([u'display_name', u'filename', u'inode'])

  # Attributes that should not be used in calculating the event key.
  # TODO: remove uuid when test files have been updated.
  _EXCLUDED_ATTRIBUTES = frozenset([
      u'data_type',
      u'display_name',
      u'filename',
      u'inode',
      u'parser',
      u'pathspec',
      u'tag',
      u'timestamp'])

  def __init__(self, output_module, check_dedups=True):
    """Initializes an event buffer object.

    This class is used for buffering up events for duplicate removals
    and for other post-processing/analysis of events before being presented
    by the appropriate output module.

    Args:
      output_module (OutputModule): output module.
      check_dedups (Optional[bool]): True if the event buffer should check and
          merge duplicate events.
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

  def _GetEventIdentifier(self, event):
    """Determines an unique identifier of an event from its attributes.

    Args:
      event (EventObject): event.

    Returns:
      str: unique identifier representation of the event that can be used for
          equality comparison.
    """
    attributes = {}
    for attribute_name, attribute_value in event.GetAttributes():
      if attribute_name in self._EXCLUDED_ATTRIBUTES:
        continue

      if isinstance(attribute_value, dict):
        attribute_value = sorted(attribute_value.items())

      elif isinstance(attribute_value, set):
        attribute_value = sorted(list(attribute_value))

      attributes[attribute_name] = attribute_value

    if event.pathspec:
      attributes[u'pathspec'] = event.pathspec.comparable

    try:
      event_identifier_string = u'|'.join([
          u'{0:s}={1!s}'.format(attribute_name, attribute_value)
          for attribute_name, attribute_value in sorted(attributes.items())])

    except UnicodeDecodeError:
      event_identifier = event.GetIdentifier()
      event_identifier_string = u'identifier={0:s}'.format(
          event_identifier.CopyToString())

    event_identifier_string = u'{0:d}|{1:s}|{2:s}'.format(
        event.timestamp, event.data_type, event_identifier_string)
    return event_identifier_string

  def Append(self, event):
    """Appends an event.

    Args:
      event (EventObject): event.
    """
    if not self.check_dedups:
      self._output_module.WriteEvent(event)
      return

    if event.timestamp != self._current_timestamp:
      self._current_timestamp = event.timestamp
      self.Flush()

    lookup_key = self._GetEventIdentifier(event)
    if lookup_key in self._events_per_key:
      duplicate_event = self._events_per_key.pop(lookup_key)
      self.JoinEvents(event, duplicate_event)

    self._events_per_key[lookup_key] = event

  def End(self):
    """Closes the buffer.

    Buffered events are written using the output module, an optional footer is
    written and the output is closed.
    """
    self.Flush()

    if self._output_module:
      self._output_module.WriteFooter()
      self._output_module.Close()

  def Flush(self):
    """Flushes the buffer.

    Buffered events are written using the output module.
    """
    if not self._events_per_key:
      return

    # The heap is used to make sure the events are sorted in
    # a deterministic way.
    events_heap = _EventsHeap()
    events_heap.PushEvents(self._events_per_key.values())
    self._events_per_key = {}

    event = events_heap.PopEvent()
    while event:
      try:
        self._output_module.WriteEvent(event)
      except errors.WrongFormatter as exception:
        # TODO: store errors and report them at the end of psort.
        logging.error(
            u'Unable to write event with error: {0:s}'.format(exception))

      event = events_heap.PopEvent()

  def JoinEvents(self, first_event, second_event):
    """Joins the attributes of two events.

    Args:
      first_event (EventObject): first event.
      second_event (EventObject): second event.
    """
    self.duplicate_counter += 1

    # TODO: Currently we are using the first event pathspec, perhaps that
    # is not the best approach. There is no need to have all the pathspecs
    # inside the combined event, however which one should be chosen is
    # perhaps something that can be evaluated here (regular TSK in favor of
    # an event stored deep inside a VSS for instance).

    for attribute_name in self._JOIN_ATTRIBUTES:
      first_value = getattr(first_event, attribute_name, None)
      if first_value is None:
        first_value_set = set()

      else:
        if isinstance(first_value, py2to3.STRING_TYPES):
          first_value = first_value.split(u';')
        else:
          first_value = [first_value]

        first_value_set = set(first_value)

      second_value = getattr(second_event, attribute_name, None)
      if second_value is None:
        second_value_set = set()

      else:
        if isinstance(second_value, py2to3.STRING_TYPES):
          second_value = second_value.split(u';')
        else:
          second_value = [second_value]

        second_value_set = set(second_value)

      values_list = list(first_value_set.union(second_value_set))
      values_list.sort()

      if not values_list:
        join_value = None
      elif len(values_list) == 1:
        join_value = values_list[0]
      else:
        join_value = u';'.join(values_list)

      setattr(first_event, attribute_name, join_value)

    # If two events are merged then we'll just pick the first inode value.
    inode = first_event.inode
    if isinstance(inode, py2to3.STRING_TYPES):
      inode_list = inode.split(u';')
      try:
        new_inode = int(inode_list[0], 10)
      except (IndexError, ValueError):
        new_inode = 0

      first_event.inode = new_inode

    # Special instance if this is a filestat entry we need to combine the
    # timestamp description field.
    parser_name = getattr(first_event, u'parser', None)

    if parser_name == u'filestat':
      first_description = getattr(first_event, u'timestamp_desc', u'')
      first_description_set = set(first_description.split(u';'))

      second_description = getattr(second_event, u'timestamp_desc', u'')
      second_description_set = set(second_description.split(u';'))

      if first_description_set.difference(second_description_set):
        descriptions_list = list(first_description_set.union(
            second_description_set))
        descriptions_list.sort()
        description_value = u';'.join(descriptions_list)

        setattr(first_event, u'timestamp_desc', description_value)
