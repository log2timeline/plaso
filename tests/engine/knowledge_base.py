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

  def testReadSystemConfigurationArtifact(self):
    """Tests the ReadSystemConfigurationArtifact function."""
    knowledge_base_object = knowledge_base.KnowledgeBase()

    system_configuration = artifacts.SystemConfigurationArtifact()
    system_configuration.hostname = artifacts.HostnameArtifact(
        name='myhost.mydomain')

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

  def testSetTimeZone(self):
    """Tests the SetTimeZone function."""
    knowledge_base_object = knowledge_base.KnowledgeBase()

    knowledge_base_object.SetTimeZone('Europe/Zurich')
    self.assertEqual(knowledge_base_object._time_zone.zone, 'Europe/Zurich')

    with self.assertRaises(ValueError):
      knowledge_base_object.SetTimeZone('Bogus')


if __name__ == '__main__':
  unittest.main()
