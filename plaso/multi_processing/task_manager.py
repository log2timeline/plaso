# -*- coding: utf-8 -*-
"""The task manager."""

import collections
import heapq
import logging
import threading
import time

from dfvfs.lib import definitions as dfvfs_definitions

from plaso.containers import tasks
from plaso.engine import processing_status


class _PendingMergeTaskHeap(object):
  """Heap to manage pending merge tasks."""

  def __init__(self):
    """Initializes a pending merge task heap."""
    super(_PendingMergeTaskHeap, self).__init__()
    self._heap = []
    self._task_identifiers = set()

  def __len__(self):
    """int: number of tasks on the heap."""
    return len(self._heap)

  def __contains__(self, task_identifier):
    """Checks for an task identifier being present in the heap.

    Args:
      task_identifier (str): task identifier to check for.

    Returns:
      bool: True if the task with the given identifier is present in the heap.
    """
    return task_identifier in self._task_identifiers

  def PeekTask(self):
    """Retrieves the first task from the heap without removing it.

    Returns:
      Task: task or None if the heap is empty.
    """
    try:
      _, task = self._heap[0]

    except IndexError:
      return

    return task

  def PopTask(self):
    """Retrieves and removes the first task from the heap.

    Returns:
      Task: the task or None if the heap is empty.
    """
    try:
      _, task = heapq.heappop(self._heap)

    except IndexError:
      return
    self._task_identifiers.remove(task.identifier)
    return task

  def PushTask(self, task):
    """Pushes a task onto the heap.

    Args:
      task (Task): task.

    Raises:
      ValueError: if the size of the storage file is not set in the task.
    """
    storage_file_size = getattr(task, u'storage_file_size', None)
    if not storage_file_size:
      raise ValueError(u'Task storage file size not set')

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

  * abandoned: no status information has been recently received from a worker
      about the task, and is assumed to be abandoned.
  * queued: the task is waiting for a worker to start processing it. It's also
      possible that a worker has already completed the task, but no status
      update was collected from the worker while it processed the task.
  * processing: a worker is processing the task.
  * pending_merge: a worker has completed processing the task and the
      results are ready to be merged with the session storage.
  * merging: tasks that are being merged by the engine.

  Once the engine reports that a task is completely merged, it is removed
  from the task manager.

  Tasks that are not abandoned, or abandoned, but need to be retried are
  considered "pending", as there is more work that needs to be done to complete
  them.
  """

  # Consider a task inactive after 5 minutes of no activity.
  _TASK_INACTIVE_TIME = 5 * 60 * 1000000

  def __init__(self):
    """Initializes a task manager."""
    super(TaskManager, self).__init__()
    self._lock = threading.Lock()
    # This dictionary maps task identifiers to tasks that have been abandoned,
    # as no worker has reported processing the task in the expected interval.
    self._tasks_abandoned = {}
    self._tasks_pending_merge = _PendingMergeTaskHeap()
    # This dictionary maps task identifiers to tasks that are currently
    # being processed by a worker.
    self._tasks_processing = {}
    # Use ordered dictionary to preserve the order in which tasks were added.
    # This dictionary maps task identifiers to tasks that are waiting to be
    # processed.
    self._tasks_queued = collections.OrderedDict()
    # This dictionary maps task identifiers to tasks that are being merged
    # by the foreman.
    self._tasks_merging = {}

    # TODO: implement a limit on the number of tasks.
    self._total_number_of_tasks = 0

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
    with self._lock:
      self._tasks_queued[task.identifier] = task

    self._total_number_of_tasks += 1
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
        logging.debug(u'Task {0:s} is complete.'.format(task.identifier))

      if task.identifier in self._tasks_pending_merge:
        logging.debug(u'Task {0:s} completed while pending merge.'.format(
            task.identifier))
        return

      if task.identifier in self._tasks_processing:
        del self._tasks_processing[task.identifier]
        logging.debug(u'Task {0:s} completed from processing'.format(
            task.identifier))
        return

      if task.identifier in self._tasks_queued:
        del self._tasks_queued[task.identifier]
        logging.debug(u'Task {0:s} is completed from queued'.format(
            task.identifier))
        return

  def GetAbandonedTasks(self):
    """Retrieves all abandoned tasks.

    Returns:
      list[Task]: tasks.
    """
    with self._lock:
      abandoned_tasks = list(self._tasks_abandoned.values())
    return abandoned_tasks

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
      return

    if current_task and next_task.merge_priority > current_task.merge_priority:
      return

    with self._lock:
      next_task = self._tasks_pending_merge.PopTask()
    self._tasks_merging[next_task.identifier] = next_task
    return next_task

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

  def _TimeoutTasks(self, tasks_for_timeout):
    """Checks for inactive tasks, and marks such tasks as abandoned.

    Note that this method does not lock the manager, and should be called
    by a method holding the manager lock.

    Args:
      tasks_for_timeout (dict[str, Task]): mapping of task identifiers to Tasks
        that will be checked for inactivity, and marked as abandoned if
        required.
    """
    if not tasks_for_timeout:
      return
    inactive_time = int(time.time() * 1000000) - self._TASK_INACTIVE_TIME

    for task_identifier, task in iter(tasks_for_timeout.items()):
      last_active_time = task.last_processing_time
      if not last_active_time:
        last_active_time = task.start_time
      if last_active_time < inactive_time:
        logging.debug(u'Task {0:s} is abandoned'.format(task_identifier))
        self._tasks_abandoned[task_identifier] = task
        del tasks_for_timeout[task_identifier]

  def HasPendingTasks(self):
    """Determines if there are tasks running, or in need of retrying.

    Returns:
      bool: True if there are tasks that are active, ready to be merged, or
          need to be retried.
    """
    with self._lock:
      self._TimeoutTasks(self._tasks_processing)
      if self._tasks_processing:
        return True
      # There are no tasks being processed, but we might be
      # waiting for some tasks to be merged.
      if self._HasTasksPendingMerge():
        return True
      # There are no tasks processing, or pending merge, but there may
      # still be some waiting to be retried, so we check that.
      if self._HasTasksPendingRetry():
        return True
      # It's possible that a worker received a task and didn't report it.
      # Check for tasks that we believe are queued that might need to be marked
      # as abandoned, as all the workers are idle, and the task has been queued
      # for longer than the timeout.
      self._TimeoutTasks(self._tasks_queued)
      if self._tasks_queued:
        return True
      if self._tasks_merging:
        return True

    # There are no tasks pending any work.
    return False

  def _HasTasksPendingMerge(self):
    """Determines if there are tasks waiting to be merged.

    Note that this method does not lock the manager, and should be called
    by a method holding the manager lock.

    Returns:
      bool: True if there are abandoned tasks that need to be retried.
    """
    return bool(self._tasks_pending_merge)

  def _HasTasksPendingRetry(self):
    """Determines if there are abandoned tasks that still need to be retried.

    Note that this method does not lock the manager, and should be called
    by a method holding the manager lock.

    Returns:
      bool: True if there are abandoned tasks that need to be retried.
    """
    for abandoned_task in self._tasks_abandoned.values():
      if not abandoned_task.retried:
        return True

  def GetRetryTask(self):
    """Creates a task that is an attempt to retry an abandoned task.

    Returns:
      Task: a task that is a retry of an existing task, or None if there are
          no tasks that need to be retried.
    """
    with self._lock:
      for abandoned_task in self._tasks_abandoned.values():
        # Only retry abandoned tasks that are yet to be retried, and
        # aren't themselves retries of another task.
        if not (abandoned_task.retried or
                abandoned_task.original_task_identifier):
          retry_task = abandoned_task.CreateRetry()
          logging.debug(
              u'Retrying task {0:s} as {1:s}'.format(
                  abandoned_task.identifier, retry_task.identifier))
          self._tasks_queued[retry_task.identifier] = retry_task
          self._total_number_of_tasks += 1
          return retry_task

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
        raise KeyError(u'Status of task {0:s} is unknown'.format(
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
      logging.warning(
          u'Previously abandoned task {0:s} is now pending merge'.format(
              task.identifier))
    else:
      logging.debug(u'Task {0:s} is pending merge'.format(task.identifier))

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
        logging.debug(u'Task {0:s} was queued, now processing'.format(
            task_identifier))
        self._tasks_processing[task_identifier] = task_queued
        del self._tasks_queued[task_identifier]
        task_queued.UpdateProcessingTime()
        return

      task_abandoned = self._tasks_abandoned.get(task_identifier, None)
      if task_abandoned:
        del self._tasks_abandoned[task_identifier]
        self._tasks_processing[task_identifier] = task_abandoned
        logging.debug(u'Task {0:s} was abandoned, but now processing'.format(
            task_identifier))
        task_abandoned.UpdateProcessingTime()
        return

      if task_identifier in self._tasks_pending_merge:
        # No need to update the processing time, as this task is already
        # has already finished processing, and is just waiting for merge.
        return

    # If we get here, we don't know what state the tasks is in, so raise.
    raise KeyError(u'Status of task {0:s} is unknown'.format(task_identifier))
