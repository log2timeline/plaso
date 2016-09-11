# -*- coding: utf-8 -*-
"""The task manager."""

import collections
import heapq
import time

from dfvfs.lib import definitions as dfvfs_definitions

from plaso.containers import tasks


class _PendingMergeTaskHeap(object):
  """Class that defines a pending merge task heap."""

  def __init__(self):
    """Initializes a pending merge task heap."""
    super(_PendingMergeTaskHeap, self).__init__()
    self._heap = []

  def PeekTask(self):
    """Retrieves the first task identifier from the heap without removing it.

    Returns:
      str: unique identifier of the task or None if the heap is empty.
    """
    try:
      _, task_identifier = self._heap[0]

    except IndexError:
      return

    return task_identifier

  def PopTask(self):
    """Retrieves and removes the first task identifier from the heap.

    Returns:
      str: unique identifier of the task or None if the heap is empty.
    """
    try:
      _, task_identifier = heapq.heappop(self._heap)

    except IndexError:
      return

    return task_identifier

  def PushTask(self, task, file_size):
    """Pushes a task onto the heap.

    Args:
      task (Task): task.
      file_size (int): size of the task storage file.
    """
    if task.file_entry_type == dfvfs_definitions.FILE_ENTRY_TYPE_DIRECTORY:
      weight = 1
    else:
      weight = file_size

    task.merge_weight = weight

    heap_values = (weight, task.identifier)
    heapq.heappush(self._heap, heap_values)


class TaskManager(object):
  """Class that manages tasks and tracks their completion and status.

  Currently a task can have the following status:
  * abandoned: since no status information has been recently received from
      the worker about the task, we assume it was abandoned.
  * active: a task managed by the task manager that has not been abandoned.
  * completed: a worker has completed processing the task and the results
      have been merged with the session storage.
  * pending_merge: a worker has completed processing the task and the results
      are ready to be merged with the session storage.
  * processing: a worker is processing the task.
  """

  # Consider a task inactive after 5 minutes of no activity.
  _TASK_INACTIVE_TIME = 5 * 60 * 1000000

  def __init__(self, maximum_number_of_tasks=0):
    """Initializes a task manager object.

    Args:
      maximum_number_of_tasks (Optional[int]): maximum number of concurrent
          tasks, where 0 represents no limit.
    """
    super(TaskManager, self).__init__()
    self._abandoned_tasks = {}
    self._active_tasks = {}
    self._maximum_number_of_tasks = maximum_number_of_tasks
    self._tasks_pending_merge = _PendingMergeTaskHeap()
    # Use ordered dictionaries to preserve the order in which tasks were added.
    self._tasks_processing = collections.OrderedDict()

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
    self._active_tasks[task.identifier] = task
    return task

  def CompleteTask(self, task_identifier):
    """Completes a task.

    The task is complete and can be removed from the task manager.

    Args:
      task_identifier (str): unique identifier of the task.

    Raises:
      KeyError: if the task was not active.
    """
    if task_identifier not in self._active_tasks:
      raise KeyError(u'Task not active')

    del self._active_tasks[task_identifier]

  def GetAbandonedTasks(self):
    """Retrieves all abandoned tasks.

    Returns:
      list[task]: task.
    """
    return self._abandoned_tasks.values()

  def GetTasksProcessing(self):
    """Retrieves the tasks that are processing.

    Returns:
      list[str]: unique identifiers of the tasks.
    """
    return self._tasks_processing.keys()

  def GetTaskPendingMerge(self, merge_task_identifier):
    """Retrieves the first task that is pending merge.

    This function will check if there is a task with a higher merge priority
    availble.

    Args:
      merge_task_identifier (str): unique identifier of the current task being
          merged or None.

    Returns:
      str: unique identifier of the task or None.
    """
    task_identifier = self._tasks_pending_merge.PeekTask()
    if not task_identifier:
      return

    if merge_task_identifier:
      task = self._active_tasks[task_identifier]
      merge_task = self._active_tasks[merge_task_identifier]

      if task.merge_weight > merge_task.merge_weight:
        return

    return self._tasks_pending_merge.PopTask()

  def HasActiveTasks(self):
    """Determines if there are active tasks.

    A task will be abandoned if it last update exceeds the inactive time.

    Returns:
      bool: True if there are active tasks.
    """
    if not self._active_tasks:
      return False

    inactive_time = int(time.time() * 1000000) - self._TASK_INACTIVE_TIME

    has_active_tasks = False
    for task_identifier, last_update in iter(self._tasks_processing.items()):
      if last_update > inactive_time:
        has_active_tasks = True
      else:
        del self._tasks_processing[task_identifier]
        task = self._active_tasks[task_identifier]
        self._abandoned_tasks[task_identifier] = task
        del self._active_tasks[task_identifier]

    return has_active_tasks

  def RescheduleTask(self, task_identifier):
    """Reschedules a previous abandoned task.

    Args:
      task_identifier (str): unique identifier of the task.

    Raises:
      KeyError: if the task was not abandoned.
    """
    if task_identifier not in self._abandoned_tasks:
      raise KeyError(u'Task not abandoned')

    task = self._abandoned_tasks[task_identifier]
    self._active_tasks[task_identifier] = task
    del self._abandoned_tasks[task_identifier]

    self._tasks_processing[task_identifier] = int(time.time() * 1000000)

  def UpdateTask(self, task_identifier):
    """Updates a task.

    Args:
      task_identifier (str): unique identifier of the task.

    Raises:
      KeyError: if the task is not processing.
    """
    if task_identifier not in self._tasks_processing:
      raise KeyError(u'Task not processing')

    self._tasks_processing[task_identifier] = int(time.time() * 1000000)

  def UpdateTaskAsPendingMerge(self, task_identifier, file_size):
    """Updates the task manager to reflect the task is ready to be merged.

    Args:
      task_identifier (str): unique identifier of the task.
      file_size (int): file size of the task storage file.

    Raises:
      KeyError: if the task was not processing.
    """
    if task_identifier not in self._tasks_processing:
      raise KeyError(u'Task not processing')

    task = self._active_tasks[task_identifier]
    self._tasks_pending_merge.PushTask(task, file_size)
    del self._tasks_processing[task_identifier]

  def UpdateTaskAsProcessing(self, task_identifier):
    """Updates the task manager to reflect the task is processing.

    Args:
      task_identifier (str): unique identifier of the task.

    Raises:
      KeyError: if the task is already processing.
    """
    if task_identifier in self._tasks_processing:
      raise KeyError(u'Task already processing')

    # TODO: add check for maximum_number_of_tasks.
    self._tasks_processing[task_identifier] = int(time.time() * 1000000)
