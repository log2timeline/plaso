#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""This file contains tests for the task manager."""

import time
import unittest

from dfvfs.lib import definitions as dfvfs_definitions

from plaso.containers import tasks
from plaso.lib import definitions
from plaso.multi_process import task_manager

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

  def testLength(self):
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
    task.file_entry_type = dfvfs_definitions.FILE_ENTRY_TYPE_FILE
    task.storage_file_size = 10

    heap = task_manager._PendingMergeTaskHeap()
    self.assertEqual(len(heap), 0)

    heap.PushTask(task)
    self.assertEqual(len(heap), 1)

    task = tasks.Task()
    task.file_entry_type = dfvfs_definitions.FILE_ENTRY_TYPE_FILE
    task.storage_file_size = 100

    heap.PushTask(task)
    self.assertEqual(len(heap), 2)
    self.assertIsNotNone(heap._heap[0])
    self.assertEqual(heap._heap[0][0], 10)

    task = tasks.Task()
    task.file_entry_type = dfvfs_definitions.FILE_ENTRY_TYPE_DIRECTORY
    task.storage_file_size = 1000

    heap.PushTask(task)
    self.assertEqual(len(heap), 3)
    self.assertIsNotNone(heap._heap[0])
    self.assertEqual(heap._heap[0][0], -1)

    task = tasks.Task()
    with self.assertRaises(ValueError):
      heap.PushTask(task)


