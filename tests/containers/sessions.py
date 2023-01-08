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

  def testCopyAttributesFromSessionCompletion(self):
    """Tests the CopyAttributesFromSessionCompletion function."""
    attribute_container = sessions.Session()

    session_completion = sessions.SessionCompletion(
        identifier=attribute_container.identifier)
    attribute_container.CopyAttributesFromSessionCompletion(session_completion)

    with self.assertRaises(ValueError):
      session_completion = sessions.SessionCompletion()
      attribute_container.CopyAttributesFromSessionCompletion(
          session_completion)

  def testCopyAttributesFromSessionConfiguration(self):
    """Tests the CopyAttributesFromSessionConfiguration function."""
    attribute_container = sessions.Session()

    session_configuration = sessions.SessionConfiguration(
        identifier=attribute_container.identifier)
    attribute_container.CopyAttributesFromSessionConfiguration(
        session_configuration)

    with self.assertRaises(ValueError):
      session_configuration = sessions.SessionConfiguration()
      attribute_container.CopyAttributesFromSessionConfiguration(
          session_configuration)

  def testCopyAttributesFromSessionStart(self):
    """Tests the CopyAttributesFromSessionStart function."""
    attribute_container = sessions.Session()

    session_start = sessions.SessionStart(
        identifier=attribute_container.identifier)
    attribute_container.CopyAttributesFromSessionStart(session_start)

  def testCreateSessionCompletion(self):
    """Tests the CreateSessionCompletion function."""
    attribute_container = sessions.Session()

    session_completion = attribute_container.CreateSessionCompletion()
    self.assertIsNotNone(session_completion)
    self.assertEqual(
        session_completion.identifier, attribute_container.identifier)

  def testCreateSessionStart(self):
    """Tests the CreateSessionStart function."""
    attribute_container = sessions.Session()

    session_start = attribute_container.CreateSessionStart()
    self.assertIsNotNone(session_start)
    self.assertEqual(session_start.identifier, attribute_container.identifier)


class SessionCompletionTest(shared_test_lib.BaseTestCase):
  """Tests for the session completion attribute container."""

  def testGetAttributeNames(self):
    """Tests the GetAttributeNames function."""
    attribute_container = sessions.SessionCompletion()

    expected_attribute_names = [
        'aborted',
        'identifier',
        'timestamp']

    attribute_names = sorted(attribute_container.GetAttributeNames())

    self.assertEqual(attribute_names, expected_attribute_names)


class SessionConfiguration(shared_test_lib.BaseTestCase):
  """Tests for the session configuration attribute container."""

  def testGetAttributeNames(self):
    """Tests the GetAttributeNames function."""
    attribute_container = sessions.SessionConfiguration()

    expected_attribute_names = [
        'artifact_filters',
        'command_line_arguments',
        'debug_mode',
        'enabled_parser_names',
        'filter_file',
        'identifier',
        'parser_filter_expression',
        'preferred_codepage',
        'preferred_encoding',
        'preferred_language',
        'preferred_time_zone',
        'preferred_year']

    attribute_names = sorted(attribute_container.GetAttributeNames())

    self.assertEqual(attribute_names, expected_attribute_names)


class SessionStartTest(shared_test_lib.BaseTestCase):
  """Tests for the session start attribute container."""

  def testGetAttributeNames(self):
    """Tests the GetAttributeNames function."""
    attribute_container = sessions.SessionStart()

    expected_attribute_names = [
        'identifier',
        'product_name',
        'product_version',
        'timestamp']

    attribute_names = sorted(attribute_container.GetAttributeNames())

    self.assertEqual(attribute_names, expected_attribute_names)


if __name__ == '__main__':
  unittest.main()
