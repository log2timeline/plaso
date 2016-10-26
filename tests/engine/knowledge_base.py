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

      user_account_artifact = artifacts.UserAccountArtifact(
          identifier=identifier, user_directory=user.get(u'path', None),
          username=user.get(u'name', None))

      # TODO: refactor the use of store number.
      user_account_artifact.store_number = 0
      knowledge_base_object.SetUserAccount(user_account_artifact)

  def testGetSetEnvironmentVariable(self):
    """Tests the Get and SetEnvironmentVariable functions."""
    knowledge_base_object = knowledge_base.KnowledgeBase()

    environment_variable = artifacts.EnvironmentVariableArtifact(
        case_sensitive=False, name=u'SystemRoot', value=u'C:\\Windows')
    knowledge_base_object.SetEnvironmentVariable(environment_variable)

    test_environment_variable = knowledge_base_object.GetEnvironmentVariable(
        u'SystemRoot')
    self.assertIsNotNone(test_environment_variable)

    test_environment_variable = knowledge_base_object.GetEnvironmentVariable(
        u'sYsTeMrOoT')
    self.assertIsNotNone(test_environment_variable)

    test_environment_variable = knowledge_base_object.GetEnvironmentVariable(
        u'Bogus')
    self.assertIsNone(test_environment_variable)

  def testGetPathAttributes(self):
    """Tests the GetPathAttributes function."""
    knowledge_base_object = knowledge_base.KnowledgeBase()

    environment_variable = artifacts.EnvironmentVariableArtifact(
        case_sensitive=False, name=u'SystemRoot', value=u'C:\\Windows')
    knowledge_base_object.SetEnvironmentVariable(environment_variable)

    environment_variable = artifacts.EnvironmentVariableArtifact(
        case_sensitive=False, name=u'WinDir', value=u'C:\\Windows')
    knowledge_base_object.SetEnvironmentVariable(environment_variable)

    expected_path_attributes = {
        u'SystemRoot': u'C:\\Windows',
        u'WinDir': u'C:\\Windows'}
    path_attributes = knowledge_base_object.GetPathAttributes()
    self.assertEqual(path_attributes, expected_path_attributes)

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


if __name__ == '__main__':
  unittest.main()
