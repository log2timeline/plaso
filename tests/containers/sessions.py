#!/usr/bin/python
# -*- coding: utf-8 -*-
"""This file contains the tests for the sessions attribute container objects."""

import unittest
import uuid

import plaso
from plaso.containers import sessions

from tests.containers import test_lib


class SessionCompletionTest(test_lib.AttributeContainerTestCase):
  """Tests for the session completion attributes container object."""

  def testCopyToDict(self):
    """Tests the CopyToDict function."""
    session_identifier = u'{0:s}'.format(uuid.uuid4().get_hex())
    session_completion = sessions.SessionCompletion(
        identifier=session_identifier)

    expected_dict = {
        u'identifier': session_completion.identifier,
        u'timestamp': session_completion.timestamp}

    test_dict = session_completion.CopyToDict()

    self.assertEqual(test_dict, expected_dict)

  # TODO: add more tests.


class SessionStartTest(test_lib.AttributeContainerTestCase):
  """Tests for the session start attributes container object."""

  def testCopyToDict(self):
    """Tests the CopyToDict function."""
    session_start = sessions.SessionStart()

    self.assertIsNotNone(session_start.identifier)

    expected_dict = {
        u'command_line_arguments': u'',
        u'debug_mode': False,
        u'filter_expression': u'',
        u'filter_file': u'',
        u'identifier': session_start.identifier,
        u'parser_filter_expression': u'',
        u'preferred_encoding': u'utf-8',
        u'product_name': u'plaso',
        u'product_version': plaso.GetVersion(),
        u'timestamp': session_start.timestamp}

    test_dict = session_start.CopyToDict()

    self.assertEqual(test_dict, expected_dict)

  # TODO: add more tests.


if __name__ == '__main__':
  unittest.main()
