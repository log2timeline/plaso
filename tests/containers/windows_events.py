#!/usr/bin/env python3
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
    test_uuid = uuid.UUID(uuid.uuid1().hex)
    attribute_container = (
        windows_events.WindowsDistributedLinkTrackingEventData(test_uuid, None))

    expected_attribute_names = [
        '_event_data_stream_identifier',
        '_event_values_hash',
        '_parser_chain',
        'creation_time',
        'data_type',
        'mac_address',
        'origin',
        'uuid']

    attribute_names = sorted(attribute_container.GetAttributeNames())

    self.assertEqual(attribute_names, expected_attribute_names)


class WindowsShellItemFileEntryEventDataTest(shared_test_lib.BaseTestCase):
  """Tests for the Windows shell item event attribute container."""

  def testGetAttributeNames(self):
    """Tests the GetAttributeNames function."""
    attribute_container = windows_events.WindowsShellItemFileEntryEventData()

    expected_attribute_names = [
        '_event_data_stream_identifier',
        '_event_values_hash',
        '_parser_chain',
        'access_time',
        'creation_time',
        'data_type',
        'file_reference',
        'localized_name',
        'long_name',
        'modification_time',
        'name',
        'origin',
        'shell_item_path']

    attribute_names = sorted(attribute_container.GetAttributeNames())

    self.assertEqual(attribute_names, expected_attribute_names)


class WindowsVolumeEventDataTest(shared_test_lib.BaseTestCase):
  """Tests for the Windows volume event data attribute container."""

  def testGetAttributeNames(self):
    """Tests the GetAttributeNames function."""
    attribute_container = windows_events.WindowsVolumeEventData()

    expected_attribute_names = [
        '_event_data_stream_identifier',
        '_event_values_hash',
        '_parser_chain',
        'creation_time',
        'data_type',
        'device_path',
        'origin',
        'serial_number']

    attribute_names = sorted(attribute_container.GetAttributeNames())

    self.assertEqual(attribute_names, expected_attribute_names)


if __name__ == '__main__':
  unittest.main()
