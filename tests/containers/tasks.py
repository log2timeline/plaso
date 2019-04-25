#!/usr/bin/env python3
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
        'has_retry': False,
        'identifier': task.identifier,
        'session_identifier': task.session_identifier,
        'start_time': task.start_time}

    test_dict = task.CopyToDict()

    self.assertEqual(test_dict, expected_dict)

  def testCreateRetryTask(self):
    """Tests the CreateRetryTask function."""
    session_identifier = '{0:s}'.format(uuid.uuid4().hex)
    task = tasks.Task(session_identifier=session_identifier)
    task.path_spec = 'test_path_spec'

    retry_task = task.CreateRetryTask()
    self.assertNotEqual(retry_task.identifier, task.identifier)
    self.assertTrue(task.has_retry)
    self.assertFalse(retry_task.has_retry)
    self.assertEqual(retry_task.path_spec, task.path_spec)

  def testCreateTaskCompletion(self):
    """Tests the CreateTaskCompletion function."""
    session_identifier = '{0:s}'.format(uuid.uuid4().hex)
    task = tasks.Task(session_identifier=session_identifier)

    task_completion = task.CreateTaskCompletion()
    self.assertIsNotNone(task_completion)

  def testCreateTaskStart(self):
    """Tests the CreateTaskStart function."""
    session_identifier = '{0:s}'.format(uuid.uuid4().hex)
    task = tasks.Task(session_identifier=session_identifier)

    task_start = task.CreateTaskStart()
    self.assertIsNotNone(task_start)

  def testUpdateProcessingTime(self):
    """Tests the UpdateProcessingTime function."""
    session_identifier = '{0:s}'.format(uuid.uuid4().hex)
    task = tasks.Task(session_identifier=session_identifier)

    self.assertIsNone(task.last_processing_time)

    task.UpdateProcessingTime()
    self.assertIsNotNone(task.last_processing_time)


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
