#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the processing configuration classes."""

import unittest

from plaso.engine import configurations


class CredentialConfigurationTest(unittest.TestCase):
  """Tests the credential configuration settings."""

  def testInitialization(self):
    """Tests the __init__ function."""
    configuration = configurations.CredentialConfiguration()
    self.assertIsNotNone(configuration)


class EventExtractionConfigurationTest(unittest.TestCase):
  """Tests the event extraction configuration settings."""

  def testInitialization(self):
    """Tests the __init__ function."""
    configuration = configurations.EventExtractionConfiguration()
    self.assertIsNotNone(configuration)


class ExtractionConfigurationTest(unittest.TestCase):
  """Tests the extraction configuration settings."""

  def testInitialization(self):
    """Tests the __init__ function."""
    configuration = configurations.ExtractionConfiguration()
    self.assertIsNotNone(configuration)


class ProfilingConfigurationTest(unittest.TestCase):
  """Tests the profiling configuration settings."""

  def testInitialization(self):
    """Tests the __init__ function."""
    configuration = configurations.ProfilingConfiguration()
    self.assertIsNotNone(configuration)

  def testHaveProfileAnalyzers(self):
    """Tests the HaveProfileAnalyzers function."""
    configuration = configurations.ProfilingConfiguration()
    self.assertFalse(configuration.HaveProfileAnalyzers())

  def testHaveProfileFormatChecks(self):
    """Tests the HaveProfileFormatChecks function."""
    configuration = configurations.ProfilingConfiguration()
    self.assertFalse(configuration.HaveProfileFormatChecks())

  def testHaveProfileMemory(self):
    """Tests the HaveProfileMemory function."""
    configuration = configurations.ProfilingConfiguration()
    self.assertFalse(configuration.HaveProfileMemory())

  def testHaveProfileParsers(self):
    """Tests the HaveProfileParsers function."""
    configuration = configurations.ProfilingConfiguration()
    self.assertFalse(configuration.HaveProfileParsers())

  def testHaveProfileProcessing(self):
    """Tests the HaveProfileProcessing function."""
    configuration = configurations.ProfilingConfiguration()
    self.assertFalse(configuration.HaveProfileProcessing())

  def testHaveProfileSerializers(self):
    """Tests the HaveProfileSerializers function."""
    configuration = configurations.ProfilingConfiguration()
    self.assertFalse(configuration.HaveProfileSerializers())

  def testHaveProfileStorage(self):
    """Tests the HaveProfileStorage function."""
    configuration = configurations.ProfilingConfiguration()
    self.assertFalse(configuration.HaveProfileStorage())

  def testHaveProfileTaskQueue(self):
    """Tests the HaveProfileTaskQueue function."""
    configuration = configurations.ProfilingConfiguration()
    self.assertFalse(configuration.HaveProfileTaskQueue())

  def testHaveProfileTasks(self):
    """Tests the HaveProfileTasks function."""
    configuration = configurations.ProfilingConfiguration()
    self.assertFalse(configuration.HaveProfileTasks())


class ProcessingConfigurationTest(unittest.TestCase):
  """Tests the processing configuration settings."""

  def testInitialization(self):
    """Tests the __init__ function."""
    configuration = configurations.ProcessingConfiguration()
    self.assertIsNotNone(configuration)


if __name__ == '__main__':
  unittest.main()
