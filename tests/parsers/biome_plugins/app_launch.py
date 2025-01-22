#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Apple biome file parser plugin for Application Launch."""

import unittest

from plaso.parsers.biome_plugins import app_launch

from tests.parsers.biome_plugins import test_lib


class ApplicationLaunchBiomePluginTest(test_lib.AppleBiomeTestCase):
  """Tests for the Application launch Apple biome parser plugin."""

  def testProcess(self):
    """Tests the Process function."""
    plugin = app_launch.ApplicationLaunchBiomePlugin()
    storage_writer = self._ParseAppleBiomeFileWithPlugin(
        ['apple_biome', 'applaunch-segb'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 85)

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)

    self.assertEqual(
        event_data.event_time.GetDateWithTimeOfDay(), (2024, 4, 3, 15, 4, 27))
    self.assertEqual(
        event_data.launcher,
        None)
    self.assertEqual(
        event_data.launched_application, 'com.apple.purplebuddy')

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 84)

    self.assertEqual(
        event_data.event_time.GetDateWithTimeOfDay(), (2024, 4, 17, 13, 27, 19))
    self.assertEqual(
        event_data.launcher,
        'com.apple.SpringBoard.backlight.transitionReason.idleTimer')
    self.assertEqual(
        event_data.launched_application, 'org.coolstar.SileoStore')




if __name__ == '__main__':
  unittest.main()
