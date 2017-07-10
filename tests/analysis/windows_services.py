#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the windows services analysis plugin."""

import unittest

from dfdatetime import filetime as dfdatetime_filetime
from dfvfs.path import fake_path_spec

from plaso.analysis import windows_services
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.parsers import winreg

from tests import test_lib as shared_test_lib
from tests.analysis import test_lib


class WindowsServicesTest(test_lib.AnalysisPluginTestCase):
  """Tests for the Windows Services analysis plugin."""

  _TEST_EVENTS = [
      {u'key_path': u'\\ControlSet001\\services\\TestbDriver',
       u'regvalue': {u'ImagePath': u'C:\\Dell\\testdriver.sys', u'Type': 2,
                     u'Start': 2, u'ObjectName': u''},
       u'timestamp': 1346145829002031},
      # This is almost the same, but different timestamp and source, so that
      # we can test the service de-duplication.
      {u'key_path': u'\\ControlSet003\\services\\TestbDriver',
       u'regvalue': {u'ImagePath': u'C:\\Dell\\testdriver.sys', u'Type': 2,
                     u'Start': 2, u'ObjectName': u''},
       u'timestamp': 1346145839002031},
  ]

  def _CreateTestEventObject(self, event_dictionary):
    """Create a test event with a set of attributes.

    Args:
      event_dictionary (dict[str, str]): contains attributes of an event to add
          to the queue.

    Returns:
      EventObject: event with the appropriate attributes for testing.
    """
    date_time = dfdatetime_filetime.Filetime(
        timestamp=event_dictionary[u'timestamp'])
    event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_WRITTEN)
    event.data_type = u'windows:registry:service'

    for attribute_name, attribute_value in event_dictionary.items():
      setattr(event, attribute_name, attribute_value)

    return event

  def testExamineEventAndCompileReport(self):
    """Tests the ExamineEvent and CompileReport functions."""
    events = []
    for event_dictionary in self._TEST_EVENTS:
      event_dictionary[u'pathspec'] = fake_path_spec.FakePathSpec(
          location=u'C:\\WINDOWS\\system32\\SYSTEM')

      event = self._CreateTestEventObject(event_dictionary)
      events.append(event)

    plugin = windows_services.WindowsServicesAnalysisPlugin()
    storage_writer = self._AnalyzeEvents(events, plugin)

    self.assertEqual(len(storage_writer.analysis_reports), 1)

    analysis_report = storage_writer.analysis_reports[0]

    expected_text = (
        u'Listing Windows Services\n'
        u'TestbDriver\n'
        u'\tImage Path    = C:\\Dell\\testdriver.sys\n'
        u'\tService Type  = File System Driver (0x2)\n'
        u'\tStart Type    = Auto Start (2)\n'
        u'\tService Dll   = \n'
        u'\tObject Name   = \n'
        u'\tSources:\n'
        u'\t\tC:\\WINDOWS\\system32\\SYSTEM:'
        u'\\ControlSet001\\services\\TestbDriver\n'
        u'\t\tC:\\WINDOWS\\system32\\SYSTEM:'
        u'\\ControlSet003\\services\\TestbDriver\n\n')

    self.assertEqual(expected_text, analysis_report.text)
    self.assertEqual(analysis_report.plugin_name, 'windows_services')

  @shared_test_lib.skipUnlessHasTestFile([u'SYSTEM'])
  def testExamineEventAndCompileReportOnSystemFile(self):
    """Tests the ExamineEvent and CompileReport functions on a SYSTEM file."""
    # We could remove the non-Services plugins, but testing shows that the
    # performance gain is negligible.

    parser = winreg.WinRegistryParser()
    plugin = windows_services.WindowsServicesAnalysisPlugin()

    storage_writer = self._ParseAndAnalyzeFile([u'SYSTEM'], parser, plugin)

    self.assertEqual(storage_writer.number_of_events, 31436)

    self.assertEqual(len(storage_writer.analysis_reports), 1)

    analysis_report = storage_writer.analysis_reports[0]

    # We'll check that a few strings are in the report, like they're supposed
    # to be, rather than checking for the exact content of the string,
    # as that's dependent on the full path to the test files.
    test_strings = [
        u'1394ohci',
        u'WwanSvc',
        u'Sources:',
        u'ControlSet001',
        u'ControlSet002']

    for string in test_strings:
      self.assertIn(string, analysis_report.text)

  @shared_test_lib.skipUnlessHasTestFile([u'SYSTEM'])
  def testExamineEventAndCompileReportOnSystemFileWithYAML(self):
    """Tests the ExamineEvent and CompileReport with YAML."""
    # We could remove the non-Services plugins, but testing shows that the
    # performance gain is negligible.

    parser = winreg.WinRegistryParser()
    plugin = windows_services.WindowsServicesAnalysisPlugin()
    plugin.SetOutputFormat(u'yaml')

    storage_writer = self._ParseAndAnalyzeFile([u'SYSTEM'], parser, plugin)

    self.assertEqual(storage_writer.number_of_events, 31436)

    self.assertEqual(len(storage_writer.analysis_reports), 1)

    analysis_report = storage_writer.analysis_reports[0]

    # We'll check that a few strings are in the report, like they're supposed
    # to be, rather than checking for the exact content of the string,
    # as that's dependent on the full path to the test files.
    test_strings = [
        windows_services.WindowsService.yaml_tag,
        u'1394ohci',
        u'WwanSvc',
        u'ControlSet001',
        u'ControlSet002']

    for string in test_strings:
      self.assertIn(string, analysis_report.text)


if __name__ == '__main__':
  unittest.main()
