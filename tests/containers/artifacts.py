#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for the artifacts attribute containers."""

from __future__ import unicode_literals

import unittest

from plaso.containers import artifacts
from plaso.lib import definitions

from tests import test_lib as shared_test_lib


class EnvironmentVariableArtifactTest(shared_test_lib.BaseTestCase):
  """Tests for the environment variable artifact."""

  def testGetAttributeNames(self):
    """Tests the GetAttributeNames function."""
    attribute_container = artifacts.EnvironmentVariableArtifact()

    expected_attribute_names = ['case_sensitive', 'name', 'value']

    attribute_names = sorted(attribute_container.GetAttributeNames())
    self.assertEqual(attribute_names, expected_attribute_names)


class HostnameArtifactTest(shared_test_lib.BaseTestCase):
  """Tests for the hostname artifact."""

  def testGetAttributeNames(self):
    """Tests the GetAttributeNames function."""
    attribute_container = artifacts.HostnameArtifact()

    expected_attribute_names = ['name', 'schema']

    attribute_names = sorted(attribute_container.GetAttributeNames())
    self.assertEqual(attribute_names, expected_attribute_names)


class OperatingSystemArtifactTest(shared_test_lib.BaseTestCase):
  """Tests for the operating system artifact."""

  def testNormalizedProduct(self):
    """Tests the normalized_product property."""
    attribute_container = artifacts.OperatingSystemArtifact(
        product='Windows Server 2012 R2 Standard')

    self.assertEqual(attribute_container.normalized_product, 'Windows 2012')

  def testVersionTuple(self):
    """Tests the version_tuplele property."""
    attribute_container = artifacts.OperatingSystemArtifact(version="5.1")
    self.assertEqual(attribute_container.version_tuple, (5, 1))

    attribute_container = artifacts.OperatingSystemArtifact()
    self.assertIsNone(attribute_container.version_tuple)

    attribute_container = artifacts.OperatingSystemArtifact(version="5.a")
    self.assertIsNone(attribute_container.version_tuple)

  def testCompare(self):
    """Tests the Compare function."""
    attribute_container1 = artifacts.OperatingSystemArtifact(
        product='Windows 2012')
    attribute_container2 = artifacts.OperatingSystemArtifact(
        product='Windows XP')

    self.assertFalse(attribute_container1.Compare(attribute_container2))
    self.assertFalse(attribute_container2.Compare(attribute_container1))

    attribute_container1 = artifacts.OperatingSystemArtifact(
        name=definitions.OPERATING_SYSTEM_WINDOWS_NT, version='6.2')
    attribute_container2 = artifacts.OperatingSystemArtifact(
        name=definitions.OPERATING_SYSTEM_WINDOWS_NT, version='5.1')

    self.assertFalse(attribute_container1.Compare(attribute_container2))
    self.assertFalse(attribute_container2.Compare(attribute_container1))

    attribute_container1 = artifacts.OperatingSystemArtifact(
        name=definitions.OPERATING_SYSTEM_WINDOWS_9x)
    attribute_container2 = artifacts.OperatingSystemArtifact(
        name=definitions.OPERATING_SYSTEM_WINDOWS_NT)

    self.assertFalse(attribute_container1.Compare(attribute_container2))
    self.assertFalse(attribute_container2.Compare(attribute_container1))

    attribute_container1 = artifacts.OperatingSystemArtifact(
        name=definitions.OPERATING_SYSTEM_WINDOWS_NT, version='5.1')
    attribute_container2 = artifacts.OperatingSystemArtifact(
        product='Windows XP')

    self.assertTrue(attribute_container1.Compare(attribute_container2))
    self.assertTrue(attribute_container2.Compare(attribute_container1))

  def testGetAttributeNames(self):
    """Tests the GetAttributeNames function."""
    attribute_container = artifacts.OperatingSystemArtifact()

    expected_attribute_names = ['name', 'product', 'version']

    attribute_names = sorted(attribute_container.GetAttributeNames())
    self.assertEqual(attribute_names, expected_attribute_names)


class SystemConfigurationArtifactTest(shared_test_lib.BaseTestCase):
  """Tests for the system configuration artifact."""

  def testGetAttributeNames(self):
    """Tests the GetAttributeNames function."""
    attribute_container = artifacts.SystemConfigurationArtifact()

    expected_attribute_names = [
        'code_page', 'hostname', 'keyboard_layout', 'operating_system',
        'operating_system_product', 'operating_system_version', 'time_zone',
        'user_accounts']

    attribute_names = sorted(attribute_container.GetAttributeNames())
    self.assertEqual(attribute_names, expected_attribute_names)


class UserAccountArtifactTest(shared_test_lib.BaseTestCase):
  """Tests for the user account artifact."""

  def testGetAttributeNames(self):
    """Tests the GetAttributeNames function."""
    attribute_container = artifacts.UserAccountArtifact()

    expected_attribute_names = [
        'full_name', 'group_identifier', 'identifier', 'user_directory',
        'username']

    attribute_names = sorted(attribute_container.GetAttributeNames())
    self.assertEqual(attribute_names, expected_attribute_names)


if __name__ == '__main__':
  unittest.main()
