#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Zeitgeist event formatter."""

import unittest

from plaso.formatters import zeitgeist

from tests.formatters import test_lib


class ZeitgeistFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the Zeitgeist activity database event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = zeitgeist.ZeitgeistFormatter()
    self.assertNotEqual(event_formatter, None)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = zeitgeist.ZeitgeistFormatter()

    expected_attribute_names = [u'subject_uri']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
