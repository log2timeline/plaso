#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Zeitgeist event formatter."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import zeitgeist

from tests.formatters import test_lib


class ZeitgeistFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the Zeitgeist activity database event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = zeitgeist.ZeitgeistFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = zeitgeist.ZeitgeistFormatter()

    expected_attribute_names = ['subject_uri']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
