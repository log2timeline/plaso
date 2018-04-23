#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""This file contains tests for the task manager."""

from __future__ import unicode_literals

import time
import unittest

from dfvfs.lib import definitions as dfvfs_definitions

from plaso.containers import tasks
from plaso.lib import definitions
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

  def testAbandonInactiveProcessingTasks(self):
    """Tests the _AbandonInactiveProcessingTasks function."""
    manager = task_manager.TaskManager()

    task = manager.CreateTask(self._TEST_SESSION_IDENTIFIER)

    # Indicate to the task manager that the task is processing.
    manager.UpdateTaskAsProcessingByIdentifier(task.identifier)

    self.assertIsNotNone(task.last_processing_time)

    self.assertEqual(len(manager._tasks_queued), 0)
    self.assertEqual(len(manager._tasks_processing), 1)
    self.assertEqual(len(manager._tasks_abandoned), 0)
    self.assertEqual(len(manager._tasks_pending_merge), 0)

    manager._AbandonInactiveProcessingTasks()

    self.assertEqual(len(manager._tasks_queued), 0)
    self.assertEqual(len(manager._tasks_processing), 1)
    self.assertEqual(len(manager._tasks_abandoned), 0)
    self.assertEqual(len(manager._tasks_pending_merge), 0)

    task.last_processing_time -= (
        2 * manager._TASK_INACTIVE_TIME * definitions.MICROSECONDS_PER_SECOND)

    manager._AbandonInactiveProcessingTasks()

    self.assertEqual(len(manager._tasks_queued), 0)
    self.assertEqual(len(manager._tasks_processing), 0)
    self.assertEqual(len(manager._tasks_abandoned), 1)
    self.assertEqual(len(manager._tasks_pending_merge), 0)

  def testAbandonInactiveQueuedTasks(self):
    """Tests the _AbandonInactiveQueuedTasks function."""
    manager = task_manager.TaskManager()

    task = manager.CreateTask(self._TEST_SESSION_IDENTIFIER)

    self.assertIsNotNone(task.start_time)

    self.assertEqual(len(manager._tasks_queued), 1)
    self.assertEqual(len(manager._tasks_processing), 0)
    self.assertEqual(len(manager._tasks_abandoned), 0)
    self.assertEqual(len(manager._tasks_pending_merge), 0)

    manager._AbandonInactiveQueuedTasks()

    self.assertEqual(len(manager._tasks_queued), 1)
    self.assertEqual(len(manager._tasks_processing), 0)
    self.assertEqual(len(manager._tasks_abandoned), 0)
    self.assertEqual(len(manager._tasks_pending_merge), 0)

    manager._task_last_processing_time -= (
        2 * manager._TASK_INACTIVE_TIME * definitions.MICROSECONDS_PER_SECOND)

    manager._AbandonInactiveQueuedTasks()

    self.assertEqual(len(manager._tasks_queued), 0)
    self.assertEqual(len(manager._tasks_processing), 0)
    self.assertEqual(len(manager._tasks_abandoned), 1)
    self.assertEqual(len(manager._tasks_pending_merge), 0)

  def testGetTaskPendingRetry(self):
    """Tests the _GetTaskPendingRetry function."""
    manager = task_manager.TaskManager()
    task = manager.CreateTask(self._TEST_SESSION_IDENTIFIER)

    self.assertEqual(len(manager._tasks_queued), 1)
    self.assertEqual(len(manager._tasks_abandoned), 0)

    result_task = manager._GetTaskPendingRetry()
    self.assertIsNone(result_task)

    self.assertEqual(len(manager._tasks_queued), 1)
    self.assertEqual(len(manager._tasks_abandoned), 0)

    manager._task_last_processing_time -= (
        2 * manager._TASK_INACTIVE_TIME * definitions.MICROSECONDS_PER_SECOND)

    manager._AbandonInactiveQueuedTasks()

    self.assertEqual(len(manager._tasks_queued), 0)
    self.assertEqual(len(manager._tasks_abandoned), 1)

    result_task = manager._GetTaskPendingRetry()
    self.assertEqual(result_task, task)

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

  # TODO: add tests for _UpdateProcessingTimeFromTask

  def testCreateRetryTask(self):
    """Tests the CreateRetryTask function."""
    manager = task_manager.TaskManager()
    manager.CreateTask(self._TEST_SESSION_IDENTIFIER)

    self.assertEqual(len(manager._tasks_queued), 1)
    self.assertEqual(len(manager._tasks_abandoned), 0)

    self.assertEqual(manager._total_number_of_tasks, 1)

    retry_task = manager.CreateRetryTask()
    self.assertIsNone(retry_task)

    self.assertEqual(len(manager._tasks_queued), 1)
    self.assertEqual(len(manager._tasks_abandoned), 0)

    manager._task_last_processing_time -= (
        2 * manager._TASK_INACTIVE_TIME * definitions.MICROSECONDS_PER_SECOND)

    manager._AbandonInactiveQueuedTasks()

    result_task = manager.CreateRetryTask()
    self.assertIsNotNone(result_task)

    # TODO: improve test coverage.

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

  def testGetFailedTasks(self):
    """Tests the GetFailedTasks function."""
    manager = task_manager.TaskManager()
    task = manager.CreateTask(self._TEST_SESSION_IDENTIFIER)

    result_tasks = manager.GetFailedTasks()
    self.assertEqual(result_tasks, [])

    self.assertEqual(len(manager._tasks_queued), 1)
    self.assertEqual(len(manager._tasks_abandoned), 0)

    manager._task_last_processing_time -= (
        2 * manager._TASK_INACTIVE_TIME * definitions.MICROSECONDS_PER_SECOND)

    manager._AbandonInactiveQueuedTasks()

    self.assertEqual(len(manager._tasks_queued), 0)
    self.assertEqual(len(manager._tasks_abandoned), 1)

    result_tasks = manager.GetFailedTasks()
    self.assertEqual(result_tasks, [task])

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
    current_task = tasks.Task()
    current_task.storage_file_size = 10

    manager = task_manager.TaskManager()

    self.assertEqual(len(manager._tasks_queued), 0)
    self.assertEqual(len(manager._tasks_pending_merge), 0)
    self.assertEqual(len(manager._tasks_merging), 0)

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

    manager._task_last_processing_time -= (
        2 * manager._TASK_INACTIVE_TIME * definitions.MICROSECONDS_PER_SECOND)

    manager._AbandonInactiveQueuedTasks()

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

    time.sleep(0.01)

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


if __name__ == '__main__':
  unittest.main()
