# -*- coding: utf-8 -*-
"""Storage related functions and classes for testing."""

from plaso.dfwinreg import fake as dfwinreg_fake
from plaso.events import text_events
from plaso.events import windows_events
from plaso.lib import timelib


def CreateTestEventObjects():
  """Creates the event objects for testing.

  Returns:
    A list of event objects (instances of EventObject).
  """
  event_objects = []
  filetime = dfwinreg_fake.Filetime()

  filetime.CopyFromString(u'2012-04-20 22:38:46.929596')
  values_dict = {u'Value': u'c:/Temp/evil.exe'}
  event_object = windows_events.WindowsRegistryEvent(
      filetime.timestamp, u'MY AutoRun key', values_dict)
  event_object.parser = 'UNKNOWN'
  event_objects.append(event_object)

  filetime.CopyFromString(u'2012-05-02 13:43:26.929596')
  values_dict = {u'Value': u'send all the exes to the other world'}
  event_object = windows_events.WindowsRegistryEvent(
      filetime.timestamp, u'\\HKCU\\Secret\\EvilEmpire\\Malicious_key',
      values_dict)
  event_object.parser = 'UNKNOWN'
  event_objects.append(event_object)

  filetime.CopyFromString(u'2012-04-20 16:44:46')
  values_dict = {u'Value': u'run all the benign stuff'}
  event_object = windows_events.WindowsRegistryEvent(
      filetime.timestamp, u'\\HKCU\\Windows\\Normal', values_dict)
  event_object.parser = 'UNKNOWN'
  event_objects.append(event_object)

  timemstamp = timelib.Timestamp.CopyFromString(u'2009-04-05 12:27:39')
  text_dict = {
      u'hostname': u'nomachine',
      u'text': (
          u'This is a line by someone not reading the log line properly. And '
          u'since this log line exceeds the accepted 80 chars it will be '
          u'shortened.'),
      u'username': u'johndoe'}
  event_object = text_events.TextEvent(timemstamp, 12, text_dict)
  event_object.parser = 'UNKNOWN'
  event_objects.append(event_object)

  return event_objects
