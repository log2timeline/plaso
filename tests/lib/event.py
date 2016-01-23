#!/usr/bin/python
# -*- coding: utf-8 -*-
"""This file contains a unit test for the EventObject.

This is an implementation of an unit test for EventObject storage mechanism for
plaso.

The test consists of creating six EventObjects.

Error handling. The following tests are performed for error handling:
 + Access attributes that are not set.
"""

import unittest

from dfwinreg import filetime as dfwinreg_filetime

from plaso.events import text_events
from plaso.events import windows_events
from plaso.lib import event
from plaso.lib import timelib


class TestEvent(event.EventObject):
  """A test event object."""
  DATA_TYPE = 'test:event'

  def __init__(self, timestamp, attributes):
    """Initializes the test event object."""
    super(TestEvent, self).__init__()
    self.timestamp = timestamp
    self.timestamp_desc = u'Some time in the future'
    for attribute, value in attributes.iteritems():
      setattr(self, attribute, value)


class FailEvent(event.EventObject):
  """An test event object without the minimal required initialization."""


def GetEventObjects():
  """Returns a list of test event objects."""
  event_objects = []
  hostname = u'MYHOSTNAME'
  data_type = 'test:event'

  event_object = event.EventObject()
  event_object.username = u'joesmith'
  event_object.filename = u'c:/Users/joesmith/NTUSER.DAT'
  event_object.hostname = hostname
  event_object.timestamp = 0
  event_object.data_type = data_type
  event_object.text = u''
  event_objects.append(event_object)

  filetime = dfwinreg_filetime.Filetime()

  # TODO: move this to a WindowsRegistryEvent unit test.
  filetime.CopyFromString(u'2012-04-20 22:38:46.929596')
  values_dict = {u'Run': u'c:/Temp/evil.exe'}
  event_object = windows_events.WindowsRegistryEvent(
      filetime.timestamp, u'MY AutoRun key', values_dict)
  event_object.hostname = hostname
  event_objects.append(event_object)

  filetime.CopyFromString(u'2012-04-20 23:56:46.929596')
  values_dict = {u'Value': u'send all the exes to the other world'}
  event_object = windows_events.WindowsRegistryEvent(
      filetime.timestamp, u'//HKCU/Secret/EvilEmpire/Malicious_key',
      values_dict)
  event_object.hostname = hostname
  event_objects.append(event_object)

  filetime.CopyFromString(u'2012-04-20 16:44:46.000000')
  values_dict = {u'Value': u'run all the benign stuff'}
  event_object = windows_events.WindowsRegistryEvent(
      filetime.timestamp, u'//HKCU/Windows/Normal', values_dict)
  event_object.hostname = hostname
  event_objects.append(event_object)

  timestamp = timelib.Timestamp.CopyFromString(u'2012-04-30 10:29:47.929596')
  filename = u'c:/Temp/evil.exe'
  attributes = {
      u'text': u'This log line reads ohh so much.'}
  event_object = TestEvent(timestamp, attributes)
  event_object.filename = filename
  event_object.hostname = hostname

  event_objects.append(event_object)

  timestamp = timelib.Timestamp.CopyFromString(u'2012-04-30 10:29:47.929596')
  attributes = {
      u'text': u'Nothing of interest here, move on.'}
  event_object = TestEvent(timestamp, attributes)
  event_object.filename = filename
  event_object.hostname = hostname

  event_objects.append(event_object)

  timestamp = timelib.Timestamp.CopyFromString(u'2012-04-30 13:06:47.939596')
  attributes = {
      u'text': u'Mr. Evil just logged into the machine and got root.'}
  event_object = TestEvent(timestamp, attributes)
  event_object.filename = filename
  event_object.hostname = hostname

  event_objects.append(event_object)

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

  event_objects.append(event_object)

  return event_objects


