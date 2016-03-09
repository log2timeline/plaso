#!/usr/bin/python
# -*- coding: utf-8 -*-
"""This file contains the tests for the event attribute container objects."""

import unittest

from plaso.containers import events

from tests.containers import test_lib


class InvalidEventObject(events.EventObject):
  """An event object without the required initialization."""


class EventObjectTest(test_lib.AttributeContainerTestCase):
  """Tests for the event attributes container object."""

  def testCopyToDict(self):
    """Tests the CopyToDict function."""
    event = events.EventObject()
    event.timestamp = 123
    event.timestamp_desc = u'LAST WRITTEN'
    event.data_type = 'mock:nothing'
    event.inode = 124
    event.filename = u'c:/bull/skrytinmappa/skra.txt'
    event.another_attribute = False
    event.metadata = {
        u'author': u'Some Random Dude',
        u'version': 1245L,
        u'last_changed': u'Long time ago'}
    event.strings = [u'This ', u'is a ', u'long string']
    event.uuid = u'11fca043ea224a688137deaa8d162807'

    expected_dict = {
        u'another_attribute': False,
        u'data_type': 'mock:nothing',
        u'filename': u'c:/bull/skrytinmappa/skra.txt',
        u'inode': 124,
        u'metadata': {
            u'author': u'Some Random Dude',
            u'last_changed': u'Long time ago',
            u'version': 1245L},
        u'strings': [u'This ', u'is a ', u'long string'],
        u'timestamp': 123,
        u'timestamp_desc': u'LAST WRITTEN',
        u'uuid': u'11fca043ea224a688137deaa8d162807'}

    test_dict = event.CopyToDict()

    self.assertEqual(test_dict, expected_dict)

  def testSameEvent(self):
    """Test the EventObject comparison."""
    event_a = events.EventObject()
    event_b = events.EventObject()
    event_c = events.EventObject()
    event_d = events.EventObject()
    event_e = events.EventObject()

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
    event_a = events.EventObject()
    event_b = events.EventObject()
    event_c = events.EventObject()
    event_d = events.EventObject()
    event_e = events.EventObject()
    event_f = events.EventObject()

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
    event_a = events.EventObject()
    event_b = events.EventObject()

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
    event_a = events.EventObject()
    event_b = events.EventObject()

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
    event_object = test_lib.TestEvent(0, {})

    with self.assertRaises(AttributeError):
      getattr(event_object, u'doesnotexist')

  def testInvalidEventObject(self):
    """Calls to format_string_short that has not been defined."""
    event_object = InvalidEventObject()

    with self.assertRaises(AttributeError):
      getattr(event_object, u'format_string_short')


class EventTagTest(test_lib.AttributeContainerTestCase):
  """Tests for the event tag attributes container object."""

  def testCopyToDict(self):
    """Tests the CopyToDict function."""
    event_tag = events.EventTag(
        comment=u'This is a test event tag.',
        event_uuid=u'11fca043ea224a688137deaa8d162807')

    expected_dict = {
        u'comment': u'This is a test event tag.',
        u'event_uuid': u'11fca043ea224a688137deaa8d162807',
        u'labels': []}

    test_dict = event_tag.CopyToDict()

    self.assertEqual(test_dict, expected_dict)

  # TODO: add more tests.


if __name__ == '__main__':
  unittest.main()
