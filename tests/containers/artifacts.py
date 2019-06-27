#!/usr/bin/env python3
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

  # pylint: disable=protected-access

  def testVersionTuple(self):
    """Tests the version_tuplele property."""
    attribute_container = artifacts.OperatingSystemArtifact(version="5.1")
    self.assertEqual(attribute_container.version_tuple, (5, 1))

    attribute_container = artifacts.OperatingSystemArtifact()
    self.assertIsNone(attribute_container.version_tuple)

    attribute_container = artifacts.OperatingSystemArtifact(version="5.a")
    self.assertIsNone(attribute_container.version_tuple)

  def testGetNameFromProduct(self):
    """Tests the _GetNameFromProduct function."""
    attribute_container = artifacts.OperatingSystemArtifact(
        product='Windows Server 2012 R2 Standard')

    name = attribute_container._GetNameFromProduct()
    self.assertEqual(name, 'Windows 2012 R2')

    attribute_container = artifacts.OperatingSystemArtifact(
        product='Microsoft Windows Server 2003')

    name = attribute_container._GetNameFromProduct()
    self.assertEqual(name, 'Windows 2003')

  def testIsEquivalent(self):
    """Tests the IsEquivalent function."""
    win2k12_container = artifacts.OperatingSystemArtifact(
        product='Windows 2012')
    winxp_container = artifacts.OperatingSystemArtifact(product='Windows XP')

    self.assertFalse(win2k12_container.IsEquivalent(winxp_container))
    self.assertFalse(winxp_container.IsEquivalent(win2k12_container))

    winnt62_container = artifacts.OperatingSystemArtifact(
        family=definitions.OPERATING_SYSTEM_FAMILY_WINDOWS_NT, version='6.2')
    winnt51_container = artifacts.OperatingSystemArtifact(
        family=definitions.OPERATING_SYSTEM_FAMILY_WINDOWS_NT, version='5.1')

    self.assertFalse(winnt62_container.IsEquivalent(winnt51_container))
    self.assertFalse(winnt51_container.IsEquivalent(winnt62_container))

    win9x_container = artifacts.OperatingSystemArtifact(
        family=definitions.OPERATING_SYSTEM_FAMILY_WINDOWS_9x)
    winnt_container = artifacts.OperatingSystemArtifact(
        family=definitions.OPERATING_SYSTEM_FAMILY_WINDOWS_NT)

    self.assertFalse(win9x_container.IsEquivalent(winnt_container))
    self.assertFalse(winnt_container.IsEquivalent(win9x_container))

    winnt51_container = artifacts.OperatingSystemArtifact(
        family=definitions.OPERATING_SYSTEM_FAMILY_WINDOWS_NT, version='5.1')
    winxp_container = artifacts.OperatingSystemArtifact(product='Windows XP')

    self.assertTrue(winnt51_container.IsEquivalent(winxp_container))
    self.assertTrue(winxp_container.IsEquivalent(winnt51_container))

  def testGetAttributeNames(self):
    """Tests the GetAttributeNames function."""
    attribute_container = artifacts.OperatingSystemArtifact()

    expected_attribute_names = ['family', 'name', 'product', 'version']

    attribute_names = sorted(attribute_container.GetAttributeNames())
    self.assertEqual(attribute_names, expected_attribute_names)


class SystemConfigurationArtifactTest(shared_test_lib.BaseTestCase):
  """Tests for the system configuration artifact."""

  def testGetAttributeNames(self):
    """Tests the GetAttributeNames function."""
    attribute_container = artifacts.SystemConfigurationArtifact()

    expected_attribute_names = [
        'available_time_zones', 'code_page', 'hostname', 'keyboard_layout',
        'operating_system', 'operating_system_product',
        'operating_system_version', 'time_zone', 'user_accounts']

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
