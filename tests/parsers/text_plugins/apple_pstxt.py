#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Apple ps.txt files text parser plugin."""

import unittest

from plaso.parsers.text_plugins import apple_pstxt

from tests.parsers.text_plugins import test_lib


class ApplePSTextPluginTest(test_lib.TextPluginTestCase):
  """Tests for the ApplePSTextPlugin parser plugin."""

  def testProcess(self):
    """Tests the Process function."""
    plugin = apple_pstxt.ApplePSTextPlugin()

    storage_writer = self._ParseCompressedTextFileWithPlugin(
        'test_data/text_parser/ps.txt.gz', plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 299)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
      'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'command': '/usr/libexec/UserEventAgent (System)',
        'control_terminal_name': '??',
        'cpu': '3.1',
        'flags': '4004004',
        'memory': '0.5',
        'nice_value': '0',
        'persona': '199',
        'process_identifier': '29',
        'parent_process_identifier': '1',
        'resident_set_size': '10208',
        'scheduling_priority': '37',
        'start_time': '2022-02-23T00:00:00+00:00',
        'symbolic_process_state': 'Ss',
        'up_time': '154:26.18',
        'user': 'root',
        'user_identifier': '0',
        'virtual_size': '407963424',
        'wait_channel': '-'
    }

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 1)
    self.CheckEventData(event_data, expected_event_values)

    expected_event_values = {
        'command': '/usr/libexec/findmydeviced',
        'control_terminal_name': '??',
        'cpu': '0.0',
        'flags': '4004004',
        'memory': '0.2',
        'nice_value': '0',
        'persona': '199',
        'process_identifier': '18988',
        'parent_process_identifier': '1',
        'resident_set_size': '3456',
        'scheduling_priority': '4',
        'start_time': '2022-04-08T11:00:00+00:00',
        'symbolic_process_state': 'Ss',
        'up_time': '0:11.52',
        'user': 'mobile',
        'user_identifier': '501',
        'virtual_size': '407957312',
        'wait_channel': '-'
    }

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 52)
    self.CheckEventData(event_data, expected_event_values)

    expected_event_values = {
        'command': ('/System/Library/PrivateFrameworks/'
                    'MediaAnalysis.framework/mediaanalysisd'),
        'control_terminal_name': '??',
        'cpu': '0.0',
        'flags': '4004004',
        'memory': '0.1',
        'nice_value': '0',
        'persona': '199',
        'process_identifier': '64983',
        'parent_process_identifier': '1',
        'resident_set_size': '1680',
        'scheduling_priority': '4',
        'start_time': '2022-04-13T06:21:00+00:00',
        'symbolic_process_state': 'Ss',
        'up_time': '0:00.18',
        'user': 'mobile',
        'user_identifier': '501',
        'virtual_size': '407952752',
        'wait_channel': '-'
    }

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 258)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
