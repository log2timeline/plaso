#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the sessions attribute containers."""

import unittest

from plaso.containers import sessions

from tests import test_lib as shared_test_lib


class SessionTest(shared_test_lib.BaseTestCase):
  """Tests for the session attribute container."""

  def testGetAttributeNames(self):
    """Tests the GetAttributeNames function."""
    attribute_container = sessions.Session()

    expected_attribute_names = [
        'aborted',
        'artifact_filters',
        'command_line_arguments',
        'completion_time',
        'debug_mode',
        'enabled_parser_names',
        'filter_file',
        'identifier',
        'parser_filter_expression',
        'preferred_codepage',
        'preferred_encoding',
        'preferred_language',
        'preferred_time_zone',
        'preferred_year',
        'product_name',
        'product_version',
        'start_time']

    attribute_names = sorted(attribute_container.GetAttributeNames())

    self.assertEqual(attribute_names, expected_attribute_names)


if __name__ == '__main__':
  unittest.main()
