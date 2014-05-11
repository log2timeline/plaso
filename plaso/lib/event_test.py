#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2012 The Plaso Project Authors.
# Please see the AUTHORS file for details on individual authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""This file contains a unit test for the EventObject.

This is an implementation of an unit test for EventObject storage mechanism for
plaso.

The test consists of creating six EventObjects.

Error handling. The following tests are performed for error handling:
 + Access attributes that are not set.
"""

import unittest

from plaso.lib import event


class TestEvent1(event.EventObject):
  """A test event object."""
  DATA_TYPE = 'test:event1'

  def __init__(self, timestamp, attributes):
    """Initializes the test event object."""
    super(TestEvent1, self).__init__()
    self.timestamp = timestamp
    self.timestamp_desc = 'Some time in the future'
    for attribute, value in attributes.iteritems():
      setattr(self, attribute, value)


class FailEvent(event.EventObject):
  """An test event object without the minimal required initialization."""


def GetEventObjects():
  """Returns a list of test event objects."""
  event_objects = []
  hostname = 'MYHOSTNAME'
  data_type = 'test:event1'

  event_a = event.EventObject()
  event_a.username = 'joesmith'
  event_a.filename = 'c:/Users/joesmith/NTUSER.DAT'
  event_a.hostname = hostname
  event_a.timestamp = 0
  event_a.data_type = data_type

  event_b = event.WinRegistryEvent(
      u'MY AutoRun key', {u'Run': u'c:/Temp/evil.exe'},
      timestamp=1334961526929596)
  event_b.hostname = hostname
  event_objects.append(event_b)

  event_c = event.WinRegistryEvent(
      u'//HKCU/Secret/EvilEmpire/Malicious_key',
      {u'Value': u'REGALERT: send all the exes to the other world'},
      timestamp=1334966206929596)
  event_c.hostname = hostname
  event_objects.append(event_c)

  event_d = event.WinRegistryEvent(
      u'//HKCU/Windows/Normal', {u'Value': u'run all the benign stuff'},
      timestamp=1334940286000000)
  event_d.hostname = hostname
  event_objects.append(event_d)

  event_objects.append(event_a)

  filename = 'c:/Temp/evil.exe'
  event_e = TestEvent1(1335781787929596, {
      'text': 'This log line reads ohh so much.'})
  event_e.filename = filename
  event_e.hostname = hostname

  event_objects.append(event_e)

  event_f = TestEvent1(1335781787929596, {
      'text': 'Nothing of interest here, move on.'})
  event_f.filename = filename
  event_f.hostname = hostname

  event_objects.append(event_f)

  event_g = TestEvent1(1335791207939596, {
      'text': 'Mr. Evil just logged into the machine and got root.'})
  event_g.filename = filename
  event_g.hostname = hostname

  event_objects.append(event_g)

  text_dict = {'body': (
      u'This is a line by someone not reading the log line properly. And '
      u'since this log line exceeds the accepted 80 chars it will be '
      u'shortened.'), 'hostname': u'nomachine', 'username': u'johndoe'}

  event_h = event.TextEvent(1338934459000000, text_dict)
  event_h.text = event_h.body
  event_h.hostname = hostname
  event_h.filename = filename

  event_objects.append(event_h)

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
    event_b.filename = 'c:/bull/skrytinmappa/skra.txt'
    event_b.another_attribute = False
    event_b.metadata = {
        'author': 'Some Random Dude',
        'version': 1245L,
        'last_changed': 'Long time ago'}
    event_b.strings = [
        'This ', 'is a ', 'long string']

    event_c.timestamp = 123
    event_c.timestamp_desc = 'LAST UPDATED'
    event_c.data_type = 'mock:nothing'
    event_c.inode = 124
    event_c.filename = 'c:/bull/skrytinmappa/skra.txt'
    event_c.another_attribute = False

    event_d.timestamp = 14523
    event_d.timestamp_desc = 'LAST WRITTEN'
    event_d.data_type = 'mock:nothing'
    event_d.inode = 124
    event_d.filename = 'c:/bull/skrytinmappa/skra.txt'
    event_d.another_attribute = False

    event_e.timestamp = 123
    event_e.timestamp_desc = 'LAST WRITTEN'
    event_e.data_type = 'mock:nothing'
    event_e.inode = 623423
    event_e.filename = 'c:/afrit/onnurskra.txt'
    event_e.another_attribute = False
    event_e.metadata = {
        'author': 'Some Random Dude',
        'version': 1245,
        'last_changed': 'Long time ago'}
    event_e.strings = [
        'This ', 'is a ', 'long string']

    self.assertEquals(event_a, event_b)
    self.assertNotEquals(event_a, event_c)
    self.assertEquals(event_a, event_e)
    self.assertNotEquals(event_c, event_d)

  def testEqualityString(self):
    """Test the EventObject EqualityString."""
    event_a = event.EventObject()
    event_b = event.EventObject()
    event_c = event.EventObject()
    event_d = event.EventObject()
    event_e = event.EventObject()
    event_f = event.EventObject()

    event_a.timestamp = 123
    event_a.timestamp_desc = 'LAST WRITTEN'
    event_a.data_type = 'mock:nothing'
    event_a.inode = 124
    event_a.filename = 'c:/bull/skrytinmappa/skra.txt'
    event_a.another_attribute = False

    event_b.timestamp = 123
    event_b.timestamp_desc = 'LAST WRITTEN'
    event_b.data_type = 'mock:nothing'
    event_b.inode = 124
    event_b.filename = 'c:/bull/skrytinmappa/skra.txt'
    event_b.another_attribute = False

    event_c.timestamp = 123
    event_c.timestamp_desc = 'LAST UPDATED'
    event_c.data_type = 'mock:nothing'
    event_c.inode = 124
    event_c.filename = 'c:/bull/skrytinmappa/skra.txt'
    event_c.another_attribute = False

    event_d.timestamp = 14523
    event_d.timestamp_desc = 'LAST WRITTEN'
    event_d.data_type = 'mock:nothing'
    event_d.inode = 124
    event_d.filename = 'c:/bull/skrytinmappa/skra.txt'
    event_d.another_attribute = False

    event_e.timestamp = 123
    event_e.timestamp_desc = 'LAST WRITTEN'
    event_e.data_type = 'mock:nothing'
    event_e.inode = 623423
    event_e.filename = 'c:/afrit/öñṅûŗ₅ḱŖūα.txt'
    event_e.another_attribute = False

    event_f.timestamp = 14523
    event_f.timestamp_desc = 'LAST WRITTEN'
    event_f.data_type = 'mock:nothing'
    event_f.inode = 124
    event_f.filename = 'c:/bull/skrytinmappa/skra.txt'
    event_f.another_attribute = False
    event_f.weirdness = 'I am a potato'

    self.assertEquals(event_a.EqualityString(), event_b.EqualityString())
    self.assertNotEquals(event_a.EqualityString(), event_c.EqualityString())
    self.assertEquals(event_a.EqualityString(), event_e.EqualityString())
    self.assertNotEquals(event_c.EqualityString(), event_d.EqualityString())
    self.assertNotEquals(event_d.EqualityString(), event_f.EqualityString())

  def testEqualityFileStatParserMissingInode(self):
    """Test that FileStatParser files with missing inodes are distinct"""
    event_a = event.EventObject()
    event_b = event.EventObject()

    event_a.timestamp = 123
    event_a.timestamp_desc = 'LAST WRITTEN'
    event_a.data_type = 'mock:nothing'
    event_a.parser = 'filestat'
    event_a.filename = 'c:/bull/skrytinmappa/skra.txt'
    event_a.another_attribute = False

    event_b.timestamp = 123
    event_b.timestamp_desc = 'LAST WRITTEN'
    event_b.data_type = 'mock:nothing'
    event_b.parser = 'filestat'
    event_b.filename = 'c:/bull/skrytinmappa/skra.txt'
    event_b.another_attribute = False

    self.assertNotEquals(event_a, event_b)

  def testEqualityStringFileStatParserMissingInode(self):
    """Test that FileStatParser files with missing inodes are distinct"""
    event_a = event.EventObject()
    event_b = event.EventObject()

    event_a.timestamp = 123
    event_a.timestamp_desc = 'LAST WRITTEN'
    event_a.data_type = 'mock:nothing'
    event_a.parser = 'filestat'
    event_a.filename = 'c:/bull/skrytinmappa/skra.txt'
    event_a.another_attribute = False

    event_b.timestamp = 123
    event_b.timestamp_desc = 'LAST WRITTEN'
    event_b.data_type = 'mock:nothing'
    event_b.parser = 'filestat'
    event_b.filename = 'c:/bull/skrytinmappa/skra.txt'
    event_b.another_attribute = False

    self.assertNotEquals(event_a.EqualityString(), event_b.EqualityString())

  def testNotInEventAndNoParent(self):
    """Call to an attribute that does not exist."""
    event_object = TestEvent1(0, {})

    with self.assertRaises(AttributeError):
      getattr(event_object, 'doesnotexist')

  def testFailEvent(self):
    """Calls to format_string_short that has not been defined."""
    e = FailEvent()

    with self.assertRaises(AttributeError):
      getattr(e, 'format_string_short')


if __name__ == '__main__':
  unittest.main()
