#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the knowledge base."""

import unittest

from plaso.containers import artifacts
from plaso.engine import knowledge_base

from tests import test_lib as shared_test_lib


class KnowledgeBaseTest(shared_test_lib.BaseTestCase):
  """Tests for the knowledge base."""

  _MACOSX_PATHS = [
      u'/Users/dude/Library/Application Data/Google/Chrome/Default/Extensions',
      (u'/Users/dude/Library/Application Data/Google/Chrome/Default/Extensions/'
       u'apdfllckaahabafndbhieahigkjlhalf'),
      u'/private/var/log/system.log',
      u'/Users/frank/Library/Application Data/Google/Chrome/Default',
      u'/Users/hans/Library/Application Data/Google/Chrome/Default',
      (u'/Users/frank/Library/Application Data/Google/Chrome/Default/'
       u'Extensions/pjkljhegncpnkpknbcohdijeoejaedia'),
      u'/Users/frank/Library/Application Data/Google/Chrome/Default/Extensions']

  _MACOSX_USERS = [
      {u'name': u'root', u'path': u'/var/root', u'sid': u'0'},
      {u'name': u'frank', u'path': u'/Users/frank', u'sid': u'4052'},
      {u'name': u'hans', u'path': u'/Users/hans', u'sid': u'4352'},
      {u'name': u'dude', u'path': u'/Users/dude', u'sid': u'1123'}]

  _WINDOWS_PATHS = [
      u'C:\\Users\\Dude\\SomeFolder\\Chrome\\Default\\Extensions',
      (u'C:\\Users\\Dude\\SomeNoneStandardFolder\\Chrome\\Default\\Extensions\\'
       u'hmjkmjkepdijhoojdojkdfohbdgmmhki'),
      (u'C:\\Users\\frank\\AppData\\Local\\Google\\Chrome\\Extensions\\'
       u'blpcfgokakmgnkcojhhkbfbldkacnbeo'),
      u'C:\\Users\\frank\\AppData\\Local\\Google\\Chrome\\Extensions',
      (u'C:\\Users\\frank\\AppData\\Local\\Google\\Chrome\\Extensions\\'
       u'icppfcnhkcmnfdhfhphakoifcfokfdhg'),
      u'C:\\Windows\\System32',
      u'C:\\Stuff/with path separator\\Folder']

  _WINDOWS_USERS = [
      {u'name': u'dude', u'path': u'C:\\Users\\dude', u'sid': u'S-1'},
      {u'name': u'frank', u'path': u'C:\\Users\\frank', u'sid': u'S-2'}]

  def _SetUserAccounts(self, knowledge_base_object, users):
    """Sets the user accounts in the knowledge base.

    Args:
      knowledge_base_object (KnowledgeBase): knowledge base.
      users (list[dict[str,str])): users.
    """
    for user in users:
      identifier = user.get(u'sid', user.get(u'uid', None))
      if not identifier:
        continue

      user_account = artifacts.UserAccountArtifact(
          identifier=identifier, user_directory=user.get(u'path', None),
          username=user.get(u'name', None))

      knowledge_base_object.AddUserAccount(user_account)

  def testCodepageProperty(self):
    """Tests the codepage property."""
    knowledge_base_object = knowledge_base.KnowledgeBase()

    self.assertEqual(knowledge_base_object.codepage, u'cp1252')

  def testHostnameProperty(self):
    """Tests the hostname property."""
    knowledge_base_object = knowledge_base.KnowledgeBase()

    self.assertEqual(knowledge_base_object.hostname, u'')

  def testPlatformProperty(self):
    """Tests the platform property."""
    knowledge_base_object = knowledge_base.KnowledgeBase()

    self.assertEqual(knowledge_base_object.platform, u'')

    knowledge_base_object.platform = u'Windows'

    self.assertEqual(knowledge_base_object.platform, u'Windows')

  def testTimezoneProperty(self):
    """Tests the timezone property."""
    knowledge_base_object = knowledge_base.KnowledgeBase()

    self.assertEqual(knowledge_base_object.timezone.zone, u'UTC')

  def testUserAccountsProperty(self):
    """Tests the user accounts property."""
    knowledge_base_object = knowledge_base.KnowledgeBase()

    self.assertEqual(len(knowledge_base_object.user_accounts), 0)

    user_account = artifacts.UserAccountArtifact(
        identifier=u'1000', user_directory=u'/home/testuser',
        username=u'testuser')
    knowledge_base_object.AddUserAccount(user_account)

    self.assertEqual(len(knowledge_base_object.user_accounts), 1)

  def testYearProperty(self):
    """Tests the year property."""
    knowledge_base_object = knowledge_base.KnowledgeBase()

    self.assertEqual(knowledge_base_object.year, 0)

  def testAddUserAccount(self):
    """Tests the AddUserAccount function."""
    knowledge_base_object = knowledge_base.KnowledgeBase()

    user_account = artifacts.UserAccountArtifact(
        identifier=u'1000', user_directory=u'/home/testuser',
        username=u'testuser')
    knowledge_base_object.AddUserAccount(user_account)

    with self.assertRaises(KeyError):
      knowledge_base_object.AddUserAccount(user_account)

  def testAddEnvironmentVariable(self):
    """Tests the AddEnvironmentVariable function."""
    knowledge_base_object = knowledge_base.KnowledgeBase()

    environment_variable = artifacts.EnvironmentVariableArtifact(
        case_sensitive=False, name=u'SystemRoot', value=u'C:\\Windows')

    knowledge_base_object.AddEnvironmentVariable(environment_variable)

    with self.assertRaises(KeyError):
      knowledge_base_object.AddEnvironmentVariable(environment_variable)

  def testGetEnvironmentVariable(self):
    """Tests the GetEnvironmentVariable functions."""
    knowledge_base_object = knowledge_base.KnowledgeBase()

    environment_variable = artifacts.EnvironmentVariableArtifact(
        case_sensitive=False, name=u'SystemRoot', value=u'C:\\Windows')
    knowledge_base_object.AddEnvironmentVariable(environment_variable)

    test_environment_variable = knowledge_base_object.GetEnvironmentVariable(
        u'SystemRoot')
    self.assertIsNotNone(test_environment_variable)

    test_environment_variable = knowledge_base_object.GetEnvironmentVariable(
        u'sYsTeMrOoT')
    self.assertIsNotNone(test_environment_variable)

    test_environment_variable = knowledge_base_object.GetEnvironmentVariable(
        u'Bogus')
    self.assertIsNone(test_environment_variable)

  def testGetEnvironmentVariables(self):
    """Tests the GetEnvironmentVariables function."""
    knowledge_base_object = knowledge_base.KnowledgeBase()

    environment_variable = artifacts.EnvironmentVariableArtifact(
        case_sensitive=False, name=u'SystemRoot', value=u'C:\\Windows')
    knowledge_base_object.AddEnvironmentVariable(environment_variable)

    environment_variable = artifacts.EnvironmentVariableArtifact(
        case_sensitive=False, name=u'WinDir', value=u'C:\\Windows')
    knowledge_base_object.AddEnvironmentVariable(environment_variable)

    environment_variables = knowledge_base_object.GetEnvironmentVariables()
    self.assertEqual(len(environment_variables), 2)

  def testGetHostname(self):
    """Tests the GetHostname function."""
    knowledge_base_object = knowledge_base.KnowledgeBase()

    hostname = knowledge_base_object.GetHostname()
    self.assertEqual(hostname, u'')

  def testGetSystemConfigurationArtifact(self):
    """Tests the GetSystemConfigurationArtifact function."""
    knowledge_base_object = knowledge_base.KnowledgeBase()

    hostname_artifact = artifacts.HostnameArtifact(name=u'myhost.mydomain')
    knowledge_base_object.SetHostname(hostname_artifact)

    user_account = artifacts.UserAccountArtifact(
        identifier=u'1000', user_directory=u'/home/testuser',
        username=u'testuser')
    knowledge_base_object.AddUserAccount(user_account)

    system_configuration = (
        knowledge_base_object.GetSystemConfigurationArtifact())
    self.assertIsNotNone(system_configuration)
    self.assertIsNotNone(system_configuration.hostname)
    self.assertEqual(system_configuration.hostname.name, u'myhost.mydomain')

  def testGetUsernameByIdentifier(self):
    """Tests the GetUsernameByIdentifier function."""
    knowledge_base_object = knowledge_base.KnowledgeBase()

    user_account = artifacts.UserAccountArtifact(
        identifier=u'1000', user_directory=u'/home/testuser',
        username=u'testuser')
    knowledge_base_object.AddUserAccount(user_account)

    usename = knowledge_base_object.GetUsernameByIdentifier(u'1000')
    self.assertEqual(usename, u'testuser')

    usename = knowledge_base_object.GetUsernameByIdentifier(1000)
    self.assertEqual(usename, u'')

    usename = knowledge_base_object.GetUsernameByIdentifier(u'1001')
    self.assertEqual(usename, u'')

  def testGetUsernameForPath(self):
    """Tests the GetUsernameForPath function."""
    knowledge_base_object = knowledge_base.KnowledgeBase()
    self._SetUserAccounts(knowledge_base_object, self._MACOSX_USERS)

    username = knowledge_base_object.GetUsernameForPath(
        self._MACOSX_PATHS[0])
    self.assertEqual(username, u'dude')

    username = knowledge_base_object.GetUsernameForPath(
        self._MACOSX_PATHS[4])
    self.assertEqual(username, u'hans')

    username = knowledge_base_object.GetUsernameForPath(
        self._WINDOWS_PATHS[0])
    self.assertIsNone(username)

    knowledge_base_object = knowledge_base.KnowledgeBase()
    self._SetUserAccounts(knowledge_base_object, self._WINDOWS_USERS)

    username = knowledge_base_object.GetUsernameForPath(
        self._WINDOWS_PATHS[0])
    self.assertEqual(username, u'dude')

    username = knowledge_base_object.GetUsernameForPath(
        self._WINDOWS_PATHS[2])
    self.assertEqual(username, u'frank')

    username = knowledge_base_object.GetUsernameForPath(
        self._MACOSX_PATHS[2])
    self.assertIsNone(username)

  def testGetSetValue(self):
    """Tests the Get and SetValue functions."""
    knowledge_base_object = knowledge_base.KnowledgeBase()

    expected_value = u'test value'
    knowledge_base_object.SetValue(u'Test', expected_value)

    value = knowledge_base_object.GetValue(u'Test')
    self.assertEqual(value, expected_value)

    value = knowledge_base_object.GetValue(u'tEsT')
    self.assertEqual(value, expected_value)

    value = knowledge_base_object.GetValue(u'Bogus')
    self.assertIsNone(value)

  def testHasUserAccounts(self):
    """Tests the HasUserAccounts function."""
    knowledge_base_object = knowledge_base.KnowledgeBase()

    self.assertFalse(knowledge_base_object.HasUserAccounts())

    user_account = artifacts.UserAccountArtifact(
        identifier=u'1000', user_directory=u'/home/testuser',
        username=u'testuser')
    knowledge_base_object.AddUserAccount(user_account)

    self.assertTrue(knowledge_base_object.HasUserAccounts())

  def testReadSystemConfigurationArtifact(self):
    """Tests the ReadSystemConfigurationArtifact function."""
    knowledge_base_object = knowledge_base.KnowledgeBase()

    system_configuration = artifacts.SystemConfigurationArtifact()
    system_configuration.hostname = artifacts.HostnameArtifact(
        name=u'myhost.mydomain')

    user_account = artifacts.UserAccountArtifact(
        identifier=u'1000', user_directory=u'/home/testuser',
        username=u'testuser')
    system_configuration.user_accounts.append(user_account)

    knowledge_base_object.ReadSystemConfigurationArtifact(system_configuration)

    hostname = knowledge_base_object.GetHostname()
    self.assertEqual(hostname, u'myhost.mydomain')

  def testSetCodepage(self):
    """Tests the SetCodepage function."""
    knowledge_base_object = knowledge_base.KnowledgeBase()

    knowledge_base_object.SetCodepage(u'cp1252')

    with self.assertRaises(ValueError):
      knowledge_base_object.SetCodepage(u'bogus')

  def testSetHostname(self):
    """Tests the SetHostname function."""
    knowledge_base_object = knowledge_base.KnowledgeBase()

    hostname_artifact = artifacts.HostnameArtifact(name=u'myhost.mydomain')
    knowledge_base_object.SetHostname(hostname_artifact)

  def testSetTimeZone(self):
    """Tests the SetTimeZone function."""
    knowledge_base_object = knowledge_base.KnowledgeBase()

    knowledge_base_object.SetTimeZone(u'Europe/Zurich')

    with self.assertRaises(ValueError):
      knowledge_base_object.SetTimeZone(u'Bogus')


if __name__ == '__main__':
  unittest.main()
