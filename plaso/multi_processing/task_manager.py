# -*- coding: utf-8 -*-
"""The task manager."""

from __future__ import unicode_literals

import collections
import heapq
import threading
import time

from dfvfs.lib import definitions as dfvfs_definitions

from plaso.containers import tasks
from plaso.engine import processing_status
from plaso.multi_processing import logger


class _PendingMergeTaskHeap(object):
  """Heap to manage pending merge tasks."""

  def __init__(self):
    """Initializes a pending merge task heap."""
    super(_PendingMergeTaskHeap, self).__init__()
    self._heap = []
    self._task_identifiers = set()

  def __contains__(self, task_identifier):
    """Checks for an task identifier being present in the heap.

    Args:
      task_identifier (str): task identifier to check for.

    Returns:
      bool: True if the task with the given identifier is present in the heap.
    """
    return task_identifier in self._task_identifiers

  def __len__(self):
    """int: number of tasks on the heap."""
    return len(self._heap)

  def PeekTask(self):
    """Retrieves the first task from the heap without removing it.

    Returns:
      Task: task or None if the heap is empty.
    """
    try:
      _, task = self._heap[0]

    except IndexError:
      return None

    return task

  def PopTask(self):
    """Retrieves and removes the first task from the heap.

    Returns:
      Task: the task or None if the heap is empty.
    """
    try:
      _, task = heapq.heappop(self._heap)

    except IndexError:
      return None
    self._task_identifiers.remove(task.identifier)
    return task

  def PushTask(self, task):
    """Pushes a task onto the heap.

    Args:
      task (Task): task.

    Raises:
      ValueError: if the size of the storage file is not set in the task.
    """
    storage_file_size = getattr(task, 'storage_file_size', None)
    if not storage_file_size:
      raise ValueError('Task storage file size not set.')

    if task.file_entry_type == dfvfs_definitions.FILE_ENTRY_TYPE_DIRECTORY:
      weight = 1
    else:
      weight = storage_file_size

    task.merge_priority = weight

    heap_values = (weight, task)
    heapq.heappush(self._heap, heap_values)
    self._task_identifiers.add(task.identifier)


