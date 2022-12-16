#!/usr/bin/env python3
# -*_ coding: utf-8 -*-
"""Tests for the SCCM log text parser plugin."""

import unittest

from dfvfs.file_io import fake_file_io
from dfvfs.path import fake_path_spec
from dfvfs.resolver import context as dfvfs_context

from plaso.parsers import text_parser
from plaso.parsers.text_plugins import sccm

from tests.parsers.text_plugins import test_lib


class SCCMTextPluginTest(test_lib.TextPluginTestCase):
  """Tests for the SCCM log text parser plugin."""

  def testCheckRequiredFormat(self):
    """Tests for the CheckRequiredFormat method."""
    plugin = sccm.SCCMTextPlugin()

    resolver_context = dfvfs_context.Context()
    test_path_spec = fake_path_spec.FakePathSpec(location='/file.txt')

    file_object = fake_file_io.FakeFile(resolver_context, test_path_spec, (
        b'<![LOG[    A user is logged on to the system.]LOG]!>'
        b'<time="19:33:19.766-330" date="11-28-2014" component="AppEnforce" '
        b'context="" type="1" thread="8744" file="appprovider.cpp:2083">\n'))
    file_object.Open()

    text_reader = text_parser.EncodedTextReader(file_object)
    text_reader.ReadLines()

    result = plugin.CheckRequiredFormat(None, text_reader)
    self.assertTrue(result)

    file_object = fake_file_io.FakeFile(resolver_context, test_path_spec, (
        b'(Microsoft.SoftwareCenter.Client.Data.Widget at Thingamabob)]LOG]!>'
        b'<time="10:22:50.8422964" date="1-2-2015" component="SCClient" '
        b'context="" type="0" thread="16" file="">\n'))
    file_object.Open()

    text_reader = text_parser.EncodedTextReader(file_object)
    text_reader.ReadLines()

    result = plugin.CheckRequiredFormat(None, text_reader)
    self.assertFalse(result)

  def testProcess(self):
    """Tests the Process function."""
    plugin = sccm.SCCMTextPlugin()
    storage_writer = self._ParseTextFileWithPlugin(['sccm_various.log'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 10)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    # Test log entry with milliseconds precision and time zone offset.
    # time="19:33:19.766-330" date="11-28-2014"
    expected_event_values = {
        'component': 'AppEnforce',
        'data_type': 'sccm_log:entry',
        'text': ('+++ Starting Install enforcement for App DT "Application '
                 'Foo Version 2.2" ApplicationDeliveryType - ScopeId_AD87A846-'
                 'E6A5-4088-875F-066CF1082D30/DeploymentType_14a11199-ee14-'
                 '4c06-a5a7-68eadf501337, Revision - 10, ContentPath - '
                 'C:\\Windows\\ccmcache\\u, Execution Context - System'),
        'written_time': '2014-11-28T19:33:19.766-06:30'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)

    # Test log entry with 100ns precision and time zone offset.
    # time="10:22:50.8422964" date="1-2-2015"
    expected_event_values = {
        'component': 'SCClient',
        'data_type': 'sccm_log:entry',
        'written_time': '2015-01-02T10:22:50.873496+00:00'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 3)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
