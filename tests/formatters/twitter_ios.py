#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for Twitter on iOS 8+ database event formatter."""

import unittest

from plaso.formatters import twitter_ios
from tests.formatters import test_lib


class TwitterIOSContactFormatterTest(test_lib.EventFormatterTestCase):
  """Tests the Twitter on iOS 8+ contact event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = twitter_ios.TwitterIOSContactFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = twitter_ios.TwitterIOSContactFormatter()

    expected_attribute_names = [
        u'screen_name',
        u'profile_url',
        u'name',
        u'location',
        u'description',
        u'url',
        u'following',
        u'followers_count',
        u'following_count',
    ]

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)


class TwitterIOSStatusFormatterTest(test_lib.EventFormatterTestCase):
  """Tests the Twitter on iOS 8+ status event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = twitter_ios.TwitterIOSStatusFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = twitter_ios.TwitterIOSStatusFormatter()

    expected_attribute_names = [
        u'text',
        u'user_id',
        u'name',
        u'retweet_count',
        u'favorite_count',
        u'favorited',
    ]

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)


if __name__ == '__main__':
  unittest.main()
