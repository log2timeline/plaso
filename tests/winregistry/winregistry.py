#!/usr/bin/python
# -*- coding: utf-8 -*-
"""This file contains the tests for the Windows Registry library."""

import unittest

from plaso.winregistry import registry as winregistry

from tests.winregistry import test_lib


class RegistryUnitTest(test_lib.WinRegTestCase):
  """Tests for the Windows Registry library."""

  def testInitialize(self):
    """Tests the initialization function."""
    registry = winregistry.WinRegistry(
        backend=winregistry.WinRegistry.BACKEND_PYREGF)

    self.assertNotEqual(registry, None)


if __name__ == '__main__':
  unittest.main()
