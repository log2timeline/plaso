#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the MSIE cache file custom event formatter helpers."""

import unittest

from plaso.formatters import msiecf

from tests.formatters import test_lib


class MSIECFCachedPathFormatterHelperTest(test_lib.EventFormatterTestCase):
  """Tests for the MSIE cache file cached path formatter helper."""

  def testFormatEventValues(self):
    """Tests the FormatEventValues function."""
    formatter_helper = msiecf.MSIECFCachedPathFormatterHelper()

    output_mediator = self._CreateOutputMediator()

    event_values = {
        'cached_filename': 'file',
        'cache_directory_name': 'directory'}
    formatter_helper.FormatEventValues(output_mediator, event_values)
    self.assertEqual(event_values['cached_file_path'], 'directory\\file')

    event_values = {
        'cached_filename': 'file',
        'cache_directory_name': None}
    formatter_helper.FormatEventValues(output_mediator, event_values)
    self.assertEqual(event_values['cached_file_path'], 'file')

    event_values = {
        'cached_filename': None,
        'cache_directory_name': 'directory'}
    formatter_helper.FormatEventValues(output_mediator, event_values)
    self.assertNotIn('cached_file_path', event_values)


class MSIECFHTTPHeadersventFormatterHelperTest(test_lib.EventFormatterTestCase):
  """Tests for the MSIE cache file HTTP headers formatter helper."""

  def testFormatEventValues(self):
    """Tests the FormatEventValues function."""
    formatter_helper = msiecf.MSIECFHTTPHeadersventFormatterHelper()

    output_mediator = self._CreateOutputMediator()

    event_values = {'http_headers': 'header1\r\nheader2'}
    formatter_helper.FormatEventValues(output_mediator, event_values)
    self.assertEqual(event_values['http_headers'], 'header1 - header2')

    event_values = {'http_headers': None}
    formatter_helper.FormatEventValues(output_mediator, event_values)
    self.assertIsNone(event_values['http_headers'])


if __name__ == '__main__':
  unittest.main()
