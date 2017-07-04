#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for the errors attribute containers."""

from __future__ import unicode_literals

import unittest

from plaso.containers import errors

from tests import test_lib as shared_test_lib


class ExtractionErrorTest(shared_test_lib.BaseTestCase):
  """Tests for the extraction error attribute container."""

  def testGetAttributeNames(self):
    """Tests the GetAttributeNames function."""
    attribute_container = errors.ExtractionError()

    expected_attribute_names = [
        'message', 'parser_chain', 'path_spec']

    attribute_names = sorted(attribute_container.GetAttributeNames())

    self.assertEqual(attribute_names, expected_attribute_names)


if __name__ == '__main__':
  unittest.main()
