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
            "cookie_hash": "5b4342ed6e2b0ae16f7e2c4c",
            "cookie_name": "abid",
            "cookie_value": "fcc450d1-8674-1bd3-4074-a240cff5c5b1",
            "cookie_value_raw": "66636334353064312d383637342d316264332d343037342d61323430636666356335623100",
            "data_type": "msie:cookie:entry",
            "entry_identifier": 13,
            "flags": 2148017153,
            "rdomain": "com.associates-amazon",
             }




    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 10)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