class EventObjectTest(unittest.TestCase):
  """Tests for the event object."""

  def testSameEvent(self):
    """Test the EventObject comparison."""
    event_a = event.EventObject()
    event_b = event.EventObject()
    event_c = event.EventObject()
    event_d = event.EventObject()
    event_e = event.EventObject()

    event_a.timestamp = 123
    event_a.timestamp_desc = u'LAST WRITTEN'
    event_a.data_type = 'mock:nothing'
    event_a.inode = 124
    event_a.filename = u'c:/bull/skrytinmappa/skra.txt'
    event_a.another_attribute = False
    event_a.metadata = {
        u'author': u'Some Random Dude',
        u'version': 1245L,
        u'last_changed': u'Long time ago'}
    event_a.strings = [
        u'This ', u'is a ', u'long string']

    event_b.timestamp = 123
    event_b.timestamp_desc = 'LAST WRITTEN'
    event_b.data_type = 'mock:nothing'
    event_b.inode = 124
    event_b.filename = u'c:/bull/skrytinmappa/skra.txt'
    event_b.another_attribute = False
    event_b.metadata = {
        u'author': u'Some Random Dude',
        u'version': 1245L,
        u'last_changed': u'Long time ago'}
    event_b.strings = [
        u'This ', u'is a ', u'long string']

    event_c.timestamp = 123
    event_c.timestamp_desc = u'LAST UPDATED'
    event_c.data_type = 'mock:nothing'
    event_c.inode = 124
    event_c.filename = u'c:/bull/skrytinmappa/skra.txt'
    event_c.another_attribute = False

    event_d.timestamp = 14523
    event_d.timestamp_desc = u'LAST WRITTEN'
    event_d.data_type = 'mock:nothing'
    event_d.inode = 124
    event_d.filename = u'c:/bull/skrytinmappa/skra.txt'
    event_d.another_attribute = False

    event_e.timestamp = 123
    event_e.timestamp_desc = u'LAST WRITTEN'
    event_e.data_type = 'mock:nothing'
    event_e.inode = 623423
    event_e.filename = u'c:/afrit/onnurskra.txt'
    event_e.another_attribute = False
    event_e.metadata = {
        u'author': u'Some Random Dude',
        u'version': 1245,
        u'last_changed': u'Long time ago'}
    event_e.strings = [
        u'This ', u'is a ', u'long string']

    self.assertEqual(event_a, event_b)
    self.assertNotEqual(event_a, event_c)
    self.assertEqual(event_a, event_e)
    self.assertNotEqual(event_c, event_d)

  def testEqualityString(self):
    """Test the EventObject EqualityString."""
    event_a = event.EventObject()
    event_b = event.EventObject()
    event_c = event.EventObject()
    event_d = event.EventObject()
    event_e = event.EventObject()
    event_f = event.EventObject()

    event_a.timestamp = 123
    event_a.timestamp_desc = u'LAST WRITTEN'
    event_a.data_type = 'mock:nothing'
    event_a.inode = 124
    event_a.filename = u'c:/bull/skrytinmappa/skra.txt'
    event_a.another_attribute = False

    event_b.timestamp = 123
    event_b.timestamp_desc = u'LAST WRITTEN'
    event_b.data_type = 'mock:nothing'
    event_b.inode = 124
    event_b.filename = u'c:/bull/skrytinmappa/skra.txt'
    event_b.another_attribute = False

    event_c.timestamp = 123
    event_c.timestamp_desc = u'LAST UPDATED'
    event_c.data_type = 'mock:nothing'
    event_c.inode = 124
    event_c.filename = u'c:/bull/skrytinmappa/skra.txt'
    event_c.another_attribute = False

    event_d.timestamp = 14523
    event_d.timestamp_desc = u'LAST WRITTEN'
    event_d.data_type = 'mock:nothing'
    event_d.inode = 124
    event_d.filename = u'c:/bull/skrytinmappa/skra.txt'
    event_d.another_attribute = False

    event_e.timestamp = 123
    event_e.timestamp_desc = u'LAST WRITTEN'
    event_e.data_type = 'mock:nothing'
    event_e.inode = 623423
    event_e.filename = u'c:/afrit/öñṅûŗ₅ḱŖūα.txt'
    event_e.another_attribute = False

    event_f.timestamp = 14523
    event_f.timestamp_desc = u'LAST WRITTEN'
    event_f.data_type = 'mock:nothing'
    event_f.inode = 124
    event_f.filename = u'c:/bull/skrytinmappa/skra.txt'
    event_f.another_attribute = False
    event_f.weirdness = u'I am a potato'

    self.assertEqual(event_a.EqualityString(), event_b.EqualityString())
    self.assertNotEqual(event_a.EqualityString(), event_c.EqualityString())
    self.assertEqual(event_a.EqualityString(), event_e.EqualityString())
    self.assertNotEqual(event_c.EqualityString(), event_d.EqualityString())
    self.assertNotEqual(event_d.EqualityString(), event_f.EqualityString())

  def testEqualityFileStatParserMissingInode(self):
    """Test that FileStatParser files with missing inodes are distinct"""
    event_a = event.EventObject()
    event_b = event.EventObject()

    event_a.timestamp = 123
    event_a.timestamp_desc = u'LAST WRITTEN'
    event_a.data_type = 'mock:nothing'
    event_a.parser = u'filestat'
    event_a.filename = u'c:/bull/skrytinmappa/skra.txt'
    event_a.another_attribute = False

    event_b.timestamp = 123
    event_b.timestamp_desc = u'LAST WRITTEN'
    event_b.data_type = 'mock:nothing'
    event_b.parser = u'filestat'
    event_b.filename = u'c:/bull/skrytinmappa/skra.txt'
    event_b.another_attribute = False

    self.assertNotEqual(event_a, event_b)

  def testEqualityStringFileStatParserMissingInode(self):
    """Test that FileStatParser files with missing inodes are distinct"""
    event_a = event.EventObject()
    event_b = event.EventObject()

    event_a.timestamp = 123
    event_a.timestamp_desc = u'LAST WRITTEN'
    event_a.data_type = 'mock:nothing'
    event_a.parser = u'filestat'
    event_a.filename = u'c:/bull/skrytinmappa/skra.txt'
    event_a.another_attribute = False

    event_b.timestamp = 123
    event_b.timestamp_desc = u'LAST WRITTEN'
    event_b.data_type = 'mock:nothing'
    event_b.parser = u'filestat'
    event_b.filename = u'c:/bull/skrytinmappa/skra.txt'
    event_b.another_attribute = False

    self.assertNotEqual(event_a.EqualityString(), event_b.EqualityString())

  def testNotInEventAndNoParent(self):
    """Call to an attribute that does not exist."""
    event_object = TestEvent(0, {})

    with self.assertRaises(AttributeError):
      getattr(event_object, u'doesnotexist')

  def testFailEvent(self):
    """Calls to format_string_short that has not been defined."""
    e = FailEvent()

    with self.assertRaises(AttributeError):
      getattr(e, u'format_string_short')


if __name__ == '__main__':
  unittest.main()
