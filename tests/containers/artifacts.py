#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the artifacts attribute containers."""

import unittest

from plaso.containers import artifacts

from tests import test_lib as shared_test_lib


class EnvironmentVariableArtifactTest(shared_test_lib.BaseTestCase):
  """Tests for the environment variable aritifact."""

  # TODO: replace by GetAttributeNames test
  def testCopyToDict(self):
    """Tests the CopyToDict function."""
    attribute_container = artifacts.EnvironmentVariableArtifact(
        case_sensitive=False, name=u'SystemRoot', value=u'C:\\Windows')

    self.assertEqual(attribute_container.name, u'SystemRoot')

    expected_dict = {
        u'case_sensitive': False,
        u'name': u'SystemRoot',
        u'value': u'C:\\Windows'}

    test_dict = attribute_container.CopyToDict()

    self.assertEqual(test_dict, expected_dict)


class HostnameArtifactTest(shared_test_lib.BaseTestCase):
  """Tests for the hostname aritifact."""

  # TODO: replace by GetAttributeNames test
  def testCopyToDict(self):
    """Tests the CopyToDict function."""
    attribute_container = artifacts.HostnameArtifact(name=u'mydomain.com')

    self.assertEqual(attribute_container.name, u'mydomain.com')

    expected_dict = {
        u'name': u'mydomain.com',
        u'schema': u'DNS'}

    test_dict = attribute_container.CopyToDict()

    self.assertEqual(test_dict, expected_dict)


class SystemConfigurationArtifactTest(shared_test_lib.BaseTestCase):
  """Tests for the system configuration aritifact."""

  # TODO: replace by GetAttributeNames test
  def testCopyToDict(self):
    """Tests the CopyToDict function."""
    attribute_container = artifacts.SystemConfigurationArtifact(
        code_page=u'cp1252', time_zone=u'UTC')

    self.assertEqual(attribute_container.time_zone, u'UTC')

    expected_dict = {
        u'code_page': u'cp1252',
        u'time_zone': u'UTC',
        u'user_accounts': []}

    test_dict = attribute_container.CopyToDict()

    self.assertEqual(test_dict, expected_dict)


class UserAccountArtifactTest(shared_test_lib.BaseTestCase):
  """Tests for the user account artifact."""

  # TODO: replace by GetAttributeNames test
  def testCopyToDict(self):
    """Tests the CopyToDict function."""
    attribute_container = artifacts.UserAccountArtifact(
        full_name=u'Full Name', group_identifier=1001, identifier=1000,
        user_directory=u'/home/username', username=u'username')

    self.assertEqual(attribute_container.username, u'username')

    expected_dict = {
        u'full_name': u'Full Name',
        u'group_identifier': 1001,
        u'identifier': 1000,
        u'user_directory': u'/home/username',
        u'username': u'username'}

    test_dict = attribute_container.CopyToDict()

    self.assertEqual(test_dict, expected_dict)


if __name__ == '__main__':
  unittest.main()
