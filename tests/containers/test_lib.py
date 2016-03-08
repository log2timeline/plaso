#!/usr/bin/python
# -*- coding: utf-8 -*-
"""This file contains the tests for the event attribute container objects."""

import unittest

from dfwinreg import filetime as dfwinreg_filetime

from plaso.containers import events
from plaso.events import text_events
from plaso.events import windows_events
from plaso.lib import timelib


def GetEventObjects():
  """Returns a list of test event objects."""
  test_events = []
  hostname = u'MYHOSTNAME'
  data_type = 'test:event'

  event_object = events.EventObject()
  event_object.username = u'joesmith'
  event_object.filename = u'c:/Users/joesmith/NTUSER.DAT'
  event_object.hostname = hostname
  event_object.timestamp = 0
  event_object.data_type = data_type
  event_object.text = u''

  test_events.append(event_object)

  filetime = dfwinreg_filetime.Filetime()

  # TODO: move this to a WindowsRegistryEvent unit test.
  filetime.CopyFromString(u'2012-04-20 22:38:46.929596')
  values_dict = {u'Run': u'c:/Temp/evil.exe'}
  event_object = windows_events.WindowsRegistryEvent(
      filetime.timestamp, u'MY AutoRun key', values_dict)
  event_object.hostname = hostname

  test_events.append(event_object)

  filetime.CopyFromString(u'2012-04-20 23:56:46.929596')
  values_dict = {u'Value': u'send all the exes to the other world'}
  event_object = windows_events.WindowsRegistryEvent(
      filetime.timestamp, u'//HKCU/Secret/EvilEmpire/Malicious_key',
      values_dict)
  event_object.hostname = hostname

  test_events.append(event_object)

  filetime.CopyFromString(u'2012-04-20 16:44:46.000000')
  values_dict = {u'Value': u'run all the benign stuff'}
  event_object = windows_events.WindowsRegistryEvent(
      filetime.timestamp, u'//HKCU/Windows/Normal', values_dict)
  event_object.hostname = hostname

  test_events.append(event_object)

  timestamp = timelib.Timestamp.CopyFromString(u'2012-04-30 10:29:47.929596')
  filename = u'c:/Temp/evil.exe'
  attributes = {
      u'text': u'This log line reads ohh so much.'}
  event_object = TestEvent(timestamp, attributes)
  event_object.filename = filename
  event_object.hostname = hostname

  test_events.append(event_object)

  timestamp = timelib.Timestamp.CopyFromString(u'2012-04-30 10:29:47.929596')
  attributes = {
      u'text': u'Nothing of interest here, move on.'}
  event_object = TestEvent(timestamp, attributes)
  event_object.filename = filename
  event_object.hostname = hostname

  test_events.append(event_object)

  timestamp = timelib.Timestamp.CopyFromString(u'2012-04-30 13:06:47.939596')
  attributes = {
      u'text': u'Mr. Evil just logged into the machine and got root.'}
  event_object = TestEvent(timestamp, attributes)
  event_object.filename = filename
  event_object.hostname = hostname

  test_events.append(event_object)

  text_dict = {u'body': (
      u'This is a line by someone not reading the log line properly. And '
      u'since this log line exceeds the accepted 80 chars it will be '
      u'shortened.'), u'hostname': u'nomachine', u'username': u'johndoe'}

  # TODO: move this to a TextEvent unit test.
  timestamp = timelib.Timestamp.CopyFromString(u'2012-06-05 22:14:19.000000')
  event_object = text_events.TextEvent(timestamp, 12, text_dict)
  event_object.text = event_object.body
  event_object.hostname = hostname
  event_object.filename = filename

  test_events.append(event_object)

  return test_events


class TestEvent(events.EventObject):
  """A test event object."""
  DATA_TYPE = 'test:event'

  def __init__(self, timestamp, attributes):
    """Initializes the test event object."""
    super(TestEvent, self).__init__()
    self.timestamp = timestamp
    self.timestamp_desc = u'Some time in the future'
    for attribute, value in attributes.iteritems():
      setattr(self, attribute, value)


class AttributeContainerTestCase(unittest.TestCase):
  """The unit test case for an attribute container object."""

  # Show full diff results, part of TestCase so does not follow our naming
  # conventions.
  maxDiff = None
