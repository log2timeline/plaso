#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for Twitter on Android database event formatter."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import twitter_android
from tests.formatters import test_lib


class TwitterAndroidStatusFormatterTest(test_lib.EventFormatterTestCase):
  """Tests the Twitter on Android status event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = twitter_android.TwitterAndroidStatusFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = twitter_android.TwitterAndroidStatusFormatter()

    expected_attribute_names = [
        'username',
        'content',
        'favorited',
        'retweeted'
    ]

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)


if __name__ == '__main__':
  unittest.main()
