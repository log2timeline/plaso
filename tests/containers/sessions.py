#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the sessions attribute containers."""

from __future__ import unicode_literals

import time
import unittest
import uuid

import plaso
from plaso.containers import sessions

from tests import test_lib as shared_test_lib


class SessionTest(shared_test_lib.BaseTestCase):
  """Tests for the session attribute container."""

  # TODO: replace by GetAttributeNames test
  def testCopyToDict(self):
    """Tests the CopyToDict function."""
    session = sessions.Session()

    self.assertIsNotNone(session.identifier)
    self.assertIsNotNone(session.start_time)
    self.assertIsNone(session.completion_time)

    expected_dict = {
        'aborted': False,
        'analysis_reports_counter': session.analysis_reports_counter,
        'debug_mode': False,
        'event_labels_counter': session.event_labels_counter,
        'identifier': session.identifier,
        'parsers_counter': session.parsers_counter,
        'preferred_encoding': 'utf-8',
        'preferred_time_zone': 'UTC',
        'product_name': 'plaso',
        'product_version': plaso.__version__,
        'start_time': session.start_time}

    test_dict = session.CopyToDict()

    self.assertEqual(test_dict, expected_dict)

  # TODO: add tests for CopyAttributesFromSessionCompletion
  # TODO: add tests for CopyAttributesFromSessionStart
  # TODO: add tests for CreateSessionCompletion
  # TODO: add tests for CreateSessionStart


class SessionCompletionTest(shared_test_lib.BaseTestCase):
  """Tests for the session completion attribute container."""

  # TODO: replace by GetAttributeNames test
  def testCopyToDict(self):
    """Tests the CopyToDict function."""
    timestamp = int(time.time() * 1000000)
    session_identifier = '{0:s}'.format(uuid.uuid4().hex)
    session_completion = sessions.SessionCompletion(
        identifier=session_identifier)
    session_completion.timestamp = timestamp

    self.assertEqual(session_completion.identifier, session_identifier)

    expected_dict = {
        'aborted': False,
        'identifier': session_completion.identifier,
        'timestamp': timestamp}

    test_dict = session_completion.CopyToDict()

    self.assertEqual(test_dict, expected_dict)


class SessionStartTest(shared_test_lib.BaseTestCase):
  """Tests for the session start attribute container."""

  # TODO: replace by GetAttributeNames test
  def testCopyToDict(self):
    """Tests the CopyToDict function."""
    timestamp = int(time.time() * 1000000)
    session_identifier = '{0:s}'.format(uuid.uuid4().hex)
    session_start = sessions.SessionStart(identifier=session_identifier)
    session_start.timestamp = timestamp
    session_start.product_name = 'plaso'
    session_start.product_version = plaso.__version__

    self.assertEqual(session_start.identifier, session_identifier)

    expected_dict = {
        'debug_mode': False,
        'identifier': session_start.identifier,
        'product_name': 'plaso',
        'product_version': plaso.__version__,
        'timestamp': timestamp}

    test_dict = session_start.CopyToDict()

    self.assertEqual(test_dict, expected_dict)


if __name__ == '__main__':
  unittest.main()
