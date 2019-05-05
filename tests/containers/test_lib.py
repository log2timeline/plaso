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


def CreateTestEvents():
  """Creates events for testing.

  Returns:
    list[tuple[EventObject, EventData]]: events.
  """
  test_events = []

  event = events.EventObject()
  event.timestamp = 0
  event.timestamp_desc = definitions.TIME_DESCRIPTION_UNKNOWN

  event_data = events.EventData()
  event_data.data_type = 'test:event'
  event_data.filename = 'c:/Users/joesmith/NTUSER.DAT'
  event_data.hostname = 'MYHOSTNAME'
  event_data.text = ''
  event_data.username = 'joesmith'

  test_events.append((event, event_data))

  # TODO: move this to a WindowsRegistryEvent unit test.
  event_data = windows_events.WindowsRegistryEventData()
  event_data.key_path = 'MY AutoRun key'
  event_data.hostname = 'MYHOSTNAME'
  event_data.regvalue = {'Value': 'c:/Temp/evil.exe'}

  filetime = dfdatetime_filetime.Filetime()
  filetime.CopyFromDateTimeString('2012-04-20 22:38:46.929596')
  event = time_events.DateTimeValuesEvent(
      filetime, definitions.TIME_DESCRIPTION_WRITTEN)

  test_events.append((event, event_data))

  event_data = windows_events.WindowsRegistryEventData()
  event_data.key_path = 'HKEY_CURRENT_USER\\Secret\\EvilEmpire\\Malicious_key'
  event_data.hostname = 'MYHOSTNAME'
  event_data.regvalue = {'Value': 'send all the exes to the other world'}

  filetime = dfdatetime_filetime.Filetime()
  filetime.CopyFromDateTimeString('2012-04-20 23:56:46.929596')
  event = time_events.DateTimeValuesEvent(
      filetime, definitions.TIME_DESCRIPTION_WRITTEN)

  test_events.append((event, event_data))

  event_data = windows_events.WindowsRegistryEventData()
  event_data.key_path = 'HKEY_CURRENT_USER\\Windows\\Normal'
  event_data.hostname = 'MYHOSTNAME'
  event_data.regvalue = {'Value': 'run all the benign stuff'}

  filetime = dfdatetime_filetime.Filetime()
  filetime.CopyFromDateTimeString('2012-04-20 16:44:46')
  event = time_events.DateTimeValuesEvent(
      filetime, definitions.TIME_DESCRIPTION_WRITTEN)

  test_events.append((event, event_data))

  event = events.EventObject()
  event.timestamp = timelib.Timestamp.CopyFromString(
      '2012-04-30 10:29:47.929596')
  event.timestamp_desc = definitions.TIME_DESCRIPTION_UNKNOWN

  event_data = events.EventData()
  event_data.data_type = 'test:event'
  event_data.filename = 'c:/Temp/evil.exe'
  event_data.hostname = 'MYHOSTNAME'
  event_data.text = 'This log line reads ohh so much.'

  test_events.append((event, event_data))

  event = events.EventObject()
  event.timestamp = timelib.Timestamp.CopyFromString(
      '2012-04-30 10:29:47.929596')
  event.timestamp_desc = definitions.TIME_DESCRIPTION_UNKNOWN

  event_data = events.EventData()
  event_data.data_type = 'test:event'
  event_data.filename = 'c:/Temp/evil.exe'
  event_data.hostname = 'MYHOSTNAME'
  event_data.text = 'Nothing of interest here, move on.'

  test_events.append((event, event_data))

  event = events.EventObject()
  event.timestamp = timelib.Timestamp.CopyFromString(
      '2012-04-30 13:06:47.939596')
  event.timestamp_desc = definitions.TIME_DESCRIPTION_UNKNOWN

  event_data = events.EventData()
  event_data.data_type = 'test:event'
  event_data.filename = 'c:/Temp/evil.exe'
  event_data.hostname = 'MYHOSTNAME'
  event_data.text = 'Mr. Evil just logged into the machine and got root.'

  test_events.append((event, event_data))

  event = events.EventObject()
  event.timestamp = timelib.Timestamp.CopyFromString(
      '2012-06-05 22:14:19.000000')
  event.timestamp_desc = definitions.TIME_DESCRIPTION_WRITTEN

  event_data = events.EventData()
  event_data.body = (
      'This is a line by someone not reading the log line properly. And '
      'since this log line exceeds the accepted 80 chars it will be '
      'shortened.')
  event_data.data_type = 'text:entry'
  event_data.hostname = 'nomachine'
  event_data.offset = 12
  # TODO: fix missing body attribute
  event_data.text = event_data.body
  event_data.username = 'johndoe'

  test_events.append((event, event_data))

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
