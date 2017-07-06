#!/usr/bin/python
# -*- coding: utf-8 -*-
"""This file contains tests for the task manager."""

import time
import unittest

from dfvfs.lib import definitions as dfvfs_definitions

from plaso.containers import tasks
from plaso.multi_processing import task_manager

from tests import test_lib as shared_test_lib


class TaskManagerTestCase(shared_test_lib.BaseTestCase):
  """Tests for the TaskManager."""

  # pylint: disable=protected-access

  _TEST_SESSION_IDENTIFIER = u'4'

  def testCreateTask(self):
    """Tests the CreateTask methods."""
    manager = task_manager.TaskManager()
    task = manager.CreateTask(self._TEST_SESSION_IDENTIFIER)
    self.assertIsInstance(task, tasks.Task)
    self.assertEqual(task.session_identifier, self._TEST_SESSION_IDENTIFIER)
    self.assertIsNotNone(task.identifier)

  def testTaskProcessing(self):
    """Tests the UpdateTaskAsProcessing and GetTasksCheckMerge methods."""
    manager = task_manager.TaskManager()
    tasks_processing = manager.GetTasksCheckMerge()
    self.assertEqual(0, len(tasks_processing))

    task = manager.CreateTask(self._TEST_SESSION_IDENTIFIER)
    self.assertIsNone(task.last_processing_time)

    manager.UpdateTaskAsProcessing(task)
    tasks_processing = manager.GetTasksCheckMerge()
    self.assertEqual(1, len(tasks_processing))
    task = tasks_processing[0]
    self.assertIsNotNone(task.last_processing_time)

  def testPendingMerge(self):
    """Tests the UpdateTaskPendingMerge and GetTaskPending merge methods."""
    manager = task_manager.TaskManager()
    task_pending_merge = manager.GetTaskPendingMerge(None)
    self.assertIsNone(task_pending_merge)

    task = manager.CreateTask(self._TEST_SESSION_IDENTIFIER)
    with self.assertRaises(KeyError):
      manager.UpdateTaskAsPendingMerge(task)
    manager.UpdateTaskAsProcessing(task)

    task_pending_merge = manager.GetTaskPendingMerge(None)
    self.assertIsNone(task_pending_merge)

    task.storage_file_size = 10
    manager.UpdateTaskAsPendingMerge(task)
    task_pending_merge = manager.GetTaskPendingMerge(None)
    self.assertEqual(task, task_pending_merge)
    manager.CompleteTask(task)

    small_task = manager.CreateTask(self._TEST_SESSION_IDENTIFIER)
    small_task.storage_file_size = 100
    manager.UpdateTaskAsProcessing(small_task)
    large_task = manager.CreateTask(self._TEST_SESSION_IDENTIFIER)
    large_task.storage_file_size = 1000
    manager.UpdateTaskAsProcessing(large_task)
    directory_task = manager.CreateTask(self._TEST_SESSION_IDENTIFIER)
    directory_task.file_entry_type = dfvfs_definitions.FILE_ENTRY_TYPE_DIRECTORY
    directory_task.storage_file_size = 1000
    manager.UpdateTaskAsProcessing(directory_task)

    manager.UpdateTaskAsPendingMerge(small_task)
    manager.UpdateTaskAsPendingMerge(directory_task)
    # Test that a directory task preempts a small task.
    merging_task = manager.GetTaskPendingMerge(small_task)
    self.assertEqual(merging_task, directory_task)

    # Test that a small task is not preempted by a large task.
    manager.UpdateTaskAsPendingMerge(large_task)
    merging_task = manager.GetTaskPendingMerge(small_task)
    self.assertEqual(merging_task, small_task)

  def testTaskAbandonment(self):
    """Tests the abandoning and adoption of tasks"""
    manager = task_manager.TaskManager()
    task = manager.CreateTask(self._TEST_SESSION_IDENTIFIER)
    self.assertEqual(manager.GetAbandonedTasks(), [])
    self.assertTrue(manager.HasActiveTasks())
    self.assertIsNone(manager.GetRetryTask())

    manager.UpdateTaskAsProcessing(task)
    timestamp = int(time.time() * 1000000)
    inactive_time = timestamp - task_manager.TaskManager._TASK_INACTIVE_TIME
    task.last_processing_time = inactive_time - 1
    # HasActiveTasks is responsible for marking tasks as abandoned.
    self.assertFalse(manager.HasActiveTasks())
    self.assertTrue(manager.HasPendingTasks())
    abandoned_tasks = manager.GetAbandonedTasks()
    self.assertIn(task, abandoned_tasks)

    retry_task = manager.GetRetryTask()
    self.assertIsNotNone(retry_task)
    self.assertEqual(task.identifier, retry_task.original_task_identifier)
    self.assertTrue(task.retried)
    manager.CompleteTask(retry_task)

    manager.AdoptTask(task)
    self.assertEqual(manager.GetAbandonedTasks(), [])
    self.assertTrue(manager.HasActiveTasks())

  # TODO: Add tests for updating tasks.


if __name__ == '__main__':
  unittest.main()
