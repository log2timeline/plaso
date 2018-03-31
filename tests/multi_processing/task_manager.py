#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""This file contains tests for the task manager."""

from __future__ import unicode_literals

import time
import unittest

from dfvfs.lib import definitions as dfvfs_definitions

from plaso.containers import tasks
from plaso.multi_processing import task_manager

from tests import test_lib as shared_test_lib


class PendingMergeTaskHeapTest(shared_test_lib.BaseTestCase):
  """Tests for the heap to manage pending merge tasks."""

  # pylint: disable=protected-access

  def testContains(self):
    """Tests the __contains__ function."""
    task = tasks.Task()
    task.storage_file_size = 10

    heap = task_manager._PendingMergeTaskHeap()
    heap.PushTask(task)

    self.assertIn(task.identifier, heap)

  def testLengthProperty(self):
    """Tests the __len__ function."""
    task = tasks.Task()
    task.storage_file_size = 10

    heap = task_manager._PendingMergeTaskHeap()
    self.assertEqual(len(heap), 0)

    heap.PushTask(task)
    self.assertEqual(len(heap), 1)

  def testPeekTask(self):
    """Tests the PeekTask function."""
    task = tasks.Task()
    task.storage_file_size = 10

    heap = task_manager._PendingMergeTaskHeap()

    result_task = heap.PeekTask()
    self.assertIsNone(result_task)

    heap.PushTask(task)
    self.assertEqual(len(heap), 1)

    result_task = heap.PeekTask()
    self.assertEqual(len(heap), 1)
    self.assertEqual(result_task, task)

  def testPopTask(self):
    """Tests the PopTask function."""
    task = tasks.Task()
    task.storage_file_size = 10

    heap = task_manager._PendingMergeTaskHeap()

    result_task = heap.PopTask()
    self.assertIsNone(result_task)

    heap.PushTask(task)
    self.assertEqual(len(heap), 1)

    result_task = heap.PopTask()
    self.assertEqual(len(heap), 0)
    self.assertEqual(result_task, task)

  def testPushTask(self):
    """Tests the PushTask function."""
    task = tasks.Task()
    task.storage_file_size = 10

    heap = task_manager._PendingMergeTaskHeap()
    self.assertEqual(len(heap), 0)

    heap.PushTask(task)
    self.assertEqual(len(heap), 1)

    task = tasks.Task()
    task.storage_file_size = 100

    heap.PushTask(task)
    self.assertEqual(len(heap), 2)

    task = tasks.Task()
    with self.assertRaises(ValueError):
      heap.PushTask(task)


