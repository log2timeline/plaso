#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Google Chrome history custom event formatter helpers."""

import unittest

from plaso.formatters import chrome

from tests.formatters import test_lib


class ChromeHistoryTypedCountFormatterHelperTest(
    test_lib.EventFormatterTestCase):
  """Tests for the Google Chrome history typed count formatter helper."""

  def testFormatEventValues(self):
    """Tests the FormatEventValues function."""
    formatter_helper = chrome.ChromeHistoryTypedCountFormatterHelper()

    output_mediator = self._CreateOutputMediator()

    event_values = {'typed_count': 0}
    formatter_helper.FormatEventValues(output_mediator, event_values)
    self.assertEqual(
        event_values['url_typed_string'], '(URL not typed directly)')

    event_values = {'typed_count': 1}
    formatter_helper.FormatEventValues(output_mediator, event_values)
    self.assertEqual(
        event_values['url_typed_string'], '(URL typed 1 time)')

    event_values = {'typed_count': 3}
    formatter_helper.FormatEventValues(output_mediator, event_values)
    self.assertEqual(
        event_values['url_typed_string'], '(URL typed 3 times)')

    event_values = {'typed_count': -1}
    formatter_helper.FormatEventValues(output_mediator, event_values)
    self.assertEqual(event_values['url_typed_string'], -1)

    event_values = {'typed_count': None}
    formatter_helper.FormatEventValues(output_mediator, event_values)
    self.assertNotIn('url_typed_string', event_values)


if __name__ == '__main__':
  unittest.main()
