#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Mozilla Firefox history custom event formatter helpers."""

import unittest

from plaso.formatters import firefox

from tests.formatters import test_lib


class FirefoxHistoryTypedCountFormatterHelperTest(
    test_lib.EventFormatterTestCase):
  """Tests for the Mozilla Firefox history typed count formatter helper."""

  def testFormatEventValues(self):
    """Tests the FormatEventValues function."""
    formatter_helper = firefox.FirefoxHistoryTypedCountFormatterHelper()

    output_mediator = self._CreateOutputMediator()

    event_values = {'typed': '1'}
    formatter_helper.FormatEventValues(output_mediator, event_values)
    self.assertEqual(event_values['url_typed_string'], '(URL directly typed)')

    event_values = {'typed': None}
    formatter_helper.FormatEventValues(output_mediator, event_values)
    self.assertEqual(
        event_values['url_typed_string'], '(URL not typed directly)')


class FirefoxHistoryURLHiddenFormatterHelperTest(
    test_lib.EventFormatterTestCase):
  """Tests for the Mozilla Firefox history URL hidden formatter helper."""

  def testFormatEventValues(self):
    """Tests the FormatEventValues function."""
    formatter_helper = firefox.FirefoxHistoryURLHiddenFormatterHelper()

    output_mediator = self._CreateOutputMediator()

    event_values = {'hidden': '1'}
    formatter_helper.FormatEventValues(output_mediator, event_values)
    self.assertEqual(event_values['url_hidden_string'], '(URL hidden)')

    event_values = {'hidden': None}
    formatter_helper.FormatEventValues(output_mediator, event_values)
    self.assertNotIn('url_hidden_string', event_values)


if __name__ == '__main__':
  unittest.main()
