#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the knowledge base."""

import unittest

from plaso.containers import artifacts
from plaso.engine import knowledge_base

from tests import test_lib as shared_test_lib


class KnowledgeBaseTest(shared_test_lib.BaseTestCase):
  """Tests for the knowledge base."""

  # pylint: disable=protected-access

  _MACOS_PATHS = [
      '/Users/dude/Library/Application Data/Google/Chrome/Default/Extensions',
      ('/Users/dude/Library/Application Data/Google/Chrome/Default/Extensions/'
       'apdfllckaahabafndbhieahigkjlhalf'),
      '/private/var/log/system.log',
      '/Users/frank/Library/Application Data/Google/Chrome/Default',
      '/Users/hans/Library/Application Data/Google/Chrome/Default',
      ('/Users/frank/Library/Application Data/Google/Chrome/Default/'
       'Extensions/pjkljhegncpnkpknbcohdijeoejaedia'),
      '/Users/frank/Library/Application Data/Google/Chrome/Default/Extensions']

  _MACOS_USERS = [
      {'name': 'root', 'path': '/var/root', 'sid': '0'},
      {'name': 'frank', 'path': '/Users/frank', 'sid': '4052'},
      {'name': 'hans', 'path': '/Users/hans', 'sid': '4352'},
      {'name': 'dude', 'path': '/Users/dude', 'sid': '1123'}]

  _WINDOWS_PATHS = [
      'C:\\Users\\Dude\\SomeFolder\\Chrome\\Default\\Extensions',
      ('C:\\Users\\Dude\\SomeNoneStandardFolder\\Chrome\\Default\\Extensions\\'
       'hmjkmjkepdijhoojdojkdfohbdgmmhki'),
      ('C:\\Users\\frank\\AppData\\Local\\Google\\Chrome\\Extensions\\'
       'blpcfgokakmgnkcojhhkbfbldkacnbeo'),
      'C:\\Users\\frank\\AppData\\Local\\Google\\Chrome\\Extensions',
      ('C:\\Users\\frank\\AppData\\Local\\Google\\Chrome\\Extensions\\'
       'icppfcnhkcmnfdhfhphakoifcfokfdhg'),
      'C:\\Windows\\System32',
      'C:\\Stuff/with path separator\\Folder']

  _WINDOWS_USERS = [
      {'name': 'dude', 'path': 'C:\\Users\\dude', 'sid': 'S-1'},
      {'name': 'frank', 'path': 'C:\\Users\\frank', 'sid': 'S-2'}]

  def _SetUserAccounts(self, knowledge_base_object, users):
    """Sets the user accounts in the knowledge base.

    Args:
      knowledge_base_object (KnowledgeBase): knowledge base.
      users (list[dict[str,str])): users.
    """
    for user in users:
      identifier = user.get('sid', user.get('uid', None))
      if not identifier:
        continue

      user_account = artifacts.UserAccountArtifact(
          identifier=identifier, user_directory=user.get('path', None),
          username=user.get('name', None))

      knowledge_base_object.AddUserAccount(user_account)

  def testCodepageProperty(self):
    """Tests the codepage property."""
    knowledge_base_object = knowledge_base.KnowledgeBase()

    self.assertEqual(knowledge_base_object.codepage, 'cp1252')

  def testOperatingSystemProperty(self):
    """Tests the operating_system property."""
    knowledge_base_object = knowledge_base.KnowledgeBase()

    operating_system = knowledge_base_object.GetValue('operating_system')
    self.assertIsNone(operating_system)

    knowledge_base_object.SetValue('operating_system', 'Windows')

    operating_system = knowledge_base_object.GetValue('operating_system')
    self.assertEqual(operating_system, 'Windows')

  def testTimezoneProperty(self):
    """Tests the timezone property."""
    knowledge_base_object = knowledge_base.KnowledgeBase()

    self.assertEqual(knowledge_base_object.timezone.zone, 'UTC')

  def testUserAccountsProperty(self):
    """Tests the user accounts property."""
    knowledge_base_object = knowledge_base.KnowledgeBase()

    self.assertEqual(len(knowledge_base_object.user_accounts), 0)

    user_account = artifacts.UserAccountArtifact(
        identifier='1000', user_directory='/home/testuser',
        username='testuser')
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
        identifier='1000', user_directory='/home/testuser',
        username='testuser')
    knowledge_base_object.AddUserAccount(user_account)

    with self.assertRaises(KeyError):
      knowledge_base_object.AddUserAccount(user_account)

  def testAddEnvironmentVariable(self):
    """Tests the AddEnvironmentVariable function."""
    knowledge_base_object = knowledge_base.KnowledgeBase()

    environment_variable = artifacts.EnvironmentVariableArtifact(
        case_sensitive=False, name='SystemRoot', value='C:\\Windows')

    knowledge_base_object.AddEnvironmentVariable(environment_variable)

    with self.assertRaises(KeyError):
      knowledge_base_object.AddEnvironmentVariable(environment_variable)

  def testGetEnvironmentVariable(self):
    """Tests the GetEnvironmentVariable functions."""
    knowledge_base_object = knowledge_base.KnowledgeBase()

    environment_variable = artifacts.EnvironmentVariableArtifact(
        case_sensitive=False, name='SystemRoot', value='C:\\Windows')
    knowledge_base_object.AddEnvironmentVariable(environment_variable)

    test_environment_variable = knowledge_base_object.GetEnvironmentVariable(
        'SystemRoot')
    self.assertIsNotNone(test_environment_variable)

    test_environment_variable = knowledge_base_object.GetEnvironmentVariable(
        'sYsTeMrOoT')
    self.assertIsNotNone(test_environment_variable)

    test_environment_variable = knowledge_base_object.GetEnvironmentVariable(
        'Bogus')
    self.assertIsNone(test_environment_variable)

  def testGetEnvironmentVariables(self):
    """Tests the GetEnvironmentVariables function."""
    knowledge_base_object = knowledge_base.KnowledgeBase()

    environment_variable = artifacts.EnvironmentVariableArtifact(
        case_sensitive=False, name='SystemRoot', value='C:\\Windows')
    knowledge_base_object.AddEnvironmentVariable(environment_variable)

    environment_variable = artifacts.EnvironmentVariableArtifact(
        case_sensitive=False, name='WinDir', value='C:\\Windows')
    knowledge_base_object.AddEnvironmentVariable(environment_variable)

    environment_variables = knowledge_base_object.GetEnvironmentVariables()
    self.assertEqual(len(environment_variables), 2)

  def testGetHostname(self):
    """Tests the GetHostname function."""
    knowledge_base_object = knowledge_base.KnowledgeBase()

    hostname = knowledge_base_object.GetHostname()
    self.assertEqual(hostname, '')

  def testGetSystemConfigurationArtifact(self):
    """Tests the GetSystemConfigurationArtifact function."""
    knowledge_base_object = knowledge_base.KnowledgeBase()

    hostname_artifact = artifacts.HostnameArtifact(name='myhost.mydomain')
    knowledge_base_object.SetHostname(hostname_artifact)

    user_account = artifacts.UserAccountArtifact(
        identifier='1000', user_directory='/home/testuser',
        username='testuser')
    knowledge_base_object.AddUserAccount(user_account)

    system_configuration = (
        knowledge_base_object.GetSystemConfigurationArtifact())
    self.assertIsNotNone(system_configuration)
    self.assertIsNotNone(system_configuration.hostname)
    self.assertEqual(system_configuration.hostname.name, 'myhost.mydomain')

  # TODO: add tests for GetTextPrepend.

  def testGetUsernameByIdentifier(self):
    """Tests the GetUsernameByIdentifier function."""
    knowledge_base_object = knowledge_base.KnowledgeBase()

    user_account = artifacts.UserAccountArtifact(
        identifier='1000', user_directory='/home/testuser',
        username='testuser')
    knowledge_base_object.AddUserAccount(user_account)

    usename = knowledge_base_object.GetUsernameByIdentifier('1000')
    self.assertEqual(usename, 'testuser')

    usename = knowledge_base_object.GetUsernameByIdentifier(1000)
    self.assertEqual(usename, '')

    usename = knowledge_base_object.GetUsernameByIdentifier('1001')
    self.assertEqual(usename, '')

  def testGetUsernameForPath(self):
    """Tests the GetUsernameForPath function."""
    knowledge_base_object = knowledge_base.KnowledgeBase()
    self._SetUserAccounts(knowledge_base_object, self._MACOS_USERS)

    username = knowledge_base_object.GetUsernameForPath(
        self._MACOS_PATHS[0])
    self.assertEqual(username, 'dude')

    username = knowledge_base_object.GetUsernameForPath(
        self._MACOS_PATHS[4])
    self.assertEqual(username, 'hans')

    username = knowledge_base_object.GetUsernameForPath(
        self._WINDOWS_PATHS[0])
    self.assertIsNone(username)

    knowledge_base_object = knowledge_base.KnowledgeBase()
    self._SetUserAccounts(knowledge_base_object, self._WINDOWS_USERS)

    username = knowledge_base_object.GetUsernameForPath(
        self._WINDOWS_PATHS[0])
    self.assertEqual(username, 'dude')

    username = knowledge_base_object.GetUsernameForPath(
        self._WINDOWS_PATHS[2])
    self.assertEqual(username, 'frank')

    username = knowledge_base_object.GetUsernameForPath(
        self._MACOS_PATHS[2])
    self.assertIsNone(username)

  def testGetSetValue(self):
    """Tests the Get and SetValue functions."""
    knowledge_base_object = knowledge_base.KnowledgeBase()

    expected_value = 'test value'
    knowledge_base_object.SetValue('Test', expected_value)

    value = knowledge_base_object.GetValue('Test')
    self.assertEqual(value, expected_value)

    value = knowledge_base_object.GetValue('tEsT')
    self.assertEqual(value, expected_value)

    value = knowledge_base_object.GetValue('Bogus')
    self.assertIsNone(value)

  def testHasUserAccounts(self):
    """Tests the HasUserAccounts function."""
    knowledge_base_object = knowledge_base.KnowledgeBase()

    self.assertFalse(knowledge_base_object.HasUserAccounts())

    user_account = artifacts.UserAccountArtifact(
        identifier='1000', user_directory='/home/testuser',
        username='testuser')
    knowledge_base_object.AddUserAccount(user_account)

    self.assertTrue(knowledge_base_object.HasUserAccounts())

  def testReadSystemConfigurationArtifact(self):
    """Tests the ReadSystemConfigurationArtifact function."""
    knowledge_base_object = knowledge_base.KnowledgeBase()

    system_configuration = artifacts.SystemConfigurationArtifact()
    system_configuration.hostname = artifacts.HostnameArtifact(
        name='myhost.mydomain')

    user_account = artifacts.UserAccountArtifact(
        identifier='1000', user_directory='/home/testuser',
        username='testuser')
    system_configuration.user_accounts.append(user_account)

    knowledge_base_object.ReadSystemConfigurationArtifact(system_configuration)

    hostname = knowledge_base_object.GetHostname()
    self.assertEqual(hostname, 'myhost.mydomain')

  def testSetActiveSession(self):
    """Tests the SetActiveSession function."""
    knowledge_base_object = knowledge_base.KnowledgeBase()

    knowledge_base_object.SetActiveSession('ddda05bedf324cbd99fa8c24b8a0037a')
    self.assertEqual(
        knowledge_base_object._active_session,
        'ddda05bedf324cbd99fa8c24b8a0037a')

    knowledge_base_object.SetActiveSession(
        knowledge_base_object._DEFAULT_ACTIVE_SESSION)
    self.assertEqual(
        knowledge_base_object._active_session,
        knowledge_base_object._DEFAULT_ACTIVE_SESSION)

  def testSetCodepage(self):
    """Tests the SetCodepage function."""
    knowledge_base_object = knowledge_base.KnowledgeBase()

    knowledge_base_object.SetCodepage('cp1252')

    with self.assertRaises(ValueError):
      knowledge_base_object.SetCodepage('bogus')

  def testSetHostname(self):
    """Tests the SetHostname function."""
    knowledge_base_object = knowledge_base.KnowledgeBase()

    hostname_artifact = artifacts.HostnameArtifact(name='myhost.mydomain')
    knowledge_base_object.SetHostname(hostname_artifact)

  # TODO: add tests for SetTextPrepend.

  def testSetTimeZone(self):
    """Tests the SetTimeZone function."""
    knowledge_base_object = knowledge_base.KnowledgeBase()

    time_zone_artifact = artifacts.TimeZoneArtifact(
        localized_name='Eastern (standaardtijd)', mui_form='@tzres.dll,-112',
        name='Eastern Standard Time')

    knowledge_base_object.AddAvailableTimeZone(time_zone_artifact)

    # Set an IANA time zone name.
    knowledge_base_object.SetTimeZone('Europe/Zurich')
    self.assertEqual(knowledge_base_object._time_zone.zone, 'Europe/Zurich')

    # Set a Windows time zone name.
    knowledge_base_object.SetTimeZone('Eastern Standard Time')
    self.assertEqual(knowledge_base_object._time_zone.zone, 'America/New_York')

    # Set a localized Windows time zone name.
    knowledge_base_object.SetTimeZone('Eastern (standaardtijd)')
    self.assertEqual(knowledge_base_object._time_zone.zone, 'America/New_York')

    # Set a MUI form Windows time zone name.
    knowledge_base_object.SetTimeZone('@tzres.dll,-112')
    self.assertEqual(knowledge_base_object._time_zone.zone, 'America/New_York')

    with self.assertRaises(ValueError):
      knowledge_base_object.SetTimeZone('Bogus')


if __name__ == '__main__':
  unittest.main()