class TaskManagerTest(shared_test_lib.BaseTestCase):
  """Tests for the task manager."""

  # pylint: disable=protected-access

  _TEST_SESSION_IDENTIFIER = 'b362ab408b054cb08cf69b4c7989df89'

  def testHasTasksPendingMerge(self):
    """Tests the _HasTasksPendingMerge function."""
    manager = task_manager.TaskManager()

    result = manager._HasTasksPendingMerge()
    self.assertFalse(result)

    # TODO: test True condition.

  def testHasTasksPendingRetry(self):
    """Tests the _HasTasksPendingRetry function."""
    manager = task_manager.TaskManager()

    result = manager._HasTasksPendingRetry()
    self.assertFalse(result)

    # TODO: test True condition.

  def testTaskIsRetriable(self):
    """Tests the _TaskIsRetriable function."""
    task = tasks.Task()

    manager = task_manager.TaskManager()

    result = manager._TaskIsRetriable(task)
    self.assertTrue(result)

    task.retried = True
    result = manager._TaskIsRetriable(task)
    self.assertFalse(result)

  def testTimeoutTasks(self):
    """Tests the _TimeoutTasks function."""
    task = tasks.Task()
    task.storage_file_size = 10

    manager = task_manager.TaskManager()

    self.assertEqual(len(manager._tasks_abandoned), 0)

    tasks_for_timeout = {}
    manager._TimeoutTasks(tasks_for_timeout)
    self.assertEqual(len(manager._tasks_abandoned), 0)

    tasks_for_timeout = {task.identifier: task}

    manager._TimeoutTasks(tasks_for_timeout)
    self.assertEqual(len(manager._tasks_abandoned), 0)
    self.assertNotEqual(tasks_for_timeout, {})

    task.start_time -= 2 * manager._TASK_INACTIVE_TIME

    manager._TimeoutTasks(tasks_for_timeout)
    self.assertEqual(len(manager._tasks_abandoned), 1)
    self.assertEqual(tasks_for_timeout, {})

  def testCreateTask(self):
    """Tests the CreateTask function."""
    manager = task_manager.TaskManager()

    self.assertEqual(len(manager._tasks_queued), 0)

    task = manager.CreateTask(self._TEST_SESSION_IDENTIFIER)
    self.assertEqual(len(manager._tasks_queued), 1)

    self.assertIsInstance(task, tasks.Task)
    self.assertEqual(task.session_identifier, self._TEST_SESSION_IDENTIFIER)
    self.assertIsNotNone(task.identifier)
    self.assertIsNone(task.last_processing_time)

  def testCompleteTask(self):
    """Tests the CompleteTask function."""
    manager = task_manager.TaskManager()

    task = manager.CreateTask(self._TEST_SESSION_IDENTIFIER)
    self.assertEqual(len(manager._tasks_queued), 1)

    manager.CompleteTask(task)
    self.assertEqual(len(manager._tasks_queued), 0)

    # TODO: improve test coverage.

  def testGetAbandonedTasks(self):
    """Tests the GetAbandonedTasks function."""
    manager = task_manager.TaskManager()

    result_tasks = manager.GetAbandonedTasks()
    self.assertEqual(result_tasks, [])

    # TODO: improve test coverage.

  def testGetRetryTask(self):
    """Tests the GetRetryTask function."""
    manager = task_manager.TaskManager()

    result_task = manager.GetRetryTask()
    self.assertIsNone(result_task)

    # TODO: improve test coverage.

  def testGetStatusInformation(self):
    """Tests the GetStatusInformation function."""
    manager = task_manager.TaskManager()
    manager.CreateTask(self._TEST_SESSION_IDENTIFIER)

    result_status = manager.GetStatusInformation()
    self.assertIsNotNone(result_status)

    self.assertEqual(result_status.number_of_abandoned_tasks, 0)
    self.assertEqual(result_status.number_of_queued_tasks, 1)
    self.assertEqual(result_status.number_of_tasks_pending_merge, 0)
    self.assertEqual(result_status.number_of_tasks_processing, 0)
    self.assertEqual(result_status.total_number_of_tasks, 1)

  def testGetTasksCheckMerge(self):
    """Tests the GetTasksCheckMerge function."""
    manager = task_manager.TaskManager()
    task = manager.CreateTask(self._TEST_SESSION_IDENTIFIER)

    result_tasks = manager.GetTasksCheckMerge()
    self.assertEqual(result_tasks, [task])

  def testGetTaskPendingMerge(self):
    """Tests the GetTaskPendingMerge function."""
    manager = task_manager.TaskManager()
    task = manager.CreateTask(self._TEST_SESSION_IDENTIFIER)

    result_task = manager.GetTaskPendingMerge(None)
    self.assertIsNone(result_task)

    # TODO: improve test coverage.

  def testHasPendingTasks(self):
    """Tests the HasPendingTasks function."""
    manager = task_manager.TaskManager()

    result = manager.HasPendingTasks()
    self.assertFalse(result)

    manager.CreateTask(self._TEST_SESSION_IDENTIFIER)

    result = manager.HasPendingTasks()
    self.assertTrue(result)

    # TODO: improve test coverage.

  def testUpdateTaskAsPendingMerge(self):
    """Tests the UpdateTaskAsPendingMerge function."""
    manager = task_manager.TaskManager()

    self.assertEqual(len(manager._tasks_queued), 0)
    self.assertEqual(len(manager._tasks_processing), 0)
    self.assertEqual(len(manager._tasks_abandoned), 0)
    self.assertEqual(len(manager._tasks_pending_merge), 0)

    task = manager.CreateTask(self._TEST_SESSION_IDENTIFIER)
    task.storage_file_size = 10

    self.assertEqual(len(manager._tasks_queued), 1)
    self.assertEqual(len(manager._tasks_processing), 0)
    self.assertEqual(len(manager._tasks_abandoned), 0)
    self.assertEqual(len(manager._tasks_pending_merge), 0)

    # Indicate to the task manager that a queued task is pending merge.
    manager.UpdateTaskAsPendingMerge(task)

    self.assertEqual(len(manager._tasks_queued), 0)
    self.assertEqual(len(manager._tasks_processing), 0)
    self.assertEqual(len(manager._tasks_abandoned), 0)
    self.assertEqual(len(manager._tasks_pending_merge), 1)

    # Indicate to the task manager that a processing task is pending merge.
    task = manager.CreateTask(self._TEST_SESSION_IDENTIFIER)
    task.storage_file_size = 10

    self.assertEqual(len(manager._tasks_queued), 1)
    self.assertEqual(len(manager._tasks_processing), 0)
    self.assertEqual(len(manager._tasks_abandoned), 0)
    self.assertEqual(len(manager._tasks_pending_merge), 1)

    manager.UpdateTaskAsProcessingByIdentifier(task.identifier)

    self.assertEqual(len(manager._tasks_queued), 0)
    self.assertEqual(len(manager._tasks_processing), 1)
    self.assertEqual(len(manager._tasks_abandoned), 0)
    self.assertEqual(len(manager._tasks_pending_merge), 1)

    manager.UpdateTaskAsPendingMerge(task)

    self.assertEqual(len(manager._tasks_queued), 0)
    self.assertEqual(len(manager._tasks_processing), 0)
    self.assertEqual(len(manager._tasks_abandoned), 0)
    self.assertEqual(len(manager._tasks_pending_merge), 2)

    # Indicate to the task manager that an abandoned task is pending merge.
    task = manager.CreateTask(self._TEST_SESSION_IDENTIFIER)
    task.storage_file_size = 10

    self.assertEqual(len(manager._tasks_queued), 1)
    self.assertEqual(len(manager._tasks_processing), 0)
    self.assertEqual(len(manager._tasks_abandoned), 0)
    self.assertEqual(len(manager._tasks_pending_merge), 2)

    task.start_time -= 2 * manager._TASK_INACTIVE_TIME

    manager._TimeoutTasks(manager._tasks_queued)

    self.assertEqual(len(manager._tasks_queued), 0)
    self.assertEqual(len(manager._tasks_processing), 0)
    self.assertEqual(len(manager._tasks_abandoned), 1)
    self.assertEqual(len(manager._tasks_pending_merge), 2)

    manager.UpdateTaskAsPendingMerge(task)

    self.assertEqual(len(manager._tasks_queued), 0)
    self.assertEqual(len(manager._tasks_processing), 0)
    self.assertEqual(len(manager._tasks_abandoned), 0)
    self.assertEqual(len(manager._tasks_pending_merge), 3)

    # Indicate to the task manager that an unknown task is pending merge.
    task = tasks.Task()
    task.storage_file_size = 10

    with self.assertRaises(KeyError):
       manager.UpdateTaskAsProcessingByIdentifier(task.identifier)

  def testUpdateTasksAsPendingMerge(self):
    """Tests the UpdateTasksAsPendingMerge function."""
    manager = task_manager.TaskManager()

    self.assertEqual(len(manager._tasks_queued), 0)
    self.assertEqual(len(manager._tasks_processing), 0)
    self.assertEqual(len(manager._tasks_abandoned), 0)
    self.assertEqual(len(manager._tasks_pending_merge), 0)

    task1 = manager.CreateTask(self._TEST_SESSION_IDENTIFIER)
    task1.storage_file_size = 10

    task2 = manager.CreateTask(self._TEST_SESSION_IDENTIFIER)
    task2.storage_file_size = 10

    self.assertEqual(len(manager._tasks_queued), 2)
    self.assertEqual(len(manager._tasks_processing), 0)
    self.assertEqual(len(manager._tasks_abandoned), 0)
    self.assertEqual(len(manager._tasks_pending_merge), 0)

    manager.UpdateTasksAsPendingMerge([task1, task2])

    self.assertEqual(len(manager._tasks_queued), 0)
    self.assertEqual(len(manager._tasks_processing), 0)
    self.assertEqual(len(manager._tasks_abandoned), 0)
    self.assertEqual(len(manager._tasks_pending_merge), 2)

  def testUpdateTaskAsProcessingByIdentifier(self):
    """Tests the UpdateTaskAsProcessingByIdentifier function."""
    manager = task_manager.TaskManager()

    self.assertEqual(len(manager._tasks_queued), 0)
    self.assertEqual(len(manager._tasks_processing), 0)
    self.assertEqual(len(manager._tasks_abandoned), 0)
    self.assertEqual(len(manager._tasks_pending_merge), 0)

    task = manager.CreateTask(self._TEST_SESSION_IDENTIFIER)
    self.assertIsNone(task.last_processing_time)

    self.assertEqual(len(manager._tasks_queued), 1)
    self.assertEqual(len(manager._tasks_processing), 0)
    self.assertEqual(len(manager._tasks_abandoned), 0)
    self.assertEqual(len(manager._tasks_pending_merge), 0)

    # Indicate to the task manager that the task is processing.
    manager.UpdateTaskAsProcessingByIdentifier(task.identifier)

    self.assertEqual(len(manager._tasks_queued), 0)
    self.assertEqual(len(manager._tasks_processing), 1)
    self.assertEqual(len(manager._tasks_abandoned), 0)
    self.assertEqual(len(manager._tasks_pending_merge), 0)

    # Check if the last processing time was set.
    self.assertIsNotNone(task.last_processing_time)

    last_processing_time = task.last_processing_time

    # Indicate to the task manager that the task is still processing.
    manager.UpdateTaskAsProcessingByIdentifier(task.identifier)

    self.assertEqual(len(manager._tasks_queued), 0)
    self.assertEqual(len(manager._tasks_processing), 1)
    self.assertEqual(len(manager._tasks_abandoned), 0)
    self.assertEqual(len(manager._tasks_pending_merge), 0)

    # Check if the last processing time was updated.
    self.assertGreater(task.last_processing_time, last_processing_time)

    # TODO: test abandoned task

    # Indicate to the task manager that the task is pending merge.
    task.storage_file_size = 10

    manager.UpdateTaskAsPendingMerge(task)

    self.assertEqual(len(manager._tasks_queued), 0)
    self.assertEqual(len(manager._tasks_processing), 0)
    self.assertEqual(len(manager._tasks_abandoned), 0)
    self.assertEqual(len(manager._tasks_pending_merge), 1)

    manager.UpdateTaskAsProcessingByIdentifier(task.identifier)

    self.assertEqual(len(manager._tasks_queued), 0)
    self.assertEqual(len(manager._tasks_processing), 0)
    self.assertEqual(len(manager._tasks_abandoned), 0)
    self.assertEqual(len(manager._tasks_pending_merge), 1)

    # Indicate to the task manager that an unknown task is pending merge.
    task = tasks.Task()

    with self.assertRaises(KeyError):
       manager.UpdateTaskAsProcessingByIdentifier(task.identifier)

  # TODO: determine what to do with the following tests.

  def testPendingMerge(self):
    """Tests the UpdateTaskPendingMerge and GetTaskPending merge methods."""
    manager = task_manager.TaskManager()
    task_pending_merge = manager.GetTaskPendingMerge(None)
    self.assertIsNone(task_pending_merge)

    task = manager.CreateTask(self._TEST_SESSION_IDENTIFIER)
    with self.assertRaises(ValueError):
      manager.UpdateTaskAsPendingMerge(task)
    manager.UpdateTaskAsProcessingByIdentifier(task.identifier)

    task_pending_merge = manager.GetTaskPendingMerge(None)
    self.assertIsNone(task_pending_merge)

    task.storage_file_size = 10
    manager.UpdateTaskAsPendingMerge(task)
    task_pending_merge = manager.GetTaskPendingMerge(None)
    self.assertEqual(task, task_pending_merge)
    manager.CompleteTask(task)

    small_task = manager.CreateTask(self._TEST_SESSION_IDENTIFIER)
    small_task.storage_file_size = 100
    manager.UpdateTaskAsProcessingByIdentifier(small_task.identifier)
    large_task = manager.CreateTask(self._TEST_SESSION_IDENTIFIER)
    large_task.storage_file_size = 1000
    manager.UpdateTaskAsProcessingByIdentifier(large_task.identifier)
    directory_task = manager.CreateTask(self._TEST_SESSION_IDENTIFIER)
    directory_task.file_entry_type = dfvfs_definitions.FILE_ENTRY_TYPE_DIRECTORY
    directory_task.storage_file_size = 1000
    manager.UpdateTaskAsProcessingByIdentifier(directory_task.identifier)

    manager.UpdateTaskAsPendingMerge(small_task)
    # Simulate a delayed update from a worker that the task is still processing
    manager.UpdateTaskAsProcessingByIdentifier(small_task.identifier)
    manager.UpdateTaskAsPendingMerge(directory_task)
    # Test that a directory task preempts a small task.
    merging_task = manager.GetTaskPendingMerge(small_task)
    self.assertEqual(merging_task, directory_task)
    self.assertEqual(manager._tasks_merging.keys(), [directory_task.identifier])
    manager.CompleteTask(directory_task)

    # Test that a small task is not preempted by a large task.
    manager.UpdateTaskAsPendingMerge(large_task)
    merging_task = manager.GetTaskPendingMerge(small_task)
    self.assertEqual(merging_task, small_task)
    self.assertEqual(manager._tasks_merging.keys(), [small_task.identifier])

  def testTaskAbandonment(self):
    """Tests the abandoning and adoption of tasks"""
    manager = task_manager.TaskManager()
    task = manager.CreateTask(self._TEST_SESSION_IDENTIFIER)
    self.assertEqual(manager.GetAbandonedTasks(), [])
    self.assertTrue(manager.HasPendingTasks())
    self.assertIsNone(manager.GetRetryTask())

    manager.UpdateTaskAsProcessingByIdentifier(task.identifier)
    timestamp = int(time.time() * 1000000)
    inactive_time = timestamp - task_manager.TaskManager._TASK_INACTIVE_TIME
    task.last_processing_time = inactive_time - 1
    # HasPendingTasks is responsible for marking tasks as abandoned, and it
    # should still return True if the task is abandoned, as it needs to be
    # retried.
    self.assertTrue(manager.HasPendingTasks())
    abandoned_tasks = manager.GetAbandonedTasks()
    self.assertIn(task, abandoned_tasks)
    self.assertTrue(manager._TaskIsRetriable(task))

    retry_task = manager.GetRetryTask()
    self.assertIsNotNone(retry_task)
    self.assertEqual(task.identifier, retry_task.original_task_identifier)
    self.assertTrue(task.retried)
    self.assertFalse(manager._TaskIsRetriable(retry_task))
    manager.CompleteTask(retry_task)

    manager.UpdateTaskAsProcessingByIdentifier(task.identifier)
    self.assertEqual(manager.GetAbandonedTasks(), [])
    self.assertTrue(manager.HasPendingTasks())

  # TODO: Add tests for updating tasks.


if __name__ == '__main__':
  unittest.main()
