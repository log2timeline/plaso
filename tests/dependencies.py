#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the dependencies helper functions."""

import socket
import unittest

from plaso import dependencies


try:
  hostname = socket.gethostbyname(u'github.com')
except socket.error:
  hostname = None


class DependenciesTest(unittest.TestCase):
  """A unit test for the dependencies helper functions."""

  # pylint: disable=protected-access

  # Show full diff results, part of TestCase so does not follow our naming
  # conventions.
  maxDiff = None

  def testCheckLibyal(self):
    """Tests the _CheckLibyal function."""
    result = dependencies._CheckLibyal(
        {u'pybde': 20140531}, verbose_output=False)
    self.assertTrue(result)

    result = dependencies._CheckLibyal({u'bogus': 0}, verbose_output=False)
    self.assertFalse(result)

  @unittest.skipUnless(hostname, 'no internet connectivity')
  def testCheckLibyalWithLatestVersionCheck(self):
    """Tests the _CheckLibyal function with latest version check."""
    result = dependencies._CheckLibyal(
        {u'pybde': 20140531}, latest_version_check=True,
        verbose_output=False)
    self.assertTrue(result)

  def testCheckPythonModule(self):
    """Tests the _CheckPythonModule function."""
    result = dependencies._CheckPythonModule(
        u'dfvfs', u'__version__', u'20160510', verbose_output=False)
    self.assertTrue(result)

    result = dependencies._CheckPythonModule(
        u'bogus', u'__version__', u'0', verbose_output=False)
    self.assertFalse(result)

  def testCheckPytsk(self):
    """Tests the _CheckPytsk function."""
    result = dependencies._CheckPytsk(verbose_output=False)
    self.assertTrue(result)

  def testCheckSqlite3(self):
    """Tests the _CheckSqlite3 function."""
    result = dependencies._CheckSqlite3(verbose_output=False)
    self.assertTrue(result)

  @unittest.skipUnless(hostname, 'no internet connectivity')
  def testDownloadPageContent(self):
    """Tests the _DownloadPageContent function."""
    download_url = u'https://github.com/log2timeline/plaso/releases'
    page_content = dependencies._DownloadPageContent(download_url)
    self.assertIsNotNone(page_content)

    download_url = u'https://github.com/log2timeline/plaso/bogus'
    page_content = dependencies._DownloadPageContent(download_url)
    self.assertIsNone(page_content)

  @unittest.skipUnless(hostname, 'no internet connectivity')
  def testGetLibyalGithubReleasesLatestVersion(self):
    """Tests the _GetLibyalGithubReleasesLatestVersion function."""
    version = dependencies._GetLibyalGithubReleasesLatestVersion(u'libbde')
    self.assertNotEqual(version, 0)

    version = dependencies._GetLibyalGithubReleasesLatestVersion(u'bogus')
    self.assertEqual(version, 0)

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
    dependencies.CheckModuleVersion(u'dfwinreg')

    with self.assertRaises(ImportError):
      dependencies.CheckModuleVersion(u'bogus')

  # CheckTestDependencies is tested in ./run_tests.py

  def testGetDPKGDepends(self):
    """Tests the GetDPKGDepends function."""
    install_requires = dependencies.GetDPKGDepends()
    self.assertIn(u'libbde-python >= 20140531', install_requires)

    install_requires = dependencies.GetDPKGDepends(exclude_version=True)
    self.assertIn(u'libbde-python', install_requires)

  def testGetInstallRequires(self):
    """Tests the GetInstallRequires function."""
    install_requires = dependencies.GetInstallRequires()
    self.assertIn(u'pybde >= 20140531', install_requires)

  def testGetRPMRequires(self):
    """Tests the GetRPMRequires function."""
    install_requires = dependencies.GetRPMRequires()
    self.assertIn(u'libbde-python >= 20140531', install_requires)


if __name__ == '__main__':
  unittest.main()
