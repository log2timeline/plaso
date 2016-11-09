#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the dependencies helper functions."""

import unittest

from plaso import dependencies


class DependenciesTest(unittest.TestCase):
  """A unit test for the dependencies helper functions."""

  # pylint: disable=protected-access

  # Show full diff results, part of TestCase so does not follow our naming
  # conventions.
  maxDiff = None

  def testCheckPythonModule(self):
    """Tests the _CheckPythonModule function."""
    result = dependencies._CheckPythonModule(
        u'dfdatetime', u'__version__', u'20160319', verbose_output=False)
    self.assertTrue(result)

    result = dependencies._CheckPythonModule(
        u'bogus', u'__version__', u'0', verbose_output=False)
    self.assertFalse(result)

  def testCheckSQLite3(self):
    """Tests the _CheckSQLite3 function."""
    result = dependencies._CheckSQLite3(verbose_output=False)
    self.assertTrue(result)

  def testImportPythonModule(self):
    """Tests the _ImportPythonModule function."""
    module = dependencies._ImportPythonModule(u'os')
    self.assertIsNotNone(module)

    module = dependencies._ImportPythonModule(u'bogus')
    self.assertIsNone(module)

  def testCheckDependencies(self):
    """Tests the CheckDependencies function."""
    result = dependencies.CheckDependencies(verbose_output=False)
    self.assertTrue(result)

  def testCheckModuleVersion(self):
    """Tests the CheckModuleVersion function."""
    dependencies.CheckModuleVersion(u'dfdatetime')

    with self.assertRaises(ImportError):
      dependencies.CheckModuleVersion(u'bogus')

  # CheckTestDependencies is tested in ./run_tests.py

  def testGetDPKGDepends(self):
    """Tests the GetDPKGDepends function."""
    install_requires = dependencies.GetDPKGDepends()
    self.assertIn(u'libbde-python (>= 20140531)', install_requires)

    install_requires = dependencies.GetDPKGDepends(exclude_version=True)
    self.assertIn(u'libbde-python', install_requires)

  def testGetInstallRequires(self):
    """Tests the GetInstallRequires function."""
    install_requires = dependencies.GetInstallRequires()
    self.assertIn(u'libbde-python >= 20140531', install_requires)

  def testGetRPMRequires(self):
    """Tests the GetRPMRequires function."""
    install_requires = dependencies.GetRPMRequires()
    self.assertIn(u'libbde-python >= 20140531', install_requires)


if __name__ == '__main__':
  unittest.main()
