#!/usr/bin/python
# -*- coding: utf-8 -*-
"""This file contains the tests for the sessions attribute container objects."""

import time
import unittest
import uuid

import plaso
from plaso.containers import sessions

from tests.containers import test_lib


class SessionCompletionTest(test_lib.AttributeContainerTestCase):
  """Tests for the session completion attributes container object."""

  def testCopyToDict(self):
    """Tests the CopyToDict function."""
    timestamp = int(time.time() * 1000000)
    session_identifier = u'{0:s}'.format(uuid.uuid4().get_hex())
    session_completion = sessions.SessionCompletion(
        identifier=session_identifier)
    session_completion.timestamp = timestamp

    self.assertEquals(session_completion.identifier, session_identifier)

    expected_dict = {
        u'identifier': session_completion.identifier,
        u'timestamp': timestamp}

    test_dict = session_completion.CopyToDict()

    self.assertEqual(test_dict, expected_dict)

  # TODO: add more tests.


class SessionStartTest(test_lib.AttributeContainerTestCase):
  """Tests for the session start attributes container object."""

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
