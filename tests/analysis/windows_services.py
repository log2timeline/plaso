#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the windows services analysis plugin."""

from __future__ import unicode_literals

import unittest

from dfvfs.path import fake_path_spec

from plaso.analysis import windows_services
from plaso.lib import definitions
from plaso.parsers import winreg

from tests.analysis import test_lib


class WindowsServicesTest(test_lib.AnalysisPluginTestCase):
  """Tests for the Windows Services analysis plugin."""

  _TEST_EVENTS = [
      {'data_type': 'windows:registry:service',
       'image_path': 'C:\\Dell\\testdriver.sys',
       'key_path': '\\ControlSet001\\services\\TestbDriver',
       'name': 'TestbDriver',
       'object_name': None,
       'pathspec': fake_path_spec.FakePathSpec(
           location='C:\\WINDOWS\\system32\\SYSTEM'),
       'service_dll': None,
       'service_type': 2,
       'start_type': 2,
       'timestamp': 1346145829002031,
       'timestamp_desc': definitions.TIME_DESCRIPTION_WRITTEN},
      # This is almost the same, but different timestamp and source, so that
      # we can test the service de-duplication.
      {'data_type': 'windows:registry:service',
       'image_path': 'C:\\Dell\\testdriver.sys',
       'key_path': '\\ControlSet003\\services\\TestbDriver',
       'name': 'TestbDriver',
       'object_name': None,
       'pathspec': fake_path_spec.FakePathSpec(
           location='C:\\WINDOWS\\system32\\SYSTEM'),
       'service_dll': None,
       'service_type': 2,
       'start_type': 2,
       'timestamp': 1346145839002031,
       'timestamp_desc': definitions.TIME_DESCRIPTION_WRITTEN}]

  def testExamineEventAndCompileReport(self):
    """Tests the ExamineEvent and CompileReport functions."""
    plugin = windows_services.WindowsServicesAnalysisPlugin()
    storage_writer = self._AnalyzeEvents(self._TEST_EVENTS, plugin)

    self.assertEqual(len(storage_writer.analysis_reports), 1)

    analysis_report = storage_writer.analysis_reports[0]

    expected_text = (
        'Listing Windows Services\n'
        'TestbDriver\n'
        '\tImage Path    = C:\\Dell\\testdriver.sys\n'
        '\tService Type  = File System Driver (0x2)\n'
        '\tStart Type    = Auto Start (2)\n'
        '\tService Dll   = \n'
        '\tObject Name   = \n'
        '\tSources:\n'
        '\t\tC:\\WINDOWS\\system32\\SYSTEM:'
        '\\ControlSet001\\services\\TestbDriver\n'
        '\t\tC:\\WINDOWS\\system32\\SYSTEM:'
        '\\ControlSet003\\services\\TestbDriver\n\n')

    self.assertEqual(expected_text, analysis_report.text)
    self.assertEqual(analysis_report.plugin_name, 'windows_services')

  def testExamineEventAndCompileReportOnSystemFile(self):
    """Tests the ExamineEvent and CompileReport functions on a SYSTEM file."""
    # We could remove the non-Services plugins, but testing shows that the
    # performance gain is negligible.

    parser = winreg.WinRegistryParser()
    plugin = windows_services.WindowsServicesAnalysisPlugin()

    storage_writer = self._ParseAndAnalyzeFile(['SYSTEM'], parser, plugin)

    self.assertEqual(storage_writer.number_of_events, 31436)

    self.assertEqual(len(storage_writer.analysis_reports), 1)

    analysis_report = storage_writer.analysis_reports[0]

    # We'll check that a few strings are in the report, like they're supposed
    # to be, rather than checking for the exact content of the string,
    # as that's dependent on the full path to the test files.
    test_strings = [
        '1394ohci',
        'WwanSvc',
        'Sources:',
        'ControlSet001',
        'ControlSet002']

    for string in test_strings:
      self.assertIn(string, analysis_report.text)

  def testExamineEventAndCompileReportOnSystemFileWithYAML(self):
    """Tests the ExamineEvent and CompileReport with YAML."""
    # We could remove the non-Services plugins, but testing shows that the
    # performance gain is negligible.

    parser = winreg.WinRegistryParser()
    plugin = windows_services.WindowsServicesAnalysisPlugin()
    plugin.SetOutputFormat('yaml')

    storage_writer = self._ParseAndAnalyzeFile(['SYSTEM'], parser, plugin)

    self.assertEqual(storage_writer.number_of_events, 31436)

    self.assertEqual(len(storage_writer.analysis_reports), 1)

    analysis_report = storage_writer.analysis_reports[0]

    # We'll check that a few strings are in the report, like they're supposed
    # to be, rather than checking for the exact content of the string,
    # as that's dependent on the full path to the test files.
    test_strings = [
        windows_services.WindowsService.yaml_tag,
        '1394ohci',
        'WwanSvc',
        'ControlSet001',
        'ControlSet002']

    for string in test_strings:
      self.assertIn(string, analysis_report.text)


if __name__ == '__main__':
  unittest.main()
