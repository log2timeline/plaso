# -*- coding: utf-8 -*-
"""Tests for the function to expand Windows environment variables."""

import unittest

from plaso.winnt import environ_expand


class ExpandWindowsEnvironmentVariablesTest(unittest.TestCase):
  """Tests for the function to expand Windows environment variables."""

  def testExpandWindowsEnvironmentVariables(self):
    """Tests the ExpandWindowsEnvironmentVariables function."""
    expanded_path = environ_expand.ExpandWindowsEnvironmentVariables(
        u'%SystemRoot%\\System32', {u'SystemRoot': u'C:\\Windows'})
    self.assertEqual(expanded_path, u'C:\\Windows\\System32')

    expanded_path = environ_expand.ExpandWindowsEnvironmentVariables(
        u'%SystemRoot%\\System32', None)
    self.assertEqual(expanded_path, u'%SystemRoot%\\System32')

    expanded_path = environ_expand.ExpandWindowsEnvironmentVariables(
        u'%Bogus%\\System32', {u'SystemRoot': u'C:\\Windows'})
    self.assertEqual(expanded_path, u'%Bogus%\\System32')


if __name__ == '__main__':
  unittest.main()
