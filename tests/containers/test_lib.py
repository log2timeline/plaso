#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Containers related functions and classes for testing."""

from __future__ import unicode_literals

from plaso.containers import events
from plaso.containers import interface


def CreateEventFromValues(event_values):
  """Creates an event and event data from event values.

  Args:
    event_values (dict[str, str]): event values.

  Returns:
    tuple[EventObject, EventData]: event and event data for testing.
  """
  copy_of_event_values = dict(event_values)

  timestamp = copy_of_event_values.get('timestamp', None)
  if 'timestamp' in copy_of_event_values:
    del copy_of_event_values['timestamp']

  timestamp_desc = copy_of_event_values.get('timestamp_desc', None)
  if 'timestamp_desc' in copy_of_event_values:
    del copy_of_event_values['timestamp_desc']

  event = events.EventObject()
  event.timestamp = timestamp
  event.timestamp_desc = timestamp_desc

  event_data = events.EventData()
  event_data.CopyFromDict(copy_of_event_values)

  return event, event_data


def CreateEventsFromValues(event_values_list):
  """Creates events and event data from a list of event values.

  Args:
    event_values_list (list[dict[str, str]]): list of event values.

  Yields:
    tuple[EventObject, EventData]: event and event data for testing.
  """
  for event_values in event_values_list:
    yield CreateEventFromValues(event_values)


class TestAttributeContainer(interface.AttributeContainer):
  """Test attribute container."""

  CONTAINER_TYPE = 'test_attribute_container'
