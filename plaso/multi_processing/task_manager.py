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

  @property
  def number_of_items(self):
    """int: number of items in the heap."""
    return len(self._heap)

  def PopTask(self):
    """Pops a task from the heap.

    Returns:
      str: unique identifier of the task or None.
    """
    try:
      _, task_identifier = heapq.heappop(self._heap)

    except IndexError:
      return

    return task_identifier

  def PushTask(self, task):
    """Pushes a task onto the heap.

    Args:
      task (Task): task.
    """
    if task.file_entry_type == dfvfs_definitions.FILE_ENTRY_TYPE_DIRECTORY:
      weight = 1
    else:
      weight = 100

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

  def GetTaskPendingMerge(self):
    """Retrieves the first task that is pending merge.

    Returns:
      str: unique identifier of the task or None.
    """
    task_identifier = self._tasks_pending_merge.PopTask()
    if task_identifier:
      del self._active_tasks[task_identifier]

    return task_identifier

  def HasActiveTasks(self):
    """Determines if there are active tasks.

    A task will be abandoned if it last update exceeds the inactive time.

    Returns:
      bool: True if there are active tasks.
    """
    if self._tasks_pending_merge.number_of_items > 0:
      has_active_tasks = True
    else:
      has_active_tasks = False

    if not self._tasks_processing and not has_active_tasks:
      return False

    inactive_time = int(time.time() * 1000000) - self._TASK_INACTIVE_TIME

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

  def UpdateTaskAsPendingMerge(self, task_identifier):
    """Updates the task manager to reflect the task is ready to be merged.

    Args:
      task_identifier (str): unique identifier of the task.

    Raises:
      KeyError: if the task was not processing.
    """
    if task_identifier not in self._tasks_processing:
      raise KeyError(u'Task not processing')

    task = self._active_tasks[task_identifier]
    self._tasks_pending_merge.PushTask(task)
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
