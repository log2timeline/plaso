#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the warnings attribute containers."""

import unittest

from plaso.containers import warnings

from tests import test_lib as shared_test_lib


class AnalysisWarningTest(shared_test_lib.BaseTestCase):
  """Tests for the analysis warning attribute container."""

  def testGetAttributeNames(self):
    """Tests the GetAttributeNames function."""
    attribute_container = warnings.AnalysisWarning()

    attribute_names = sorted(attribute_container.GetAttributeNames())
    self.assertEqual(attribute_names, ['message', 'plugin_name'])


class ExtractionWarningTest(shared_test_lib.BaseTestCase):
  """Tests for the extraction warning attribute container."""

  def testGetAttributeNames(self):
    """Tests the GetAttributeNames function."""
    attribute_container = warnings.ExtractionWarning()

    attribute_names = sorted(attribute_container.GetAttributeNames())
    self.assertEqual(attribute_names, ['message', 'parser_chain', 'path_spec'])


class PreprocessingWarningTest(shared_test_lib.BaseTestCase):
  """Tests for the preprocessing warning attribute container."""

  def testGetAttributeNames(self):
    """Tests the GetAttributeNames function."""
    attribute_container = warnings.PreprocessingWarning()

    attribute_names = sorted(attribute_container.GetAttributeNames())
    self.assertEqual(attribute_names, ['message', 'path_spec', 'plugin_name'])


class RecoveryWarningTest(shared_test_lib.BaseTestCase):
  """Tests for the recovery warning attribute container."""

  def testGetAttributeNames(self):
    """Tests the GetAttributeNames function."""
    attribute_container = warnings.RecoveryWarning()

    attribute_names = sorted(attribute_container.GetAttributeNames())
    self.assertEqual(attribute_names, ['message', 'parser_chain', 'path_spec'])


if __name__ == '__main__':
  unittest.main()
