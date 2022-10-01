#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Containers related functions and classes for testing."""

from dfdatetime import posix_time as dfdatetime_posix_time

from plaso.containers import events

from tests import test_lib as shared_test_lib


def CreateEventFromValues(event_values):
  """Creates an event and event data from event values.

  Args:
    event_values (dict[str, str]): event values.

  Returns:
    tuple[EventObject, EventData, EventDataStream]: event, event data and
        event data stream for testing.
  """
  copy_of_event_values = dict(event_values)

  event = events.EventObject()
  for attribute_name in ('timestamp', 'timestamp_desc'):
    attribute_value = copy_of_event_values.pop(attribute_name, None)
    if attribute_value is not None:
      if attribute_name == 'timestamp' and isinstance(attribute_value, str):
        attribute_value = shared_test_lib.CopyTimestampFromString(
            attribute_value)
      setattr(event, attribute_name, attribute_value)

  event.date_time = dfdatetime_posix_time.PosixTimeInMicroseconds(
      timestamp=event.timestamp)

  event_data_stream = events.EventDataStream()
  for attribute_name in ('path_spec', 'md5_hash', 'sha256_hash'):
    attribute_value = copy_of_event_values.pop(attribute_name, None)
    if attribute_value is not None:
      setattr(event_data_stream, attribute_name, attribute_value)

  event_data = events.EventData()
  event_data.CopyFromDict(copy_of_event_values)

  return event, event_data, event_data_stream


def CreateEventsFromValues(event_values_list):
  """Creates events and event data from a list of event values.

  Args:
    event_values_list (list[dict[str, str]]): list of event values.

  Yields:
    tuple[EventObject, EventData, EventDataStream]: event, event data and
        event data stream for testing.
  """
  for event_values in event_values_list:
    yield CreateEventFromValues(event_values)
