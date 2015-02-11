#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the windows services analysis plugin."""

import argparse
import unittest

from dfvfs.path import fake_path_spec

from plaso.analysis import test_lib
from plaso.analysis import windows_services
from plaso.engine import queue
from plaso.engine import single_process
from plaso.events import windows_events
from plaso.parsers import winreg


class WindowsServicesTest(test_lib.AnalysisPluginTestCase):
  """Tests for the Windows Services analysis plugin."""

  SERVICE_EVENTS = [
      {u'path': u'\\ControlSet001\\services\\TestbDriver',
       u'text_dict': {u'ImagePath': u'C:\\Dell\\testdriver.sys', u'Type': 2,
                      u'Start': 2, u'ObjectName': u''},
       u'timestamp': 1346145829002031},
      # This is almost the same, but different timestamp and source, so that
      # we can test the service de-duplication.
      {u'path': u'\\ControlSet003\\services\\TestbDriver',
       u'text_dict': {u'ImagePath': u'C:\\Dell\\testdriver.sys', u'Type': 2,
                      u'Start': 2, u'ObjectName': u''},
       u'timestamp': 1346145839002031},
  ]

  def _CreateAnalysisPlugin(self, input_queue, output_mode):
    """Create an analysis plugin to test with.

    Args:
      input_queue: A queue the plugin will read events from.
      output_mode: The output format the plugin will use.
          Valid options are 'text' and 'yaml'.

    Returns:
      An instance of AnalyzeWindowsServicesPlugin.
    """
    argument_parser = argparse.ArgumentParser()
    plugin_args = windows_services.AnalyzeWindowsServicesPlugin.ARGUMENTS
    for parameter, config in plugin_args:
      argument_parser.add_argument(parameter, **config)
    arguments = ['--windows-services-output', output_mode]
    options = argument_parser.parse_args(arguments)
    analysis_plugin = windows_services.AnalyzeWindowsServicesPlugin(
        input_queue, options)
    return analysis_plugin


  def _CreateTestEventObject(self, service_event):
    """Create a test event object with a particular path.

    Args:
      service_event: A hash containing attributes of an event to add to the
                     queue.

    Returns:
      An EventObject representing the service to be created.
    """
    test_pathspec = fake_path_spec.FakePathSpec(
        location=u'C:\\WINDOWS\\system32\\SYSTEM')
    event_object = windows_events.WindowsRegistryServiceEvent(
        service_event[u'timestamp'], service_event[u'path'],
        service_event[u'text_dict'])
    event_object.pathspec = test_pathspec
    return event_object

  def testSyntheticKeysText(self):
    """Test the plugin against mock events."""
    event_queue = single_process.SingleProcessQueue()

    # Fill the incoming queue with events.
    test_queue_producer = queue.ItemQueueProducer(event_queue)
    events = [self._CreateTestEventObject(service_event)
              for service_event
              in self.SERVICE_EVENTS]
    test_queue_producer.ProduceItems(events)
    test_queue_producer.SignalEndOfInput()

    # Initialize plugin.
    analysis_plugin = self._CreateAnalysisPlugin(event_queue, u'text')

    # Run the analysis plugin.
    knowledge_base = self._SetUpKnowledgeBase()
    analysis_report_queue_consumer = self._RunAnalysisPlugin(
        analysis_plugin, knowledge_base)
    analysis_reports = self._GetAnalysisReportsFromQueue(
        analysis_report_queue_consumer)

    self.assertEquals(len(analysis_reports), 1)

    analysis_report = analysis_reports[0]

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

    self.assertEquals(expected_text, analysis_report.text)
    self.assertEquals(analysis_report.plugin_name, 'windows_services')

  def testRealEvents(self):
    """Test the plugin with text output against real events from the parser."""
    parser = winreg.WinRegistryParser()
    # We could remove the non-Services plugins, but testing shows that the
    # performance gain is negligible.

    knowledge_base = self._SetUpKnowledgeBase()
    test_path = self._GetTestFilePath(['SYSTEM'])
    event_queue = self._ParseFile(parser, test_path, knowledge_base)

    # Run the analysis plugin.
    analysis_plugin = self._CreateAnalysisPlugin(event_queue, u'text')
    analysis_report_queue_consumer = self._RunAnalysisPlugin(
        analysis_plugin, knowledge_base)
    analysis_reports = self._GetAnalysisReportsFromQueue(
        analysis_report_queue_consumer)

    report = analysis_reports[0]
    text = report.text

    # We'll check that a few strings are in the report, like they're supposed
    # to be, rather than checking for the exact content of the string,
    # as that's dependent on the full path to the test files.
    test_strings = [u'1394ohci', u'WwanSvc', u'Sources:', u'ControlSet001',
                    u'ControlSet002']
    for string in test_strings:
      self.assertTrue(string in text)

  def testRealEventsYAML(self):
    """Test the plugin with YAML output against real events from the parser."""
    parser = winreg.WinRegistryParser()
    # We could remove the non-Services plugins, but testing shows that the
    # performance gain is negligible.

    knowledge_base = self._SetUpKnowledgeBase()
    test_path = self._GetTestFilePath(['SYSTEM'])
    event_queue = self._ParseFile(parser, test_path, knowledge_base)

    # Run the analysis plugin.
    analysis_plugin = self._CreateAnalysisPlugin(event_queue, 'yaml')
    analysis_report_queue_consumer = self._RunAnalysisPlugin(
        analysis_plugin, knowledge_base)
    analysis_reports = self._GetAnalysisReportsFromQueue(
        analysis_report_queue_consumer)

    report = analysis_reports[0]
    text = report.text

    # We'll check that a few strings are in the report, like they're supposed
    # to be, rather than checking for the exact content of the string,
    # as that's dependent on the full path to the test files.
    test_strings = [windows_services.WindowsService.yaml_tag, u'1394ohci',
                    u'WwanSvc', u'ControlSet001', u'ControlSet002']

    for string in test_strings:
      self.assertTrue(string in text, u'{0:s} not found in report text'.format(
          string))


if __name__ == '__main__':
  unittest.main()
