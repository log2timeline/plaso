#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for Twitter on iOS 8+ database event formatter."""

import unittest

from plaso.formatters import twitter_ios
from tests.formatters import test_lib


class TwitterContactCreationFormatterTest(test_lib.EventFormatterTestCase):
  """Test for the Twitter contacts creation event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = (twitter_ios.TwitterIOSContactCreationFormatter())
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = (twitter_ios.TwitterIOSContactCreationFormatter())

    expected_attribute_names = [
        u'screen_name',
        u'profile_url',
        u'name',
        u'location',
        u'description',
        u'url',
        u'following',
        u'followers_cnt',
        u'following_cnt',
    ]

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)


class TwitterContactUpdateFormatterTest(test_lib.EventFormatterTestCase):
  """Test for the Twitter contacts update event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = (twitter_ios.TwitterIOSContactUpdateFormatter())
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = (twitter_ios.TwitterIOSContactUpdateFormatter())

    expected_attribute_names = [
        u'screen_name',
        u'profile_url',
        u'name',
        u'location',
        u'description',
        u'url',
        u'following',
        u'followers_cnt',
        u'following_cnt',
    ]

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)


class TwitterStatusCreationFormatterTest(test_lib.EventFormatterTestCase):
  """Test for the Twitter contacts update event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = (twitter_ios.TwitterIOSStatusCreationFormatter())
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = (twitter_ios.TwitterIOSStatusCreationFormatter())

    expected_attribute_names = [
        u'text',
        u'user_id',
        u'name',
        u'retweet_cnt',
        u'favorite_cnt',
        u'favorited',
    ]

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)


class TwitterStatusUpdateFormatterTest(test_lib.EventFormatterTestCase):
  """Test for the Twitter contacts update event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = (twitter_ios.TwitterIOSStatusUpdateFormatter())
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = (twitter_ios.TwitterIOSStatusUpdateFormatter())

    expected_attribute_names = [
        u'text',
        u'user_id',
        u'name',
        u'retweet_cnt',
        u'favorite_cnt',
        u'favorited',
    ]

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)


if __name__ == '__main__':
  unittest.main()
