#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Containers related functions and classes for testing."""

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
  hostname = u'MYHOSTNAME'
  data_type = u'test:event'

  event = events.EventObject()
  event.username = u'joesmith'
  event.filename = u'c:/Users/joesmith/NTUSER.DAT'
  event.hostname = hostname
  event.timestamp = 0
  event.data_type = data_type
  event.text = u''

  test_events.append(event)

  filetime = dfdatetime_filetime.Filetime()

  # TODO: move this to a WindowsRegistryEvent unit test.
  event_data = windows_events.WindowsRegistryEventData()
  event_data.key_path = u'MY AutoRun key'
  event_data.hostname = hostname
  event_data.regvalue = {u'Value': u'c:/Temp/evil.exe'}

  filetime.CopyFromString(u'2012-04-20 22:38:46.929596')
  event = time_events.DateTimeValuesEvent(
      filetime, definitions.TIME_DESCRIPTION_WRITTEN)

  _MergeEventAndEventData(event, event_data)
  test_events.append(event)

  event_data = windows_events.WindowsRegistryEventData()
  event_data.key_path = u'HKEY_CURRENT_USER\\Secret\\EvilEmpire\\Malicious_key'
  event_data.hostname = hostname
  event_data.regvalue = {u'Value': u'send all the exes to the other world'}

  filetime.CopyFromString(u'2012-04-20 23:56:46.929596')
  event = time_events.DateTimeValuesEvent(
      filetime, definitions.TIME_DESCRIPTION_WRITTEN)

  _MergeEventAndEventData(event, event_data)
  test_events.append(event)

  event_data = windows_events.WindowsRegistryEventData()
  event_data.key_path = u'HKEY_CURRENT_USER\\Windows\\Normal'
  event_data.hostname = hostname
  event_data.regvalue = {u'Value': u'run all the benign stuff'}

  filetime.CopyFromString(u'2012-04-20 16:44:46')
  event = time_events.DateTimeValuesEvent(
      filetime, definitions.TIME_DESCRIPTION_WRITTEN)

  _MergeEventAndEventData(event, event_data)
  test_events.append(event)

  timestamp = timelib.Timestamp.CopyFromString(u'2012-04-30 10:29:47.929596')
  filename = u'c:/Temp/evil.exe'
  attributes = {
      u'text': u'This log line reads ohh so much.'}
  event = TestEvent(timestamp, attributes)
  event.filename = filename
  event.hostname = hostname

  test_events.append(event)

  timestamp = timelib.Timestamp.CopyFromString(u'2012-04-30 10:29:47.929596')
  attributes = {
      u'text': u'Nothing of interest here, move on.'}
  event = TestEvent(timestamp, attributes)
  event.filename = filename
  event.hostname = hostname

  test_events.append(event)

  timestamp = timelib.Timestamp.CopyFromString(u'2012-04-30 13:06:47.939596')
  attributes = {
      u'text': u'Mr. Evil just logged into the machine and got root.'}
  event = TestEvent(timestamp, attributes)
  event.filename = filename
  event.hostname = hostname

  test_events.append(event)

  timestamp = timelib.Timestamp.CopyFromString(u'2012-06-05 22:14:19.000000')
  # TODO: refactor to use event data.
  event = time_events.TimestampEvent(
      timestamp, definitions.TIME_DESCRIPTION_WRITTEN,
      data_type=u'text:entry')
  event.hostname = u'nomachine'
  event.offset = 12
  event.body = (
      u'This is a line by someone not reading the log line properly. And '
      u'since this log line exceeds the accepted 80 chars it will be '
      u'shortened.')
  # TODO: fix missing body attribute
  event.text = event.body
  event.username = u'johndoe'

  test_events.append(event)

  return test_events


class TestAttributeContainer(interface.AttributeContainer):
  """Class to define a test attribute container."""
  CONTAINER_TYPE = u'test_attribute_container'


class TestEvent(events.EventObject):
  """Class to define a test event."""
  DATA_TYPE = u'test:event'

  def __init__(self, timestamp, attributes):
    """Initializes an event object."""
    super(TestEvent, self).__init__()
    self.timestamp = timestamp
    self.timestamp_desc = u'Some time in the future'
    for attribute, value in iter(attributes.items()):
      setattr(self, attribute, value)
