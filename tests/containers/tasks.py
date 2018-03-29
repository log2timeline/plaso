#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for the tasks attribute containers."""

from __future__ import unicode_literals

import time
import unittest
import uuid

from plaso.containers import tasks

from tests import test_lib as shared_test_lib


class TaskTest(shared_test_lib.BaseTestCase):
  """Tests for the task attribute container."""

  # TODO: replace by GetAttributeNames test
  def testCopyToDict(self):
    """Tests the CopyToDict function."""
    session_identifier = '{0:s}'.format(uuid.uuid4().hex)
    task = tasks.Task(session_identifier=session_identifier)

    self.assertIsNotNone(task.identifier)
    self.assertIsNotNone(task.start_time)
    self.assertIsNone(task.completion_time)

    expected_dict = {
        'aborted': False,
        'identifier': task.identifier,
        'retried': False,
        'session_identifier': task.session_identifier,
        'start_time': task.start_time}

    test_dict = task.CopyToDict()

    self.assertEqual(test_dict, expected_dict)

  def testCreateRetry(self):
    """Tests the CreateRetry function."""
    session_identifier = '{0:s}'.format(uuid.uuid4().hex)
    task = tasks.Task(session_identifier=session_identifier)
    task.path_spec = 'test_pathspec_value'
    retry_task = task.CreateRetry()

    self.assertEqual(task.path_spec, retry_task.path_spec)
    self.assertNotEqual(task.identifier, retry_task.identifier)
    self.assertTrue(task.retried)
    self.assertEqual(task.identifier, retry_task.original_task_identifier)

  # TODO: add tests for CreateTaskCompletion
  # TODO: add tests for CreateTaskStart
  # TODO: add tests for UpdateProcessingTime


class TaskCompletionTest(shared_test_lib.BaseTestCase):
  """Tests for the task completion attribute container."""

  # TODO: replace by GetAttributeNames test
  def testCopyToDict(self):
    """Tests the CopyToDict function."""
    session_identifier = '{0:s}'.format(uuid.uuid4().hex)
    timestamp = int(time.time() * 1000000)
    task_identifier = '{0:s}'.format(uuid.uuid4().hex)
    task_completion = tasks.TaskCompletion(
        identifier=task_identifier, session_identifier=session_identifier)
    task_completion.timestamp = timestamp

    self.assertEqual(task_completion.identifier, task_identifier)

    expected_dict = {
        'aborted': False,
        'identifier': task_completion.identifier,
        'session_identifier': task_completion.session_identifier,
        'timestamp': timestamp}

    test_dict = task_completion.CopyToDict()

    self.assertEqual(test_dict, expected_dict)


class TaskStartTest(shared_test_lib.BaseTestCase):
  """Tests for the task start attribute container."""

  # TODO: replace by GetAttributeNames test
  def testCopyToDict(self):
    """Tests the CopyToDict function."""
    session_identifier = '{0:s}'.format(uuid.uuid4().hex)
    timestamp = int(time.time() * 1000000)
    task_identifier = '{0:s}'.format(uuid.uuid4().hex)
    task_start = tasks.TaskStart(
        identifier=task_identifier, session_identifier=session_identifier)
    task_start.timestamp = timestamp

    self.assertEqual(task_start.identifier, task_identifier)

    expected_dict = {
        'identifier': task_start.identifier,
        'session_identifier': session_identifier,
        'timestamp': timestamp}

    test_dict = task_start.CopyToDict()

    self.assertEqual(test_dict, expected_dict)


if __name__ == '__main__':
  unittest.main()
