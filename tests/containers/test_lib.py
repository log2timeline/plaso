#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Containers related functions and classes for testing."""

from __future__ import unicode_literals

from dfdatetime import filetime as dfdatetime_filetime

from plaso.containers import events
from plaso.containers import interface
from plaso.containers import time_events
from plaso.containers import windows_events
from plaso.lib import definitions
from plaso.lib import timelib


# TODO: remove after event data refactor.
def _MergeEventAndEventData(event, event_data):
  """Merges the event data with the event.

  args:
    event (EventObject): event.
    event_data (EventData): event_data.
  """
  for attribute_name, attribute_value in event_data.GetAttributes():
    setattr(event, attribute_name, attribute_value)


def CreateTestEvents():
  """Creates events for testing.

  Returns:
    list[EventObject]: events.
  """
  test_events = []
  hostname = 'MYHOSTNAME'
  data_type = 'test:event'

  event = events.EventObject()
  event.username = 'joesmith'
  event.filename = 'c:/Users/joesmith/NTUSER.DAT'
  event.hostname = hostname
  event.timestamp = 0
  event.data_type = data_type
  event.text = ''

  test_events.append(event)

  filetime = dfdatetime_filetime.Filetime()

  # TODO: move this to a WindowsRegistryEvent unit test.
  event_data = windows_events.WindowsRegistryEventData()
  event_data.key_path = 'MY AutoRun key'
  event_data.hostname = hostname
  event_data.regvalue = {'Value': 'c:/Temp/evil.exe'}

  filetime.CopyFromDateTimeString('2012-04-20 22:38:46.929596')
  event = time_events.DateTimeValuesEvent(
      filetime, definitions.TIME_DESCRIPTION_WRITTEN)

  _MergeEventAndEventData(event, event_data)
  test_events.append(event)

  event_data = windows_events.WindowsRegistryEventData()
  event_data.key_path = 'HKEY_CURRENT_USER\\Secret\\EvilEmpire\\Malicious_key'
  event_data.hostname = hostname
  event_data.regvalue = {'Value': 'send all the exes to the other world'}

  filetime.CopyFromDateTimeString('2012-04-20 23:56:46.929596')
  event = time_events.DateTimeValuesEvent(
      filetime, definitions.TIME_DESCRIPTION_WRITTEN)

  _MergeEventAndEventData(event, event_data)
  test_events.append(event)

  event_data = windows_events.WindowsRegistryEventData()
  event_data.key_path = 'HKEY_CURRENT_USER\\Windows\\Normal'
  event_data.hostname = hostname
  event_data.regvalue = {'Value': 'run all the benign stuff'}

  filetime.CopyFromDateTimeString('2012-04-20 16:44:46')
  event = time_events.DateTimeValuesEvent(
      filetime, definitions.TIME_DESCRIPTION_WRITTEN)

  _MergeEventAndEventData(event, event_data)
  test_events.append(event)

  timestamp = timelib.Timestamp.CopyFromString('2012-04-30 10:29:47.929596')
  filename = 'c:/Temp/evil.exe'
  attributes = {
      'text': 'This log line reads ohh so much.'}
  event = TestEvent(timestamp, attributes)
  event.filename = filename
  event.hostname = hostname

  test_events.append(event)

  timestamp = timelib.Timestamp.CopyFromString('2012-04-30 10:29:47.929596')
  attributes = {
      'text': 'Nothing of interest here, move on.'}
  event = TestEvent(timestamp, attributes)
  event.filename = filename
  event.hostname = hostname

  test_events.append(event)

  timestamp = timelib.Timestamp.CopyFromString('2012-04-30 13:06:47.939596')
  attributes = {
      'text': 'Mr. Evil just logged into the machine and got root.'}
  event = TestEvent(timestamp, attributes)
  event.filename = filename
  event.hostname = hostname

  test_events.append(event)

  timestamp = timelib.Timestamp.CopyFromString('2012-06-05 22:14:19.000000')
  # TODO: refactor to use event data.
  event = time_events.TimestampEvent(
      timestamp, definitions.TIME_DESCRIPTION_WRITTEN,
      data_type='text:entry')
  event.hostname = 'nomachine'
  event.offset = 12
  event.body = (
      'This is a line by someone not reading the log line properly. And '
      'since this log line exceeds the accepted 80 chars it will be '
      'shortened.')
  # TODO: fix missing body attribute
  event.text = event.body
  event.username = 'johndoe'

  test_events.append(event)

  return test_events


class TestAttributeContainer(interface.AttributeContainer):
  """Test attribute container."""

  CONTAINER_TYPE = 'test_attribute_container'


class TestEvent(events.EventObject):
  """Test event."""

  DATA_TYPE = 'test:event'

  def __init__(self, timestamp, attributes=None):
    """Initializes an event.

    Args:
      timestamp (int): timestamp, which contains the number of microseconds
          since January 1, 1970, 00:00:00 UTC.
      attributes (dict[str, object]): event attributes.
    """
    super(TestEvent, self).__init__()
    self.timestamp = timestamp

    attributes = attributes or {}
    for attribute, value in iter(attributes.items()):
      setattr(self, attribute, value)
