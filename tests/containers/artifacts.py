#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for the artifacts attribute containers."""

from __future__ import unicode_literals

import unittest

from plaso.containers import artifacts

from tests import test_lib as shared_test_lib


class EnvironmentVariableArtifactTest(shared_test_lib.BaseTestCase):
  """Tests for the environment variable artifact."""

  # TODO: replace by GetAttributeNames test
  def testCopyToDict(self):
    """Tests the CopyToDict function."""
    attribute_container = artifacts.EnvironmentVariableArtifact(
        case_sensitive=False, name='SystemRoot', value='C:\\Windows')

    self.assertEqual(attribute_container.name, 'SystemRoot')

    expected_dict = {
        'case_sensitive': False,
        'name': 'SystemRoot',
        'value': 'C:\\Windows'}

    test_dict = attribute_container.CopyToDict()

    self.assertEqual(test_dict, expected_dict)


class HostnameArtifactTest(shared_test_lib.BaseTestCase):
  """Tests for the hostname artifact."""

  # TODO: replace by GetAttributeNames test
  def testCopyToDict(self):
    """Tests the CopyToDict function."""
    attribute_container = artifacts.HostnameArtifact(name='mydomain.com')

    self.assertEqual(attribute_container.name, 'mydomain.com')

    expected_dict = {
        'name': 'mydomain.com',
        'schema': 'DNS'}

    test_dict = attribute_container.CopyToDict()

    self.assertEqual(test_dict, expected_dict)


class SystemConfigurationArtifactTest(shared_test_lib.BaseTestCase):
  """Tests for the system configuration artifact."""

  # TODO: replace by GetAttributeNames test
  def testCopyToDict(self):
    """Tests the CopyToDict function."""
    attribute_container = artifacts.SystemConfigurationArtifact(
        code_page='cp1252', time_zone='UTC')

    self.assertEqual(attribute_container.time_zone, 'UTC')

    expected_dict = {
        'code_page': 'cp1252',
        'time_zone': 'UTC',
        'user_accounts': []}

    test_dict = attribute_container.CopyToDict()

    self.assertEqual(test_dict, expected_dict)


class UserAccountArtifactTest(shared_test_lib.BaseTestCase):
  """Tests for the user account artifact."""

  # TODO: replace by GetAttributeNames test
  def testCopyToDict(self):
    """Tests the CopyToDict function."""
    attribute_container = artifacts.UserAccountArtifact(
        full_name='Full Name', group_identifier=1001, identifier=1000,
        user_directory='/home/username', username='username')

    self.assertEqual(attribute_container.username, 'username')

    expected_dict = {
        'full_name': 'Full Name',
        'group_identifier': 1001,
        'identifier': 1000,
        'user_directory': '/home/username',
        'username': 'username'}

    test_dict = attribute_container.CopyToDict()

    self.assertEqual(test_dict, expected_dict)


if __name__ == '__main__':
  unittest.main()
