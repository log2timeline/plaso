#!/usr/bin/python
# -*- coding: utf-8 -*-
"""This file contains the tests for the event attribute containers."""

import unittest

from plaso.containers import events

from tests import test_lib as shared_test_lib
from tests.containers import test_lib


class InvalidEvent(events.EventObject):
  """An event without the required initialization."""


class EventObjectTest(shared_test_lib.BaseTestCase):
  """Tests for the event attributes container."""

  def testCopyToDict(self):
    """Tests the CopyToDict function."""
    event = events.EventObject()
    event.timestamp = 123
    event.timestamp_desc = u'LAST WRITTEN'
    event.data_type = u'mock:nothing'
    event.inode = 124
    event.filename = u'c:/bull/skrytinmappa/skra.txt'
    event.another_attribute = False
    event.metadata = {
        u'author': u'Some Random Dude',
        u'version': 1245,
        u'last_changed': u'Long time ago'}
    event.strings = [u'This ', u'is a ', u'long string']

    expected_dict = {
        u'another_attribute': False,
        u'data_type': 'mock:nothing',
        u'filename': u'c:/bull/skrytinmappa/skra.txt',
        u'inode': 124,
        u'metadata': {
            u'author': u'Some Random Dude',
            u'last_changed': u'Long time ago',
            u'version': 1245},
        u'strings': [u'This ', u'is a ', u'long string'],
        u'timestamp': 123,
        u'timestamp_desc': u'LAST WRITTEN'}

    test_dict = event.CopyToDict()

    self.assertEqual(test_dict, expected_dict)

  def testNotInEventAndNoParent(self):
    """Call to an attribute that does not exist."""
    event = test_lib.TestEvent(0, {})

    with self.assertRaises(AttributeError):
      getattr(event, u'doesnotexist')

  def testInvalidEvent(self):
    """Calls to format_string_short that has not been defined."""
    event = InvalidEvent()

    with self.assertRaises(AttributeError):
      getattr(event, u'format_string_short')


class EventTagTest(shared_test_lib.BaseTestCase):
  """Tests for the event tag attributes container."""

  def testCopyToDict(self):
    """Tests the CopyToDict function."""
    event_tag = events.EventTag(
        comment=u'This is a test event tag.')

    expected_dict = {
        u'comment': u'This is a test event tag.',
        u'labels': []}

    test_dict = event_tag.CopyToDict()

    self.assertEqual(test_dict, expected_dict)

  # TODO: add more tests.


if __name__ == '__main__':
  unittest.main()
