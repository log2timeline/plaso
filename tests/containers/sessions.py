#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the sessions attribute containers."""

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
        u'aborted': False,
        u'analysis_reports_counter': session.analysis_reports_counter,
        u'debug_mode': False,
        u'event_labels_counter': session.event_labels_counter,
        u'identifier': session.identifier,
        u'parsers_counter': session.parsers_counter,
        u'preferred_encoding': u'utf-8',
        u'preferred_time_zone': u'UTC',
        u'product_name': u'plaso',
        u'product_version': plaso.__version__,
        u'start_time': session.start_time}

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
    session_identifier = u'{0:s}'.format(uuid.uuid4().get_hex())
    session_completion = sessions.SessionCompletion(
        identifier=session_identifier)
    session_completion.timestamp = timestamp

    self.assertEqual(session_completion.identifier, session_identifier)

    expected_dict = {
        u'aborted': False,
        u'identifier': session_completion.identifier,
        u'timestamp': timestamp}

    test_dict = session_completion.CopyToDict()

    self.assertEqual(test_dict, expected_dict)


class SessionStartTest(shared_test_lib.BaseTestCase):
  """Tests for the session start attribute container."""

  # TODO: replace by GetAttributeNames test
  def testCopyToDict(self):
    """Tests the CopyToDict function."""
    timestamp = int(time.time() * 1000000)
    session_identifier = u'{0:s}'.format(uuid.uuid4().get_hex())
    session_start = sessions.SessionStart(identifier=session_identifier)
    session_start.timestamp = timestamp
    session_start.product_name = u'plaso'
    session_start.product_version = plaso.__version__

    self.assertEqual(session_start.identifier, session_identifier)

    expected_dict = {
        u'debug_mode': False,
        u'identifier': session_start.identifier,
        u'product_name': u'plaso',
        u'product_version': plaso.__version__,
        u'timestamp': timestamp}

    test_dict = session_start.CopyToDict()

    self.assertEqual(test_dict, expected_dict)


if __name__ == '__main__':
  unittest.main()
