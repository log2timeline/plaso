#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the storage media attribute containers."""

from __future__ import unicode_literals

import unittest

from plaso.containers import storage_media

from tests import test_lib as shared_test_lib


class MountPointTest(shared_test_lib.BaseTestCase):
  """Tests for the mount point attribute container."""

  def testGetAttributeNames(self):
    """Tests the GetAttributeNames function."""
    attribute_container = storage_media.MountPoint()

    expected_attribute_names = ['mount_path', 'path_specification']

    attribute_names = sorted(attribute_container.GetAttributeNames())

    self.assertEqual(attribute_names, expected_attribute_names)


if __name__ == '__main__':
  unittest.main()
