#!/usr/bin/python
# -*- coding: utf-8 -*-
"""This file contains the tests for the artifacts attribute containers."""

import unittest

from plaso.containers import artifacts

from tests import test_lib as shared_test_lib


class EnvironmentVariableArtifactTest(shared_test_lib.BaseTestCase):
  """Tests for the environment variable aritifact."""

  def testCopyToDict(self):
    """Tests the CopyToDict function."""
    evironment_variable = artifacts.EnvironmentVariableArtifact(
        case_sensitive=False, name=u'SystemRoot', value=u'C:\\Windows')

    self.assertEqual(evironment_variable.name, u'SystemRoot')

    expected_dict = {
        u'case_sensitive': False,
        u'name': u'SystemRoot',
        u'value': u'C:\\Windows'}

    evironment_variable_dict = evironment_variable.CopyToDict()

    self.assertEqual(evironment_variable_dict, expected_dict)

  # TODO: add more tests.


class HostnameArtifactTest(shared_test_lib.BaseTestCase):
  """Tests for the hostname aritifact."""

  def testCopyToDict(self):
    """Tests the CopyToDict function."""
    hostname = artifacts.HostnameArtifact(name=u'mydomain.com')

    self.assertEqual(hostname.name, u'mydomain.com')

    expected_dict = {
        u'name': u'mydomain.com',
        u'schema': u'DNS'}

    hostname_dict = hostname.CopyToDict()

    self.assertEqual(hostname_dict, expected_dict)

  # TODO: add more tests.


class SystemConfigurationArtifactTest(shared_test_lib.BaseTestCase):
  """Tests for the system configuration aritifact."""

  def testCopyToDict(self):
    """Tests the CopyToDict function."""
    system_configuration = artifacts.SystemConfigurationArtifact(
        code_page=u'cp1252', time_zone=u'UTC')

    self.assertEqual(system_configuration.time_zone, u'UTC')

    expected_dict = {
        u'code_page': u'cp1252',
        u'time_zone': u'UTC',
        u'user_accounts': []}

    system_configuration_dict = system_configuration.CopyToDict()

    self.assertEqual(system_configuration_dict, expected_dict)

  # TODO: add more tests.


class UserAccountArtifactTest(shared_test_lib.BaseTestCase):
  """Tests for the user account artifact."""

  def testCopyToDict(self):
    """Tests the CopyToDict function."""
    user_account = artifacts.UserAccountArtifact(
        full_name=u'Full Name', group_identifier=1001, identifier=1000,
        user_directory=u'/home/username', username=u'username')

    self.assertEqual(user_account.username, u'username')

    expected_dict = {
        u'full_name': u'Full Name',
        u'group_identifier': 1001,
        u'identifier': 1000,
        u'user_directory': u'/home/username',
        u'username': u'username'}

    user_account_dict = user_account.CopyToDict()

    self.assertEqual(user_account_dict, expected_dict)

  # TODO: add more tests.


if __name__ == '__main__':
  unittest.main()