class TaskManagerTest(shared_test_lib.BaseTestCase):
  """Tests for the task manager."""

  # pylint: disable=protected-access

  _TEST_SESSION_IDENTIFIER = 'b362ab408b054cb08cf69b4c7989df89'

  def testAbandonInactiveProcessingTasks(self):
    """Tests the _AbandonInactiveProcessingTasks function."""
    manager = task_manager.TaskManager()

    test_tasks = []
    for _ in range(2):
      task = manager.CreateTask(self._TEST_SESSION_IDENTIFIER)
      manager.UpdateTaskAsProcessingByIdentifier(task.identifier)
      self.assertIsNotNone(task.last_processing_time)
      test_tasks.append(task)

    self.assertEqual(len(manager._tasks_queued), 0)
    self.assertEqual(len(manager._tasks_processing), 2)
    self.assertEqual(len(manager._tasks_pending_merge), 0)
    self.assertEqual(len(manager._tasks_abandoned), 0)

    manager._AbandonInactiveProcessingTasks()

    self.assertEqual(len(manager._tasks_queued), 0)
    self.assertEqual(len(manager._tasks_processing), 2)
    self.assertEqual(len(manager._tasks_pending_merge), 0)
    self.assertEqual(len(manager._tasks_abandoned), 0)

    for task in test_tasks:
      task.last_processing_time -= (
          2 * manager._TASK_INACTIVE_TIME * definitions.MICROSECONDS_PER_SECOND)

    manager._AbandonInactiveProcessingTasks()

    self.assertEqual(len(manager._tasks_queued), 0)
    self.assertEqual(len(manager._tasks_processing), 0)
    self.assertEqual(len(manager._tasks_pending_merge), 0)
    self.assertEqual(len(manager._tasks_abandoned), 2)

  def testAbandonQueuedTasks(self):
    """Tests the _AbandonQueuedTasks function."""
    manager = task_manager.TaskManager()

    test_tasks = [
        manager.CreateTask(self._TEST_SESSION_IDENTIFIER) for _ in range(2)]

    for task in test_tasks:
      self.assertIsNotNone(task.start_time)

    self.assertEqual(len(manager._tasks_queued), 2)
    self.assertEqual(len(manager._tasks_processing), 0)
    self.assertEqual(len(manager._tasks_pending_merge), 0)
    self.assertEqual(len(manager._tasks_abandoned), 0)

    manager._AbandonQueuedTasks()

    self.assertEqual(len(manager._tasks_queued), 0)
    self.assertEqual(len(manager._tasks_processing), 0)
    self.assertEqual(len(manager._tasks_pending_merge), 0)
    self.assertEqual(len(manager._tasks_abandoned), 2)

  def testGetTaskPendingRetry(self):
    """Tests the _GetTaskPendingRetry function."""
    manager = task_manager.TaskManager()

    test_tasks = [
        manager.CreateTask(self._TEST_SESSION_IDENTIFIER) for _ in range(2)]

    self.assertEqual(len(manager._tasks_queued), 2)
    self.assertEqual(len(manager._tasks_abandoned), 0)

    result_task = manager._GetTaskPendingRetry()
    self.assertIsNone(result_task)

    self.assertEqual(len(manager._tasks_queued), 2)
    self.assertEqual(len(manager._tasks_abandoned), 0)

    manager._AbandonQueuedTasks()

    self.assertEqual(len(manager._tasks_queued), 0)
    self.assertEqual(len(manager._tasks_abandoned), 2)

    result_task = manager._GetTaskPendingRetry()
    self.assertIn(result_task, test_tasks)

  def testHasTasksPendingMerge(self):
    """Tests the _HasTasksPendingMerge function."""
    manager = task_manager.TaskManager()

    test_tasks = []
    for _ in range(2):
      task = manager.CreateTask(self._TEST_SESSION_IDENTIFIER)
      task.storage_file_size = 10
      test_tasks.append(task)

    result = manager._HasTasksPendingMerge()
    self.assertFalse(result)

    for task in test_tasks:
      manager.UpdateTaskAsPendingMerge(task)

    result = manager._HasTasksPendingMerge()
    self.assertTrue(result)

  def testHasTasksPendingRetry(self):
    """Tests the _HasTasksPendingRetry function."""
    manager = task_manager.TaskManager()

    for _ in range(2):
      manager.CreateTask(self._TEST_SESSION_IDENTIFIER)

    result = manager._HasTasksPendingRetry()
    self.assertFalse(result)

    manager._AbandonQueuedTasks()

    result = manager._HasTasksPendingRetry()
    self.assertTrue(result)

  def testUpdateLatestProcessingTime(self):
    """Tests the _UpdateLatestProcessingTime function."""
    manager = task_manager.TaskManager()
    task = manager.CreateTask(self._TEST_SESSION_IDENTIFIER)
    task.UpdateProcessingTime()

    manager._UpdateLatestProcessingTime(task)

  def testCheckTaskToMerge(self):
    """Tests the CheckTaskToMerge function."""
    manager = task_manager.TaskManager()

    self.assertEqual(len(manager._tasks_queued), 0)
    self.assertEqual(len(manager._tasks_processing), 0)
    self.assertEqual(len(manager._tasks_pending_merge), 0)
    self.assertEqual(len(manager._tasks_abandoned), 0)

    # Test with queued task.
    task = manager.CreateTask(self._TEST_SESSION_IDENTIFIER)
    task.storage_file_size = 10

    self.assertEqual(len(manager._tasks_queued), 1)
    self.assertEqual(len(manager._tasks_processing), 0)
    self.assertEqual(len(manager._tasks_pending_merge), 0)
    self.assertEqual(len(manager._tasks_abandoned), 0)

    result = manager.CheckTaskToMerge(task)
    self.assertTrue(result)

    # Test with processing task.
    manager.UpdateTaskAsProcessingByIdentifier(task.identifier)

    self.assertEqual(len(manager._tasks_queued), 0)
    self.assertEqual(len(manager._tasks_processing), 1)
    self.assertEqual(len(manager._tasks_pending_merge), 0)
    self.assertEqual(len(manager._tasks_merging), 0)

    result = manager.CheckTaskToMerge(task)
    self.assertTrue(result)

    # Test with abandoned task.
    task.last_processing_time -= (
        2 * manager._TASK_INACTIVE_TIME * definitions.MICROSECONDS_PER_SECOND)

    manager._AbandonInactiveProcessingTasks()

    self.assertEqual(len(manager._tasks_queued), 0)
    self.assertEqual(len(manager._tasks_processing), 0)
    self.assertEqual(len(manager._tasks_pending_merge), 0)
    self.assertEqual(len(manager._tasks_abandoned), 1)

    result = manager.CheckTaskToMerge(task)
    self.assertTrue(result)

    # Test with abandoned task that is retried.
    retry_task = manager.CreateRetryTask()
    self.assertIsNotNone(retry_task)

    self.assertEqual(len(manager._tasks_queued), 1)
    self.assertEqual(len(manager._tasks_processing), 0)
    self.assertEqual(len(manager._tasks_pending_merge), 0)
    self.assertEqual(len(manager._tasks_abandoned), 1)

    result = manager.CheckTaskToMerge(task)
    self.assertFalse(result)

    # Test status of task is unknown.
    del manager._tasks_abandoned[task.identifier]

    self.assertEqual(len(manager._tasks_queued), 1)
    self.assertEqual(len(manager._tasks_processing), 0)
    self.assertEqual(len(manager._tasks_pending_merge), 0)
    self.assertEqual(len(manager._tasks_merging), 0)

    with self.assertRaises(KeyError):
      manager.CheckTaskToMerge(task)

  def testCreateRetryTask(self):
    """Tests the CreateRetryTask function."""
    manager = task_manager.TaskManager()
    task = manager.CreateTask(self._TEST_SESSION_IDENTIFIER)

    self.assertEqual(len(manager._tasks_queued), 1)
    self.assertEqual(len(manager._tasks_abandoned), 0)

    self.assertEqual(manager._total_number_of_tasks, 1)

    retry_task = manager.CreateRetryTask()
    self.assertIsNone(retry_task)

    manager._AbandonQueuedTasks()

    self.assertEqual(len(manager._tasks_queued), 0)
    self.assertEqual(len(manager._tasks_abandoned), 1)

    retry_task = manager.CreateRetryTask()
    self.assertIsNotNone(retry_task)
    self.assertNotEqual(retry_task, task)

    self.assertEqual(len(manager._tasks_queued), 1)
    self.assertEqual(len(manager._tasks_abandoned), 1)

    self.assertEqual(manager._total_number_of_tasks, 2)

  def testCreateTask(self):
    """Tests the CreateTask function."""
    manager = task_manager.TaskManager()

    self.assertEqual(len(manager._tasks_queued), 0)
    self.assertEqual(len(manager._tasks_processing), 0)
    self.assertEqual(len(manager._tasks_pending_merge), 0)
    self.assertEqual(len(manager._tasks_merging), 0)
    self.assertEqual(len(manager._tasks_abandoned), 0)

    self.assertEqual(manager._total_number_of_tasks, 0)

    task = manager.CreateTask(self._TEST_SESSION_IDENTIFIER)

    self.assertEqual(len(manager._tasks_queued), 1)
    self.assertEqual(len(manager._tasks_processing), 0)
    self.assertEqual(len(manager._tasks_pending_merge), 0)
    self.assertEqual(len(manager._tasks_merging), 0)
    self.assertEqual(len(manager._tasks_abandoned), 0)

    self.assertEqual(manager._total_number_of_tasks, 1)

    self.assertIsInstance(task, tasks.Task)
    self.assertEqual(task.session_identifier, self._TEST_SESSION_IDENTIFIER)
    self.assertIsNotNone(task.identifier)
    self.assertIsNone(task.last_processing_time)

  def testCompleteTask(self):
    """Tests the CompleteTask function."""
    manager = task_manager.TaskManager()

    # Test with queued task.
    task = manager.CreateTask(self._TEST_SESSION_IDENTIFIER)
    task.storage_file_size = 10

    self.assertEqual(len(manager._tasks_queued), 1)
    self.assertEqual(len(manager._tasks_processing), 0)
    self.assertEqual(len(manager._tasks_pending_merge), 0)
    self.assertEqual(len(manager._tasks_merging), 0)
    self.assertEqual(len(manager._tasks_abandoned), 0)

    with self.assertRaises(KeyError):
      manager.CompleteTask(task)

    # Test with processing task.
    manager.UpdateTaskAsProcessingByIdentifier(task.identifier)

    self.assertEqual(len(manager._tasks_queued), 0)
    self.assertEqual(len(manager._tasks_processing), 1)
    self.assertEqual(len(manager._tasks_pending_merge), 0)
    self.assertEqual(len(manager._tasks_merging), 0)
    self.assertEqual(len(manager._tasks_abandoned), 0)

    with self.assertRaises(KeyError):
      manager.CompleteTask(task)

    # Test with task pending merge.
    manager.UpdateTaskAsPendingMerge(task)

    self.assertEqual(len(manager._tasks_queued), 0)
    self.assertEqual(len(manager._tasks_processing), 0)
    self.assertEqual(len(manager._tasks_pending_merge), 1)
    self.assertEqual(len(manager._tasks_merging), 0)
    self.assertEqual(len(manager._tasks_abandoned), 0)

    with self.assertRaises(KeyError):
      manager.CompleteTask(task)

    # Test with merging task.
    result_task = manager.GetTaskPendingMerge(None)
    self.assertIsNotNone(result_task)

    self.assertEqual(len(manager._tasks_queued), 0)
    self.assertEqual(len(manager._tasks_processing), 0)
    self.assertEqual(len(manager._tasks_pending_merge), 0)
    self.assertEqual(len(manager._tasks_merging), 1)
    self.assertEqual(len(manager._tasks_abandoned), 0)

    manager.CompleteTask(task)

    self.assertEqual(len(manager._tasks_queued), 0)
    self.assertEqual(len(manager._tasks_processing), 0)
    self.assertEqual(len(manager._tasks_pending_merge), 0)
    self.assertEqual(len(manager._tasks_merging), 0)
    self.assertEqual(len(manager._tasks_abandoned), 0)

    # Test with abandoned task.
    task = manager.CreateTask(self._TEST_SESSION_IDENTIFIER)
    task.storage_file_size = 10

    manager._AbandonQueuedTasks()

    self.assertEqual(len(manager._tasks_queued), 0)
    self.assertEqual(len(manager._tasks_processing), 0)
    self.assertEqual(len(manager._tasks_pending_merge), 0)
    self.assertEqual(len(manager._tasks_merging), 0)
    self.assertEqual(len(manager._tasks_abandoned), 1)

    with self.assertRaises(KeyError):
      manager.CompleteTask(task)

    # Test with retry task.
    retry_task = manager.CreateRetryTask()
    self.assertIsNotNone(retry_task)

    manager.UpdateTaskAsPendingMerge(retry_task)

    result_task = manager.GetTaskPendingMerge(None)
    self.assertIsNotNone(result_task)

    self.assertEqual(len(manager._tasks_queued), 0)
    self.assertEqual(len(manager._tasks_processing), 0)
    self.assertEqual(len(manager._tasks_pending_merge), 0)
    self.assertEqual(len(manager._tasks_merging), 1)
    self.assertEqual(len(manager._tasks_abandoned), 1)

    manager.CompleteTask(retry_task)

    self.assertEqual(len(manager._tasks_queued), 0)
    self.assertEqual(len(manager._tasks_processing), 0)
    self.assertEqual(len(manager._tasks_pending_merge), 0)
    self.assertEqual(len(manager._tasks_merging), 0)
    self.assertEqual(len(manager._tasks_abandoned), 1)

  def testGetFailedTasks(self):
    """Tests the GetFailedTasks function."""
    manager = task_manager.TaskManager()
    test_tasks = [
        manager.CreateTask(self._TEST_SESSION_IDENTIFIER) for _ in range(2)]

    self.assertEqual(len(manager._tasks_queued), 2)
    self.assertEqual(len(manager._tasks_abandoned), 0)

    result_tasks = manager.GetFailedTasks()
    self.assertEqual(result_tasks, [])

    manager._AbandonQueuedTasks()

    self.assertEqual(len(manager._tasks_queued), 0)
    self.assertEqual(len(manager._tasks_abandoned), 2)

    result_tasks = manager.GetFailedTasks()
    self.assertEqual(set(result_tasks), set(test_tasks))

  def testGetProcessedTaskByIdentifier(self):
    """Tests the GetProcessedTaskByIdentifier function."""
    manager = task_manager.TaskManager()

    # Test with queued task.
    test_tasks = []
    for _ in range(3):
      task = manager.CreateTask(self._TEST_SESSION_IDENTIFIER)
      task.storage_file_size = 10
      test_tasks.append(task)

    self.assertEqual(len(manager._tasks_queued), 3)
    self.assertEqual(len(manager._tasks_processing), 0)
    self.assertEqual(len(manager._tasks_pending_merge), 0)
    self.assertEqual(len(manager._tasks_abandoned), 0)

    task = test_tasks[0]
    processed_task = manager.GetProcessedTaskByIdentifier(task.identifier)
    self.assertEqual(processed_task, task)

    # Test with processing task.
    manager.UpdateTaskAsProcessingByIdentifier(task.identifier)

    self.assertEqual(len(manager._tasks_queued), 2)
    self.assertEqual(len(manager._tasks_processing), 1)
    self.assertEqual(len(manager._tasks_pending_merge), 0)
    self.assertEqual(len(manager._tasks_abandoned), 0)

    processed_task = manager.GetProcessedTaskByIdentifier(task.identifier)
    self.assertEqual(processed_task, task)

    # Test with abandoned task.
    task.last_processing_time -= (
        2 * manager._TASK_INACTIVE_TIME * definitions.MICROSECONDS_PER_SECOND)

    manager._AbandonInactiveProcessingTasks()

    self.assertEqual(len(manager._tasks_queued), 2)
    self.assertEqual(len(manager._tasks_processing), 0)
    self.assertEqual(len(manager._tasks_pending_merge), 0)
    self.assertEqual(len(manager._tasks_abandoned), 1)

    processed_task = manager.GetProcessedTaskByIdentifier(task.identifier)
    self.assertEqual(processed_task, task)

    # Test status of task is unknown.
    task = tasks.Task()

    with self.assertRaises(KeyError):
      manager.GetProcessedTaskByIdentifier(task.identifier)

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

  def testGetTaskPendingMerge(self):
    """Tests the GetTaskPendingMerge function."""
    current_task = tasks.Task()
    current_task.storage_file_size = 10

    manager = task_manager.TaskManager()
    task = manager.CreateTask(self._TEST_SESSION_IDENTIFIER)
    task.storage_file_size = 10

    self.assertEqual(len(manager._tasks_queued), 1)
    self.assertEqual(len(manager._tasks_pending_merge), 0)
    self.assertEqual(len(manager._tasks_merging), 0)

    # Determine if there are tasks pending merge when _tasks_pending_merge is
    # empty.
    result_task = manager.GetTaskPendingMerge(current_task)
    self.assertIsNone(result_task)

    self.assertEqual(len(manager._tasks_queued), 1)
    self.assertEqual(len(manager._tasks_pending_merge), 0)
    self.assertEqual(len(manager._tasks_merging), 0)

    manager.UpdateTaskAsPendingMerge(task)

    self.assertEqual(len(manager._tasks_queued), 0)
    self.assertEqual(len(manager._tasks_pending_merge), 1)
    self.assertEqual(len(manager._tasks_merging), 0)

    # Determine if there are tasks pending merge when there is a current task
    # with a higher merge priority.
    current_task.merge_priority = 1
    task.merge_priority = 1000

    result_task = manager.GetTaskPendingMerge(current_task)
    self.assertIsNone(result_task)

    self.assertEqual(len(manager._tasks_queued), 0)
    self.assertEqual(len(manager._tasks_pending_merge), 1)
    self.assertEqual(len(manager._tasks_merging), 0)

    # Determine if there are tasks pending merge.
    result_task = manager.GetTaskPendingMerge(None)
    self.assertIsNotNone(result_task)

    self.assertEqual(len(manager._tasks_queued), 0)
    self.assertEqual(len(manager._tasks_pending_merge), 0)
    self.assertEqual(len(manager._tasks_merging), 1)

  def testHasPendingTasks(self):
    """Tests the HasPendingTasks function."""
    manager = task_manager.TaskManager()

    self.assertEqual(len(manager._tasks_queued), 0)
    self.assertEqual(len(manager._tasks_processing), 0)
    self.assertEqual(len(manager._tasks_pending_merge), 0)
    self.assertEqual(len(manager._tasks_merging), 0)
    self.assertEqual(len(manager._tasks_abandoned), 0)

    result = manager.HasPendingTasks()
    self.assertFalse(result)

    # Test with queued task.
    task = manager.CreateTask(self._TEST_SESSION_IDENTIFIER)
    task.storage_file_size = 10

    self.assertEqual(len(manager._tasks_queued), 1)
    self.assertEqual(len(manager._tasks_processing), 0)
    self.assertEqual(len(manager._tasks_pending_merge), 0)
    self.assertEqual(len(manager._tasks_merging), 0)
    self.assertEqual(len(manager._tasks_abandoned), 0)

    result = manager.HasPendingTasks()
    self.assertTrue(result)

    # Test with processing task.
    manager.UpdateTaskAsProcessingByIdentifier(task.identifier)

    self.assertEqual(len(manager._tasks_queued), 0)
    self.assertEqual(len(manager._tasks_processing), 1)
    self.assertEqual(len(manager._tasks_pending_merge), 0)
    self.assertEqual(len(manager._tasks_merging), 0)
    self.assertEqual(len(manager._tasks_abandoned), 0)

    result = manager.HasPendingTasks()
    self.assertTrue(result)

    # Test with abandoned task.
    task.last_processing_time -= (
        2 * manager._TASK_INACTIVE_TIME * definitions.MICROSECONDS_PER_SECOND)

    manager._AbandonInactiveProcessingTasks()

    self.assertEqual(len(manager._tasks_queued), 0)
    self.assertEqual(len(manager._tasks_processing), 0)
    self.assertEqual(len(manager._tasks_pending_merge), 0)
    self.assertEqual(len(manager._tasks_merging), 0)
    self.assertEqual(len(manager._tasks_abandoned), 1)

    result = manager.HasPendingTasks()
    self.assertTrue(result)

    # Test with task pending merge.
    manager.UpdateTaskAsPendingMerge(task)

    self.assertEqual(len(manager._tasks_queued), 0)
    self.assertEqual(len(manager._tasks_processing), 0)
    self.assertEqual(len(manager._tasks_pending_merge), 1)
    self.assertEqual(len(manager._tasks_merging), 0)
    self.assertEqual(len(manager._tasks_abandoned), 0)

    result = manager.HasPendingTasks()
    self.assertTrue(result)

    # Test with merging task.
    result_task = manager.GetTaskPendingMerge(None)
    self.assertIsNotNone(result_task)

    self.assertEqual(len(manager._tasks_queued), 0)
    self.assertEqual(len(manager._tasks_pending_merge), 0)
    self.assertEqual(len(manager._tasks_pending_merge), 0)
    self.assertEqual(len(manager._tasks_merging), 1)
    self.assertEqual(len(manager._tasks_abandoned), 0)

    result = manager.HasPendingTasks()
    self.assertTrue(result)

  def testRemoveTask(self):
    """Tests the RemoveTask function."""
    manager = task_manager.TaskManager()

    # Test with queued task.
    task = manager.CreateTask(self._TEST_SESSION_IDENTIFIER)
    task.storage_file_size = 10

    self.assertEqual(len(manager._tasks_queued), 1)
    self.assertEqual(len(manager._tasks_processing), 0)
    self.assertEqual(len(manager._tasks_pending_merge), 0)
    self.assertEqual(len(manager._tasks_abandoned), 0)

    with self.assertRaises(KeyError):
      manager.RemoveTask(task)

    # Test with abandoned task that was not retried (has no retry task).
    manager._AbandonQueuedTasks()

    self.assertEqual(len(manager._tasks_queued), 0)
    self.assertEqual(len(manager._tasks_processing), 0)
    self.assertEqual(len(manager._tasks_pending_merge), 0)
    self.assertEqual(len(manager._tasks_abandoned), 1)

    with self.assertRaises(KeyError):
      manager.RemoveTask(task)

    # Test with abandoned task that was retried (has retry task).
    task.has_retry = True

    manager.RemoveTask(task)

    self.assertEqual(len(manager._tasks_queued), 0)
    self.assertEqual(len(manager._tasks_processing), 0)
    self.assertEqual(len(manager._tasks_pending_merge), 0)
    self.assertEqual(len(manager._tasks_abandoned), 0)

  # TODO: add tests for SampleTaskStatus
  # TODO: add tests for StartProfiling
  # TODO: add tests for StopProfiling

  def testUpdateTaskAsPendingMerge(self):
    """Tests the UpdateTaskAsPendingMerge function."""
    manager = task_manager.TaskManager()

    # Test with queued task.
    task = manager.CreateTask(self._TEST_SESSION_IDENTIFIER)
    task.storage_file_size = 10

    self.assertEqual(len(manager._tasks_queued), 1)
    self.assertEqual(len(manager._tasks_processing), 0)
    self.assertEqual(len(manager._tasks_pending_merge), 0)
    self.assertEqual(len(manager._tasks_abandoned), 0)

    manager.UpdateTaskAsPendingMerge(task)

    self.assertEqual(len(manager._tasks_queued), 0)
    self.assertEqual(len(manager._tasks_processing), 0)
    self.assertEqual(len(manager._tasks_pending_merge), 1)
    self.assertEqual(len(manager._tasks_abandoned), 0)

    # Test with processing task.
    task = manager.CreateTask(self._TEST_SESSION_IDENTIFIER)
    task.storage_file_size = 10

    self.assertEqual(len(manager._tasks_queued), 1)
    self.assertEqual(len(manager._tasks_processing), 0)
    self.assertEqual(len(manager._tasks_pending_merge), 1)
    self.assertEqual(len(manager._tasks_abandoned), 0)

    manager.UpdateTaskAsProcessingByIdentifier(task.identifier)

    self.assertEqual(len(manager._tasks_queued), 0)
    self.assertEqual(len(manager._tasks_processing), 1)
    self.assertEqual(len(manager._tasks_pending_merge), 1)
    self.assertEqual(len(manager._tasks_abandoned), 0)

    manager.UpdateTaskAsPendingMerge(task)

    self.assertEqual(len(manager._tasks_queued), 0)
    self.assertEqual(len(manager._tasks_processing), 0)
    self.assertEqual(len(manager._tasks_pending_merge), 2)
    self.assertEqual(len(manager._tasks_abandoned), 0)

    # Test with abandoned task.
    task = manager.CreateTask(self._TEST_SESSION_IDENTIFIER)
    task.storage_file_size = 10

    self.assertEqual(len(manager._tasks_queued), 1)
    self.assertEqual(len(manager._tasks_processing), 0)
    self.assertEqual(len(manager._tasks_pending_merge), 2)
    self.assertEqual(len(manager._tasks_abandoned), 0)

    manager._AbandonQueuedTasks()

    self.assertEqual(len(manager._tasks_queued), 0)
    self.assertEqual(len(manager._tasks_processing), 0)
    self.assertEqual(len(manager._tasks_pending_merge), 2)
    self.assertEqual(len(manager._tasks_abandoned), 1)

    manager.UpdateTaskAsPendingMerge(task)

    self.assertEqual(len(manager._tasks_queued), 0)
    self.assertEqual(len(manager._tasks_processing), 0)
    self.assertEqual(len(manager._tasks_pending_merge), 3)
    self.assertEqual(len(manager._tasks_abandoned), 0)

    # Test status of task is unknown.
    task = tasks.Task()
    task.storage_file_size = 10

    with self.assertRaises(KeyError):
      manager.UpdateTaskAsProcessingByIdentifier(task.identifier)

    # Test with abandoned task that is retried.
    task = manager.CreateTask(self._TEST_SESSION_IDENTIFIER)
    task.storage_file_size = 10

    self.assertEqual(len(manager._tasks_queued), 1)
    self.assertEqual(len(manager._tasks_processing), 0)
    self.assertEqual(len(manager._tasks_pending_merge), 3)
    self.assertEqual(len(manager._tasks_abandoned), 0)

    manager._AbandonQueuedTasks()

    self.assertEqual(len(manager._tasks_queued), 0)
    self.assertEqual(len(manager._tasks_processing), 0)
    self.assertEqual(len(manager._tasks_pending_merge), 3)
    self.assertEqual(len(manager._tasks_abandoned), 1)

    retry_task = manager.CreateRetryTask()
    self.assertIsNotNone(retry_task)

    self.assertEqual(len(manager._tasks_queued), 1)
    self.assertEqual(len(manager._tasks_processing), 0)
    self.assertEqual(len(manager._tasks_pending_merge), 3)
    self.assertEqual(len(manager._tasks_abandoned), 1)

    with self.assertRaises(KeyError):
      manager.UpdateTaskAsPendingMerge(task)

  def testUpdateTaskAsProcessingByIdentifier(self):
    """Tests the UpdateTaskAsProcessingByIdentifier function."""
    manager = task_manager.TaskManager()

    # Test with queued task.
    task = manager.CreateTask(self._TEST_SESSION_IDENTIFIER)
    self.assertIsNone(task.last_processing_time)

    self.assertEqual(len(manager._tasks_queued), 1)
    self.assertEqual(len(manager._tasks_processing), 0)
    self.assertEqual(len(manager._tasks_pending_merge), 0)
    self.assertEqual(len(manager._tasks_abandoned), 0)

    # Indicate to the task manager that the task is processing.
    manager.UpdateTaskAsProcessingByIdentifier(task.identifier)

    self.assertEqual(len(manager._tasks_queued), 0)
    self.assertEqual(len(manager._tasks_processing), 1)
    self.assertEqual(len(manager._tasks_pending_merge), 0)
    self.assertEqual(len(manager._tasks_abandoned), 0)

    # Check if the last processing time was set.
    self.assertIsNotNone(task.last_processing_time)

    last_processing_time = task.last_processing_time

    time.sleep(0.01)

    # Indicate to the task manager that the task is still processing.
    manager.UpdateTaskAsProcessingByIdentifier(task.identifier)

    self.assertEqual(len(manager._tasks_queued), 0)
    self.assertEqual(len(manager._tasks_processing), 1)
    self.assertEqual(len(manager._tasks_pending_merge), 0)
    self.assertEqual(len(manager._tasks_abandoned), 0)

    # Check if the last processing time was updated.
    self.assertGreater(task.last_processing_time, last_processing_time)

    # Test with abandoned task.
    task.last_processing_time -= (
        2 * manager._TASK_INACTIVE_TIME * definitions.MICROSECONDS_PER_SECOND)

    manager._AbandonInactiveProcessingTasks()

    self.assertEqual(len(manager._tasks_queued), 0)
    self.assertEqual(len(manager._tasks_processing), 0)
    self.assertEqual(len(manager._tasks_pending_merge), 0)
    self.assertEqual(len(manager._tasks_abandoned), 1)

    # Indicate to the task manager that the task is still processing.
    manager.UpdateTaskAsProcessingByIdentifier(task.identifier)

    self.assertEqual(len(manager._tasks_queued), 0)
    self.assertEqual(len(manager._tasks_processing), 1)
    self.assertEqual(len(manager._tasks_pending_merge), 0)
    self.assertEqual(len(manager._tasks_abandoned), 0)

    # Indicate to the task manager that the task is pending merge.
    task.storage_file_size = 10

    manager.UpdateTaskAsPendingMerge(task)

    self.assertEqual(len(manager._tasks_queued), 0)
    self.assertEqual(len(manager._tasks_processing), 0)
    self.assertEqual(len(manager._tasks_pending_merge), 1)
    self.assertEqual(len(manager._tasks_abandoned), 0)

    manager.UpdateTaskAsProcessingByIdentifier(task.identifier)

    self.assertEqual(len(manager._tasks_queued), 0)
    self.assertEqual(len(manager._tasks_processing), 0)
    self.assertEqual(len(manager._tasks_pending_merge), 1)
    self.assertEqual(len(manager._tasks_abandoned), 0)

    # Test status of task is unknown.
    task = tasks.Task()

    with self.assertRaises(KeyError):
      manager.UpdateTaskAsProcessingByIdentifier(task.identifier)


if __name__ == '__main__':
  unittest.main()
