#!/usr/bin/python
# -*- coding: utf-8 -*-
"""This file contains the tests for the tasks attribute containers."""

import time
import unittest
import uuid

from plaso.containers import tasks

from tests.containers import test_lib


class TaskTest(test_lib.AttributeContainerTestCase):
  """Tests for the task attributes container."""

  def testCopyToDict(self):
    """Tests the CopyToDict function."""
    session_identifier = u'{0:s}'.format(uuid.uuid4().get_hex())
    task = tasks.Task(session_identifier=session_identifier)

    self.assertIsNotNone(task.identifier)
    self.assertIsNotNone(task.start_time)
    self.assertIsNone(task.completion_time)

    expected_dict = {
        u'aborted': False,
        u'identifier': task.identifier,
        u'session_identifier': task.session_identifier,
        u'start_time': task.start_time}

    test_dict = task.CopyToDict()

    self.assertEqual(test_dict, expected_dict)

  # TODO: add more tests.


class TaskCompletionTest(test_lib.AttributeContainerTestCase):
  """Tests for the task completion attributes container."""

  def testCopyToDict(self):
    """Tests the CopyToDict function."""
    session_identifier = u'{0:s}'.format(uuid.uuid4().get_hex())
    timestamp = int(time.time() * 1000000)
    task_identifier = u'{0:s}'.format(uuid.uuid4().get_hex())
    task_completion = tasks.TaskCompletion(
        identifier=task_identifier, session_identifier=session_identifier)
    task_completion.timestamp = timestamp

    self.assertEquals(task_completion.identifier, task_identifier)

    expected_dict = {
        u'aborted': False,
        u'identifier': task_completion.identifier,
        u'session_identifier': task_completion.session_identifier,
        u'timestamp': timestamp}

    test_dict = task_completion.CopyToDict()

    self.assertEqual(test_dict, expected_dict)

  # TODO: add more tests.


class TaskStartTest(test_lib.AttributeContainerTestCase):
  """Tests for the task start attributes container."""

  def testCopyToDict(self):
    """Tests the CopyToDict function."""
    session_identifier = u'{0:s}'.format(uuid.uuid4().get_hex())
    timestamp = int(time.time() * 1000000)
    task_identifier = u'{0:s}'.format(uuid.uuid4().get_hex())
    task_start = tasks.TaskStart(
        identifier=task_identifier, session_identifier=session_identifier)
    task_start.timestamp = timestamp

    self.assertEquals(task_start.identifier, task_identifier)

    expected_dict = {
        u'identifier': task_start.identifier,
        u'session_identifier': session_identifier,
        u'timestamp': timestamp}

    test_dict = task_start.CopyToDict()

    self.assertEqual(test_dict, expected_dict)

  # TODO: add more tests.


if __name__ == '__main__':
  unittest.main()
