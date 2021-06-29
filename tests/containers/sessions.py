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
        'analysis_reports_counter',
        'artifact_filters',
        'command_line_arguments',
        'completion_time',
        'debug_mode',
        'enabled_parser_names',
        'event_labels_counter',
        'filter_file',
        'identifier',
        'parser_filter_expression',
        'parsers_counter',
        'preferred_encoding',
        'preferred_time_zone',
        'preferred_year',
        'product_name',
        'product_version',
        'source_configurations',
        'start_time',
        'text_prepend']

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

  def testCreateSessionConfiguration(self):
    """Tests the CreateSessionConfiguration function."""
    attribute_container = sessions.Session()

    session_configuration = attribute_container.CreateSessionConfiguration()
    self.assertIsNotNone(session_configuration)
    self.assertEqual(
        session_configuration.identifier, attribute_container.identifier)

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
        'analysis_reports_counter',
        'event_labels_counter',
        'identifier',
        'parsers_counter',
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
        'preferred_encoding',
        'preferred_time_zone',
        'preferred_year',
        'source_configurations',
        'text_prepend']

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
