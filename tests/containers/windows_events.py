#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Windows event data attribute containers."""

from __future__ import unicode_literals

import unittest
import uuid

from plaso.containers import windows_events

from tests import test_lib as shared_test_lib


class WindowsDistributedLinkTrackingEventDataTest(shared_test_lib.BaseTestCase):
  """Tests for the Windows distributed link event data attribute container."""

  def testGetAttributeNames(self):
    """Tests the GetAttributeNames function."""
    test_uuid = uuid.UUID(uuid.uuid1().hex)
    attribute_container = (
        windows_events.WindowsDistributedLinkTrackingEventData(test_uuid, None))

    expected_attribute_names = [
        'data_type', 'mac_address', 'offset', 'origin', 'query', 'uuid']

    attribute_names = sorted(attribute_container.GetAttributeNames())

    self.assertEqual(attribute_names, expected_attribute_names)


class WindowsRegistryInstallationEventDataTest(shared_test_lib.BaseTestCase):
  """Tests for the Windows installation event data attribute container."""

  def testGetAttributeNames(self):
    """Tests the GetAttributeNames function."""
    attribute_container = windows_events.WindowsRegistryInstallationEventData()

    expected_attribute_names = [
        'data_type', 'key_path', 'offset', 'owner', 'product_name',
        'query', 'service_pack', 'version']

    attribute_names = sorted(attribute_container.GetAttributeNames())

    self.assertEqual(attribute_names, expected_attribute_names)


class WindowsRegistryListEventDataTest(shared_test_lib.BaseTestCase):
  """Tests for the Windows Registry list event data attribute container."""

  def testGetAttributeNames(self):
    """Tests the GetAttributeNames function."""
    attribute_container = windows_events.WindowsRegistryListEventData()

    expected_attribute_names = [
        'data_type', 'key_path', 'known_folder_identifier', 'list_name',
        'list_values', 'offset', 'query', 'value_name']

    attribute_names = sorted(attribute_container.GetAttributeNames())

    self.assertEqual(attribute_names, expected_attribute_names)


class WindowsRegistryServiceEventDataTest(shared_test_lib.BaseTestCase):
  """Tests for the Windows Registry service event data attribute container."""

  def testGetAttributeNames(self):
    """Tests the GetAttributeNames function."""
    attribute_container = windows_events.WindowsRegistryServiceEventData()

    expected_attribute_names = [
        'data_type', 'key_path', 'offset', 'query', 'regvalue',
        'source_append', 'urls']

    attribute_names = sorted(attribute_container.GetAttributeNames())

    self.assertEqual(attribute_names, expected_attribute_names)


class WindowsVolumeEventDataTest(shared_test_lib.BaseTestCase):
  """Tests for the Windows volume event data attribute container."""

  def testGetAttributeNames(self):
    """Tests the GetAttributeNames function."""
    attribute_container = windows_events.WindowsVolumeEventData()

    expected_attribute_names = [
        'data_type', 'device_path', 'offset', 'origin', 'query',
        'serial_number']

    attribute_names = sorted(attribute_container.GetAttributeNames())

    self.assertEqual(attribute_names, expected_attribute_names)


if __name__ == '__main__':
  unittest.main()