class TaskManager(object):
  """Manages tasks and tracks their completion and status.

  A task being tracked by the manager must be in exactly one of the
  following states:

  * abandoned: a task assumed to be abandoned because a tasks that has been
      queued or was processing exceeds the maximum inactive time.
  * queued: the task is waiting for a worker to start processing it. It is also
      possible that a worker has already completed the task, but no status
      update was collected from the worker while it processed the task.
  * processing: a worker is processing the task.
  * processed: a worker has completed processing the task.
  * pending_merge: the task is process and awaiting to be merged with the
      session storage.
  * merging: tasks that are being merged by the engine.

  Once the engine reports that a task is completely merged, it is removed
  from the task manager.

  Tasks are considered "pending" when there is more work that needs to be done
  to complete these tasks. Pending applies to tasks that are:
  * not abandoned;
  * abandoned, but need to be retried.
  """

  # Stop pylint from reporting:
  # Context manager 'lock' doesn't implement __enter__ and __exit__.
  # pylint: disable=not-context-manager

  _MICROSECONDS_PER_SECOND = 1000000

  # Consider a processing task inactive after 5 minutes of no activity.
  _PROCESSING_TASK_INACTIVE_TIME = 5.0 * 60.0

  # Consider a queued task inactive after 30 minutes of no activity.
  _QUEUED_TASK_INACTIVE_TIME = 30.0 * 60.0

  def __init__(self):
    """Initializes a task manager."""
    super(TaskManager, self).__init__()
    self._lock = threading.Lock()

    # This dictionary maps task identifiers to tasks that have been abandoned,
    # as no worker has reported processing the task in the expected interval.
    self._tasks_abandoned = {}

    # This dictionary maps task identifiers to tasks that are being merged
    # by the foreman.
    self._tasks_merging = {}

    # Use ordered dictionary to preserve the order in which tasks were added.
    # This dictionary maps task identifiers to tasks that are waiting to be
    # processed.
    self._tasks_queued = collections.OrderedDict()

    self._tasks_pending_merge = _PendingMergeTaskHeap()

    # This dictionary maps task identifiers to tasks that are currently
    # being processed by a worker.
    self._tasks_processing = {}

    # TODO: implement a limit on the number of tasks.
    self._total_number_of_tasks = 0

  def _AbandonInactiveProcessingTasks(self):
    """Marks processing tasks that exceed the inactive time as abandoned.

    This method does not lock the manager and should be called by a method
    holding the manager lock.
    """
    if self._tasks_processing:
      inactive_time = time.time() - self._PROCESSING_TASK_INACTIVE_TIME
      inactive_time = int(inactive_time * self._MICROSECONDS_PER_SECOND)

      for task_identifier, task in iter(self._tasks_processing.items()):
        if task.last_processing_time < inactive_time:
          logger.debug('Abandoned processing task: {0:s}.'.format(
              task_identifier))

          self._tasks_abandoned[task_identifier] = task
          del self._tasks_processing[task_identifier]

  def _AbandonInactiveQueuedTasks(self):
    """Marks queued tasks that exceed the inactive time as abandoned.

    This method does not lock the manager and should be called by a method
    holding the manager lock.
    """
    if self._tasks_queued:
      inactive_time = time.time() - self._QUEUED_TASK_INACTIVE_TIME
      inactive_time = int(inactive_time * self._MICROSECONDS_PER_SECOND)

      for task_identifier, task in iter(self._tasks_queued.items()):
        if task.start_time < inactive_time:
          logger.debug('Abandoned queued task: {0:s}.'.format(task_identifier))

          self._tasks_abandoned[task_identifier] = task
          del self._tasks_queued[task_identifier]

  def _GetTaskPendingRetry(self):
    """Retrieves an abandoned task that should be retried.

    This method does not lock the manager and should be called by a method
    holding the manager lock.

    Returns:
      Task: a task that was abandoned but should be retried or None if there are
          no abandoned tasks that should be retried.
    """
    for task in self._tasks_abandoned.values():
      # Only retry abandoned tasks that are yet to be retried and
      # are not themselves retries of another task.
      if not (task.retried or task.original_task_identifier):
        return task

    return None

  def _HasTasksPendingMerge(self):
    """Determines if there are tasks waiting to be merged.

    This method does not lock the manager and should be called by a method
    holding the manager lock.

    Returns:
      bool: True if there are abandoned tasks that need to be retried.
    """
    return bool(self._tasks_pending_merge)

  def _HasTasksPendingRetry(self):
    """Determines if there are abandoned tasks that still need to be retried.

    This method does not lock the manager and should be called by a method
    holding the manager lock.

    Returns:
      bool: True if there are abandoned tasks that need to be retried.
    """
    return bool(self._GetTaskPendingRetry())

  def _QueueTask(self, task):
    """Queues a task.

    This method does not lock the manager and should be called by a method
    holding the manager lock.

    Args:
      task (Task): task to queue.
    """
    self._tasks_queued[task.identifier] = task
    self._total_number_of_tasks += 1

  def CreateRetryTask(self):
    """Creates a task that to retry a previously abandoned task.

    Returns:
      Task: a task that was abandoned but should be retried or None if there are
          no abandoned tasks that should be retried.
    """
    with self._lock:
      abandoned_task = self._GetTaskPendingRetry()
      if not abandoned_task:
        return None

      retry_task = abandoned_task.CreateRetry()
      logger.debug('Retrying task {0:s} as {1:s}.'.format(
          abandoned_task.identifier, retry_task.identifier))

      self._QueueTask(retry_task)
      return retry_task

  # TODO: add support for task types.
  def CreateTask(self, session_identifier):
    """Creates a task.

    Args:
      session_identifier (str): the identifier of the session the task is
          part of.

    Returns:
      Task: task attribute container.
    """
    task = tasks.Task(session_identifier)
    logger.debug('Created task: {0:s}.'.format(task.identifier))

    with self._lock:
      self._QueueTask(task)

    return task

  def CompleteTask(self, task):
    """Completes a task.

    The task is complete and can be removed from the task manager.

    Args:
      task (Task): task.
    """
    with self._lock:
      if task.identifier in self._tasks_merging:
        del self._tasks_merging[task.identifier]
        logger.debug('Task {0:s} is complete.'.format(task.identifier))

      if task.identifier in self._tasks_pending_merge:
        logger.debug('Task {0:s} completed while pending merge.'.format(
            task.identifier))
        return

      if task.identifier in self._tasks_processing:
        del self._tasks_processing[task.identifier]
        logger.debug('Task {0:s} completed from processing.'.format(
            task.identifier))
        return

      if task.identifier in self._tasks_queued:
        del self._tasks_queued[task.identifier]
        logger.debug('Task {0:s} is completed from queued.'.format(
            task.identifier))
        return

  def GetAbandonedTasks(self):
    """Retrieves all abandoned tasks.

    Returns:
      list[Task]: tasks.
    """
    with self._lock:
      return list(self._tasks_abandoned.values())

  def GetProcessedTasksByIdentifier(self, task_identifier):
    """Retrieves a task when it completed processing.

    Args:
      task_identifier (str): unique identifier of the task.

    Returns:
      Task: a task that is pending merge.

    Raises:
      KeyError: if the task was not processing, queued or abandoned.
    """
    with self._lock:
      task = self._tasks_processing.get(task_identifier, None)
      if not task:
        task = self._tasks_queued.get(task_identifier, None)
      if not task:
        task = self._tasks_abandoned.get(task_identifier, None)
      if not task:
        raise KeyError('Status of task {0:s} is unknown'.format(
            task_identifier))

    return task

  def GetProcessedTaskByIdentifier(self, task_identifier):
    """Retrieves a task that has been processed.

    Args:
      task_identifier (str): unique identifier of the task.
    Returns:
      Task: a task that has been processed.

    Raises:
      KeyError: if the task was not processing, queued or abandoned.
    """
    with self._lock:
      task = self._tasks_processing.get(task_identifier, None)
      if not task:
        task = self._tasks_queued.get(task_identifier, None)
      if not task:
        task = self._tasks_abandoned.get(task_identifier, None)
      if not task:
        raise KeyError('Status of task {0:s} is unknown.'.format(
            task_identifier))

    return task

  def GetStatusInformation(self):
    """Retrieves status information about the tasks.

    Returns:
      TasksStatus: tasks status information.
    """
    status = processing_status.TasksStatus()

    with self._lock:
      status.number_of_abandoned_tasks = len(self._tasks_abandoned)
      status.number_of_queued_tasks = len(self._tasks_queued)
      status.number_of_tasks_pending_merge = len(self._tasks_pending_merge)
      status.number_of_tasks_processing = len(self._tasks_processing)
      status.total_number_of_tasks = self._total_number_of_tasks

    return status

  def GetTasksCheckMerge(self):
    """Retrieves the tasks that need to be checked if they are ready for merge.

    Returns:
      list[Task]: tasks that are being processed by workers or that have been
          abandoned.
    """
    with self._lock:
      tasks_list = list(self._tasks_processing.values())
      tasks_list.extend(self._tasks_queued.values())
      tasks_list.extend(self._tasks_abandoned.values())
    return tasks_list

  def GetTaskPendingMerge(self, current_task):
    """Retrieves the first task that is pending merge or has a higher priority.

    This function will check if there is a task with a higher merge priority
    than the current_task being merged. If so, that task with the higher
    priority is returned.

    Args:
      current_task (Task): current task being merged or None if no such task.

    Returns:
      Task: the next task to merge or None if there is no task pending merge or
          with a higher priority.
    """
    next_task = self._tasks_pending_merge.PeekTask()
    if not next_task:
      return None

    if current_task and next_task.merge_priority > current_task.merge_priority:
      return None

    with self._lock:
      next_task = self._tasks_pending_merge.PopTask()
    self._tasks_merging[next_task.identifier] = next_task
    return next_task

  def HasPendingTasks(self):
    """Determines if there are tasks running or in need of retrying.

    Returns:
      bool: True if there are tasks that are active, ready to be merged or
          need to be retried.
    """
    with self._lock:
      self._AbandonInactiveProcessingTasks()

      if self._tasks_processing:
        return True

      # There are no tasks being processed, but we might be
      # waiting for some tasks to be merged.
      if self._HasTasksPendingMerge():
        return True

      # There are no tasks processing or pending merge, but there may
      # still be some waiting to be retried, so we check that.
      if self._HasTasksPendingRetry():
        return True

      # It is possible that a worker worked on a task and the foreman does not
      # know about it, since there is no feedback from the worker when it pops
      # a task from the queue. Hence we check for tasks that we believe are
      # queued that might need to be marked as abandoned, as all the workers
      # are idle and the task has been queued for longer than the timeout.
      self._AbandonInactiveQueuedTasks()

      if self._tasks_queued:
        return True

      if self._tasks_merging:
        return True

    # There are no tasks pending any work.
    return False

  def UpdateTaskAsPendingMerge(self, task):
    """Updates the task manager to reflect the task is ready to be merged.

    Args:
      task (Task): task.

    Raises:
      KeyError: if the task was not processing or abandoned.
    """
    with self._lock:
      is_processing = task.identifier in self._tasks_processing
      is_abandoned = task.identifier in self._tasks_abandoned
      is_queued = task.identifier in self._tasks_queued

      if not (is_queued or is_abandoned or is_processing):
        raise KeyError('Status of task {0:s} is unknown.'.format(
            task.identifier))

      self._tasks_pending_merge.PushTask(task)
      task.UpdateProcessingTime()

      if is_queued:
        del self._tasks_queued[task.identifier]

      if is_processing:
        del self._tasks_processing[task.identifier]

      if is_abandoned:
        del self._tasks_abandoned[task.identifier]

    if is_abandoned:
      logger.warning(
          'Previously abandoned task {0:s} is now pending merge.'.format(
              task.identifier))
    else:
      logger.debug('Task {0:s} is pending merge.'.format(task.identifier))

  def UpdateTaskAsProcessingByIdentifier(self, task_identifier):
    """Updates the task manager to reflect the task is processing.

    Args:
      task_identifier (str): unique identifier of the task.

    Raises:
      KeyError: if the task is not known to the task manager.
    """
    with self._lock:
      task_processing = self._tasks_processing.get(task_identifier, None)
      if task_processing:
        task_processing.UpdateProcessingTime()
        return

      task_queued = self._tasks_queued.get(task_identifier, None)
      if task_queued:
        logger.debug('Task {0:s} was queued, now processing.'.format(
            task_identifier))
        self._tasks_processing[task_identifier] = task_queued
        del self._tasks_queued[task_identifier]
        task_queued.UpdateProcessingTime()
        return

      task_abandoned = self._tasks_abandoned.get(task_identifier, None)
      if task_abandoned:
        del self._tasks_abandoned[task_identifier]
        self._tasks_processing[task_identifier] = task_abandoned
        logger.debug('Task {0:s} was abandoned, but now processing.'.format(
            task_identifier))
        task_abandoned.UpdateProcessingTime()
        return

      if task_identifier in self._tasks_pending_merge:
        # No need to update the processing time, as this task is already
        # finished processing and is just waiting for merge.
        return

    # If we get here, we don't know what state the tasks is in, so raise.
    raise KeyError('Status of task {0:s} is unknown.'.format(task_identifier))
