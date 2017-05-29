#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Windows event data attribute containers."""

import unittest
import uuid

from plaso.containers import windows_events

from tests import test_lib as shared_test_lib


class WindowsDistributedLinkTrackingEventDataTest(shared_test_lib.BaseTestCase):
  """Tests for the Windows distributed link event data attribute container."""

  def testGetAttributeNames(self):
    """Tests the GetAttributeNames function."""
    test_uuid = uuid.UUID(uuid.uuid1().get_hex())
    attribute_container = (
        windows_events.WindowsDistributedLinkTrackingEventData(test_uuid, None))

    expected_attribute_names = [
        u'data_type', u'mac_address', u'offset', u'origin', u'query', u'uuid']

    attribute_names = sorted(attribute_container.GetAttributeNames())

    self.assertEqual(attribute_names, expected_attribute_names)


class WindowsRegistryInstallationEventDataTest(shared_test_lib.BaseTestCase):
  """Tests for the Windows installation event data attribute container."""

  def testGetAttributeNames(self):
    """Tests the GetAttributeNames function."""
    attribute_container = windows_events.WindowsRegistryInstallationEventData()

    expected_attribute_names = [
        u'data_type', u'key_path', u'offset', u'owner', u'product_name',
        u'query', u'service_pack', u'version']

    attribute_names = sorted(attribute_container.GetAttributeNames())

    self.assertEqual(attribute_names, expected_attribute_names)


class WindowsRegistryListEventDataTest(shared_test_lib.BaseTestCase):
  """Tests for the Windows Registry list event data attribute container."""

  def testGetAttributeNames(self):
    """Tests the GetAttributeNames function."""
    attribute_container = windows_events.WindowsRegistryListEventData()

    expected_attribute_names = [
        u'data_type', u'key_path', u'list_name', u'list_values', u'offset',
        u'query', u'value_name']

    attribute_names = sorted(attribute_container.GetAttributeNames())

    self.assertEqual(attribute_names, expected_attribute_names)


class WindowsRegistryServiceEventDataTest(shared_test_lib.BaseTestCase):
  """Tests for the Windows Registry service event data attribute container."""

  def testGetAttributeNames(self):
    """Tests the GetAttributeNames function."""
    attribute_container = windows_events.WindowsRegistryServiceEventData()

    expected_attribute_names = [
        u'data_type', u'key_path', u'offset', u'query', u'regvalue',
        u'source_append', u'urls']

    attribute_names = sorted(attribute_container.GetAttributeNames())

    self.assertEqual(attribute_names, expected_attribute_names)


class WindowsVolumeEventDataTest(shared_test_lib.BaseTestCase):
  """Tests for the Windows volume event data attribute container."""

  def testGetAttributeNames(self):
    """Tests the GetAttributeNames function."""
    attribute_container = windows_events.WindowsVolumeEventData()

    expected_attribute_names = [
        u'data_type', u'device_path', u'offset', u'origin', u'query',
        u'serial_number']

    attribute_names = sorted(attribute_container.GetAttributeNames())

    self.assertEqual(attribute_names, expected_attribute_names)


if __name__ == '__main__':
  unittest.main()
