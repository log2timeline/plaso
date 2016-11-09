#!/usr/bin/python
# -*- coding: utf-8 -*-
"""This file contains the tests for the sessions attribute containers."""

import time
import unittest
import uuid

import plaso
from plaso.containers import sessions

from tests import test_lib as shared_test_lib


class SessionTest(shared_test_lib.BaseTestCase):
  """Tests for the session attributes container."""

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
        u'product_name': u'plaso',
        u'product_version': plaso.GetVersion(),
        u'start_time': session.start_time}

    test_dict = session.CopyToDict()

    self.assertEqual(test_dict, expected_dict)

  # TODO: add more tests.


class SessionCompletionTest(shared_test_lib.BaseTestCase):
  """Tests for the session completion attributes container."""

  def testCopyToDict(self):
    """Tests the CopyToDict function."""
    timestamp = int(time.time() * 1000000)
    session_identifier = u'{0:s}'.format(uuid.uuid4().get_hex())
    session_completion = sessions.SessionCompletion(
        identifier=session_identifier)
    session_completion.timestamp = timestamp

    self.assertEquals(session_completion.identifier, session_identifier)

    expected_dict = {
        u'aborted': False,
        u'identifier': session_completion.identifier,
        u'timestamp': timestamp}

    test_dict = session_completion.CopyToDict()

    self.assertEqual(test_dict, expected_dict)

  # TODO: add more tests.


class SessionStartTest(shared_test_lib.BaseTestCase):
  """Tests for the session start attributes container."""

  def testCopyToDict(self):
    """Tests the CopyToDict function."""
    timestamp = int(time.time() * 1000000)
    session_identifier = u'{0:s}'.format(uuid.uuid4().get_hex())
    session_start = sessions.SessionStart(identifier=session_identifier)
    session_start.timestamp = timestamp
    session_start.product_name = u'plaso'
    session_start.product_version = plaso.GetVersion()

    self.assertEquals(session_start.identifier, session_identifier)

    expected_dict = {
        u'debug_mode': False,
        u'identifier': session_start.identifier,
        u'product_name': u'plaso',
        u'product_version': plaso.GetVersion(),
        u'timestamp': timestamp}

    test_dict = session_start.CopyToDict()

    self.assertEqual(test_dict, expected_dict)

  # TODO: add more tests.


if __name__ == '__main__':
  unittest.main()
