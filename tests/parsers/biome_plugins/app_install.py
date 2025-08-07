#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Apple biome file parser plugin for Application Launch."""

import unittest

from plaso.parsers.biome_plugins import app_install

from tests.parsers.biome_plugins import test_lib


class ApplicationInstallBiomePluginTest(test_lib.AppleBiomeTestCase):
  """Tests for the Application install Apple biome parser plugin."""

  def testProcess(self):
    """Tests the Process function."""
    plugin = app_install.ApplicationInstallBiomePlugin()
    storage_writer = self._ParseAppleBiomeFileWithPlugin(
        ['apple_biome', 'appInstall-segb'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 41)

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 2)

    self.assertEqual(
        event_data.action_guid, 'C1B7E595-401E-4331-A805-6D745F078B4C')
    self.assertEqual(event_data.action_name, '/app/install')
    self.assertEqual(
        event_data.application_name, None)
    self.assertEqual(event_data.bundle_identifier, 'com.apple.stocks')
    self.assertEqual(
        event_data.event_time.GetDateWithTimeOfDay(), (2024, 4, 3, 15, 6, 15))

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 31)

    self.assertEqual(
        event_data.action_guid, '790F0F66-3021-46CF-8440-086022E7E1E8')
    self.assertEqual(event_data.action_name, '/app/install')
    self.assertEqual(
        event_data.application_name, 'X')
    self.assertEqual(event_data.bundle_identifier, 'com.atebits.Tweetie2')
    self.assertEqual(
        event_data.event_time.GetDateWithTimeOfDay(), (2024, 4, 3, 15, 10, 55))


if __name__ == '__main__':
  unittest.main()
