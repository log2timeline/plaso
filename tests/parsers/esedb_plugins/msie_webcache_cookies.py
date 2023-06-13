#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Microsoft Internet Explorer WebCache database."""

import unittest

from plaso.parsers.esedb_plugins import msie_webcache_cookies

from tests.parsers.esedb_plugins import test_lib


class MsieWebCacheESEDBCookiePluginTest(test_lib.ESEDBPluginTestCase):
  """Tests for the MSIE WebCache ESE database cookie plugin."""

  # pylint: disable=protected-access


  def testProcessOnDatabaseWithCookiesExTable(self):
    """Tests the Process function on database with a PartitionsEx table."""
    plugin = msie_webcache_cookies.MSIE11CookiePlugin()
    storage_writer = self._ParseESEDBFileWithPlugin(
        ['WebCacheV01_cookies.dat'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 25)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
            "cookie_hash": "e8f278e06e2b0ae186e5a07d",
            "cookie_name": "SRCHHPGUSR",
            "cookie_value": "SRCHLANG=en",
            "cookie_value_raw": "535243484c414e473d656e00",
            "data_type": "msie:cookie:entry",
            "entry_identifier": 39,
            "flags": 525312,
            "inode": "-",
            "message": "(SRCHHPGUSR) Flags: 525312",
            "parser": "esedb/msie_webcache_cookies",
            "rdomain": "com.bing",
            }

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 10)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
