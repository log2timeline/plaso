# -*- coding: utf-8 -*-
"""The task manager."""

import collections
import time

from plaso.containers import tasks


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
  * procesisng: a worker is processing the task.
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
    # Use ordered dictionaries to preserve the order in which tasks were added.
    self._tasks_pending_merge = collections.OrderedDict()
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
    if not self._tasks_pending_merge:
      return

    _, task_identifier = self._tasks_pending_merge.popitem(last=False)

    del self._active_tasks[task_identifier]
    return task_identifier

  def HasActiveTasks(self):
    """Determines if there are active tasks.

    A task will be abandoned if it last update exceeds the inactive time.

    Returns:
      bool: True if there are active tasks.
    """
    if not self._tasks_processing and not self._tasks_pending_merge:
      return False

    inactive_time = int(time.time() * 1000000) - self._TASK_INACTIVE_TIME

    if self._tasks_pending_merge:
      has_active_tasks = True
    else:
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

  def UpdateTaskAsPendingMerge(self, task_identifier):
    """Updates the task manager to reflect the task is ready to be merged.

    Args:
      task_identifier (str): unique identifier of the task.

    Raises:
      KeyError: if the task was not processing.
    """
    if task_identifier not in self._tasks_processing:
      raise KeyError(u'Task not processing')

    self._tasks_pending_merge[task_identifier] = task_identifier
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
