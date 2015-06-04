# -*- coding: utf-8 -*-
import unittest

from plaso.lib import errors


# TODO: refactor this code:
# * change the name of the class to FilterTestCase
# * fix the issues masked by the pylint override

# pylint: disable=redundant-unittest-assert
class FilterTestHelper(unittest.TestCase):
  """A simple class that provides helper functions for testing filters."""

  def setUp(self):
    """This should be overwritten."""
    self.test_filter = None

  def TestTrue(self, query):
    """A quick test that should return a valid filter."""
    if not self.test_filter:
      self.assertTrue(False)

    try:
      self.test_filter.CompileFilter(query)
      # And a success.
      self.assertTrue(True)
    except errors.WrongPlugin:
      # Let the test fail.
      self.assertTrue(False)

  def TestFail(self, query):
    """A quick failure test with a filter."""
    if not self.test_filter:
      self.assertTrue(False)

    with self.assertRaises(errors.WrongPlugin):
      self.test_filter.CompileFilter(query)
